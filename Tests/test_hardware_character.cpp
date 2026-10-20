#include "Press78Engine.h"
#include "HardwareCharacter.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <new>
#include <stdexcept>
#include <string>
#include <vector>

// These contracts protect the two explicitly chosen B scenarios. They do not
// establish the undocumented PSS-780 envelope or physical output transfer.
namespace { bool tracking = false; std::size_t allocations = 0; }
void* operator new(std::size_t n) {
    if (tracking) ++allocations;
    if (void* p = std::malloc(n ? n : 1)) return p;
    throw std::bad_alloc();
}
void* operator new[](std::size_t n) { return ::operator new(n); }
void operator delete(void* p) noexcept { std::free(p); }
void operator delete[](void* p) noexcept { std::free(p); }
#if defined(__cpp_sized_deallocation)
void operator delete(void* p, std::size_t) noexcept { std::free(p); }
void operator delete[](void* p, std::size_t) noexcept { std::free(p); }
#endif

namespace press78 {
struct Press78SustainTestAccess {
    static auto envelope(const Operator& op, int note, bool sustain) {
        Press78Engine::Envelope e;
        e.configure(op, note, sustain);
        return e;
    }
    static auto voice(const Patch& patch, int note) {
        Press78Engine::Voice v;
        v.configure(patch, note, 127, 1, 0);
        return v;
    }
    static auto voice(const Press78Engine& e, std::size_t slot = 0) {
        return e.voices_[slot];
    }
    static std::array<double, 2> output(Press78Engine& e, double input) {
        std::array<double, 2> out{};
        e.output(input, out[0], out[1]);
        return out;
    }
};
} // namespace press78

namespace {
using E = press78::Press78Engine;
using A = press78::Press78SustainTestAccess;
namespace character = press78::hardware_character;
int passed = 0, failed = 0;
#define CHECK(x) do { if (!(x)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " #x); } while (false)
template<class F> void test(const char* name, F body) {
    try { body(); ++passed; std::printf("PASS %s\n", name); }
    catch (const std::exception& e) {
        tracking = false; ++failed; std::printf("FAIL %s: %s\n", name, e.what());
    }
}
void near(double a, double b, double tolerance = 1e-12) {
    CHECK(std::abs(a - b) <= tolerance);
}
press78::Controls controls(bool reverb, bool circuit) {
    press78::Controls c;
    c.envelopeReverb = reverb; c.outputCircuit = circuit;
    c.masterGain = 1; c.toneCutoffHz = 0; c.dcBlock = false;
    c.outputLimit = false; c.chorusMix = 0; c.drive = 0;
    c.clockOffsetPpm = c.clockDriftPpm = 0;
    return c;
}
auto engine(const press78::Controls& c) {
    auto e = std::make_unique<E>();
    e->prepare(48000); e->setControls(c); e->setPatch(press78::initPatch()); e->reset();
    return e;
}
std::vector<float> render(E& e, std::size_t n) {
    std::vector<float> out(n);
    e.process(out.data(), nullptr, n);
    return out;
}
double referenceOutput(double x) {
    // Algebraically independent form of the chosen zero-centered biased tanh.
    const double b = std::tanh(.14);
    return (std::tanh(x + .14) - b) / (1 - b * b);
}
double capFor(press78::Operator op, int note) {
    op.rr = op.srr = 4;
    return A::envelope(op, note, false).release;
}
template<class V> void sameHistory(const V& a, const V& b) {
    CHECK(a.modPhase == b.modPhase && a.carrierPhase == b.carrierPhase);
    CHECK(a.prev1 == b.prev1 && a.prev2 == b.prev2 && a.ticks == b.ticks);
    CHECK(a.age == b.age && a.held == b.held && a.released == b.released);
    CHECK(a.modEnvelope.attenuation == b.modEnvelope.attenuation);
    CHECK(a.carrierEnvelope.attenuation == b.carrierEnvelope.attenuation);
    CHECK(a.modEnvelope.stage == b.modEnvelope.stage);
    CHECK(a.carrierEnvelope.stage == b.carrierEnvelope.stage);
}
} // namespace

int main() {
    test("chosen character is enabled by default and diagnostic bypass is retained", [] {
        press78::Controls c;
        CHECK(c.envelopeReverb && c.outputCircuit);
        CHECK(character::kReleaseKneeDb == 18.0);
        c.envelopeReverb = false; c.outputCircuit = false;
        const auto clean = press78::sanitizeControls(c);
        CHECK(!clean.envelopeReverb && !clean.outputCircuit);
    });

    test("native RR4 cap follows note RKS and preserves slower ordinary RR or SRR", [] {
        for (int note : {0, 36, 60, 127}) for (int rks = 0; rks < 4; ++rks)
            for (int rr : {0, 2, 4, 15}) for (bool sustain : {false, true}) {
                press78::Operator op;
                op.rr = rr; op.srr = (rr + 3) % 16; op.rks = rks;
                auto e = A::envelope(op, note, sustain);
                const double ordinary = e.release, expected = capFor(op, note);
                near(e.reverbRelease, expected);
                e.attenuation = 20; e.stage = 3;
                e.next(true, true);
                near(e.attenuation - 20, std::min(ordinary, expected));
                CHECK(e.release == ordinary);
                auto off = A::envelope(op, note, sustain);
                off.attenuation = 20; off.stage = 3;
                off.next(true, false);
                near(off.attenuation - 20, ordinary);
            }
    });

    test("carrier pre-tick knee couples both operators without early crossing or held cap", [] {
        auto p = press78::initPatch();
        p.modulator.rr = 10; p.carrier.rr = 9;
        p.modulator.rks = 3; p.carrier.rks = 1;
        auto v = A::voice(p, 48);
        v.released = true; v.held = false;
        v.modEnvelope.stage = v.carrierEnvelope.stage = 3;
        v.modEnvelope.attenuation = 30;
        v.carrierEnvelope.attenuation = 17.999;
        const double modRate = v.modEnvelope.release, carrierRate = v.carrierEnvelope.release;
        const auto c = controls(true, false);
        v.next(c, 1, 0);
        near(v.modEnvelope.attenuation - 30, modRate);
        near(v.carrierEnvelope.attenuation - 17.999, carrierRate);
        CHECK(v.carrierEnvelope.attenuation > 18);
        const double m = v.modEnvelope.attenuation, a = v.carrierEnvelope.attenuation;
        v.next(c, 1, 0);
        near(v.modEnvelope.attenuation - m, std::min(modRate, capFor(p.modulator, 48)));
        near(v.carrierEnvelope.attenuation - a, std::min(carrierRate, capFor(p.carrier, 48)));
        CHECK(v.modEnvelope.release == modRate && v.carrierEnvelope.release == carrierRate);

        v = A::voice(p, 48); v.released = true;
        v.modEnvelope.stage = v.carrierEnvelope.stage = 3;
        v.modEnvelope.attenuation = 2; v.carrierEnvelope.attenuation = 18;
        v.next(c, 1, 0);
        near(v.modEnvelope.attenuation - 2, capFor(p.modulator, 48));

        auto held = A::voice(p, 48), off = held;
        held.modEnvelope.attenuation = off.modEnvelope.attenuation = 30;
        held.carrierEnvelope.attenuation = off.carrierEnvelope.attenuation = 24;
        held.modEnvelope.stage = held.carrierEnvelope.stage = 2;
        off.modEnvelope.stage = off.carrierEnvelope.stage = 2;
        CHECK(held.next(c, 1, 0) == off.next(controls(false, false), 1, 0));
        sameHistory(held, off);
    });

    test("entered release persists and finished envelopes are not revived", [] {
        auto p = press78::initPatch(); p.carrier.rr = p.modulator.rr = 10;
        auto v = A::voice(p, 60);
        v.released = false;
        v.carrierEnvelope.stage = v.modEnvelope.stage = 3;
        v.carrierEnvelope.attenuation = 18; v.modEnvelope.attenuation = 0;
        v.next(controls(true, false), 1, 0);
        near(v.carrierEnvelope.attenuation - 18, capFor(p.carrier, 60));
        near(v.modEnvelope.attenuation, capFor(p.modulator, 60));
        v.carrierEnvelope.finished = true;
        CHECK(v.next(controls(true, false), 1, 0) == 0 && !v.active);
        auto disabled = A::envelope(p.carrier, 60, false);
        disabled.disabled = true; disabled.attenuation = 18;
        CHECK(disabled.next(true, true) == 0 && disabled.attenuation == 18);
    });

    test("live Reverb switches change releasing voices without restarting history", [] {
        auto c = controls(false, false); c.sustainMode = 1;
        auto e = engine(c);
        e->noteOn(60, 127); e->process(nullptr, nullptr, 512); e->noteOff(60);
        e->process(nullptr, nullptr, 400);
        auto before = A::voice(*e);
        CHECK(before.carrierEnvelope.attenuation > 18 && !before.carrierEnvelope.finished);
        c.envelopeReverb = true; e->setControls(c);
        sameHistory(before, A::voice(*e));
        e->process(nullptr, nullptr, 1);
        auto slow = A::voice(*e);
        near(slow.carrierEnvelope.attenuation - before.carrierEnvelope.attenuation,
             std::min(before.carrierEnvelope.release, capFor(before.patch.carrier, 60)));
        CHECK(slow.carrierEnvelope.release == before.carrierEnvelope.release);
        c.envelopeReverb = false; e->setControls(c);
        sameHistory(slow, A::voice(*e));
        e->process(nullptr, nullptr, 1);
        near(A::voice(*e).carrierEnvelope.attenuation - slow.carrierEnvelope.attenuation,
             slow.carrierEnvelope.release);
    });

    test("live release refresh recomputes cap with the current note and operator RKS", [] {
        press78::Operator op; op.rr = 10; op.srr = 3; op.rks = 0;
        auto e = A::envelope(op, 36, false); e.attenuation = 18; e.stage = 3;
        op.rks = 3; op.srr = 1;
        e.updateRelease(op, 96, true);
        CHECK(e.attenuation == 18 && e.stage == 3);
        near(e.reverbRelease, capFor(op, 96));
        const double ordinary = e.release;
        e.next(true, true);
        near(e.attenuation - 18, std::min(ordinary, capFor(op, 96)));
        CHECK(e.release == ordinary);
    });

    test("output has exact zero unity small-signal slope and asymmetric bounded headroom", [] {
        CHECK(character::output(0) == 0);
        near((character::output(1e-7) - character::output(-1e-7)) / 2e-7, 1, 1e-12);
        double previous = character::output(-10);
        const double positive = 1 / (1 + std::tanh(.14));
        const double negative = -1 / (1 - std::tanh(.14));
        for (int i = 1; i <= 2000; ++i) {
            const double x = -10 + i * .01, y = character::output(x);
            CHECK(std::isfinite(y) && y > previous && y > negative && y < positive);
            near(y, referenceOutput(x), 2e-15); previous = y;
        }
        CHECK(character::output(.5) + character::output(-.5) < -.01);
        CHECK(character::output(1) < 2 * character::output(.5));
    });

    test("actual output path applies the curve before the linear circuit and retains dry bypass", [] {
        auto wet = engine(controls(false, true)), dry = engine(controls(false, false));
        press78::AnalogOutput reference; reference.prepare(48000);
        for (int i = 0; i < 4096; ++i) {
            const double x = .7 * std::sin(i * .173) + .3 * std::sin(i * .071);
            const auto a = A::output(*wet, x), b = A::output(*dry, x);
            // The curve's independent algebra is checked above. Here use its
            // identical rounded output to isolate circuit ordering: sub-ulp
            // differences between tanh forms accumulate in the slow SOS poles.
            near(a[0], reference.process(character::output(x)), 2e-12);
            CHECK(a[0] == a[1] && b[0] == x && b[1] == x);
        }
    });

    test("Reverb leaves held engine audio exact and changes only the released portion", [] {
        auto a = engine(controls(false, false)), b = engine(controls(true, false));
        a->noteOn(48, 110); b->noteOn(48, 110);
        CHECK(render(*a, 4096) == render(*b, 4096));
        a->noteOff(48); b->noteOff(48);
        const auto x = render(*a, 8192), y = render(*b, 8192);
        CHECK(x != y && b->activeVoices() == 1);
    });

    test("shared output consumes the summed native voices rather than separate saturation", [] {
        auto p = press78::initPatch(); p.carrier.tl = 0;
        auto a = A::voice(p, 60), b = A::voice(p, 67);
        auto linearA = a, linearB = b;
        auto wet = engine(controls(false, true));
        press78::AnalogOutput reference; reference.prepare(48000);
        bool jointDiffers = false;
        for (int i = 0; i < 1024; ++i) {
            const double x = a.next(controls(false, true), 1, 0);
            const double y = b.next(controls(false, true), 1, 0);
            CHECK(x == linearA.next(controls(false, false), 1, 0));
            CHECK(y == linearB.next(controls(false, false), 1, 0));
            jointDiffers = jointDiffers || std::abs(character::output(x + y)
                - character::output(x) - character::output(y)) > .001;
            near(A::output(*wet, x + y)[0], reference.process(character::output(x + y)), 2e-12);
        }
        CHECK(jointDiffers);
    });

    test("default character stays silent and reset clears active voices and output memory", [] {
        press78::Controls c; c.chorusMix = 1; c.drive = .3;
        auto dirty = engine(c), fresh = engine(c);
        const auto silence = render(*dirty, 1024);
        CHECK(std::all_of(silence.begin(), silence.end(), [](float x) { return x == 0; }));
        dirty->noteOn(36, 127); dirty->noteOn(60, 100);
        dirty->process(nullptr, nullptr, 8192); dirty->allNotesOff();
        dirty->process(nullptr, nullptr, 1024);
        CHECK(dirty->activeVoices() > 0);
        dirty->reset(); fresh->reset();
        CHECK(dirty->activeVoices() == 0);
        CHECK(render(*dirty, 1024) == render(*fresh, 1024));
        dirty->noteOn(48, 110); fresh->noteOn(48, 110);
        CHECK(render(*dirty, 8192) == render(*fresh, 8192));
    });

    test("live controls polyphony release and output processing allocate nothing", [] {
        auto c = controls(true, true); c.sustainMode = 1;
        auto e = engine(c);
        for (int n = 48; n < 60; ++n) e->noteOn(n, 127);
        std::array<float, 64> left{}, right{};
        allocations = 0; tracking = true;
        for (int i = 0; i < 128; ++i) {
            c.envelopeReverb = (i % 3) != 0; c.outputCircuit = (i % 5) != 0;
            e->setControls(c); e->sustainController(i);
            if (i == 16) e->allNotesOff();
            e->process(left.data(), right.data(), left.size());
        }
        tracking = false; CHECK(allocations == 0);
        for (float x : left) CHECK(std::isfinite(x));
        for (float x : right) CHECK(std::isfinite(x));
    });

    std::printf("Hardware character groups passed=%d failed=%d\n", passed, failed);
    return failed ? 1 : 0;
}
