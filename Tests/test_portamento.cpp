#include "Press78Engine.h"
#include "FirmwarePitch.h"

#include <cmath>
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <string>

namespace press78 {
struct Press78PortamentoTestAccess {
    static const Press78Engine::Voice& voice(const Press78Engine& e, int i) { return e.voices_[static_cast<std::size_t>(i)]; }
};
} // namespace press78

namespace {
using press78::Press78Engine;
using A = press78::Press78PortamentoTestAccess;
int passed = 0, failed = 0;
#define REQUIRE(x) do { if (!(x)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " #x); } while (false)
template<class F> void test(const char* name, F body) {
    try { body(); ++passed; std::printf("PASS %s\n", name); }
    catch (const std::exception& e) { ++failed; std::printf("FAIL %s: %s\n", name, e.what()); }
}
constexpr int kService = 120; // internal ticks per firmware main-loop pass (estimated 2.5 ms)

std::unique_ptr<Press78Engine> engine(bool on, int speed, int pitchModel = 1) {
    auto e = std::make_unique<Press78Engine>();
    e->prepare(48000.0);
    press78::Controls c;
    c.portamento = on; c.portamentoSpeed = speed; c.pitchModel = pitchModel;
    e->setControls(c);
    e->setPatch(press78::initPatch());
    e->process(nullptr, nullptr, kService); // Align note events with a service boundary.
    return e;
}
void services(Press78Engine& e, int n) { for (int i = 0; i < n; ++i) e.process(nullptr, nullptr, kService); }
int glideSteps(const Press78Engine& e, int slot) { return A::voice(e, slot).glideSteps; }
int glideOf(const Press78Engine& e, int note) {
    for (int i = 0; i < 12; ++i) if (A::voice(e, i).active && A::voice(e, i).held && A::voice(e, i).note == note) return A::voice(e, i).glideSteps;
    throw std::runtime_error("no held voice");
}
} // namespace

int main() {
    test("off: notes never glide, and controls sanitize the speed", [] {
        auto e = engine(false, 3);
        e->noteOn(60, 100); e->noteOff(60); e->noteOn(72, 100);
        REQUIRE(glideSteps(*e, 1) == 0 && A::voice(*e, 1).glideStep == 0);
        press78::Controls c; c.portamentoSpeed = 0; REQUIRE(press78::sanitizeControls(c).portamentoSpeed == 1);
        c.portamentoSpeed = 9; REQUIRE(press78::sanitizeControls(c).portamentoSpeed == 5);
    });
    test("the first note after reset has nothing to glide from", [] {
        auto e = engine(true, 3);
        e->noteOn(60, 100);
        REQUIRE(glideSteps(*e, 0) == 0 && A::voice(*e, 0).glideStep == 0);
    });
    test("every speed takes 2^(8-speed) passes whatever the interval", [] {
        for (int speed = 1; speed <= 5; ++speed) for (int interval : {1, 7, -12, 24}) {
            auto e = engine(true, speed);
            e->noteOn(60, 100);
            e->noteOn(60 + interval, 100);
            REQUIRE(glideSteps(*e, 1) == -interval * 32); // Starts at the previous pitch.
            const int passes = 1 << (8 - speed);
            services(*e, passes - 1);
            REQUIRE(glideSteps(*e, 1) != 0);
            services(*e, 1);
            REQUIRE(glideSteps(*e, 1) == 0);
            // A falling glide lands on zero and clears one pass later.
            services(*e, 1);
            REQUIRE(A::voice(*e, 1).glideOffset == 0 && A::voice(*e, 1).glideStep == 0);
        }
    });
    test("the glide is linear in 1/256 semitone, heard in 1/32 steps", [] {
        auto e = engine(true, 3); // 8 per pass per semitone of interval.
        e->noteOn(48, 100); e->noteOn(53, 100);
        for (int k = 1; k < 32; ++k) {
            services(*e, 1);
            const int offset = -5 * 256 + 5 * 8 * k;
            REQUIRE(A::voice(*e, 1).glideOffset == offset);
            REQUIRE(glideSteps(*e, 1) == static_cast<int>(std::floor(offset / 8.0)));
        }
    });
    test("Original pitch reads the command table at the glided coordinate", [] {
        auto e = engine(true, 2);
        e->noteOn(57, 100); e->noteOn(69, 100);
        services(*e, 10);
        const auto& v = A::voice(*e, 1);
        const double expected = 6.283185307179586 * press78::firmware_pitch::frequency(69, v.glideSteps) / 48000.0;
        REQUIRE(v.glideSteps < 0 && std::abs(v.carrierStep - expected) < 1e-15);
    });
    test("Equal pitch glides by the same coordinate", [] {
        auto e = engine(true, 2, 0);
        e->noteOn(57, 100); e->noteOn(69, 100);
        services(*e, 10);
        const auto& v = A::voice(*e, 1);
        REQUIRE(v.glideSteps < 0 && std::abs(v.glideMultiplier - std::pow(2.0, v.glideSteps / 384.0)) < 1e-15);
    });
    test("chords glide from the note played just before, and released keys still count", [] {
        auto e = engine(true, 4);
        e->noteOn(60, 100); e->noteOff(60);
        services(*e, 100);
        e->noteOn(64, 100); e->noteOn(67, 100);
        REQUIRE(glideOf(*e, 64) == -4 * 32);
        REQUIRE(glideOf(*e, 67) == -3 * 32);
    });
    test("the previous note is remembered while Portamento is off", [] {
        auto e = std::make_unique<Press78Engine>();
        e->prepare(48000.0);
        press78::Controls c; c.portamento = false; e->setControls(c);
        e->setPatch(press78::initPatch());
        e->noteOn(50, 100);
        c.portamento = true; e->setControls(c);
        e->noteOn(55, 100);
        REQUIRE(glideSteps(*e, 1) == -5 * 32);
    });
    std::printf("%d passed, %d failed\n", passed, failed);
    return failed ? 1 : 0;
}
