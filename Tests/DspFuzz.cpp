// U4 input fuzzing of the JUCE-free engine through the shared portfolio
// harness (Tests/FuzzHarness.h is a byte-identical copy of the master; change
// it in reason-rack-extensions). Every input starts from a fresh engine, so a
// saved crash replays alone; commands and rendered frames are bounded
// whatever the input length.
//
// Voices arrive the way an import does: 33 raw bytes through decodeVoice, or
// fields set directly to any integer, which sanitizePatch must then bound.
#include "DSP/FactoryVoices.h"
#include "DSP/Press78Engine.h"
#include "FuzzHarness.h"

#include <memory>

extern "C" int LLVMFuzzerTestOneInput (const std::uint8_t* data, std::size_t size)
{
    using namespace protocodus::fuzz;
    Input input { data, size };

    auto engine = std::make_unique<press78::Press78Engine>();
    engine->prepare (input.Rate());
    press78::Patch patch = press78::factoryPatch (static_cast<unsigned> (input.Pick (press78::kFactoryVoices.size())));
    press78::Controls controls;
    engine->setPatch (patch);

    const auto anyInt = [&] { return static_cast<int> (input.Word()); };
    const auto anyDouble = [&] { return static_cast<double> (input.Scalar()) * (input.Byte() & 1 ? 1.0e5 : 1.0); };

    constexpr std::size_t maxFrames = 512;
    Sentinels<maxFrames> block;
    for (int command = 0; command < 64 && ! input.Empty(); ++command)
    {
        switch (input.Pick (10))
        {
            case 0: engine->noteOn (anyInt() % 300, anyInt() % 300, input.Byte() & 1); break;
            case 1: engine->noteOff (anyInt() % 300, input.Byte() & 1); break;
            case 2: engine->sustainPedal (input.Byte() & 1); break;
            case 3:
            {
                std::array<std::uint8_t, 33> bytes {};
                for (auto& b : bytes) b = input.Byte();
                patch = press78::decodeVoice (bytes);
                engine->setPatch (patch, input.Byte() & 1);
                break;
            }
            case 4:
            {
                auto& op = input.Byte() & 1 ? patch.carrier : patch.modulator;
                for (int* field : { &op.mul, &op.dt1, &op.tl, &op.lksHi, &op.lksLo, &op.rks, &op.ar, &op.d1r,
                                    &op.d2r, &op.d1l, &op.rr, &op.srr, &op.wave })
                    if (input.Byte() & 1) *field = anyInt();
                op.amEnable = input.Byte() & 1;
                op.dt2 = input.Byte() & 1;
                for (int* field : { &patch.feedback, &patch.pms, &patch.ams, &patch.vibratoDelay })
                    if (input.Byte() & 1) *field = anyInt();
                engine->setPatch (patch, input.Byte() & 1);
                break;
            }
            case 5:
            {
                for (double* field : { &controls.masterGain, &controls.pitchBendSemitones, &controls.masterTuneCents,
                                       &controls.velocitySensitivity, &controls.velocityToModulation,
                                       &controls.modulationAmount, &controls.lfoRateHz, &controls.vibratoDepth,
                                       &controls.tremoloDepth, &controls.lfoDelayScale, &controls.clockOffsetPpm,
                                       &controls.clockDriftPpm, &controls.clockDriftRateHz, &controls.toneCutoffHz,
                                       &controls.drive, &controls.chorusMix, &controls.chorusRateHz,
                                       &controls.chorusDepthMs, &controls.stereoWidth, &controls.noiseRms })
                    if (input.Byte() & 1) *field = anyDouble();
                for (int* field : { &controls.polyphony, &controls.chorusMode, &controls.noiseModel })
                    if (input.Byte() & 1) *field = anyInt();
                for (bool* field : { &controls.triangleLfo, &controls.globalLfo, &controls.outputCircuit,
                                     &controls.dcBlock, &controls.outputLimit })
                    *field = input.Byte() & 1;
                engine->setControls (controls);
                break;
            }
            case 6: engine->setChorusTime (anyDouble()); break;
            case 7:
                switch (input.Pick (4))
                {
                    case 0: engine->allNotesOff(); break;
                    case 1: engine->allSoundOff(); break;
                    case 2: engine->reset(); break;
                    default: engine->prepare (input.Rate()); break;
                }
                break;
            default:
                patch = press78::factoryPatch (static_cast<unsigned> (input.Pick (press78::kFactoryVoices.size())));
                engine->setPatch (patch);
                break;
        }
        const std::size_t frames = 1 + input.Word() % maxFrames;
        block.Arm();
        engine->process (block.Left(), block.Right(), frames);
        block.Check (frames);
    }
    return 0;
}
