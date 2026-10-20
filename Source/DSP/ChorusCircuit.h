#pragma once
#include "AnalogFilter.h"

#include <array>
#include <cmath>
#include <complex>

namespace press78 {
// The BBD chorus's analog wet path, borrowed from the Yamaha PSS-270
// schematic (drawing KEC-11463, read 2026-10-20). The PSS-780 uses the same
// MN3206/MN3102 pair, and its board carries the PSS-270's 390K/68P/2.7K clock
// parts and the 47K/220P inverter parts, but its own filter values are not
// documented. The recorded effective chorus keeps its delay law, LFO and
// gains; this adds the wet signal's band limits and the right channel's
// inverter pole on top of it.
//
// Pre-BBD: 0.1 uF series, 1.5 kOhm, then 33 nF to ground at the BBD input,
// which is biased by 100k/100k from +5 V (50 kOhm to AC ground):
//   s C1 Rb / (1 + s (C1 R1 + C2 Rb + C1 Rb) + s^2 C1 R1 C2 Rb)
// Poles at 23.5 Hz and 4.35 kHz, with the 0.1u/33n divider's -2.7 dB.
// Post-BBD: 0.1 uF coupling into 100k/100k bias (50 kOhm), then a
// unity-gain Sallen-Key, 22k + 22k, 12 nF feedback, 680 pF to ground
// (f0 2.53 kHz, Q 2.1), with the wet JFET switch taken as fully on:
//   s C0 Rb / (B (1 + s C0 Rb) + s Rb C2 + s^2 Rb R2 C1 C2),
//   B = 1 + s C2 (R1 + R2) + s^2 R1 R2 C1 C2
// Pre and post together: -1.6 dB at 100 Hz, +4.1 dB at 2.39 kHz, -8.2 dB at
// 4 kHz and -19 dB at 6 kHz, relative to 1 kHz.
// Inverter: 47k in, 47k with 220 pF feedback, a pole at 15.4 kHz on the
// anti-phase (right) wet signal only.
//
// Two conventions, not circuit values: the pair is normalised to unity at
// 1 kHz, where the recorded fit's wet gain was identified, and its 1 kHz
// group delay (0.092 ms) comes off the recorded delay so the fitted timing
// still holds there. The pre-BBD stage runs after the delay read: at the
// recorded depth the delay moves by under 4 us per ms (at most a 0.4 %
// pitch shift), so swapping the two linear stages is inaudible.
class ChorusCircuit {
public:
    void prepare(double sampleRate) noexcept {
        constexpr double c1 = 0.1e-6, r1 = 1.5e3, c2 = 33e-9, rb = 50e3;
        constexpr double c0 = 0.1e-6, rp = 50e3, ra = 22e3, rbk = 22e3, cf = 12e-9, cg = 680e-12;
        constexpr double ri = 47e3, ci = 220e-12;
        const std::array<double, 3> preB{0.0, c1 * rb, 0.0};
        const std::array<double, 3> preA{1.0, c1 * r1 + c2 * rb + c1 * rb, c1 * r1 * c2 * rb};
        const double t = c0 * rp, b1 = cg * (ra + rbk), b2 = ra * rbk * cf * cg;
        const std::array<double, 4> postA{1.0, b1 + t + rp * cg, b2 + b1 * t + rp * rbk * cf * cg, b2 * t};
        const double gain = std::abs(response(preB, preA, t, postA, 1000.0));
        pre_.design(preB, preA, sampleRate, 4350.0);
        post_.design({0.0, t / gain, 0.0, 0.0}, postA, sampleRate, 2532.5);
        inverter_.design({1.0, 0.0}, {1.0, ri * ci}, sampleRate, 15392.0);
        // Group delay at 1 kHz from the phase slope of the analog pair.
        const double dw = 2.0 * kPi;
        delaySeconds_ = -std::arg(response(preB, preA, t, postA, 1001.0) / response(preB, preA, t, postA, 999.0)) / (2.0 * dw);
    }
    void reset() noexcept { pre_.reset(); post_.reset(); inverter_.reset(); }
    double delaySeconds() const noexcept { return delaySeconds_; }
    // Returns the in-phase wet signal. antiPhase receives it through the
    // inverter's pole; the caller applies the inversion's sign.
    double process(double bbdOutput, double& antiPhase) noexcept {
        const double wet = post_.process(pre_.process(bbdOutput));
        antiPhase = inverter_.process(wet);
        return wet;
    }

private:
    static constexpr double kPi = 3.14159265358979323846;
    static std::complex<double> response(const std::array<double, 3>& preB, const std::array<double, 3>& preA,
                                         double postB, const std::array<double, 4>& postA, double hz) noexcept {
        const std::complex<double> s(0.0, 2.0 * kPi * hz);
        return (preB[1] * s) / (preA[0] + preA[1] * s + preA[2] * s * s)
             * (postB * s) / (postA[0] + postA[1] * s + postA[2] * s * s + postA[3] * s * s * s);
    }
    AnalogFilter<2> pre_{};
    AnalogFilter<3> post_{};
    AnalogFilter<1> inverter_{};
    double delaySeconds_ = 0.0;
};
} // namespace press78
