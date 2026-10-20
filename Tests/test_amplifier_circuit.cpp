#include "AmplifierCircuit.h"
#include "Press78Engine.h"

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
    test("AUX follows the amplifier into the 4 ohm speaker node", [] {
        // 1000 uF into 4 ohm accounts for the datasheet curve's low end, read
        // as -1 dB at 80 Hz and -3.7 dB at 33 Hz to graph precision.
        const double speakerHz = 1.0 / (tau * 4e-3);
        REQUIRE(std::abs(pole(speakerHz, 80.0) + 1.0) < 0.1 && std::abs(pole(speakerHz, 33.0) + 3.7) < 0.25);
        for (double rate : {44100.0, 48000.0, 96000.0})
            for (double hz : {25.0, 40.0, 80.0, 200.0, 1000.0, 5000.0, 10000.0, 15000.0, 18000.0, 20000.0}) {
                const double expected = pole(speakerHz, hz) + treble(hz);
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
    std::printf("%d passed, %d failed\n", passed, failed);
    return failed ? 1 : 0;
}
