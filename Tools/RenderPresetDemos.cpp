// Renders the README's voice demos (README G3), one for each committed phrase
// in Docs/audio/midi, through the same JUCE-free engine and control
// mapping the plug-in uses. The contract and the fixed rate, block size and
// seed live in the shared PresetDemoRenderer.h.

#include "ControlMapping.h"
#include "DSP/FactoryVoices.h"
#include "PresetDemoRenderer.h"

#include <memory>
#include <stdexcept>
#include <string>

namespace
{
// Each demo plays its voice with the plug-in's default controls (the Real
// startup profile), as a session that loads the program and plays it would.
class Press78Voice final : public protocodus::demos::Voice
{
public:
    Press78Voice (const press78::Patch& patch, double sampleRate)
        : engine (std::make_unique<press78::Press78Engine>()), values (press78::defaultControlValues())
    {
        press78::writePatchValues (patch, values);
        engine->prepare (sampleRate);
        engine->setPatch (press78::patchFromValues (values));
        engine->setControls (press78::controlsFromValues (values, bend, wheel));
    }

    // The messages the plug-in handles; anything else a phrase sends is an
    // error, not a silently dropped event.
    void Midi (const std::uint8_t* bytes, int size) override
    {
        const int kind = bytes[0] & 0xf0;
        const int data1 = size > 1 ? bytes[1] : 0, data2 = size > 2 ? bytes[2] : 0;
        if (kind == 0x80 || (kind == 0x90 && data2 == 0)) engine->noteOff (data1);
        else if (kind == 0x90) engine->noteOn (data1, data2);
        else if (kind == 0xb0 && data1 == 64) engine->sustainController (data2);
        else if (kind == 0xe0 || (kind == 0xb0 && data1 == 1))
        {
            if (kind == 0xe0) bend = (data2 << 7) | data1;
            else wheel = data2 / 127.0;
            engine->setControls (press78::controlsFromValues (values, bend, wheel));
        }
        else throw std::runtime_error ("unsupported MIDI message " + std::to_string (bytes[0])
                                       + " " + std::to_string (data1));
    }

    void Render (float* left, float* right, int frames) override
    {
        engine->process (left, right, static_cast<std::size_t> (frames));
    }

private:
    std::unique_ptr<press78::Press78Engine> engine;
    press78::ControlValues values;
    int bend = press78::kBendCentre;
    double wheel = 0.0;
};
} // namespace

int main (int argc, char** argv)
{
    protocodus::demos::Instrument instrument;
    instrument.name = "Press78";
    // Output protection bounds every sample to +/-1 at the default settings.
    instrument.ceiling = 1.0f;
    for (const auto& voice : press78::kFactoryVoices)
        instrument.presets.push_back (voice.name);
    instrument.open = [] (std::size_t preset, double sampleRate, int, std::uint32_t)
    {
        // The engine's noise and clock-drift sources start from fixed states
        // in prepare(), so the renderer's seed has nothing further to set.
        return std::make_unique<Press78Voice> (press78::factoryPatch (static_cast<unsigned> (preset)), sampleRate);
    };
    return protocodus::demos::Main (argc, argv, instrument);
}
