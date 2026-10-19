// Research-only known-truth control generator. Not included in the instrument.
// No factory bank or original firmware is required. Output is not a hardware fit.
#include "Press78Engine.h"
#include "FirmwarePitch.h"
#include "RecordedChorusProfile.h"

#include <algorithm>
#include <array>
#include <cerrno>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <system_error>
#include <vector>
#include <unistd.h>

namespace {
constexpr int kRate = 44100;
constexpr std::size_t kFrames = 2 * kRate;
constexpr std::size_t kNoteOn = 3 * kRate / 10;
constexpr double kPi = 3.14159265358979323846264338327950288;
const char* kUsage =
    "Usage: pm_envelope_control output.wav note modTL carTL modD2R carD2R clockppm dry|real\n"
    "2s, stereo float32 at 44100Hz; note-on 0.3s, velocity 127, held to file end.\n"
    "dry: clockppm is constant offset [-20000,20000]; real: sinusoidal drift amplitude [0,10000] at 0.1Hz.\n"
    "Existing output files are never overwritten. No note-off or CC is sent.\n";

int integer(const char* text, int lo, int hi) {
    std::size_t end = 0;
    const std::string s(text);
    const int x = std::stoi(s, &end);
    if (end != s.size() || x < lo || x > hi) throw std::runtime_error("Integer argument out of range");
    return x;
}
double number(const char* text) {
    std::size_t end = 0;
    const std::string s(text);
    const double x = std::stod(s, &end);
    if (end != s.size() || !std::isfinite(x)) throw std::runtime_error("Clock argument must be finite");
    return x;
}
void bytes(std::FILE* f, const void* data, std::size_t n) {
    if (std::fwrite(data, 1, n, f) != n) throw std::runtime_error("Could not write complete WAV");
}
void u32(std::FILE* f, std::uint32_t x) {
    const std::array<unsigned char, 4> b{{static_cast<unsigned char>(x), static_cast<unsigned char>(x >> 8),
        static_cast<unsigned char>(x >> 16), static_cast<unsigned char>(x >> 24)}};
    bytes(f, b.data(), b.size());
}
void u16(std::FILE* f, std::uint16_t x) {
    const std::array<unsigned char, 2> b{{static_cast<unsigned char>(x), static_cast<unsigned char>(x >> 8)}};
    bytes(f, b.data(), b.size());
}
void wav(const std::string& destination, const std::vector<float>& left, const std::vector<float>& right) {
    // mkstemp creates a private unique sibling; link publishes the complete file
    // atomically and fails if any file/symlink already occupies the destination.
    std::string pattern = destination + ".tmp.XXXXXX";
    std::vector<char> temporary(pattern.begin(), pattern.end()); temporary.push_back('\0');
    const int fd = ::mkstemp(temporary.data());
    if (fd < 0) throw std::system_error(errno, std::generic_category(), "Could not create temporary WAV");
    std::FILE* f = ::fdopen(fd, "wb");
    if (!f) { const int e = errno; ::close(fd); ::unlink(temporary.data()); throw std::system_error(e, std::generic_category(), "Could not open temporary WAV"); }
    try {
        const auto n = static_cast<std::uint32_t>(left.size() * 8);
        bytes(f, "RIFF", 4); u32(f, 36 + n); bytes(f, "WAVEfmt ", 8); u32(f, 16);
        u16(f, 3); u16(f, 2); u32(f, kRate); u32(f, kRate * 8); u16(f, 8); u16(f, 32);
        bytes(f, "data", 4); u32(f, n);
        for (std::size_t i = 0; i < left.size(); ++i) {
            for (float x : {left[i], right[i]}) { std::uint32_t bits; std::memcpy(&bits, &x, 4); u32(f, bits); }
        }
        if (std::fflush(f) != 0 || ::fsync(fd) != 0) throw std::runtime_error("Could not flush complete WAV");
        const int closeResult = std::fclose(f); f = nullptr;
        if (closeResult != 0) throw std::runtime_error("Could not close complete WAV");
        if (::link(temporary.data(), destination.c_str()) != 0)
            throw std::system_error(errno, std::generic_category(), "Atomic WAV publication failed; destination may already exist");
        ::unlink(temporary.data());
    } catch (...) { if (f) std::fclose(f); ::unlink(temporary.data()); throw; }
}
double dbRate(int rate) { return rate == 0 ? 0.0 : 2.0 * std::pow(2.0, rate / 4.0); }
double amplitude(int level) { return level >= 99 ? 0.0 : std::pow(10.0, -0.75 * level / 20.0); }
} // namespace

int main(int argc, char** argv) {
    try {
        if (argc == 2 && std::string(argv[1]) == "--help") { std::cout << kUsage; return 0; }
        if (argc != 9) throw std::runtime_error(kUsage);
        const std::string output(argv[1]), requestedProfile(argv[8]);
        const int note = integer(argv[2], 0, 127), modTL = integer(argv[3], 0, 127), carTL = integer(argv[4], 0, 127);
        const int modD2R = integer(argv[5], 0, 63), carD2R = integer(argv[6], 0, 63);
        const double ppm = number(argv[7]);
        const bool real = requestedProfile == "real" || requestedProfile == "Real";
        if (!real && requestedProfile != "dry" && requestedProfile != "transparent") throw std::runtime_error("Profile must be dry or real");
        if (output.empty() || (real ? (ppm < 0 || ppm > 10000) : std::abs(ppm) > 20000)) throw std::runtime_error("Output path or clock argument is invalid");
        // A quick guard avoids expensive work for an existing file. link() also
        // handles a destination appearing concurrently or a dangling symlink.
        if (std::filesystem::exists(output) || std::filesystem::is_symlink(output)) throw std::runtime_error("Output already exists; no overwrite allowed");

        press78::Patch patch{};
        for (auto* op : {&patch.modulator, &patch.carrier}) {
            op->ar = 63; op->d1r = 1; op->d1l = 0; op->rr = 8; op->srr = 5;
            op->mul = 1; op->dt1 = 0; op->dt2 = false; op->wave = 0;
            op->lksHi = op->lksLo = op->rks = 0; op->amEnable = false;
        }
        patch.modulator.tl = modTL; patch.carrier.tl = carTL;
        patch.modulator.d2r = modD2R; patch.carrier.d2r = carD2R;
        patch.feedback = patch.pms = patch.ams = patch.vibratoDelay = 0;
        patch.vibrato = patch.sustain = false;
        press78::Controls controls;
        controls.pitchModel = 1; controls.clockOffsetPpm = real ? 0.0 : ppm;
        controls.clockDriftPpm = real ? ppm : 0.0; controls.clockDriftRateHz = 0.1;
        controls.masterGain = real ? 0.25 : 1.0; controls.drive = 0;
        controls.outputCircuit = real; controls.toneCutoffHz = real ? 14000.0 : 0.0;
        controls.dcBlock = controls.outputLimit = real;
        controls.chorusMix = real ? 1.0 : 0.0; controls.chorusMode = real ? 1 : 0;
        controls.chorusRateHz = press78::RecordedChorusProfile::rateHz;
        controls.chorusDepthMs = press78::RecordedChorusProfile::depthMs;
        controls.stereoWidth = 1.0;
        auto engine = std::make_unique<press78::Press78Engine>();
        engine->prepare(kRate); engine->setPatch(patch); engine->setControls(controls);
        std::vector<float> left(kFrames), right(kFrames);
        std::size_t cursor = 0;
        while (cursor < kFrames) {
            if (cursor == kNoteOn) engine->noteOn(note, 127);
            const auto boundary = cursor < kNoteOn ? kNoteOn : kFrames;
            const auto count = std::min<std::size_t>(128, boundary - cursor);
            engine->process(left.data() + cursor, right.data() + cursor, count); cursor += count;
        }
        std::array<double, 2> peak{};
        for (std::size_t i = 0; i < kFrames; ++i) {
            if (!std::isfinite(left[i]) || !std::isfinite(right[i])) throw std::runtime_error("Nonfinite output; no WAV published");
            peak[0] = std::max(peak[0], std::abs(static_cast<double>(left[i])));
            peak[1] = std::max(peak[1], std::abs(static_cast<double>(right[i])));
        }
        wav(output, left, right);
        std::cout << std::setprecision(17) << "{\"schema\":\"press78.pm-envelope-native-control.v1\",\"rate\":" << kRate
          << ",\"frames\":" << kFrames << ",\"note_on_frame\":" << kNoteOn << ",\"note_on_seconds\":0.3,\"note_off_sent\":false,\"velocity\":127"
          << ",\"profile\":\"" << (real ? "real" : "dry") << "\",\"note\":" << note << ",\"mod_TL\":" << modTL << ",\"carrier_TL\":" << carTL
          << ",\"mod_D2R\":" << modD2R << ",\"carrier_D2R\":" << carD2R << ",\"frequency_nominal_hz\":" << press78::firmware_pitch::frequency(note)
          << ",\"modulator_decay_nominal_db_per_second\":" << dbRate(modD2R) << ",\"carrier_decay_nominal_db_per_second\":" << dbRate(carD2R)
          << ",\"initial_beta_before_envelope\":" << 8 * kPi * amplitude(modTL)
          << ",\"initial_carrier_peak_before_envelope_and_output\":" << 0.8 * amplitude(carTL)
          << ",\"clock_offset_ppm\":" << controls.clockOffsetPpm << ",\"clock_drift_ppm\":" << controls.clockDriftPpm << ",\"clock_drift_rate_hz\":0.1"
          << ",\"pitch_model\":" << engine->effectivePitchModel() << ",\"master_gain\":" << controls.masterGain
          << ",\"resampler_delay_internal_ticks\":32,\"internal_rate_model_hz\":48000,\"nominal_delay_host_samples_exact\":29.4,\"latency_samples_ceiling\":" << engine->latencySamples()
          << ",\"latency_compensation_applied\":false,\"chorus_epoch_seconds\":0,\"additive_noise\":false,\"finite\":true,\"peak_left\":" << peak[0] << ",\"peak_right\":" << peak[1] << "}\n";
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
