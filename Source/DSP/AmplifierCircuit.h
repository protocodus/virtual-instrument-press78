#pragma once
#include "AnalogFilter.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace press78 {
// The power amplifier after the volume slider and the two jacks it feeds.
// The PSS-780 lists the same AN7148, 1000 uF/16 V output capacitors, 4 Ohm
// speakers and 3.3 uH headphone coils as the PSS-480, whose drawing
// (KEC-11861, read 2026-10-20) supplies the values below; the PSS-780's own
// amplifier drawing is not available, so they are borrowed.
//
// Amplifier: the slider's wiper drives 10 kOhm into 1 kOhm || 4700 pF at the
// AN7148 input, a pole at 37.25 kHz. The AN7148 datasheet's gain-frequency
// curve (9 V, 4 Ohm, its application circuit) is -1 dB at 15 kHz, read as one
// pole at 29.48 kHz; its low-frequency fall is the output capacitor's.
//
// AUX: the PSS-270 and PSS-560 take AUX OUT from the speaker node, after the
// output capacitor, and nothing says the PSS-780 differs; its own AUX network
// is not documented. 1000 uF into the 4 Ohm speaker, taken as resistive like
// the datasheet's load, is a 39.8 Hz high-pass. A real driver's impedance
// rises towards its resonance, which would soften this; its curve is unknown.
//
// Phones: after the output capacitor, 100 Ohm, then 0.01 uF to ground and
// 3.3 uH to the tip or ring; the sleeve returns through 3.3 uH and one shared
// 47 uF to ground, and the jack cuts the speakers (PSS-780 owner's manual,
// p.8). With a 32 Ohm headphone, an assumed load, the shared capacitor puts a
// 52.5 Hz high-pass on the mid signal only, since the side currents cancel in
// it, while the side keeps the output capacitor's 1.2 Hz. The coils and the
// shunt change the level by under 0.01 dB below 20 kHz and are left out.
//
// Level is a convention, not a circuit value: every path has unity gain in
// its passband, so Volume sets the level as before.
class AmplifierCircuit {
public:
    void prepare(double sampleRate) noexcept {
        constexpr double pi = 3.14159265358979323846;
        constexpr double inputPoleHz = 1.0 / (2.0 * pi * (10e3 * 1e3 / 11e3) * 4.7e-9);
        constexpr double ampPoleHz = 29.48e3;
        constexpr double output = 1000e-6, speaker = 4.0, series = 100.0, sleeve = 47e-6, headphone = 32.0;
        const auto power = [=](double hz) {
            return 1.0 / ((1.0 + (hz / inputPoleHz) * (hz / inputPoleHz)) * (1.0 + (hz / ampPoleHz) * (hz / ampPoleHz)));
        };
        // Both treble poles sit near or above the engine's 24 kHz Nyquist,
        // where the bilinear transform would crowd them into the top octave.
        // One first-order section instead matches their combined magnitude at
        // DC, at matchHz and at Nyquist, within 0.4 dB from 1 to 20 kHz.
        // |b0 + b1/z|^2 / |1 + a/z|^2 meeting the three targets reduces to
        // A a^2 + B a + A = 0, whose roots are reciprocal; the stable one is used.
        const double matchHz = std::min(15000.0, 0.4 * sampleRate);
        const double gm = power(matchHz), gn = power(0.5 * sampleRate), c = std::cos(2.0 * pi * matchHz / sampleRate);
        const double qa = 0.5 * ((1.0 + c) + gn * (1.0 - c)) - gm;
        const double qb = (1.0 + c) - gn * (1.0 - c) - 2.0 * gm * c;
        const double q = -0.5 * (qb + std::copysign(std::sqrt(std::max(0.0, qb * qb - 4.0 * qa * qa)), qb));
        const double a = q == 0.0 ? 0.0 : qa / q;
        const double rise = 1.0 + a, fall = std::sqrt(gn) * (1.0 - a);
        for (auto& t : treble_) t = {0.5 * (rise + fall), 0.5 * (rise - fall), a};
        const double speakerTau = output * speaker;
        for (auto& f : speaker_) f.design({0.0, speakerTau}, {1.0, speakerTau}, sampleRate, 1.0 / (2.0 * pi * speakerTau));
        const double midTau = (series + headphone) / (1.0 / output + 2.0 / sleeve);
        const double sideTau = (series + headphone) * output;
        phonesMid_.design({0.0, midTau}, {1.0, midTau}, sampleRate, 1.0 / (2.0 * pi * midTau));
        phonesSide_.design({0.0, sideTau}, {1.0, sideTau}, sampleRate, 1.0 / (2.0 * pi * sideTau));
        reset();
    }
    void reset() noexcept {
        for (auto& t : treble_) t.x1 = t.y1 = 0.0;
        for (auto& f : speaker_) f.reset();
        phonesMid_.reset(); phonesSide_.reset();
    }
    // Moves left and right from the slider towards the AUX and headphone
    // outputs by their mix weights. Every path runs at all times, so a jack
    // change never replays stale filter memory.
    void process(double& left, double& right, double auxMix, double phonesMix) noexcept {
        const double l = treble_[0].process(left), r = treble_[1].process(right);
        const double auxLeft = speaker_[0].process(l), auxRight = speaker_[1].process(r);
        const double mid = phonesMid_.process(0.5 * (l + r)), side = phonesSide_.process(0.5 * (l - r));
        left += auxMix * (auxLeft - left) + phonesMix * (mid + side - left);
        right += auxMix * (auxRight - right) + phonesMix * (mid - side - right);
    }

private:
    struct FirstOrder {
        double b0 = 1.0, b1 = 0.0, a = 0.0, x1 = 0.0, y1 = 0.0;
        double process(double x) noexcept {
            const double y = b0 * x + b1 * x1 - a * y1;
            x1 = x; y1 = y;
            return y;
        }
    };
    std::array<FirstOrder, 2> treble_{};
    std::array<AnalogFilter<1>, 2> speaker_{};
    AnalogFilter<1> phonesMid_{}, phonesSide_{};
};
} // namespace press78
