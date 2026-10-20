#include "FirmwarePitch.h"
#include "Press78Engine.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace press78 {
struct Press78ChipRateTestAccess {
    static double carrierStep(const Press78Engine& e) { return e.voices_[0].carrierStep; }
};
} // namespace press78

namespace {
int passed = 0, failed = 0;
#define REQUIRE(x) do { if (!(x)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " #x); } while (false)
template<class F> void test(const char* name, F body) {
    try { body(); ++passed; std::printf("PASS %s\n", name); }
    catch (const std::exception& e) { ++failed; std::printf("FAIL %s: %s\n", name, e.what()); }
}
constexpr double tau = 6.283185307179586476925286766559;
using E = press78::Press78Engine;

press78::Controls transparent(int chipRate) {
    press78::Controls c;
    c.chipRate = chipRate; c.pitchModel = 1;
    c.masterGain = 1.0; c.toneCutoffHz = 0.0; c.outputCircuit = false;
    c.dcBlock = false; c.outputLimit = false; c.envelopeReverb = false;
    return c;
}
// Unit modulator into the carrier at full level: FM sidebands reach past
// 50 kHz, so a high note folds partials back at either chip rate.
press78::Patch bright() {
    auto p = press78::initPatch();
    p.modulator.mul = 1; p.modulator.tl = 0; p.modulator.ar = 63; p.modulator.d1r = 0;
    p.carrier.mul = 1; p.carrier.tl = 0; p.carrier.ar = 63; p.carrier.d1r = 0;
    return p;
}
std::vector<float> render(int chipRate, const press78::Patch& patch, int note, double rate, double seconds) {
    auto e = std::make_unique<E>();
    e->prepare(rate);
    e->setControls(transparent(chipRate));
    e->setPatch(patch);
    e->noteOn(note, 127);
    std::vector<float> out(static_cast<std::size_t>(seconds * rate));
    e->process(out.data(), nullptr, out.size());
    return out;
}
// Level in dB of one frequency over [0.3 s, 1.3 s], Blackman-Harris windowed.
double levelDb(const std::vector<float>& x, double rate, double hz) {
    const auto begin = static_cast<std::size_t>(0.3 * rate), n = static_cast<std::size_t>(rate);
    double re = 0.0, im = 0.0, gain = 0.0;
    for (std::size_t i = 0; i < n; ++i) {
        const double t = static_cast<double>(i) / n;
        const double w = 0.35875 - 0.48829 * std::cos(tau * t) + 0.14128 * std::cos(2 * tau * t) - 0.01168 * std::cos(3 * tau * t);
        re += w * x[begin + i] * std::cos(tau * hz * i / rate);
        im -= w * x[begin + i] * std::sin(tau * hz * i / rate);
        gain += w;
    }
    return 20.0 * std::log10(2.0 * std::hypot(re, im) / gain + 1e-30);
}
} // namespace

int main() {
    test("the YM3420 rate is the 5.5 MHz clock over 96", [] {
        REQUIRE(E::kYm3420Rate == 5.5e6 / 96.0);
        E e;
        REQUIRE(e.chipRate() == E::kInternalRate);
        auto c = transparent(1);
        e.setControls(c);
        REQUIRE(e.effectiveChipRate() == 1 && e.chipRate() == E::kYm3420Rate);
    });
    test("a frequency word advances the phase by word / 2^20 per chip sample", [] {
        // C7 is word 2394 in block 7, a 20-bit phase step of 2394 << 4.
        E e;
        e.setControls(transparent(1));
        e.setPatch(press78::initPatch());
        e.noteOn(96, 127);
        REQUIRE(std::abs(press78::Press78ChipRateTestAccess::carrierStep(e) / tau * 1048576.0 - 38304.0) < 1e-9);
        REQUIRE(std::abs(press78::firmware_pitch::frequency(96) - 38304.0 * E::kYm3420Rate / 1048576.0) < 1e-9);
    });
    test("high notes fold back where the YM3420 folds them", [] {
        // C7 at 2092.84 Hz: harmonics 27 and 28 straddle 57,291.67 Hz and fold
        // to 785.0 and 1307.8 Hz (PSS-680 recordings: 784.9 and 1307.6 Hz),
        // where a 48 kHz core instead folds harmonics 22 and 23 to 1957.6 and
        // 135.3 Hz.
        const double f0 = press78::firmware_pitch::frequency(96);
        const double ym[] = {E::kYm3420Rate - 27 * f0, 28 * f0 - E::kYm3420Rate};
        const double legacy[] = {E::kInternalRate - 22 * f0, 23 * f0 - E::kInternalRate};
        REQUIRE(std::abs(ym[0] - 785.0) < 0.1 && std::abs(ym[1] - 1307.8) < 0.1);
        for (double rate : {48000.0, 96000.0}) {
            const auto a = render(0, bright(), 96, rate, 1.4), b = render(1, bright(), 96, rate, 1.4);
            for (double hz : ym) {
                std::printf("  %.0f Hz host, %.1f Hz: legacy %.1f dB, YM3420 %.1f dB\n", rate, hz, levelDb(a, rate, hz), levelDb(b, rate, hz));
                REQUIRE(levelDb(b, rate, hz) > -40.0 && levelDb(b, rate, hz) > levelDb(a, rate, hz) + 40.0);
            }
            for (double hz : legacy) {
                std::printf("  %.0f Hz host, %.1f Hz: legacy %.1f dB, YM3420 %.1f dB\n", rate, hz, levelDb(a, rate, hz), levelDb(b, rate, hz));
                REQUIRE(levelDb(a, rate, hz) > -40.0 && levelDb(a, rate, hz) > levelDb(b, rate, hz) + 40.0);
            }
        }
    });
    test("an unaliased note keeps its pitch, timing and latency at either rate", [] {
        // Pitch, envelopes and the 32/48000 s reconstruction delay are laws in
        // seconds, so a low sine renders the same. Both grids start at the same
        // instant, but each phase advances once before its first output, which
        // leads the faster grid's waveform by 3.4 us less. The first 10 ms,
        // where the abrupt start rings the two reconstruction kernels
        // differently, are left out.
        const double lead = tau * press78::firmware_pitch::frequency(45) * (1.0 / E::kInternalRate - 1.0 / E::kYm3420Rate);
        for (double rate : {44100.0, 48000.0, 96000.0}) {
            const auto a = render(0, press78::initPatch(), 45, rate, 0.5), b = render(1, press78::initPatch(), 45, rate, 0.5);
            double peak = 0.0, error = 0.0;
            for (std::size_t i = static_cast<std::size_t>(0.01 * rate); i < a.size(); ++i) {
                peak = std::max(peak, std::abs(double(a[i])));
                error = std::max(error, std::abs(double(a[i]) - b[i]));
            }
            REQUIRE(peak > 0.1 && error < (1.01 * lead + 1e-5) * peak);
            E x, y;
            x.prepare(rate); y.prepare(rate);
            y.setControls(transparent(1));
            REQUIRE(x.latencySamples() == y.latencySamples());
        }
    });
    test("a rate change waits for silence", [] {
        E e;
        e.setPatch(press78::initPatch());
        std::vector<float> out(4800);
        e.noteOn(60, 100);
        e.process(out.data(), nullptr, out.size());
        e.setControls(transparent(1));
        e.process(out.data(), nullptr, out.size());
        REQUIRE(e.effectiveChipRate() == 0 && e.chipRate() == E::kInternalRate);
        e.noteOff(60);
        for (int i = 0; i < 200 && e.activeVoices(); ++i) e.process(out.data(), nullptr, out.size());
        REQUIRE(e.activeVoices() == 0);
        e.process(out.data(), nullptr, 1);
        REQUIRE(e.effectiveChipRate() == 1 && e.chipRate() == E::kYm3420Rate);
        for (float x : out) REQUIRE(std::isfinite(x));
    });
    test("controls sanitize the chip rate", [] {
        press78::Controls c;
        REQUIRE(c.chipRate == 0);
        c.chipRate = 7; REQUIRE(press78::sanitizeControls(c).chipRate == 1);
        c.chipRate = -2; REQUIRE(press78::sanitizeControls(c).chipRate == 0);
    });
    std::printf("%d passed, %d failed\n", passed, failed);
    return failed ? 1 : 0;
}
