// CPU and output-parity harness for engine optimisations.
//
// Measurement protocol (Docs/benchmarks/cpu-exact-shortcuts-2026-10-25.md):
//
// 1. Build the engine as the Rack compiles it, as nearly as a host without the
//    Jukebox SDK allows: clang, C++17, -O3 -fno-builtin, no fast-math, no FMA
//    (the engine has no embedded define). From the repository root:
//      clang++ -std=c++17 -O3 -fno-builtin -DNDEBUG -ISource -ISource/DSP \
//        Tools/CpuParityBench.cpp Source/DSP/Press78Engine.cpp -o press78_cpu_bench_rack
//    The host build is the CMake target press78_cpu_bench (Release, -O3).
// 2. Render the fixed regression stream: the committed demo phrase
//    Docs/audio/midi/<NNN>-<slug>.mid of each selected factory voice, at
//    48 kHz in 64-frame blocks (the Rack's batch), each MIDI event split onto
//    its own sample, every voice from a fresh engine, the first --seconds of
//    the phrase. --profile plugin uses the plug-in's default controls (the
//    Real startup profile, YM3420 chip rate, recorded chorus, AUX, batteries);
//    --profile rack applies the Reason adapter's overrides on top of them
//    (legacy chip rate, Circuit saturation off at +12 dB headroom, 25 % power).
// 3. --out writes every voice's interleaved float32 output, in voice order, to
//    one file. Parity is byte equality of that file against the baseline's
//    (cmp); a residual report is only needed if it differs.
// 4. Count instructions with valgrind --tool=callgrind on the same command
//    and report the total Ir. The counts are reproducible on a shared machine
//    where wall-clock timings are not; any timing is a development-machine
//    figure, never a Reason-host result.
//
// Usage: press78_cpu_bench [--profile plugin|rack] [--seconds S]
//            [--presets 0,12,...] [--midi DIR] [--out FILE]

#include "ControlMapping.h"
#include "DSP/FactoryVoices.h"
#include "PresetDemoRenderer.h"

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

namespace {
constexpr int kBlock = 64;
constexpr double kRate = 48000.0;

struct Options {
    bool rack = false;
    double seconds = 6.0;
    std::vector<int> presets{0, 12, 13, 22, 30, 53, 59, 77, 84, 92};
    std::string midi = "Docs/audio/midi";
    std::string out;
};

press78::Controls profileControls(const Options& o, const press78::ControlValues& values, int bend, double wheel) {
    auto c = press78::controlsFromValues(values, bend, wheel);
    if (o.rack) {
        // The Reason adapter's fixed overrides (Examples/Press78/Press78.cpp).
        c.portamento = false; c.portamentoSpeed = 3; c.velocityCurve = 0;
        c.keyLevelModel = 0; c.allocationModel = 0; c.chorusCircuit = 0; c.chipRate = 0;
        c.circuitHeadroom = 3.9810717055349722; c.circuitSaturation = false;
        c.envelopeReverb = true; c.power = 25;
        c.outputCircuit = true; c.dcBlock = true; c.outputLimit = true;
    }
    return c;
}
} // namespace

int main(int argc, char** argv) {
    Options o;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        const auto next = [&]() -> std::string { if (i + 1 >= argc) std::exit(2); return argv[++i]; };
        if (arg == "--profile") { const auto v = next(); if (v == "rack") o.rack = true; else if (v != "plugin") return 2; }
        else if (arg == "--seconds") o.seconds = std::stod(next());
        else if (arg == "--midi") o.midi = next();
        else if (arg == "--out") o.out = next();
        else if (arg == "--presets") {
            o.presets.clear();
            std::stringstream list(next());
            for (std::string item; std::getline(list, item, ',');) o.presets.push_back(std::stoi(item));
        } else return 2;
    }
    protocodus::demos::Instrument names;
    for (const auto& voice : press78::kFactoryVoices) names.presets.push_back(voice.name);
    std::FILE* out = o.out.empty() ? nullptr : std::fopen(o.out.c_str(), "wb");
    if (!o.out.empty() && !out) return 3;
    std::vector<float> interleaved(2 * kBlock);
    for (const int preset : o.presets) {
        const auto stem = protocodus::demos::detail::Stem(names, static_cast<std::size_t>(preset));
        const auto events = protocodus::demos::ReadMidi(o.midi + "/" + stem + ".mid");
        auto engine = std::make_unique<press78::Press78Engine>();
        auto values = press78::defaultControlValues();
        press78::writePatchValues(press78::factoryPatch(static_cast<unsigned>(preset)), values);
        int bend = press78::kBendCentre;
        double wheel = 0.0;
        engine->prepare(kRate);
        engine->setPatch(press78::patchFromValues(values));
        engine->setControls(profileControls(o, values, bend, wheel));
        const auto frames = static_cast<std::size_t>(o.seconds * kRate);
        const auto due = [&](std::size_t k) { return static_cast<std::size_t>(std::llround(events[k].seconds * kRate)); };
        std::size_t next = 0, done = 0;
        std::uint64_t hash = 1469598103934665603ull;
        float left[kBlock], right[kBlock];
        while (done < frames) {
            const std::size_t blockStart = done, blockEnd = std::min(frames, done + kBlock);
            while (done < blockEnd) {
                while (next < events.size() && due(next) <= done) {
                    const auto* b = events[next].bytes;
                    const int kind = b[0] & 0xf0, d1 = b[1], d2 = b[2];
                    if (kind == 0x80 || (kind == 0x90 && d2 == 0)) engine->noteOff(d1);
                    else if (kind == 0x90) engine->noteOn(d1, d2);
                    else if (kind == 0xb0 && d1 == 64) engine->sustainController(d2);
                    else if (kind == 0xe0 || (kind == 0xb0 && d1 == 1)) {
                        if (kind == 0xe0) bend = (d2 << 7) | d1; else wheel = d2 / 127.0;
                        engine->setControls(profileControls(o, values, bend, wheel));
                    }
                    ++next;
                }
                const std::size_t until = next < events.size() ? std::min(blockEnd, due(next)) : blockEnd;
                engine->process(left + (done - blockStart), right + (done - blockStart), until - done);
                done = until;
            }
            const std::size_t n = blockEnd - blockStart;
            for (std::size_t k = 0; k < n; ++k) { interleaved[2 * k] = left[k]; interleaved[2 * k + 1] = right[k]; }
            const auto* bytes = reinterpret_cast<const unsigned char*>(interleaved.data());
            for (std::size_t k = 0; k < 2 * n * sizeof(float); ++k) hash = (hash ^ bytes[k]) * 1099511628211ull;
            if (out) std::fwrite(interleaved.data(), sizeof(float), 2 * n, out);
        }
        std::printf("%s %016llx\n", stem.c_str(), static_cast<unsigned long long>(hash));
    }
    if (out) std::fclose(out);
    return 0;
}
