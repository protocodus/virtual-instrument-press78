#include "Press78Engine.h"
#include "RecordedChorusProfile.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <memory>
#include <vector>
#include <string>

// Native wall-clock workload evidence only. This excludes the Rack wrapper,
// target translation and Reason scheduling. Never a hard realtime guarantee.
int main(int argc, char** argv) {
    const bool realOnly = argc == 2 && std::string(argv[1]) == "--real-only";
    if (argc > 1 && !realOnly) return 2;
    using Clock = std::chrono::steady_clock;
    std::cout << std::setprecision(10)
              << "{\"scope\":\"native engine wall time; excludes Reason host and target translation\",\"block_frames\":64,\"rows\":[";
    bool first = true;
    for (const int sr : {48000, 96000}) for (int mode = realOnly ? 5 : 0; mode < (realOnly ? 8 : 4); ++mode) {
        auto e = std::make_unique<press78::Press78Engine>();
        e->prepare(sr);
        auto p = press78::initPatch();
        press78::Controls c;
        const int voices = mode == 7 ? 0 : (mode == 0 || mode == 6) ? 1 : 12;
        if (mode > 0 && mode != 6) {
            p.modulator.tl = 24; p.modulator.mul = 3; p.feedback = 7;
            p.modulator.amEnable = p.carrier.amEnable = true;
            p.ams = 3; p.pms = 7; p.vibrato = true;
        }
        if (mode >= 2) {
            c.clockOffsetPpm = 5000; c.clockDriftPpm = 2000;
            c.chorusMix = 0.8; c.chorusDepthMs = 4; c.drive = 0.2;
        }
        if (mode >= 3) { c.chorusMode=1; c.chorusRateHz=press78::RecordedChorusProfile::rateHz; c.chorusDepthMs=press78::RecordedChorusProfile::depthMs; }
        if (mode >= 5) {
            // Current Rack Real profile; no additive noise.
            c.clockOffsetPpm=0; c.clockDriftPpm=20; c.clockDriftRateHz=.1;
            c.outputCircuit=true; c.chorusMode=1; c.chorusMix=1;
            c.chorusRateHz=press78::RecordedChorusProfile::rateHz;
            c.chorusDepthMs=press78::RecordedChorusProfile::depthMs;
            c.drive=0;
        }
        e->setPatch(p); e->setControls(c);
        for (int v = 0; v < voices; ++v) e->noteOn(48 + v, 100);
        std::array<float, 64> left{}, right{};
        const int blocks = 3 * sr / 64;
        std::vector<double> times; times.reserve(static_cast<std::size_t>(blocks));
        double peak = 0;
        int misses = 0;
        const double deadline = 64.0 / sr * 1e6;
        const auto begin = Clock::now();
        for (int b = 0; b < blocks; ++b) {
            const auto a = Clock::now();
            e->process(left.data(), right.data(), 64);
            const auto z = Clock::now();
            const double micros = std::chrono::duration<double, std::micro>(z - a).count();
            times.push_back(micros); if (micros > deadline) ++misses;
            for (std::size_t i = 0; i < left.size(); ++i) {
                if (!std::isfinite(left[i]) || !std::isfinite(right[i])) return 1;
                peak = std::max(peak, std::max(std::abs(static_cast<double>(left[i])), std::abs(static_cast<double>(right[i]))));
            }
        }
        const double seconds = std::chrono::duration<double>(Clock::now() - begin).count();
        std::sort(times.begin(), times.end());
        const auto percentile = [&](double q) { return times[static_cast<std::size_t>(q * static_cast<double>(times.size() - 1))]; };
        if (!first) std::cout << ',';
        first = false;
        std::cout << "{\"workload\":\"" << (mode == 7 ? "real_idle" : mode == 6 ? "real_single" : mode == 5 ? "real_12voice_fm" : mode == 0 ? "default_single" : mode == 1 ? "12voice_fm" : mode==2 ? "12voice_clock_chorus" : "12voice_clock_recorded")
                  << "\",\"sample_rate\":" << sr << ",\"voices\":" << voices << ",\"blocks\":" << blocks
                  << ",\"audio_seconds\":" << blocks * 64.0 / sr << ",\"wall_seconds\":" << seconds
                  << ",\"wall_fraction_of_realtime\":" << seconds / (blocks * 64.0 / sr)
                  << ",\"block_median_us\":" << percentile(.5) << ",\"block_p99_us\":" << percentile(.99)
                  << ",\"block_max_us\":" << times.back() << ",\"block_deadline_us\":" << deadline
                  << ",\"deadline_misses\":" << misses << ",\"output_peak\":" << peak << '}';
    }
    std::cout << "]}\n";
    return 0;
}
