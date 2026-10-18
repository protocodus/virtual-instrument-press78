// Processor contracts: parameter IDs, programs, state, MIDI rendering and the
// editor. PRESS78_EDITOR_SNAPSHOT=<file.png> also writes the editor screenshot
// the render tier checks and the main build commits.

#include "PluginEditor.h"
#include "PluginProcessor.h"

#include "DSP/FactoryVoices.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <set>
#include <vector>

namespace
{
int failures = 0;

void check (bool condition, const juce::String& what)
{
    if (! condition)
    {
        ++failures;
        std::fprintf (stderr, "FAIL %s\n", what.toRawUTF8());
    }
}

float value (Press78AudioProcessor& p, const char* id)
{
    auto* parameter = p.state().getParameter (id);
    return parameter->convertFrom0to1 (parameter->getValue());
}

void setValue (Press78AudioProcessor& p, const char* id, float v)
{
    auto* parameter = p.state().getParameter (id);
    parameter->setValueNotifyingHost (parameter->convertTo0to1 (v));
}

// Plays a two-note phrase with a bend and wheel move, `block` frames at a time.
std::vector<float> render (Press78AudioProcessor& p, int block, double rate = 48000.0)
{
    constexpr int total = 24000;
    p.setRateAndBufferSizeDetails (rate, block);
    p.prepareToPlay (rate, block);
    std::vector<std::pair<int, juce::MidiMessage>> events {
        { 0, juce::MidiMessage::noteOn (1, 60, (juce::uint8) 100) },
        { 3001, juce::MidiMessage::noteOn (1, 67, (juce::uint8) 127) },
        { 6007, juce::MidiMessage::pitchWheel (1, 12000) },
        { 9011, juce::MidiMessage::controllerEvent (1, 1, 90) },
        { 15013, juce::MidiMessage::noteOff (1, 60) },
        { 15013, juce::MidiMessage::noteOff (1, 67) },
    };
    std::vector<float> out;
    juce::AudioBuffer<float> buffer (2, block);
    for (int start = 0; start < total; start += block)
    {
        const int frames = std::min (block, total - start);
        buffer.setSize (2, frames, false, false, true);
        buffer.clear();
        juce::MidiBuffer midi;
        for (const auto& [at, message] : events)
            if (at >= start && at < start + frames)
                midi.addEvent (message, at - start);
        p.processBlock (buffer, midi);
        for (int i = 0; i < frames; ++i)
        {
            out.push_back (buffer.getSample (0, i));
            out.push_back (buffer.getSample (1, i));
        }
    }
    return out;
}

void parameterContract()
{
    Press78AudioProcessor p;
    const auto& parameters = p.getParameters();
    check (parameters.size() == static_cast<int> (press78::kPluginControls.size()), "one parameter per control");
    for (int i = 0; i < parameters.size(); ++i)
    {
        const auto& control = press78::kPluginControls[static_cast<std::size_t> (i)];
        auto* ranged = dynamic_cast<juce::RangedAudioParameter*> (parameters[i]);
        const juce::String id (control.id.data(), control.id.size());
        check (ranged != nullptr && ranged->paramID == id, "parameter " + juce::String (i) + " is " + id);
        if (ranged == nullptr)
            continue;
        check (ranged->getVersionHint() == 1, id + " keeps version hint 1");
        // JUCE stores the default normalised in a float, so a skewed range
        // (Tone cutoff, 1-20 kHz) returns it within float precision of its
        // plain value, not within a fixed absolute step.
        const auto matches = [] (double plain, double expected)
        { return std::abs (plain - expected) <= 1.0e-5 * std::max (1.0, std::abs (expected)); };
        check (matches (ranged->convertFrom0to1 (ranged->getDefaultValue()), control.defaultValue),
               id + " default matches Assets/controls.json");
        check (matches (ranged->convertFrom0to1 (0.0f), control.minimum)
                   && matches (ranged->convertFrom0to1 (1.0f), control.maximum),
               id + " range matches Assets/controls.json");
    }
}

void programContract()
{
    Press78AudioProcessor p;
    check (p.getNumPrograms() == 101 && p.getProgramName (0) == "Init", "Init then 100 factory programs");
    for (int program = 1; program < p.getNumPrograms(); ++program)
    {
        p.setCurrentProgram (program);
        const auto& voice = press78::kFactoryVoices[static_cast<std::size_t> (program - 1)];
        const auto patch = press78::sanitizePatch (press78::decodeVoice (voice.bytes));
        check (p.getProgramName (program) == voice.name, "program " + juce::String (program) + " name");
        // Independent of the processor's own mapping: each control by name.
        const std::pair<const char*, const press78::Operator*> operators[] { { "mod_", &patch.modulator },
                                                                             { "car_", &patch.carrier } };
        for (const auto& [prefix, op] : operators)
        {
            const std::pair<const char*, int> fields[] {
                { "mul", op->mul }, { "dt1", op->dt1 }, { "tl", op->tl }, { "wave", op->wave }, { "ar", op->ar },
                { "d1r", op->d1r }, { "d1l", op->d1l }, { "d2r", op->d2r }, { "rr", op->rr }, { "srr", op->srr },
                { "lksHi", op->lksHi }, { "lksLo", op->lksLo }, { "rks", op->rks },
                { "amEnable", op->amEnable ? 1 : 0 }, { "dt2", op->dt2 ? 1 : 0 } };
            for (const auto& [field, expected] : fields)
            {
                const auto id = juce::String (prefix) + field;
                check (value (p, id.toRawUTF8()) == static_cast<float> (expected),
                       voice.name + juce::String (" ") + id);
            }
        }
        check (value (p, "feedback") == patch.feedback && value (p, "pms") == patch.pms
                   && value (p, "ams") == patch.ams && value (p, "vibratoDelay") == patch.vibratoDelay
                   && value (p, "vibrato") == (patch.vibrato ? 1.0f : 0.0f)
                   && value (p, "sustain") == (patch.sustain ? 1.0f : 0.0f),
               voice.name + juce::String (" voice-level fields"));
    }
    // A program sets the sound, never the output settings.
    setValue (p, "masterGain", 1.5f);
    p.setCurrentProgram (5);
    check (value (p, "masterGain") == 1.5f, "program change keeps Volume");
}

void stateContract()
{
    Press78AudioProcessor a;
    a.setCurrentProgram (42);
    setValue (a, "car_tl", 17.0f);
    setValue (a, "chorusMode", 0.0f);
    setValue (a, "toneCutoffHz", 5000.0f);
    juce::MemoryBlock saved;
    a.getStateInformation (saved);

    Press78AudioProcessor b;
    b.setStateInformation (saved.getData(), static_cast<int> (saved.getSize()));
    check (b.getCurrentProgram() == 42, "state restores the program");
    for (auto* parameter : a.getParameters())
    {
        auto* ranged = dynamic_cast<juce::RangedAudioParameter*> (parameter);
        check (b.state().getParameter (ranged->paramID)->getValue() == ranged->getValue(),
               "state restores " + ranged->paramID);
    }
    const char garbage[] = "not a Press78 state";
    b.setStateInformation (garbage, sizeof garbage);
    check (b.getCurrentProgram() == 42, "foreign state is ignored");
}

void renderContract()
{
    Press78AudioProcessor whole, pieces;
    whole.setCurrentProgram (1);
    pieces.setCurrentProgram (1);
    const auto a = render (whole, 512), b = render (pieces, 64);
    float peak = 0.0f;
    bool finite = true;
    for (float x : a)
    {
        finite = finite && std::isfinite (x);
        peak = std::max (peak, std::abs (x));
    }
    check (finite && peak > 1.0e-3f && peak <= 1.0f, "a factory voice plays finite, audible and protected");
    check (a == b, "512- and 64-frame blocks render identical samples");
    check (whole.getLatencySamples() >= 0, "latency is reported");
}

void editorContract()
{
    Press78AudioProcessor p;
    std::unique_ptr<juce::AudioProcessorEditor> editor (p.createEditor());
    std::set<juce::String> shown;
    for (auto* child : editor->getChildren())
        if (auto* tooltip = dynamic_cast<juce::SettableTooltipClient*> (child); tooltip && tooltip->getTooltip().isNotEmpty())
            check (shown.insert (tooltip->getTooltip()).second, "one editor control per parameter");
    for (auto* parameter : p.getParameters())
        check (shown.count (parameter->getName (64)) == 1, "the editor shows " + parameter->getName (64));

    const auto image = editor->createComponentSnapshot (editor->getLocalBounds(), true, 1.0f);
    check (image.getPixelAt (4, 4).getAlpha() == 255, "the editor paints an opaque panel");

    // The main build asks for the committed screenshot through this variable,
    // so the README image tracks the real editor.
    const auto path = juce::SystemStats::getEnvironmentVariable ("PRESS78_EDITOR_SNAPSHOT", {});
    if (path.isNotEmpty())
    {
        const juce::File file (path);
        file.getParentDirectory().createDirectory();
        file.deleteFile();
        juce::FileOutputStream output (file);
        juce::PNGImageFormat png;
        check (output.openedOk() && png.writeImageToStream (image, output), "write the editor snapshot");
    }
}
} // namespace

int main()
{
    juce::ScopedJuceInitialiser_GUI juce;
    parameterContract();
    programContract();
    stateContract();
    renderContract();
    editorContract();
    std::printf ("Press78 processor contracts: %d failure(s)\n", failures);
    return failures == 0 ? 0 : 1;
}
