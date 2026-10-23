#include "PluginProcessor.h"
#include "PluginEditor.h"

#include "DSP/FactoryVoices.h"

#include <algorithm>
#include <cmath>

namespace
{
using press78::kPluginControls;

constexpr int kStateVersion = 1;

press78::Patch programPatch (int program) noexcept
{
    return program <= 0 ? press78::initPatch() : press78::factoryPatch (static_cast<unsigned> (program - 1));
}
} // namespace

Press78AudioProcessor::Press78AudioProcessor()
    : AudioProcessor (BusesProperties().withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      parameters (*this, nullptr, "Press78", createLayout()),
      engine (std::make_unique<press78::Press78Engine>())
{
    for (std::size_t i = 0; i < kPluginControls.size(); ++i)
        raw[i] = parameters.getRawParameterValue (juce::String (kPluginControls[i].id.data(),
                                                                kPluginControls[i].id.size()));
}

juce::AudioProcessorValueTreeState::ParameterLayout Press78AudioProcessor::createLayout()
{
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    for (const auto& c : kPluginControls)
    {
        const juce::ParameterID id { juce::String (c.id.data(), c.id.size()), 1 };
        const juce::String label (c.label.data(), c.label.size());
        if (! c.options.empty())
        {
            const auto names = juce::StringArray::fromTokens (juce::String (c.options.data(), c.options.size()), "|", {});
            layout.add (std::make_unique<juce::AudioParameterChoice> (id, label, names, static_cast<int> (c.defaultValue)));
        }
        else if (c.integer && c.minimum == 0.0 && c.maximum == 1.0)
            layout.add (std::make_unique<juce::AudioParameterBool> (id, label, c.defaultValue >= 0.5));
        else if (c.integer)
        {
            auto attributes = juce::AudioParameterIntAttributes();
            // Power reads as the batteries' percentage up to its top step, the adaptor.
            if (c.id == "power")
                attributes = attributes.withStringFromValueFunction ([] (int v, int) { return v > 100 ? juce::String ("AC") : juce::String (v) + " %"; })
                                       .withValueFromStringFunction ([] (const juce::String& text) { return text.trim().equalsIgnoreCase ("AC") ? 101 : text.getIntValue(); });
            layout.add (std::make_unique<juce::AudioParameterInt> (id, label, static_cast<int> (c.minimum),
                                                                   static_cast<int> (c.maximum),
                                                                   static_cast<int> (c.defaultValue), attributes));
        }
        else
        {
            juce::NormalisableRange<float> range (static_cast<float> (c.minimum), static_cast<float> (c.maximum));
            // The tone filter spans 1-20 kHz; a linear knob would spend most of its travel above 10 kHz.
            if (c.id == "toneCutoffHz")
                range.setSkewForCentre (4000.0f);
            layout.add (std::make_unique<juce::AudioParameterFloat> (id, label, range, static_cast<float> (c.defaultValue)));
        }
    }
    return layout;
}

bool Press78AudioProcessor::isBusesLayoutSupported (const BusesLayout& layouts) const
{
    return layouts.getMainOutputChannelSet() == juce::AudioChannelSet::stereo();
}

void Press78AudioProcessor::prepareToPlay (double sampleRate, int)
{
    engine->prepare (sampleRate);
    appliedValid = false;
    applyValues (readValues());
    setLatencySamples (engine->latencySamples());
}

Press78AudioProcessor::Values Press78AudioProcessor::readValues() const noexcept
{
    Values v {};
    for (std::size_t i = 0; i < raw.size(); ++i)
        v[i] = raw[i]->load (std::memory_order_relaxed);
    return v;
}

void Press78AudioProcessor::applyValues (const Values& v) noexcept
{
    if (! appliedValid || ! std::equal (v.begin(), v.begin() + press78::kFirstNonPatchControl, applied.begin()))
        engine->setPatch (press78::patchFromValues (v), true); // retimbre held voices, as the Rack does
    engine->setControls (press78::controlsFromValues (v, bend, wheel, portamentoSwitch));
    applied = v;
    appliedValid = true;
}

bool Press78AudioProcessor::handleMidi (const juce::MidiMessage& m) noexcept
{
    if (m.isNoteOn())
        engine->noteOn (m.getNoteNumber(), m.getVelocity());
    else if (m.isNoteOff())
        engine->noteOff (m.getNoteNumber());
    else if (m.isSustainPedalOn() || m.isSustainPedalOff())
        engine->sustainController (m.getControllerValue()); // Original reads any nonzero value
    else if (m.isAllSoundOff())
        engine->allSoundOff();
    else if (m.isAllNotesOff())
        engine->allNotesOff();
    else if (m.isController() && m.getControllerNumber() == 121) // Reset All Controllers
    {
        engine->sustainPedal (false);
        bend = press78::kBendCentre;
        wheel = 0.0;
        portamentoSwitch = -1;
        return true;
    }
    else if (m.isController() && m.getControllerNumber() == 65)
    {
        portamentoSwitch = m.getControllerValue();
        return true;
    }
    else if (m.isPitchWheel())
    {
        bend = m.getPitchWheelValue();
        return true;
    }
    else if (m.isController() && m.getControllerNumber() == 1)
    {
        wheel = m.getControllerValue() / 127.0;
        return true;
    }
    return false;
}

void Press78AudioProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midi)
{
    juce::ScopedNoDenormals noDenormals;
    const int frames = buffer.getNumSamples();
    auto* left = buffer.getWritePointer (0);
    auto* right = buffer.getWritePointer (1);

    const auto values = readValues();
    if (! appliedValid || values != applied)
        applyValues (values);

    // Events start at their own sample; controls are applied per segment.
    int position = 0;
    for (const auto metadata : midi)
    {
        const int at = std::clamp (metadata.samplePosition, position, frames);
        if (at > position)
            engine->process (left + position, right + position, static_cast<std::size_t> (at - position));
        position = at;
        if (handleMidi (metadata.getMessage()))
            applyValues (values);
    }
    if (frames > position)
        engine->process (left + position, right + position, static_cast<std::size_t> (frames - position));
}

void Press78AudioProcessor::setCurrentProgram (int index)
{
    if (index < 0 || index >= kProgramCount)
        return;
    currentProgram = index;
    Values v = readValues();
    press78::writePatchValues (programPatch (index), v);
    // A program sets the sound; performance and output settings stay as they are.
    for (std::size_t i = 0; i < press78::kFirstNonPatchControl; ++i)
    {
        auto* parameter = parameters.getParameter (juce::String (kPluginControls[i].id.data(), kPluginControls[i].id.size()));
        parameter->setValueNotifyingHost (parameter->convertTo0to1 (static_cast<float> (v[i])));
    }
}

const juce::String Press78AudioProcessor::getProgramName (int index)
{
    if (index == 0)
        return "Init";
    if (index > 0 && index < kProgramCount)
        return press78::kFactoryVoices[static_cast<std::size_t> (index - 1)].name;
    return {};
}

void Press78AudioProcessor::getStateInformation (juce::MemoryBlock& destData)
{
    auto state = parameters.copyState();
    state.setProperty ("stateVersion", kStateVersion, nullptr);
    state.setProperty ("program", currentProgram.load(), nullptr);
    if (auto xml = state.createXml())
        copyXmlToBinary (*xml, destData);
}

void Press78AudioProcessor::setStateInformation (const void* data, int sizeInBytes)
{
    auto xml = getXmlFromBinary (data, sizeInBytes);
    if (xml == nullptr || ! xml->hasTagName (parameters.state.getType()))
        return;
    auto state = juce::ValueTree::fromXml (*xml);
    currentProgram = std::clamp (static_cast<int> (state.getProperty ("program", 0)), 0, kProgramCount - 1);
    // 0.1.12 chose the adaptor on the Power switch; it is now Power's AC step.
    if (auto supply = state.getChildWithProperty ("id", "powerSupply"); static_cast<int> (supply.getProperty ("value", 0)) == 2)
    {
        supply.setProperty ("value", 1, nullptr);
        auto power = state.getChildWithProperty ("id", "power");
        if (! power.isValid())
        {
            power = juce::ValueTree (supply.getType());
            power.setProperty ("id", "power", nullptr);
            state.appendChild (power, nullptr);
        }
        power.setProperty ("value", 101, nullptr);
    }
    parameters.replaceState (state);
}

juce::AudioProcessorEditor* Press78AudioProcessor::createEditor()
{
    return new Press78AudioProcessorEditor (*this);
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new Press78AudioProcessor();
}
