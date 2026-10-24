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
// is not documented. The speakers stay on that node (owner's manual, p.8), so
// AUX is the 1000 uF into the driver's impedance. The PSS-780's XG516A00
// (12 cm, 4 Ohm, 3 W) has no published data; the Visaton FR 12 - 4 Ohm, a
// 12 cm weak-motor driver sold for electronic instruments, stands in: Re
// 3.4 Ohm, fs 110 Hz, Qms 5.61, Qes 2.8 (visaton.de, read 2026-10-20). Of
// four similar drivers its AUX curve is nearest their median. The drivers
// open into the case's shared cavity, whose volume and leakage are unknown,
// so they are taken in free air. The motional branch is Res = Re Qms/Qes,
// Lces = Re/(ws Qes) and Cmes = Qes/(ws Re) in parallel, in series with Re;
// its 0.1 mH coil inductance moves AUX by under 0.2 dB and is left out.
// Below resonance the driver looks inductive and lifts 60-120 Hz by up to
// 1.8 dB against a plain 4 Ohm; Re makes 20-30 Hz up to 0.9 dB weaker. The
// -3 dB corner stays at 39.4 Hz.
//
// Phones: after the output capacitor, 100 Ohm, then 0.01 uF to ground and
// 3.3 uH to the tip or ring; the sleeve returns through 3.3 uH and one shared
// 47 uF to ground, and the jack cuts the speakers (PSS-780 owner's manual,
// p.8). With a 32 Ohm headphone, an assumed load, the shared capacitor puts a
// 52.5 Hz high-pass on the mid signal only, since the side currents cancel in
// it, while the side keeps the output capacitor's 1.2 Hz. The coils and the
// shunt change the level by under 0.01 dB below 20 kHz and are left out.
//
// Slider loading: the wiper's 10 kOhm and 1 kOhm, 11 kOhm in all below the
// input pole, hang below the wiper, so the 1 uF that couples the mixer to the
// pot top (AnalogOutput, which leaves the wiper unloaded) sees less than the
// pot's own 10 kOhm as the slider rises: its 15.9 Hz corner moves to 30.4 Hz
// at the top. The AN7148's own input resistance is not given; next to the
// 1 kOhm shunt it would move these figures little.
//
// Level is a convention, not a circuit value: every path has unity gain in
// its passband, so Volume sets the level as before. Volume is twice the
// wiper's loaded share of the pot-top voltage, so its top, 2, is the slider's
// top; the slider's taper then does not matter.
//
// Clipping (Power, research 2026-10-20). One engine unit at the pot top is
// taken as 1.0 V peak: the NJM4558 mixer before the pot, on its 5 V rail,
// swings 0.72-1.72 V before it clips, and the owner's manual (pp. 11, 29) says
// chords of loud voices "occasionally" overload it, which puts one unit
// between 0.49 and 2.34 V. That mixer drives the pot top directly, as the
// PSS-480's IC12 does and AnalogOutput assumes; the PSS-780 board's third
// NJM4558 and its unassigned 47K/220P parts fit it. The PSS-270 and PSS-560
// mix passively instead, which would leave 0.148 of that level at the pot
// top. The AN7148 gains 44.5 dB (datasheet typical) over 1/11 of the wiper
// voltage. Its output follows y = v (1 + |v/Vc|^10)^(-1/10),
// fitted to the datasheet's THD-input curve at 9 V into 4 Ohm: Vc 3.66 V,
// 10 % THD at 2.10 W as its table gives, THD within 2.7 dB of the curve from
// 0.4 % to 22 %. Vc rises 0.376 V per supply volt (its output-power curves).
// Into the 132 Ohm headphone load Vc is taken as half the supply less 0.51 V,
// the least headroom the datasheet shows (8 Ohm at 9 V). Pin 3's capacitor
// holds the output's midpoint, so a fast dip of the rail lowers only the
// positive limit: 0.752 V per volt into the speakers, 1 V into headphones.
//
// Supply: the rail's 470 uF (PSS-480) is fed by the source and drawn by an
// estimated 0.2 A idle plus each channel's positive output current, the
// half the class B stage takes from the rail. Batteries are six fresh alkaline
// C cells, 9.54 V behind 1.35 Ohm (Energizer EN93 and E93). The Adaptor is an
// unregulated PA-3 class one, 16.5 V open-circuit as an owner measured a
// "12 V" PA-3C, falling to the rated 12 V at 0.7 A (6.4 Ohm), then the
// PSS-480's series 1SR35 diode, 0.969 + 0.171 log10(I/1 A) V (Sunmate
// datasheet). The adaptor's own reservoir capacitor is unknown and left out,
// so its sag on fast peaks is an upper bound. Ideal keeps the amplifier
// linear, as before.
//
// Depletion (Power below 100 %, research 2026-10-22). Through their life at
// the keyboard's 0.45 A, alkaline C cells lose voltage on load as Energizer
// E93 and Duracell MN1400 curves give it, within 0.03 V of each other; their
// resistance rises as Varta's AA pulse data does, 0.225 Ohm x 1 to 4.9 per
// cell, with the EMF the rest of the loaded voltage. Pack values are in
// kCells, from fresh to 0.80 V per cell on load, where every curve ends.
// Power is linear in that loaded voltage, 8.93 V at 100 % to 4.80 V at 1 %,
// so each step costs the same, not the same charge. The real keyboard blinks
// its LEDs near 26 % and resets on loud notes below about 19 % (PST520-C and
// -D on +5 V); Press78 plays on.
//
// +5 V (PSS-480 drawing; the PSS-780 lists the same 2SC3419 and MTZ6.2A):
// the rail feeds the follower's base through 150 Ohm, then 100 uF to ground
// and 150 Ohm to the zener. It holds +5 V while the 100 uF stays above the
// zener's 5.8 V knee plus 150 Ohm of base current, an estimated 0.15 A load
// over a gain of 110: a steady rail of 6.2 V (5.8-7.5 V). Below that, +5 V
// follows the 100 uF down. The 1.9 mF on +5 V, which slows falls past
// 80 V/s, is left out. Only the NJM4558 mixer's window is taken to follow
// +5 V: its limits track their supply one to one (datasheet), around a bias
// of half of +5 V held by 2.2k/2.2k and 100 uF, 110 ms. So a fast sag closes
// the limit above the bias and a slow one closes both by half; one volt is
// one engine unit, as for clipping. How the OPU's level and the chorus
// clock follow +5 V is not documented, and they stay fixed.

// +5 V behind its follower, and the NJM4558 mixer bias it feeds, as
// described above; drop and bias are how far each sits below its rest.
class FiveVoltSupply {
public:
    void prepare(double sampleRate) noexcept {
        heldDecay_ = std::exp(-1.0 / (sampleRate * 75.0 * 100e-6));
        freeDecay_ = std::exp(-1.0 / (sampleRate * 150.0 * 100e-6));
        biasDecay_ = std::exp(-1.0 / (sampleRate * 1.1e3 * 100e-6));
    }
    void settle(double rail) noexcept {
        node_ = rail - kBaseDrop > kKnee ? 0.5 * (rail + kZener) : rail - kBaseDrop;
        drop_ = std::max(0.0, kKnee - node_);
        bias_ = 0.5 * drop_;
    }
    void process(double rail) noexcept {
        const bool held = node_ > kKnee;
        const double node = held ? 0.5 * (rail + kZener) : rail - kBaseDrop;
        node_ = node + (node_ - node) * (held ? heldDecay_ : freeDecay_);
        drop_ = std::max(0.0, kKnee - node_);
        bias_ = 0.5 * drop_ + (bias_ - 0.5 * drop_) * biasDecay_;
    }
    double drop() const noexcept { return drop_; }
    double bias() const noexcept { return bias_; }

private:
    // The zener's knee, the base current's drop across 150 Ohm, and the
    // 100 uF node's voltage where the zener lets go.
    static constexpr double kZener = 5.8, kBaseDrop = 150.0 * 0.15 / 111.0, kKnee = kZener + kBaseDrop;
    double heldDecay_ = 0.0, freeDecay_ = 0.0, biasDecay_ = 0.0, node_ = 0.0, drop_ = 0.0, bias_ = 0.0;
};

class AmplifierCircuit {
public:
    void prepare(double sampleRate) noexcept {
        constexpr double pi = 3.14159265358979323846;
        constexpr double inputPoleHz = 1.0 / (2.0 * pi * (10e3 * 1e3 / 11e3) * 4.7e-9);
        constexpr double ampPoleHz = 29.48e3;
        constexpr double output = 1000e-6, series = 100.0, sleeve = 47e-6, headphone = 32.0;
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
        // H = sC Z / (1 + sC Z) with Z = Re + sL / (1 + sL/Res + s^2 L Cm).
        constexpr double re = 3.4, fs = 110.0, qms = 5.61, qes = 2.8;
        constexpr double ws = 2.0 * pi * fs, res = re * qms / qes, lces = re / (ws * qes), cmes = qes / (ws * re);
        constexpr double b1 = output * re, b2 = output * lces * (re / res + 1.0), b3 = output * re * lces * cmes;
        for (auto& f : speaker_) f.design({0.0, b1, b2, b3}, {1.0, lces / res + b1, lces * cmes + b2, b3}, sampleRate, fs);
        const double midTau = (series + headphone) / (1.0 / output + 2.0 / sleeve);
        const double sideTau = (series + headphone) * output;
        phonesMid_.design({0.0, midTau}, {1.0, midTau}, sampleRate, 1.0 / (2.0 * pi * midTau));
        phonesSide_.design({0.0, sideTau}, {1.0, sideTau}, sampleRate, 1.0 / (2.0 * pi * sideTau));
        twiceRate_ = 2.0 * sampleRate;
        loadSlider(wiper_);
        voltsPerUnit_ = std::pow(10.0, 44.5 / 20.0) / 11.0;
        fadeStep_ = 1.0 / (0.005 * sampleRate);
        idleSmoothing_ = 1.0 - std::exp(-1.0 / (0.005 * sampleRate));
        adaptorDecay_ = std::exp(-1.0 / (sampleRate * 6.4 * 470e-6));
        fiveVolt_.prepare(sampleRate);
        rate_ = sampleRate;
        setCells(depletion_);
        idleTarget_ = supplyVolts(kIdleAmps);
        reset();
    }
    void reset() noexcept {
        for (auto& t : slider_) t.x1 = t.y1 = 0.0;
        for (auto& t : treble_) t.x1 = t.y1 = 0.0;
        for (auto& f : speaker_) f.reset();
        phonesMid_.reset(); phonesSide_.reset();
        snapSupply();
    }
    // 0 Ideal, 1 Batteries, 2 Adaptor; depletion runs the batteries from
    // fresh (0) to spent (1). A change of source fades the clipping in or out
    // over 5 ms; the last supply powers it while it fades out.
    void setSupply(int supply, double depletion = 0.0) noexcept {
        target_ = supply == 0 ? 0.0 : 1.0;
        if (supply == 0 || (supply == source_ && (supply == 2 || depletion == depletion_))) return;
        source_ = supply;
        if (supply == 1) setCells(depletion);
        idleTarget_ = supplyVolts(kIdleAmps);
        if (clipMix_ == 0.0) settle();
    }
    void snapSupply() noexcept { clipMix_ = target_; settle(); }
    double railVolts() const noexcept { return rail_; }
    // How far the mixer's limits above and below its bias have closed, in
    // engine units; above goes negative while the bias lags a recovery.
    double mixerLossAbove() const noexcept { return clipMix_ * (fiveVolt_.drop() - fiveVolt_.bias()); }
    double mixerLossBelow() const noexcept { return clipMix_ * fiveVolt_.bias(); }
    // The share of v volts the output reaches, given its positive and
    // negative limits.
    static double swingShare(double v, double above, double below) noexcept {
        const double u = v / (v > 0.0 ? above : below), u2 = u * u, u4 = u2 * u2;
        const double base = 1.0 + u4 * u4 * u2;
        // pow(1, y) is exactly 1 (C17 F.10.4.4): small signals, near every
        // zero crossing and in silence, skip the call.
        return base == 1.0 ? 1.0 : std::pow(base, -0.1);
    }
    // Moves left and right from the slider towards the AUX and headphone
    // outputs by their mix weights. Every path runs at all times, so a jack
    // change never replays stale filter memory. wiper is the slider's loaded
    // share of the pot-top voltage, 0 to 1.
    void process(double& left, double& right, double auxMix, double phonesMix, double wiper) noexcept {
        if (wiper != wiper_) loadSlider(wiper);
        const double l = treble_[0].process(slider_[0].process(left)), r = treble_[1].process(slider_[1].process(right));
        double auxL = l, auxR = r, phonesL = l, phonesR = r;
        clipMix_ = target_ > clipMix_ ? std::min(target_, clipMix_ + fadeStep_) : std::max(target_, clipMix_ - fadeStep_);
        if (clipMix_ > 0.0) {
            idle_ += (idleTarget_ - idle_) * idleSmoothing_;
            const double volts = voltsPerUnit_ * wiper, dip = idle_ - rail_;
            const double auxBelow = 3.66 + 0.376 * (idle_ - 9.0), auxAbove = std::max(0.1, auxBelow - 0.752 * dip);
            const double phonesBelow = 0.5 * idle_ - 0.51, phonesAbove = std::max(0.1, phonesBelow - dip);
            auxL *= swingShare(l * volts, auxAbove, auxBelow); auxR *= swingShare(r * volts, auxAbove, auxBelow);
            phonesL *= swingShare(l * volts, phonesAbove, phonesBelow); phonesR *= swingShare(r * volts, phonesAbove, phonesBelow);
            const double amps = kIdleAmps + volts * (auxMix * (std::max(auxL, 0.0) + std::max(auxR, 0.0)) / 4.0
                + phonesMix * (std::max(phonesL, 0.0) + std::max(phonesR, 0.0)) / 132.0);
            const double settled = supplyVolts(amps);
            rail_ = settled + (rail_ - settled) * (source_ == 2 ? adaptorDecay_ : batteryDecay_);
            fiveVolt_.process(rail_);
            if (clipMix_ < 1.0) {
                auxL = l + clipMix_ * (auxL - l); auxR = r + clipMix_ * (auxR - r);
                phonesL = l + clipMix_ * (phonesL - l); phonesR = r + clipMix_ * (phonesR - r);
            }
        }
        const double auxLeft = speaker_[0].process(auxL), auxRight = speaker_[1].process(auxR);
        const double mid = phonesMid_.process(0.5 * (phonesL + phonesR)), side = phonesSide_.process(0.5 * (phonesL - phonesR));
        left += auxMix * (auxLeft - left) + phonesMix * (mid + side - left);
        right += auxMix * (auxRight - right) + phonesMix * (mid - side - right);
    }

private:
    static constexpr double kIdleAmps = 0.2;
    // Six alkaline C cells through life: pack EMF and resistance, cell EMF
    // the 0.45 A loaded voltage (mean of E93 and MN1400) plus 0.45 A x R, at
    // 0, 10, 20, 30, 50, 70, 80, 90 and 100 % of life to 0.9 V per cell on
    // load, then 0.80 V. Fresh is 9.54 V behind 1.35 Ohm, as before.
    struct Cells { double volts, ohms; };
    static constexpr std::array<Cells, 10> kCells{{{9.54, 1.35}, {8.5955, 1.674}, {8.273, 1.971}, {8.0305, 2.079},
        {7.7493, 2.214}, {7.7509, 3.0375}, {7.7414, 3.51}, {7.724, 4.0905}, {7.8119, 5.3595}, {7.7767, 6.615}}};
    static constexpr double loaded(const Cells& c) noexcept { return c.volts - 0.45 * c.ohms; }
    void setCells(double depletion) noexcept {
        depletion_ = std::clamp(depletion, 0.0, 1.0);
        const double target = loaded(kCells.front()) + depletion_ * (loaded(kCells.back()) - loaded(kCells.front()));
        std::size_t i = 0;
        while (i + 2 < kCells.size() && loaded(kCells[i + 1]) > target) ++i;
        const double t = (loaded(kCells[i]) - target) / (loaded(kCells[i]) - loaded(kCells[i + 1]));
        cellVolts_ = kCells[i].volts + t * (kCells[i + 1].volts - kCells[i].volts);
        cellOhms_ = kCells[i].ohms + t * (kCells[i + 1].ohms - kCells[i].ohms);
        batteryDecay_ = std::exp(-1.0 / (rate_ * cellOhms_ * 470e-6));
    }
    // The rail, the +5 V node and the mixer bias at rest on the idle rail.
    void settle() noexcept {
        idle_ = rail_ = idleTarget_;
        fiveVolt_.settle(rail_);
    }
    // The rail's source voltage while it delivers amps.
    double supplyVolts(double amps) const noexcept {
        return source_ == 2 ? 16.5 - 6.4 * amps - (0.969 + 0.171 * std::log10(amps)) : cellVolts_ - cellOhms_ * amps;
    }
    // (top / pot)(1 + s pot C)/(1 + s top C) turns the unloaded pot's high-pass
    // into the loaded one; top is the resistance the coupling capacitor sees.
    // Both corners sit far below the sample rate, so the bilinear transform
    // needs no prewarping.
    void loadSlider(double wiper) noexcept {
        constexpr double pot = 10e3, load = 11e3, coupling = 1e-6;
        wiper_ = wiper;
        const double r = std::clamp(wiper, 0.0, 1.0);
        // The resistance below the wiper whose loaded divider gives r solves
        // r a^2 - (r pot - load) a - r pot load = 0; this root form stays exact
        // as r goes to 0.
        const double b = r * pot - load;
        const double below = 2.0 * r * pot * load / (std::sqrt(b * b + 4.0 * r * r * pot * load) - b);
        const double top = pot - below + below * load / (below + load);
        const double ratio = top / pot, k = twiceRate_ * top * coupling;
        for (auto& t : slider_) { t.b0 = (ratio + k) / (1.0 + k); t.b1 = (ratio - k) / (1.0 + k); t.a = (1.0 - k) / (1.0 + k); }
    }
    struct FirstOrder {
        double b0 = 1.0, b1 = 0.0, a = 0.0, x1 = 0.0, y1 = 0.0;
        double process(double x) noexcept {
            const double y = b0 * x + b1 * x1 - a * y1;
            x1 = x; y1 = y;
            return y;
        }
    };
    std::array<FirstOrder, 2> slider_{}, treble_{};
    double twiceRate_ = 96000.0, wiper_ = 0.0;
    double voltsPerUnit_ = 0.0, fadeStep_ = 0.0, idleSmoothing_ = 0.0, batteryDecay_ = 0.0, adaptorDecay_ = 0.0;
    double rate_ = 48000.0;
    int source_ = 1;
    double depletion_ = 0.0, cellVolts_ = 9.54, cellOhms_ = 1.35;
    double target_ = 0.0, clipMix_ = 0.0, idleTarget_ = 0.0, idle_ = 0.0, rail_ = 0.0;
    FiveVoltSupply fiveVolt_{};
    std::array<AnalogFilter<3>, 2> speaker_{};
    AnalogFilter<1> phonesMid_{}, phonesSide_{};
};
} // namespace press78
