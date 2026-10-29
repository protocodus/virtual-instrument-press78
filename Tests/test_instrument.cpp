#include "Press78Instrument.h"
#include "FactoryVoices.h"

#include <cmath>
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using press78::Performance;
using press78::Press78Instrument;
using press78::Press78OutputBus;
int passed = 0, failed = 0;
#define REQUIRE(x) do { if (!(x)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " #x); } while (false)
template<class F> void test(const char* name, F body) {
    try { body(); ++passed; std::printf("PASS %s\n", name); }
    catch (const std::exception& e) { ++failed; std::printf("FAIL %s: %s\n", name, e.what()); }
}

// The Real profile on the AUX jack, so the amplifier Stage drive pushes is live.
press78::Controls realControls() {
    press78::Controls c;
    c.chorusMode = 1; c.chorusMix = 1.0; c.chorusCircuit = 1;
    c.outputJack = 1; c.powerSupply = 1; c.power = 25; c.masterGain = 0.5;
    return c;
}

// A two-note phrase, `block` frames at a time; events land at block starts.
template<class Unit, class Start>
std::vector<float> play(Unit& unit, Start start, std::size_t block, double rate = 48000.0) {
    constexpr std::size_t total = 24000;
    unit.prepare(rate);
    start(unit);
    std::vector<float> out(2 * total), left(total), right(total);
    for (std::size_t at = 0; at < total;) {
        if (at == 0) unit.noteOn(60, 100);
        if (at == 4800) unit.noteOn(67, 127);
        if (at == 16800) { unit.noteOff(60); unit.noteOff(67); }
        std::size_t frames = std::min(block, total - at);
        for (std::size_t edge : {std::size_t{4800}, std::size_t{16800}})
            if (at < edge && at + frames > edge) frames = edge - at;
        unit.process(left.data() + at, right.data() + at, frames);
        at += frames;
    }
    for (std::size_t i = 0; i < total; ++i) { out[2 * i] = left[i]; out[2 * i + 1] = right[i]; }
    return out;
}

double rms(const std::vector<float>& x) {
    double sum = 0;
    for (float v : x) sum += double(v) * v;
    return std::sqrt(sum / double(x.size()));
}
} // namespace

int main() {
    const auto patch = press78::factoryPatch(2); // PSS 02 Electric Piano 1

    test("mod wheel: no vibrato patch gets the patch depth scaled; PMS at least 3", [] {
        press78::Patch p = press78::initPatch();
        press78::Controls c; c.vibratoDepth = 2.0;
        press78::applyModWheel(0.0, p, c);
        REQUIRE(!p.vibrato && c.vibratoDepth == 2.0);
        press78::applyModWheel(0.25, p, c);
        REQUIRE(p.vibrato && p.pms == 3 && c.vibratoDepth == 0.5);
    });
    test("mod wheel: a vibrato patch gets the wheel on top and keeps a higher PMS", [] {
        press78::Patch p = press78::initPatch(); p.vibrato = true; p.pms = 5;
        press78::Controls c; c.vibratoDepth = 1.0;
        press78::applyModWheel(0.5, p, c);
        REQUIRE(p.vibrato && p.pms == 5 && c.vibratoDepth == 1.5);
    });
    test("defaults play exactly what the output bus plays, at 48 and 44.1 kHz", [&] {
        for (double rate : {48000.0, 44100.0}) {
            auto bus = std::make_unique<Press78OutputBus>();
            auto instrument = std::make_unique<Press78Instrument>();
            const auto a = play(*bus, [&](Press78OutputBus& u) { u.setControls(realControls()); u.setPatch(patch, true); }, 64, rate);
            const auto b = play(*instrument, [&](Press78Instrument& u) { u.apply(patch, realControls(), Performance{}, true); }, 64, rate);
            REQUIRE(a == b && rms(a) > 1e-3);
        }
    });
    test("block size does not change the output, Double and drive included", [&] {
        Performance perf; perf.doubleMode = true; perf.doubleDetuneCents = 12; perf.stageDriveDb = 9;
        const auto start = [&](Press78Instrument& u) { u.apply(patch, realControls(), perf, true); };
        auto a = std::make_unique<Press78Instrument>(), b = std::make_unique<Press78Instrument>();
        const auto x = play(*a, start, 64), y = play(*b, start, 997);
        REQUIRE(x == y);
    });
    test("Preamp ignores Stage drive; AUX keeps its level within 6 dB while it colours", [&] {
        const auto render = [&](int jack, double drive) {
            auto c = realControls(); c.outputJack = jack;
            Performance perf; perf.stageDriveDb = drive;
            auto u = std::make_unique<Press78Instrument>();
            return play(*u, [&](Press78Instrument& i) { i.apply(patch, c, perf, true); }, 64);
        };
        REQUIRE(render(0, 0) == render(0, 12));
        const auto clean = render(1, 0), driven = render(1, 12);
        REQUIRE(clean != driven);
        REQUIRE(std::abs(20 * std::log10(rms(driven) / rms(clean))) < 6.0);
    });
    test("Double at zero spread is mono; at full spread the units differ", [&] {
        const auto render = [&](double spread) {
            Performance perf; perf.doubleMode = true; perf.doubleSpread = spread; perf.doubleDetuneCents = 20;
            auto u = std::make_unique<Press78Instrument>();
            return play(*u, [&](Press78Instrument& i) { i.apply(patch, realControls(), perf, true); }, 64);
        };
        const auto mono = render(0.0), wide = render(1.0);
        bool same = true, differ = false;
        for (std::size_t i = 0; i < mono.size(); i += 2) {
            same = same && mono[i] == mono[i + 1];
            differ = differ || std::abs(wide[i] - wide[i + 1]) > 1e-4f;
        }
        REQUIRE(same && differ);
    });
    test("Double joins held notes and leaves after its fade", [&] {
        auto u = std::make_unique<Press78Instrument>();
        u->prepare(48000.0);
        Performance perf;
        u->apply(patch, realControls(), perf, true);
        u->noteOn(60, 100);
        std::vector<float> l(4800), r(4800);
        u->process(l.data(), r.data(), l.size());
        const auto one = u->activeVoices();
        perf.doubleMode = true;
        u->apply(patch, realControls(), perf, false);
        u->process(l.data(), r.data(), l.size());
        REQUIRE(one == 1 && u->activeVoices() == 2);
        perf.doubleMode = false;
        u->apply(patch, realControls(), perf, false);
        u->process(l.data(), r.data(), l.size());
        REQUIRE(u->activeVoices() == 1);
    });
    test("null outputs still advance time", [&] {
        auto a = std::make_unique<Press78Instrument>(), b = std::make_unique<Press78Instrument>();
        for (auto* u : {a.get(), b.get()}) { u->prepare(48000.0); u->apply(patch, realControls(), Performance{}, true); u->noteOn(60, 100); }
        std::vector<float> l(256), r(256), l2(256), r2(256);
        a->process(nullptr, nullptr, 256); a->process(l.data(), r.data(), 256);
        b->process(l2.data(), r2.data(), 256); b->process(l2.data(), r2.data(), 256);
        REQUIRE(l == l2 && r == r2);
    });

    std::printf("%d passed, %d failed\n", passed, failed);
    return failed == 0 ? 0 : 1;
}
