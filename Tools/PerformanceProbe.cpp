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
    bool realOnly = false;
    int pitchModel = -1;
    int sustainMode = -1, keyLevelModel = -1, allocationModel = -1, chipRate = -1;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--real-only") realOnly = true;
        else if (arg == "--pitch-model" && i + 1 < argc) {
            const std::string value = argv[++i];
            if (value == "equal" || value == "0") pitchModel = 0;
            else if (value == "original" || value == "1") pitchModel = 1;
            else return 2;
        } else if (arg == "--sustain-mode" && i + 1 < argc) {
            const std::string value = argv[++i];
            if (value == "legacy" || value == "0") sustainMode = 0;
            else if (value == "original" || value == "1") sustainMode = 1;
            else return 2;
        } else if (arg == "--key-level-model" && i + 1 < argc) {
            const std::string value = argv[++i];
            if (value == "legacy" || value == "0") keyLevelModel = 0;
            else if (value == "original" || value == "1") keyLevelModel = 1;
            else return 2;
        } else if (arg == "--allocation-model" && i + 1 < argc) {
            const std::string value = argv[++i];
            if (value == "legacy" || value == "0") allocationModel = 0;
            else if (value == "original" || value == "1") allocationModel = 1;
            else return 2;
        } else if (arg == "--chip-rate" && i + 1 < argc) {
            const std::string value = argv[++i];
            if (value == "legacy" || value == "0") chipRate = 0;
            else if (value == "ym3420" || value == "1") chipRate = 1;
            else return 2;
        } else return 2;
    }
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
            c.pitchModel=1;
            c.sustainMode=1; c.keyLevelModel=1; c.allocationModel=1; c.chorusCircuit=1; c.outputJack=1;
            c.chipRate=1; c.powerSupply=1;
        }
        if (pitchModel >= 0) c.pitchModel = pitchModel;
        if (sustainMode >= 0) c.sustainMode = sustainMode;
        if (keyLevelModel >= 0) c.keyLevelModel = keyLevelModel;
        if (allocationModel >= 0) c.allocationModel = allocationModel;
        if (chipRate >= 0) c.chipRate = chipRate;
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
                  << ",\"pitch_model\":" << e->effectivePitchModel()
                  << ",\"sustain_mode\":" << e->effectiveSustainMode()
                  << ",\"key_level_model\":" << e->effectiveKeyLevelModel()
                  << ",\"allocation_model\":" << e->effectiveAllocationModel()
                  << ",\"chip_rate\":" << e->chipRate()
                  << ",\"audio_seconds\":" << blocks * 64.0 / sr << ",\"wall_seconds\":" << seconds
                  << ",\"wall_fraction_of_realtime\":" << seconds / (blocks * 64.0 / sr)
                  << ",\"block_median_us\":" << percentile(.5) << ",\"block_p99_us\":" << percentile(.99)
                  << ",\"block_max_us\":" << times.back() << ",\"block_deadline_us\":" << deadline
                  << ",\"deadline_misses\":" << misses << ",\"output_peak\":" << peak << '}';
    }
    std::cout << "]}\n";
    return 0;
}
