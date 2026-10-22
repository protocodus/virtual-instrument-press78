#include "AmplifierCircuit.h"
#include "FactoryVoices.h"
#include "Press78Engine.h"

#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
int passed = 0, failed = 0;
#define REQUIRE(x) do { if (!(x)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " #x); } while (false)
template<class F> void test(const char* name, F body) {
    try { body(); ++passed; std::printf("PASS %s\n", name); }
    catch (const std::exception& e) { ++failed; std::printf("FAIL %s: %s\n", name, e.what()); }
}
constexpr double tau = 6.283185307179586476925286766559;

// Steady-state gain in dB from a sine on the left input (and on the right,
// scaled by rightSign) to the chosen output channel.
double gainDb(double hz, double auxMix, double phonesMix, double rightSign, bool rightOut, double rate = 48000.0, double wiper = 0.0) {
    press78::AmplifierCircuit a;
    a.prepare(rate);
    const int settle = static_cast<int>(rate), span = static_cast<int>(rate);
    double in = 0.0, out = 0.0;
    for (int n = 0; n < settle + span; ++n) {
        const double x = std::sin(tau * hz * n / rate);
        double l = x, r = rightSign * x;
        a.process(l, r, auxMix, phonesMix, wiper);
        if (n >= settle) { in += x * x; out += (rightOut ? r * r : l * l); }
    }
    return 10.0 * std::log10(out / in);
}
double pole(double hz, double cornerHz) { return -10.0 * std::log10(1.0 + (hz / cornerHz) * (hz / cornerHz)); }
// The analog amplifier: the PSS-480 input network's 37.25 kHz pole and the
// AN7148 datasheet's 29.48 kHz reading.
double treble(double hz) { return pole(hz, 1.0 / (tau * (10e3 / 11.0) * 4.7e-9)) + pole(hz, 29.48e3); }

// Total harmonic distortion of a sine through the amplifier, both channels
// driven alike, read on the left output over its second second.
double distortion(int supply, double amplitude, bool phones, double wiper, double* railMean = nullptr, double* railMin = nullptr, double* second = nullptr, double depletion = 0.0) {
    press78::AmplifierCircuit a;
    a.prepare(48000.0);
    a.setSupply(supply, depletion); a.snapSupply();
    constexpr int n = 48000;
    constexpr double hz = 1000.0;
    std::vector<double> out(n);
    double sum = 0.0, lowest = 1e9;
    for (int i = 0; i < 2 * n; ++i) {
        double l = amplitude * std::sin(tau * hz * i / 48000.0), r = l;
        a.process(l, r, phones ? 0.0 : 1.0, phones ? 1.0 : 0.0, wiper);
        if (i >= n) { out[i - n] = l; sum += a.railVolts(); lowest = std::min(lowest, a.railVolts()); }
    }
    const auto harmonic = [&](int k) {
        std::complex<double> c;
        for (int i = 0; i < n; ++i) c += out[i] * std::polar(1.0, -tau * k * hz * i / 48000.0);
        return std::abs(c);
    };
    double rest = 0.0;
    for (int k = 2; k <= 9; ++k) rest += harmonic(k) * harmonic(k);
    if (railMean) *railMean = sum / n;
    if (railMin) *railMin = lowest;
    if (second) *second = 20.0 * std::log10(harmonic(2) / harmonic(1));
    return std::sqrt(rest) / harmonic(1);
}

std::vector<float> render(int jack, bool right, int switchTo = -1) {
    auto e = std::make_unique<press78::Press78Engine>();
    e->prepare(48000.0);
    press78::Controls c;
    c.outputJack = jack; c.chorusMode = 1; c.chorusMix = 1.0;
    e->setControls(c);
    e->setPatch(press78::initPatch());
    e->noteOn(36, 127);
    std::vector<float> l(24000), r(24000);
    e->process(l.data(), r.data(), 12000);
    if (switchTo >= 0) { c.outputJack = switchTo; e->setControls(c); }
    e->process(l.data() + 12000, r.data() + 12000, 12000);
    return right ? r : l;
}
} // namespace

int main() {
    test("AUX follows the amplifier into the speaker node", [] {
        // 1000 uF into the datasheet's resistive 4 ohm accounts for its
        // curve's low end, read as -1 dB at 80 Hz and -3.7 dB at 33 Hz.
        const double speakerHz = 1.0 / (tau * 4e-3);
        REQUIRE(std::abs(pole(speakerHz, 80.0) + 1.0) < 0.1 && std::abs(pole(speakerHz, 33.0) + 3.7) < 0.25);
        // The instrument's node holds the stand-in driver instead: Re in
        // series with its motional R, L and C in parallel.
        const auto speaker = [](double hz) {
            const double re = 3.4, ws = tau * 110.0, qms = 5.61, qes = 2.8;
            const std::complex<double> jw(0.0, tau * hz);
            const auto z = re + 1.0 / (qes / (re * qms) + 1.0 / (jw * re / (ws * qes)) + jw * qes / (ws * re));
            return 20.0 * std::log10(std::abs(z / (z + 1.0 / (jw * 1000e-6))));
        };
        // With its 0.1 mH coil, which the model leaves out, the driver's AUX
        // curve is -7.85, -1.59, +0.83 and -1.00 dB at 20, 50, 80 and 150 Hz.
        REQUIRE(std::abs(speaker(20.0) + 7.85) < 0.07 && std::abs(speaker(50.0) + 1.59) < 0.07);
        REQUIRE(std::abs(speaker(80.0) - 0.83) < 0.07 && std::abs(speaker(150.0) + 1.00) < 0.07);
        for (double rate : {44100.0, 48000.0, 96000.0})
            for (double hz : {20.0, 25.0, 40.0, 60.0, 80.0, 100.0, 120.0, 150.0, 200.0, 1000.0, 5000.0, 10000.0, 15000.0, 18000.0, 20000.0}) {
                const double expected = speaker(hz) + treble(hz);
                REQUIRE(std::abs(gainDb(hz, 1.0, 0.0, 1.0, false, rate) - expected) < 0.4);
                REQUIRE(std::abs(gainDb(hz, 1.0, 0.0, -1.0, true, rate) - expected) < 0.4);
            }
    });
    test("the amplifier's input loads the slider", [] {
        // The pot top's 1 uF sees the pot's upper part in series with its
        // lower part in parallel with the wiper's 10k + 1k. Its loaded share
        // is found here by bisection on the resistance below the wiper.
        const auto share = [](double below) {
            const double lower = below * 11e3 / (below + 11e3);
            return lower / (10e3 - below + lower);
        };
        for (double wiper : {0.125, 0.5, 1.0}) {
            double lo = 0.0, hi = 10e3;
            for (int i = 0; i < 100; ++i) (share(0.5 * (lo + hi)) < wiper ? lo : hi) = 0.5 * (lo + hi);
            const double below = 0.5 * (lo + hi), top = 10e3 - below + below * 11e3 / (below + 11e3);
            const double cornerHz = 1.0 / (tau * top * 1e-6), unloadedHz = 1.0 / (tau * 10e3 * 1e-6);
            if (wiper == 1.0) REQUIRE(std::abs(cornerHz - 30.38) < 0.01);
            for (double hz : {10.0, 20.0, 30.0, 50.0, 100.0, 1000.0}) {
                // Relative to the unloaded slider, the loaded high-pass replaces
                // the unloaded one; the passband stays at unity.
                const double expected = pole(cornerHz, hz) - pole(unloadedHz, hz);
                for (double aux : {1.0, 0.0}) {
                    const double change = gainDb(hz, aux, 1.0 - aux, 1.0, false, 48000.0, wiper) - gainDb(hz, aux, 1.0 - aux, 1.0, false);
                    REQUIRE(std::abs(change - expected) < 0.01);
                }
            }
        }
    });
    test("headphones high-pass the mid through the shared 47 uF return", [] {
        // 100 ohm + 32 ohm; 1000 uF in series with half of the shared 47 uF.
        const double midHz = (1.0 / 1000e-6 + 2.0 / 47e-6) / (tau * 132.0);
        REQUIRE(std::abs(midHz - 52.5) < 0.1);
        for (double hz : {30.0, 52.5, 100.0, 1000.0, 10000.0}) {
            REQUIRE(std::abs(gainDb(hz, 0.0, 1.0, 1.0, false) - (pole(midHz, hz) + treble(hz))) < 0.4);
            REQUIRE(std::abs(gainDb(hz, 0.0, 1.0, -1.0, false) - (pole(1.0 / (tau * 0.132), hz) + treble(hz))) < 0.4);
        }
    });
    test("headphone bass from one side leaks into the other", [] {
        // Left alone is mid plus side; the right earpiece hears mid minus
        // side, so the leak is |Hm - Hs| / |Hm + Hs| (-6.7 dB at 50 Hz).
        const double midTau = 132.0 / (1.0 / 1000e-6 + 2.0 / 47e-6), sideTau = 0.132;
        for (double hz : {50.0, 200.0, 1000.0}) {
            const std::complex<double> sm(0.0, tau * hz * midTau), ss(0.0, tau * hz * sideTau);
            const auto hm = sm / (1.0 + sm), hs = ss / (1.0 + ss);
            const double expected = 20.0 * std::log10(std::abs(hm - hs) / std::abs(hm + hs));
            const double leak = gainDb(hz, 0.0, 1.0, 0.0, true) - gainDb(hz, 0.0, 1.0, 0.0, false);
            REQUIRE(std::abs(leak - expected) < 0.3);
        }
    });
    test("the preamp path is untouched", [] {
        press78::AmplifierCircuit a;
        a.prepare(48000.0);
        for (int n = 0; n < 4800; ++n) {
            const double x = std::sin(0.01 * n);
            double l = x, r = -0.5 * x;
            a.process(l, r, 0.0, 0.0, 0.01 * (n % 100));
            REQUIRE(l == x && r == -0.5 * x);
        }
    });
    test("the engine plays every jack and switches without a step", [] {
        const auto preamp = render(0, false), aux = render(1, false), phones = render(2, true);
        REQUIRE(preamp != aux);
        for (const auto* v : {&aux, &phones}) for (float x : *v) REQUIRE(std::isfinite(x));
        // A low note's per-sample motion bounds how far a switch may jump.
        double motion = 0.0;
        for (std::size_t i = 1; i < preamp.size(); ++i) motion = std::max(motion, std::abs(double(preamp[i]) - preamp[i - 1]));
        for (int to : {1, 2}) {
            const auto switched = render(0, false, to);
            for (std::size_t i = 11990; i < 12100; ++i) REQUIRE(std::abs(double(switched[i]) - switched[i - 1]) <= 1.5 * motion);
        }
    });
    test("controls sanitize the jack", [] {
        press78::Controls c;
        REQUIRE(c.outputJack == 0);
        c.outputJack = 9; REQUIRE(press78::sanitizeControls(c).outputJack == 2);
        c.outputJack = -1; REQUIRE(press78::sanitizeControls(c).outputJack == 0);
    });
    test("the swing law follows the AN7148 datasheet", [] {
        // Datasheet THD-input curve at 9 V into 4 Ohm (input mV rms, THD %),
        // with the curve's own 44.92 dB gain and its 0.25 % crossover floor.
        const auto thd = [](double volts, double* power = nullptr) {
            constexpr int n = 4096;
            std::vector<std::complex<double>> h(10);
            for (int i = 0; i < n; ++i) {
                const double v = volts * std::sin(tau * i / n), y = v * press78::AmplifierCircuit::swingShare(v, 3.66, 3.66);
                for (int k = 1; k < 10; ++k) h[k] += y * std::polar(2.0 / n, -tau * k * i / n);
            }
            double rest = 0.0;
            for (int k = 2; k < 10; ++k) rest += std::norm(h[k]);
            if (power) *power = std::norm(h[1]) / 8.0;
            return std::hypot(std::sqrt(rest) / std::abs(h[1]), 0.0025);
        };
        const double gain = std::sqrt(2.0) * std::pow(10.0, 44.92 / 20.0) * 1e-3;
        for (const auto& [mv, percent] : std::vector<std::pair<double, double>>{{27.93, 22.5}, {19.56, 11.9}, {15.27, 2.7}, {13.81, 1.26}, {12.75, 0.82}, {10.45, 0.375}})
            REQUIRE(std::abs(20.0 * std::log10(thd(mv * gain) / (0.01 * percent))) < 2.7);
        // Its table gives 2.10 W at 10 % THD.
        double lo = 3.0, hi = 6.0, power = 0.0;
        for (int i = 0; i < 50; ++i) (thd(0.5 * (lo + hi)) < 0.1 ? lo : hi) = 0.5 * (lo + hi);
        thd(lo, &power);
        REQUIRE(std::abs(power - 2.10) < 0.05);
    });
    test("small signals pass every supply untouched", [] {
        for (int supply : {1, 2}) for (double aux : {1.0, 0.0}) {
            press78::AmplifierCircuit ideal, powered;
            ideal.prepare(48000.0); powered.prepare(48000.0);
            powered.setSupply(supply); powered.snapSupply();
            for (int i = 0; i < 4800; ++i) {
                double l = 0.01 * std::sin(0.05 * i), r = -l, pl = l, pr = r;
                ideal.process(l, r, aux, 1.0 - aux, 0.5);
                powered.process(pl, pr, aux, 1.0 - aux, 0.5);
                REQUIRE(l == pl && r == pr);
            }
        }
    });
    test("headphones run out of swing near half the battery rail", [] {
        // The AN7148 gives 44.5 dB over the wiper's 1/11, and one engine unit
        // is 1 V at the pot top; into headphones it swings to half the idle
        // rail, 9.54 V - 1.35 Ohm x 0.2 A, less 0.51 V. The law reaches 1 % THD
        // at 0.891 of that limit and 10 % at 1.31; the little headphone current
        // barely moves the rail.
        const double voltsPerUnit = std::pow(10.0, 44.5 / 20.0) / 11.0, limit = 0.5 * (9.54 - 1.35 * 0.2) - 0.51;
        for (double wiper : {1.0, 0.5}) {
            REQUIRE(std::abs(distortion(1, 0.891 * limit / (voltsPerUnit * wiper), true, wiper) - 0.01) < 0.001);
            REQUIRE(std::abs(distortion(1, 1.31 * limit / (voltsPerUnit * wiper), true, wiper) - 0.10) < 0.005);
        }
    });
    test("speaker current sags the rail and flattens positive peaks", [] {
        // Twice the AUX limit on both channels. Batteries idle at 9.27 V; the
        // rail cannot fall below 7.59 V, where both channels held at their
        // sagged positive limit would draw just what the rail can give.
        double mean = 0.0, lowest = 0.0, second = 0.0;
        const double voltsPerUnit = std::pow(10.0, 44.5 / 20.0) / 11.0;
        distortion(1, 2.0 * 3.76 / voltsPerUnit, false, 1.0, &mean, &lowest, &second);
        REQUIRE(lowest > 7.59 && mean < 9.27 - 0.5);
        REQUIRE(second > -40.0);
        // The headphones' 132 Ohm draws far less.
        distortion(1, 2.0 * 4.125 / voltsPerUnit, true, 1.0, &mean, &lowest, &second);
        REQUIRE(lowest > 9.27 - 0.1 && second < -45.0);
        // The adaptor idles at 16.5 V - 6.4 Ohm x 0.2 A less the diode's
        // 0.969 + 0.171 log10(0.2) V.
        press78::AmplifierCircuit a;
        a.prepare(48000.0); a.setSupply(2); a.snapSupply();
        REQUIRE(std::abs(a.railVolts() - (16.5 - 1.28 - (0.969 + 0.171 * std::log10(0.2)))) < 1e-9);
    });
    test("the default Volume keeps a loud chord clean", [] {
        // Jug's chord clips most at the default Volume of the 100 PSS voices.
        unsigned jug = 0;
        while (std::string(press78::kFactoryVoices[jug].name) != "PSS 46 Jug") ++jug;
        const auto chord = [jug](int supply, double volume) {
            auto e = std::make_unique<press78::Press78Engine>();
            e->prepare(48000.0);
            press78::Controls c;
            c.outputJack = 1; c.chorusMode = 1; c.chorusMix = 1.0; c.outputCircuit = true; c.chipRate = 1;
            c.powerSupply = supply; c.masterGain = volume;
            e->setControls(c);
            e->setPatch(press78::factoryPatch(jug));
            for (int note : {48, 52, 55, 60}) e->noteOn(note, 127);
            std::vector<float> l(48000), r(48000);
            e->process(l.data(), r.data(), l.size());
            return l;
        };
        const auto change = [](const std::vector<float>& a, const std::vector<float>& b) {
            double signal = 0.0, difference = 0.0;
            for (std::size_t i = 0; i < a.size(); ++i) { signal += a[i] * a[i]; difference += (a[i] - b[i]) * (a[i] - b[i]); }
            return 10.0 * std::log10(difference / signal);
        };
        const auto peak = [](const std::vector<float>& a) { double p = 0.0; for (float x : a) p = std::max(p, std::abs(double(x))); return p; };
        for (int supply : {1, 2}) REQUIRE(change(chord(0, 0.25), chord(supply, 0.25)) < -45.0);
        const auto ideal = chord(0, 2.0), batteries = chord(1, 2.0);
        REQUIRE(change(ideal, batteries) > -30.0 && peak(batteries) < peak(ideal));
    });
    test("a supply change fades without a step", [] {
        // A loud 50 Hz sine clips hard; the change lands on a positive peak.
        // Supplies 3 and 4 are fresh and spent batteries.
        const auto play = [](int from, int to) {
            press78::AmplifierCircuit a;
            a.prepare(48000.0);
            const auto set = [&a](int s) { a.setSupply(s > 2 ? 1 : s, s == 4 ? 1.0 : 0.0); };
            set(from); a.snapSupply();
            std::vector<double> out(14400);
            for (int i = 0; i < 14400; ++i) {
                if (i == 12720) set(to);
                double l = std::sin(tau * 50.0 * i / 48000.0), r = l;
                a.process(l, r, 1.0, 0.0, 1.0);
                out[i] = l;
            }
            return out;
        };
        double motion = 0.0;
        for (int supply : {0, 1, 2, 4}) {
            const auto steady = play(supply, supply);
            for (std::size_t i = 1; i < steady.size(); ++i) motion = std::max(motion, std::abs(steady[i] - steady[i - 1]));
        }
        for (const auto& [from, to] : std::vector<std::pair<int, int>>{{0, 1}, {1, 0}, {1, 2}, {2, 1}, {2, 0}, {3, 4}, {4, 3}, {4, 2}, {0, 4}}) {
            const auto switched = play(from, to);
            for (std::size_t i = 12700; i < switched.size(); ++i) REQUIRE(std::abs(switched[i] - switched[i - 1]) <= 1.5 * motion);
        }
    });
    test("spent cells follow the discharge curves", [] {
        // Idle rails at 0.2 A: fresh, 9.54 V behind 1.35 Ohm; the 50 %-of-life
        // row, 7.7493 V behind 2.214 Ohm, whose 6.7530 V at 0.45 A lies
        // 0.5274 of the way from fresh (8.9325 V) to spent (4.79995 V); spent,
        // 7.7767 V behind 6.615 Ohm.
        const std::vector<std::pair<double, double>> rails{{0.0, 9.54 - 0.27}, {2.1795 / 4.13255, 7.7493 - 0.4428}, {1.0, 7.7767 - 1.323}};
        for (const auto& [depletion, rail] : rails) {
            press78::AmplifierCircuit a;
            a.prepare(48000.0); a.setSupply(1, depletion); a.snapSupply();
            REQUIRE(std::abs(a.railVolts() - rail) < 1e-9);
        }
        double last = 1e9;
        for (int power = 100; power >= 1; --power) {
            press78::AmplifierCircuit a;
            a.prepare(48000.0); a.setSupply(1, (100 - power) / 99.0); a.snapSupply();
            REQUIRE(a.railVolts() < last && a.mixerLossAbove() == 0.0 && a.mixerLossBelow() == 0.0);
            last = a.railVolts();
        }
    });
    test("spent cells clip AUX sooner and sag it further", [] {
        // A sine at fresh cells' 1 % THD level.
        const double voltsPerUnit = std::pow(10.0, 44.5 / 20.0) / 11.0, amplitude = 0.891 * 3.56 / voltsPerUnit;
        double last = 0.0, lastMin = 1e9;
        for (double depletion : {0.0, 0.5, 1.0}) {
            double mean = 0.0, lowest = 0.0;
            const double d = distortion(1, amplitude, false, 1.0, &mean, &lowest, nullptr, depletion);
            REQUIRE(d > 2.0 * last && lowest < lastMin);
            last = d; lastMin = lowest;
        }
        REQUIRE(last > 0.10);
    });
    test("+5 V holds until the rail falls to 6.2 V, then follows it", [] {
        // The zener's 5.8 V knee plus 300 Ohm of 0.15 A / 111 base current.
        const double onset = 5.8 + 300.0 * 0.15 / 111.0;
        press78::FiveVoltSupply s;
        s.prepare(48000.0);
        for (double rail : {9.27, 7.0, 6.21, 6.1, 5.0, 4.0}) {
            s.settle(9.27);
            for (int i = 0; i < 48000; ++i) s.process(rail);
            const double drop = std::max(0.0, onset - rail);
            REQUIRE(std::abs(s.drop() - drop) < 1e-6 && std::abs(s.bias() - 0.5 * drop) < 1e-3);
        }
        // 50 ms after a fall to 5 V, +5 V has nearly followed, through the
        // 100 uF node, while the mixer bias's 110 ms leaves it far behind.
        s.settle(9.27);
        for (int i = 0; i < 2400; ++i) s.process(5.0);
        REQUIRE(s.drop() > 0.9 * (onset - 5.0) && s.bias() < 0.3 * 0.5 * (onset - 5.0));
    });
    test("spent cells distort loud chords at the default Volume", [] {
        unsigned jug = 0;
        while (std::string(press78::kFactoryVoices[jug].name) != "PSS 46 Jug") ++jug;
        const auto chord = [](int jack, int supply, int power, unsigned voice) {
            auto e = std::make_unique<press78::Press78Engine>();
            e->prepare(48000.0);
            press78::Controls c;
            c.outputJack = jack; c.chorusMode = 1; c.chorusMix = 1.0; c.outputCircuit = true; c.chipRate = 1;
            c.powerSupply = supply; c.power = power;
            e->setControls(c);
            e->setPatch(press78::factoryPatch(voice));
            for (int note : {48, 52, 55, 60}) e->noteOn(note, 127);
            std::vector<float> l(48000), r(48000);
            e->process(l.data(), r.data(), l.size());
            return l;
        };
        const auto change = [](const std::vector<float>& a, const std::vector<float>& b) {
            double signal = 0.0, difference = 0.0;
            for (std::size_t i = 0; i < a.size(); ++i) { signal += a[i] * a[i]; difference += (a[i] - b[i]) * (a[i] - b[i]); }
            return 10.0 * std::log10(difference / signal);
        };
        const auto fresh = chord(1, 1, 100, jug);
        const double most = change(fresh, chord(1, 1, 90, jug)), half = change(fresh, chord(1, 1, 50, jug)), spent = change(fresh, chord(1, 1, 1, jug));
        REQUIRE(most < -45.0 && most < half && half < spent && spent > -20.0);
        // Piano's chord stays inside fresh cells' swing; at 1 % most of its
        // change comes from +5 V narrowing the mixer (-31 dB without it).
        REQUIRE(change(chord(1, 1, 100, 0), chord(1, 1, 1, 0)) > -25.0);
        // The preamp draws no speaker current; the AC step is the adaptor.
        REQUIRE(chord(0, 1, 1, jug) == chord(0, 1, 100, jug));
        REQUIRE(chord(1, 1, 101, jug) == chord(1, 2, 100, jug));
    });
    test("controls sanitize the supply", [] {
        press78::Controls c;
        REQUIRE(c.powerSupply == 0);
        c.powerSupply = 7; REQUIRE(press78::sanitizeControls(c).powerSupply == 2);
        c.powerSupply = -3; REQUIRE(press78::sanitizeControls(c).powerSupply == 0);
        REQUIRE(c.power == 100);
        c.power = 0; REQUIRE(press78::sanitizeControls(c).power == 1);
        c.power = 200; REQUIRE(press78::sanitizeControls(c).power == 101);
    });
    std::printf("%d passed, %d failed\n", passed, failed);
    return failed ? 1 : 0;
}
