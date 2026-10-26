#include "ChorusCircuit.h"
#include "Press78Engine.h"

#include <cmath>
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

// Steady-state gain of one ChorusCircuit output for a sine, in dB.
double gainDb(double hz, bool antiPhase, double rate = 48000.0) {
    press78::ChorusCircuit c;
    c.prepare(rate);
    const int settle = static_cast<int>(rate), span = static_cast<int>(rate / 2);
    double in = 0.0, out = 0.0;
    for (int n = 0; n < settle + span; ++n) {
        const double x = std::sin(tau * hz * n / rate);
        double minus = 0.0;
        const double plus = c.process(x, minus);
        if (n >= settle) { in += x * x; out += (antiPhase ? minus : plus) * (antiPhase ? minus : plus); }
    }
    return 10.0 * std::log10(out / in);
}

std::vector<float> render(int chorusMode, int chorusCircuit, double mix, bool right) {
    auto e = std::make_unique<press78::Press78Engine>();
    e->prepare(48000.0);
    press78::Controls c;
    c.chorusMode = chorusMode; c.chorusCircuit = chorusCircuit; c.chorusMix = mix;
    e->setControls(c);
    e->setPatch(press78::initPatch());
    e->noteOn(76, 127);
    std::vector<float> l(24000), r(24000);
    e->process(l.data(), r.data(), l.size());
    return right ? r : l;
}
} // namespace

int main() {
    test("wet path follows the PSS-270 network, normalised at 1 kHz", [] {
        // Independent nodal solve of the transcribed PSS-270 values (ideal
        // op-amps, BBD as an ideal unity source), relative to 1 kHz. The
        // bilinear transform steepens the skirt above the 2.5 kHz peak: by
        // up to 1.2 dB at 6 kHz at 44.1 kHz, where the wet is already 19 dB
        // down, so the stopband rows carry a wider tolerance.
        const double expected[][2] = {{100, -1.638}, {500, -0.786}, {1000, 0.0}, {2000, 3.373},
                                      {2385, 4.107}, {3000, 0.248}, {4000, -8.155}, {6000, -19.123}};
        for (double rate : {44100.0, 48000.0, 96000.0, 192000.0})
            for (const auto& row : expected)
                REQUIRE(std::abs(gainDb(row[0], false, rate) - row[1]) < (row[0] <= 3000.0 ? 0.1 : 1.5));
    });
    test("the inverter adds one 15.4 kHz pole to the anti-phase wet only", [] {
        for (double rate : {44100.0, 48000.0}) {
            REQUIRE(std::abs(gainDb(1000.0, true, rate) - gainDb(1000.0, false, rate)) < 0.02);
            REQUIRE(std::abs(gainDb(15392.0, true, rate) - gainDb(15392.0, false, rate) + 3.01) < 0.05);
        }
    });
    test("the 1 kHz group delay comes off the recorded delay", [] {
        press78::ChorusCircuit c;
        c.prepare(48000.0);
        REQUIRE(std::abs(c.delaySeconds() - 0.0918e-3) < 0.002e-3);
    });
    test("Studio chorus and a dry mix ignore the circuit", [] {
        REQUIRE(render(0, 0, 1.0, false) == render(0, 1, 1.0, false));
        REQUIRE(render(1, 0, 0.0, true) == render(1, 1, 0.0, true));
    });
    test("Recorded chorus hears the circuit on both channels", [] {
        REQUIRE(render(1, 0, 1.0, false) != render(1, 1, 1.0, false));
        REQUIRE(render(1, 0, 1.0, true) != render(1, 1, 1.0, true));
        for (float x : render(1, 1, 1.0, true)) REQUIRE(std::isfinite(x));
    });
    test("Recorded circuit tails survive an empty delay buffer", [] {
        for (double rate : {48000.0, 192000.0}) {
            for (int circuit : {0, 1}) {
                auto e = std::make_unique<press78::Press78Engine>();
                e->prepare(rate);
                press78::Controls c;
                c.outputCircuit = false; c.toneCutoffHz = 0.0;
                c.dcBlock = false; c.outputLimit = false; c.masterGain = 1.0;
                c.chorusMode = 1; c.chorusCircuit = circuit; c.chorusMix = 1.0;
                e->setControls(c);
                auto patch = press78::initPatch();
                patch.modulator.tl = 127;
                patch.carrier.ar = 63; patch.carrier.d1r = 0; patch.carrier.tl = 0;
                e->setPatch(patch);
                e->noteOn(60, 127);
                e->process(nullptr, nullptr, 2000);
                // A live TL edit mutes the carrier without resetting the wet
                // filters. After 5000 samples every delay entry is zero, but
                // the circuit's IIR tail must still reach both output channels.
                patch.carrier.tl = 127;
                e->setPatch(patch, true);
                e->process(nullptr, nullptr, 5000);
                float left = 0.0f, right = 0.0f;
                e->process(&left, &right, 1);
                REQUIRE(std::isfinite(left) && std::isfinite(right));
                if (circuit == 0) REQUIRE(left == 0.0f && right == 0.0f);
                else REQUIRE(left != 0.0f && right != 0.0f);
            }
        }
    });
    test("controls sanitize the circuit switch", [] {
        press78::Controls c;
        REQUIRE(c.chorusCircuit == 0);
        c.chorusCircuit = 7; REQUIRE(press78::sanitizeControls(c).chorusCircuit == 1);
        c.chorusCircuit = -7; REQUIRE(press78::sanitizeControls(c).chorusCircuit == 0);
    });
    std::printf("%d passed, %d failed\n", passed, failed);
    return failed ? 1 : 0;
}
