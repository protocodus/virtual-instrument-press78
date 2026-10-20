#include "Press78Engine.h"
#include "FactoryVoices.h"
#include "RecordedChorus.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <memory>
#include <new>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
bool trackAllocations = false;
std::size_t allocations = 0;
}
void* operator new(std::size_t n) {
    if (trackAllocations) ++allocations;
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

namespace {
using press78::Press78Engine;
constexpr double pi = 3.1415926535897932384626433832795;
int passed = 0, failed = 0;
#define CHECK(x) do { if (!(x)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " #x); } while (false)

template<class F> void test(const char* name, F&& body) {
    try { body(); ++passed; std::printf("PASS %s\n", name); }
    catch (const std::exception& e) { ++failed; std::printf("FAIL %s: %s\n", name, e.what()); }
}
press78::Controls transparent() {
    press78::Controls c;
    c.masterGain = 1.0; c.toneCutoffHz = 0.0; c.dcBlock = false; c.outputLimit = false;
    c.outputCircuit = false; c.envelopeReverb = false;
    return c;
}
std::unique_ptr<Press78Engine> engine(double sr = 48000.0) {
    auto e = std::make_unique<Press78Engine>();
    e->prepare(sr); e->setControls(transparent()); e->setPatch(press78::initPatch());
    return e;
}
std::vector<float> render(Press78Engine& e, std::size_t n) {
    std::vector<float> l(n), r(n);
    e.process(l.data(), r.data(), n);
    return l;
}
double rms(const std::vector<float>& x, std::size_t first = 0) {
    double energy = 0.0;
    for (std::size_t i = first; i < x.size(); ++i) energy += static_cast<double>(x[i]) * x[i];
    return std::sqrt(energy / static_cast<double>(x.size() - first));
}
double frequency(const std::vector<float>& x, double sr, std::size_t begin) {
    double first = -1.0, last = -1.0;
    int cycles = -1;
    for (std::size_t i = std::max<std::size_t>(1, begin); i < x.size(); ++i) if (x[i-1] <= 0 && x[i] > 0) {
        const double crossing = static_cast<double>(i - 1) + -x[i-1] / (x[i] - x[i-1]);
        if (cycles == -1) first = crossing;
        last = crossing; ++cycles;
    }
    return cycles > 0 ? cycles * sr / (last - first) : 0.0;
}
void finiteBounded(const std::vector<float>& x, double limit = 1.0) {
    for (const float y : x) CHECK(std::isfinite(y) && std::abs(y) <= limit);
}
} // namespace

int main() {
    test("engine instance fits192KiB Rack budget", [] {
        CHECK(sizeof(Press78Engine) <= 192 * 1024);
        std::printf("engine_bytes=%zu\n", sizeof(Press78Engine));
    });
    test("documented33-byte voice fields decode independently", [] {
        std::array<std::uint8_t, 33> b{};
        b[1] = 0xB5; b[2] = 0x21; b[3] = 0xFF; b[5] = 0xDA;
        b[7] = 0xE7; b[9] = 0xD5; b[11] = 0xAA; b[13] = 0xC8;
        b[15] = 0x38; b[16] = 0x63; b[20] = 0xF4; b[22] = 0xFE; b[24] = 0xC0;
        const auto p = press78::decodeVoice(b);
        CHECK(p.modulator.mul == 5 && p.modulator.dt1 == -3 && p.carrier.dt1 == 2);
        CHECK(p.modulator.tl == 127 && p.modulator.lksHi == 13 && p.modulator.lksLo == 10);
        CHECK(p.modulator.rks == 3 && p.modulator.ar == 39);
        CHECK(p.modulator.amEnable && p.modulator.dt2 && p.modulator.d1r == 21);
        CHECK(p.modulator.wave == 2 && p.modulator.d2r == 42 && p.modulator.d1l == 12 && p.modulator.rr == 8);
        CHECK(p.feedback == 7 && p.pms == 6 && p.ams == 3 && p.modulator.srr == 4);
        CHECK(p.vibratoDelay == 126 && p.vibrato && p.sustain && p.rawData == b);
    });
    test("nominal sine has explicit32-frame latency and correct amplitude", [] {
        auto e = engine(); e->noteOn(69, 127);
        const auto x = render(*e, 48000);
        for (int i = 0; i < 32; ++i) CHECK(x[static_cast<std::size_t>(i)] == 0.0f);
        double error = 0.0;
        for (std::size_t i = 32; i < x.size(); ++i)
            error = std::max(error, std::abs(x[i] - 0.8 * std::sin(2 * pi * 440.0 * (static_cast<double>(i) - 31) / 48000.0)));
        CHECK(error < 3.1e-8); CHECK(e->latencySamples() == 32);
    });
    test("render block boundaries are bit invariant", [] {
        auto a = engine(44100), b = engine(44100);
        auto c = transparent(); c.clockOffsetPpm = 700; c.clockDriftPpm = 1200;
        c.chorusMix = 0.7; c.noiseRms = 0.0001; c.drive = 0.3;
        a->setControls(c); b->setControls(c);
        a->noteOn(62, 101); b->noteOn(62, 101);
        const auto full = render(*a, 17003);
        std::vector<float> pieces(full.size()), r(full.size());
        std::size_t position = 0, block = 1;
        while (position < pieces.size()) {
            const auto n = std::min(block, pieces.size() - position);
            b->process(pieces.data() + position, r.data() + position, n);
            position += n; block = block * 7 % 251 + 1;
        }
        CHECK(full == pieces);
    });
    test("output-rate conversion preserves440Hz and passband level", [] {
        for (const int sr : {8000, 32000, 44100, 48000, 88200, 96000, 192000}) {
            auto e = engine(sr); e->noteOn(69, 127);
            const auto x = render(*e, static_cast<std::size_t>(sr));
            CHECK(std::abs(frequency(x, sr, static_cast<std::size_t>(sr / 10)) - 440) < 0.003);
            CHECK(std::abs(rms(x, static_cast<std::size_t>(sr / 10)) - 0.8 / std::sqrt(2.0)) < 0.002);
        }
    });
    test("zero attack and TL99 suppress allocation", [] {
        auto e = engine(); auto p = press78::initPatch();
        p.carrier.ar = 0; e->setPatch(p); e->noteOn(60, 100);
        CHECK(e->activeVoices() == 0); CHECK(rms(render(*e, 1024)) == 0);
        p.carrier.ar = 63; p.carrier.tl = 99; e->setPatch(p); e->noteOn(60, 100);
        CHECK(e->activeVoices() == 0);
    });
    test("zero-height D1 plateau is independent of its unused rate", [] {
        auto e = engine();
        for (const int attack : {32, 63}) for (int wave = 0; wave < 4; ++wave) {
            auto p = press78::initPatch();
            p.carrier.ar = attack; p.carrier.wave = wave;
            p.carrier.d1l = 0; p.carrier.d1r = 0; p.carrier.d2r = 0;
            e->reset(); e->setPatch(p); e->noteOn(69, 127);
            const auto reference = render(*e, 2048);
            for (int rate = 1; rate <= 63; ++rate) {
                p.carrier.d1r = rate;
                e->reset(); e->setPatch(p); e->noteOn(69, 127);
                CHECK(render(*e, reference.size()) == reference);
            }
        }
    });
    test("zero-height D1 enters D2 immediately even with zero D1 rate", [] {
        auto e = engine();
        for (const int rate : {0, 1, 24, 63}) {
            auto p = press78::initPatch();
            p.carrier.d1l = 0; p.carrier.d1r = rate; p.carrier.d2r = 48;
            e->reset(); e->setPatch(p); e->noteOn(69, 127);
            const auto audio = render(*e, 256);
            // AR63 peaks on tick0; D2 starts on tick1. Derive the intended
            // postattack line from the model's unchanged D2 rate, not D1.
            const double dbPerTick = 96.0 / (48000.0 * 48.0 * std::pow(2.0, -48.0 / 4.0));
            for (std::size_t frame = 32; frame < audio.size(); ++frame) {
                const double tick = static_cast<double>(frame - 32);
                const double expected = 0.8 * std::sin(2*pi*440*(tick+1)/48000)
                    * std::pow(10.0, -tick*dbPerTick/20.0);
                CHECK(std::abs(audio[frame] - expected) < 3.1e-8);
            }
        }
    });
    test("positive D1 target with zero D1 rate holds before D2", [] {
        auto e = engine();
        e->noteOn(69, 127); const auto reference = render(*e, 4096);
        for (int target = 1; target <= 15; ++target) {
            auto p = press78::initPatch();
            p.carrier.d1l = target; p.carrier.d1r = 0; p.carrier.d2r = 63;
            e->reset(); e->setPatch(p); e->noteOn(69, 127);
            CHECK(render(*e, reference.size()) == reference);
        }
    });
    test("release interrupts attack D1 and D2 after endpoint correction", [] {
        for (int stage = 0; stage < 3; ++stage) {
            auto e = engine(); auto p = press78::initPatch();
            p.carrier.ar = stage == 0 ? 24 : 63;
            p.carrier.d1l = stage == 1 ? 15 : 0;
            p.carrier.d1r = stage == 1 ? 24 : 63;
            p.carrier.d2r = 0; p.carrier.rr = 15;
            e->setPatch(p); e->noteOn(69, 127);
            const auto held = render(*e, 256);
            CHECK(rms(held, 32) > 1e-5); CHECK(e->activeVoices() == 1);
            e->noteOff(69); finiteBounded(render(*e, 512));
            CHECK(e->activeVoices() == 0);
            CHECK(rms(render(*e, 128)) == 0.0);
        }
    });
    test("velocity-zero note-on releases rather than allocates", [] {
        auto e = engine(); auto p = press78::initPatch(); p.carrier.rr = 15;
        e->setPatch(p); e->noteOn(60, 100); render(*e, 512); e->noteOn(60, 0); render(*e, 512);
        CHECK(e->activeVoices() == 0);
    });
    test("MIDI and CV identical pitches release independently", [] {
        auto e = engine(); auto p = press78::initPatch(); p.carrier.rr = 15;
        e->setPatch(p); e->noteOn(60, 100, 0); e->noteOn(60, 100, 1); render(*e, 512);
        e->noteOff(60, 1); render(*e, 512); CHECK(e->activeVoices() == 1);
        e->noteOff(60, 1); render(*e, 512); CHECK(e->activeVoices() == 1);
        e->noteOff(60, 0); render(*e, 512); CHECK(e->activeVoices() == 0);
    });
    test("overlapping same-note releases are FIFO", [] {
        auto e = engine(); auto p = press78::initPatch(); p.carrier.rr = 15;
        e->setPatch(p); e->noteOn(60, 100); render(*e, 200); e->noteOn(60, 100);
        e->noteOff(60); render(*e, 512); CHECK(e->activeVoices() == 1);
        e->noteOff(60); render(*e, 512); CHECK(e->activeVoices() == 0);
    });
    test("pedal postpones release and key pedal-up flushes deferred notes", [] {
        auto e = engine(); auto p = press78::initPatch(); p.carrier.rr = 15;
        e->setPatch(p); e->noteOn(60, 127); e->sustainPedal(true); e->noteOff(60);
        CHECK(rms(render(*e, 4800), 1000) > 0.5); CHECK(e->activeVoices() == 1);
        e->sustainPedal(false); render(*e, 512); CHECK(e->activeVoices() == 0);
    });
    test("patch sustain switches to its separate release rate", [] {
        auto e = engine(); auto p = press78::initPatch();
        p.carrier.rr = 15; p.carrier.srr = 0; p.sustain = true;
        e->setPatch(p); e->noteOn(60, 127); render(*e, 512); e->noteOff(60);
        CHECK(rms(render(*e, 4800), 1000) > 0.5); CHECK(e->activeVoices() == 1);
    });
    test("twelve-voice allocation steals oldest with bounded tail", [] {
        auto e = engine();
        for (int n = 0; n < 12; ++n) e->noteOn(60 + n, 100);
        CHECK(e->activeVoices() == 12); e->noteOn(84, 100); CHECK(e->activeVoices() == 12);
        e->noteOff(60); render(*e, 12000); CHECK(e->activeVoices() == 12);
        auto c = transparent(); c.polyphony = 3; e->setControls(c); CHECK(e->activeVoices() == 3);
        finiteBounded(render(*e, 2048), 20);
    });
    test("program changes preserve held voice snapshot", [] {
        auto a = engine(), b = engine(); a->noteOn(60, 127); b->noteOn(60, 127);
        render(*a, 1024); render(*b, 1024);
        auto p = press78::initPatch(); p.carrier.mul = 3;
        a->setPatch(p); CHECK(render(*a, 4096) == render(*b, 4096));
    });
    test("explicit patch edits affect the held voice without retrigger", [] {
        auto a = engine(), b = engine(); a->noteOn(60, 127); b->noteOn(60, 127);
        render(*a, 1024); render(*b, 1024);
        auto p = press78::initPatch(); p.carrier.mul = 3;
        a->setPatch(p, true); CHECK(render(*a, 4096) != render(*b, 4096));
        CHECK(a->activeVoices() == 1);
    });
    test("live operator mute preserves the held voice for unmute", [] {
        auto e = engine(); e->noteOn(60, 127); render(*e, 512);
        auto p = press78::initPatch(); p.carrier.tl = 127; e->setPatch(p, true);
        render(*e, 512); CHECK(e->activeVoices() == 1); CHECK(rms(render(*e, 512)) == 0);
        p.carrier.tl = 0; e->setPatch(p, true); CHECK(rms(render(*e, 4096), 100) > 0.5);
    });
    test("velocity response follows exposed carrier exponent", [] {
        auto a = engine(), b = engine(); a->noteOn(60, 127); b->noteOn(60, 64);
        const double ratio = rms(render(*b, 8000), 1000) / rms(render(*a, 8000), 1000);
        CHECK(std::abs(ratio - 64.0 / 127) < 1e-6);
        auto c = transparent(); c.velocitySensitivity = 0;
        a->reset(); b->reset(); a->setControls(c); b->setControls(c);
        a->noteOn(60, 127); b->noteOn(60, 1); CHECK(render(*a, 4000) == render(*b, 4000));
    });
    test("Original velocity curve is the PSS-780 Mode 99 table, in dB times sensitivity", [] {
        // Velocity -> carrier TL addend pairs read from the PSS-780 program.
        constexpr int table[][2] = {{1, 31}, {2, 31}, {3, 30}, {8, 26}, {16, 21}, {32, 15},
                                    {64, 8}, {96, 3}, {117, 1}, {118, 0}, {127, 0}};
        for (const auto& row : table) for (const double sensitivity : {1.0, 0.5, 2.0}) {
            auto c = transparent(); c.velocityCurve = 1; c.velocitySensitivity = sensitivity;
            auto a = engine(), b = engine(); a->setControls(c); b->setControls(c);
            a->noteOn(60, 127); b->noteOn(60, row[0]);
            const double db = 20 * std::log10(rms(render(*b, 8000), 1000) / rms(render(*a, 8000), 1000));
            CHECK(std::abs(db + 0.75 * row[1] * sensitivity) < 1e-6);
        }
        // Velocity to FM keeps its linear law: the modulator differs, the curve does not.
        auto c = transparent(); c.velocitySensitivity = 0; c.velocityToModulation = 1;
        auto legacy = engine(), original = engine(); c.velocityCurve = 1; original->setControls(c);
        c.velocityCurve = 0; legacy->setControls(c);
        auto p = press78::initPatch(); p.modulator.tl = 20; legacy->setPatch(p); original->setPatch(p);
        legacy->noteOn(60, 40); original->noteOn(60, 40);
        CHECK(render(*legacy, 4000) == render(*original, 4000));
        c.velocityCurve = 9; CHECK(press78::sanitizeControls(c).velocityCurve == 1);
    });
    test("ratio0 is half and coarse detune is600cents", [] {
        auto e = engine(); auto p = press78::initPatch(); p.carrier.mul = 0;
        e->setPatch(p); e->noteOn(69, 127);
        CHECK(std::abs(frequency(render(*e, 48000), 48000, 5000) - 220) < 0.002);
        e->reset(); p.carrier.mul = 1; p.carrier.dt2 = true; e->setPatch(p); e->noteOn(69, 127);
        CHECK(std::abs(frequency(render(*e, 48000), 48000, 5000) - 440 * std::sqrt(2.0)) < 0.002);
    });
    test("four waveform families remain distinct and half waves unipolar", [] {
        std::array<double, 4> energy{};
        for (int w = 0; w < 4; ++w) {
            auto e = engine(); auto p = press78::initPatch(); p.carrier.wave = w;
            e->setPatch(p); e->noteOn(69, 127); const auto x = render(*e, 48000);
            energy[static_cast<std::size_t>(w)] = rms(x, 4000);
            if (w >= 2) for (const auto y : x) CHECK(y >= 0.0);
        }
        CHECK(energy[0] > energy[1] && energy[1] > energy[2] && energy[2] > energy[3]);
    });
    test("common clock offset moves pitch with nominal tune unchanged", [] {
        auto e = engine(); auto c = transparent(); c.clockOffsetPpm = 10000;
        e->setControls(c); e->noteOn(69, 127);
        CHECK(std::abs(frequency(render(*e, 48000), 48000, 5000) - 444.4) < 0.003);
    });
    test("clock change advances envelope as well as oscillator", [] {
        auto a = engine(), b = engine(); auto p = press78::initPatch(); p.carrier.ar = 24;
        a->setPatch(p); b->setPatch(p); auto c = transparent(); c.clockOffsetPpm = 20000;
        b->setControls(c);
        // Give the ordinary-clock reference the same oscillator pitch, so
        // the difference primarily measures envelope time, not sine cycles.
        c.clockOffsetPpm = 0; c.masterTuneCents = 1200 * std::log2(1.02);
        a->setControls(c); a->noteOn(93, 127); b->noteOn(93, 127);
        const auto x = render(*a, 2400), y = render(*b, 2400);
        CHECK(rms(y, 1800) > rms(x, 1800) * 1.01);
    });
    test("allSoundOff clears synthesis and causal effect history", [] {
        auto e = engine(); auto c = transparent(); c.chorusMix = 1;
        e->setControls(c); e->noteOn(60, 127); render(*e, 4800); e->allSoundOff();
        CHECK(e->activeVoices() == 0); CHECK(rms(render(*e, 4800)) == 0.0);
    });
    test("chorus changes stereo side while preserving raw midpoint", [] {
        auto a = engine(), b = engine(); auto c = transparent(); c.chorusMix = 0.8;
        b->setControls(c); a->noteOn(69, 127); b->noteOn(69, 127);
        const auto mono = render(*a, 10000);
        std::vector<float> left(10000), right(10000); b->process(left.data(), right.data(), left.size());
        double sideEnergy = 0;
        for (std::size_t i = 0; i < mono.size(); ++i) {
            CHECK(std::abs((left[i] + right[i]) * 0.5 - mono[i]) < 1e-7);
            sideEnergy += (left[i] - right[i]) * (left[i] - right[i]);
        }
        CHECK(sideEnergy > 10);
    });
    test("zero stereo width collapses creative chorus", [] {
        auto a = engine(), b = engine(); auto c = transparent(); c.chorusMix = 1; c.stereoWidth = 0;
        b->setControls(c); a->noteOn(69, 127); b->noteOn(69, 127);
        CHECK(render(*a, 10000) == render(*b, 10000));
    });
    test("filter and drive controls alter sound with bounded output", [] {
        auto a = engine(), b = engine(); auto c = transparent(); c.drive = 1; c.toneCutoffHz = 200;
        b->setControls(c); a->noteOn(93, 127); b->noteOn(93, 127);
        CHECK(rms(render(*b, 4800)) < rms(render(*a, 4800)) * 0.1);
    });
    test("drive approaches its exact dry bypass continuously", [] {
        auto a = engine(), b = engine(); auto c = transparent(); c.drive = 1e-9;
        b->setControls(c); a->noteOn(60, 127); b->noteOn(60, 127);
        const auto x = render(*a, 4096), y = render(*b, 4096);
        for (std::size_t i = 0; i < x.size(); ++i) CHECK(std::abs(x[i] - y[i]) < 1e-7);
    });
    test("circuit runtime is deterministic across reset at all supported rates", [] {
        for (const int sr : {8000, 44100, 44117, 48000, 96000, 192000}) {
            press78::AnalogOutput f; f.prepare(sr);
            std::array<double, 1024> impulse{};
            for (std::size_t i = 0; i < impulse.size(); ++i) {
                impulse[i] = f.process(i == 0 ? 1.0 : 0.0); CHECK(std::isfinite(impulse[i]));
            }
            f.reset();
            for (std::size_t i = 0; i < impulse.size(); ++i) CHECK(f.process(i == 0 ? 1.0 : 0.0) == impulse[i]);
        }
    });
    test("circuit bypass continues filter state for smooth re-enable", [] {
        auto a = engine(), b = engine(); auto p = press78::initPatch(); p.carrier.wave = 2;
        a->setPatch(p); b->setPatch(p); auto c = transparent(); c.outputCircuit = true;
        a->setControls(c); a->noteOn(60, 127); b->noteOn(60, 127);
        render(*a, 4800); render(*b, 4800); b->setControls(c);
        const auto x = render(*a, 12000), y = render(*b, 12000);
        for (std::size_t i = 4800; i < x.size(); ++i) CHECK(std::abs(x[i] - y[i]) < 1e-7);
    });
    test("all100 imported factory presets render finite audible output", [] {
        auto e = engine(); press78::Controls c;
        e->setControls(c);
        for (const auto& voice : press78::kFactoryVoices) {
            e->reset(); e->setPatch(press78::decodeVoice(voice.bytes)); e->noteOn(60, 100);
            const auto x = render(*e, 12000);
            finiteBounded(x); CHECK(rms(x, 32) > 1e-7);
            e->noteOff(60); finiteBounded(render(*e, 4800));
        }
    });
    test("invalid controls and malformed patch fields clamp safely", [] {
        auto e = engine(std::numeric_limits<double>::quiet_NaN());
        CHECK(e->sampleRate() == 48000);
        auto p = press78::initPatch(); p.carrier.ar = -999; p.modulator.wave = 88; p.feedback = 900;
        e->setPatch(p); CHECK(e->patch().carrier.ar == 0 && e->patch().modulator.wave == 3 && e->patch().feedback == 7);
        auto c = transparent(); c.masterGain = std::numeric_limits<double>::infinity();
        c.lfoRateHz = std::numeric_limits<double>::quiet_NaN(); c.clockOffsetPpm = -1e30; c.polyphony = -7;
        e->setControls(c); CHECK(e->controls().masterGain == .25 && e->controls().lfoRateHz == 5.24);
        CHECK(e->controls().clockOffsetPpm == -20000 && e->controls().polyphony == 1);
        finiteBounded(render(*e, 1000));
    });
    test("all extreme finite controls remain finite and limited", [] {
        auto e = engine(8000); auto p = press78::initPatch();
        p.modulator.tl = 0; p.modulator.mul = 15; p.modulator.dt2 = true;
        p.carrier.wave = 3; p.carrier.mul = 15; p.carrier.lksLo = 1;
        p.feedback = 7; p.vibrato = true; p.pms = 7; p.ams = 3;
        p.carrier.amEnable = p.modulator.amEnable = true; e->setPatch(p);
        press78::Controls c; c.masterGain = 2; c.pitchBendSemitones = 48; c.masterTuneCents = 1200;
        c.modulationAmount = 2; c.lfoRateHz = 30; c.vibratoDepth = c.tremoloDepth = 4;
        c.clockOffsetPpm = 20000; c.clockDriftPpm = 10000; c.chorusMix = 1;
        c.chorusDepthMs = 8; c.chorusRateHz = 8; c.stereoWidth = 2; c.noiseRms = .02; c.drive = 1;
        e->setControls(c); for (int i = 0; i < 25; ++i) e->noteOn(i * 5, 127);
        finiteBounded(render(*e, 8000));
    });
    test("null outputs advance state and zero-length output is inert", [] {
        auto a = engine(), b = engine(); a->noteOn(60, 127); b->noteOn(60, 127);
        a->process(nullptr, nullptr, 0); CHECK(render(*a, 1024) == render(*b, 1024));
        a->process(nullptr, nullptr, 1024); render(*b, 1024); CHECK(render(*a, 1024) == render(*b, 1024));
        std::array<float, 128> out{}; a->process(out.data(), out.data(), out.size());
        for (const auto x : out) CHECK(std::isfinite(x));
    });
    test("render and realtime control/note paths do not allocate", [] {
        auto e = engine(); std::array<float, 2048> l{}, r{}; auto c = transparent();
        allocations = 0; trackAllocations = true;
        for (int n = 0; n < 24; ++n) e->noteOn(48 + n, 100, n % 2);
        e->setPatch(press78::initPatch(), true); e->setControls(c);
        e->process(l.data(), r.data(), l.size()); e->noteOff(60, 0); e->sustainPedal(true);
        e->allNotesOff(); e->sustainPedal(false); e->process(l.data(), r.data(), l.size()); e->allSoundOff();
        trackAllocations = false; CHECK(allocations == 0);
    });
    test("recorded chorus depth stays causal within history at all control extremes", [] {
        for (const double depth : {0.0, press78::RecordedChorusProfile::depthMs, 2.0, 8.0})
            for (int i = 0; i < 10000; ++i) {
                const double d = press78::RecordedChorus::delayMilliseconds(2*pi*i/10000.0, depth);
                CHECK(d > 0.38 && d * .001 * 192000 < 4094);
            }
    });
    test("recorded effect is causal preserves mid and deterministically resets", [] {
        press78::RecordedChorus c; c.prepare(48000, 173.25);
        std::array<double, 4000> l{}, r{};
        for (std::size_t i = 0; i < l.size(); ++i) {
            const double x = std::sin(.1*i); c.process(x,l[i],r[i]);
            CHECK(std::abs(.5*(l[i]+r[i])-x) < 2e-16);
            CHECK(std::max(std::abs(l[i]),std::abs(r[i])) < 1.627);
        }
        c.reset(173.25);
        for (std::size_t i = 0; i < l.size(); ++i) {
            double a,b; c.process(std::sin(.1*i),a,b); CHECK(a == l[i] && b == r[i]);
        }
    });
    test("native recorded chorus matches the standalone effect and keeps midpoint", [] {
        auto a = engine(), b = engine(); auto c = transparent();
        c.chorusMode = 1; c.chorusMix = 1;
        c.chorusRateHz = press78::RecordedChorusProfile::rateHz;
        c.chorusDepthMs = press78::RecordedChorusProfile::depthMs;
        a->setControls(c); a->noteOn(60,127); b->noteOn(60,127);
        std::vector<float> l(24000),r(24000); a->process(l.data(),r.data(),l.size());
        const auto dry = render(*b,l.size()); press78::RecordedChorus effect; effect.prepare(48000);
        double difference = 0;
        for (std::size_t i = 0; i < l.size(); ++i) {
            double x,y; effect.process(dry[i],x,y);
            CHECK(std::abs(l[i]-x) < 1.2e-7 && std::abs(r[i]-y) < 1.2e-7);
            CHECK(std::abs(.5*(l[i]+r[i])-dry[i]) < 1.2e-7);
            difference += std::abs(l[i]-r[i]);
        }
        CHECK(difference > 100); CHECK(a->latencySamples() == 32);
    });
    test("recorded chorus mode transitions are smoothed and block invariant", [] {
        auto a=engine(),b=engine(); auto c=transparent(); c.chorusMix=1;
        c.chorusRateHz=press78::RecordedChorusProfile::rateHz;
        c.chorusDepthMs=press78::RecordedChorusProfile::depthMs;
        a->setControls(c);b->setControls(c);a->noteOn(60,127);b->noteOn(60,127);
        CHECK(render(*a,3000)==render(*b,3000)); c.chorusMode=1;a->setControls(c);b->setControls(c);
        const auto x=render(*a,12000);std::vector<float>y; y.reserve(x.size());
        while(y.size()<x.size()) {const auto z=render(*b,std::min<std::size_t>(37,x.size()-y.size()));y.insert(y.end(),z.begin(),z.end());}
        CHECK(x==y); finiteBounded(x,2);
        for(std::size_t i=1;i<x.size();++i)CHECK(std::abs(x[i]-x[i-1])<.2);
    });
    test("recorded mode nonfinite controls and inputs are bounded without allocations", [] {
        auto e=engine(192000);auto c=transparent();c.chorusMode=100;c.chorusMix=1;c.chorusDepthMs=8;
        e->setControls(c);CHECK(e->controls().chorusMode==1);e->noteOn(60,127);
        std::array<float,1024>l{},r{};allocations=0;trackAllocations=true;
        e->setChorusTime(-32.0/48000);e->process(l.data(),r.data(),l.size());
        trackAllocations=false;CHECK(allocations==0);
        press78::RecordedChorus f;f.setParameters(NAN,NAN);f.prepare(NAN,NAN);
        double x,y;f.process(NAN,x,y);CHECK(x==0&&y==0);
    });
    test("legacy noise requests preserve exact silence and both musical channels", [] {
        struct Legacy { int model; double level; };
        const std::array<Legacy,7> requests{{
            {0,.001}, {1,.002}, {1,.02}, {9,999}, {-9,-1},
            {std::numeric_limits<int>::max(),std::numeric_limits<double>::infinity()},
            {std::numeric_limits<int>::min(),std::numeric_limits<double>::quiet_NaN()}
        }};
        for (const double sr : {8000.,48000.,192000.}) for (const auto request : requests) {
            auto a=engine(sr),b=engine(sr);press78::Controls c;
            c.chorusMode=1;c.chorusMix=1;c.clockDriftPpm=20;
            a->setControls(c);c.noiseModel=request.model;c.noiseRms=request.level;b->setControls(c);
            CHECK(b->controls().noiseModel==0 && b->controls().noiseRms==0.0);
            std::array<float,2048>al{},ar{},bl{},br{};
            a->process(al.data(),ar.data(),al.size());b->process(bl.data(),br.data(),bl.size());
            for(std::size_t i=0;i<al.size();++i) CHECK(al[i]==0 && ar[i]==0 && bl[i]==0 && br[i]==0);
            const auto p=press78::decodeVoice(press78::kFactoryVoices[97].bytes);
            a->setPatch(p);b->setPatch(p);a->noteOn(60,127);b->noteOn(60,127);
            a->process(al.data(),ar.data(),al.size());b->process(bl.data(),br.data(),bl.size());
            CHECK(al==bl && ar==br);
            CHECK(std::any_of(al.begin(),al.end(),[](float x){return x!=0;}));
        }
    });
    test("legacy noise automation is inaudible and allocation free", [] {
        auto a=engine(),b=engine();press78::Controls c;c.chorusMode=1;c.chorusMix=1;
        a->setControls(c);b->setControls(c);a->noteOn(60,127);b->noteOn(60,127);
        CHECK(render(*a,4096)==render(*b,4096));
        std::array<float,64>al{},ar{},bl{},br{};bool identical=true;
        allocations=0;trackAllocations=true;
        for(int model : {0,1,9,-9}) {
            c.noiseModel=model;c.noiseRms=.02;b->setControls(c);
            a->process(al.data(),ar.data(),al.size());b->process(bl.data(),br.data(),bl.size());
            identical=identical && al==bl && ar==br;
        }
        trackAllocations=false;CHECK(allocations==0 && identical);
    });
    test("legacy noise requests preserve split blocks reset and sound-off silence", [] {
        auto a=engine(),b=engine();auto c=transparent();c.noiseModel=1;c.noiseRms=.02;
        c.chorusMode=1;c.chorusMix=1;a->setControls(c);b->setControls(c);
        a->noteOn(60,127);b->noteOn(60,127);const auto x=render(*a,12000);
        std::vector<float>y;y.reserve(x.size());
        while(y.size()<x.size()){auto z=render(*b,std::min<std::size_t>(43,x.size()-y.size()));y.insert(y.end(),z.begin(),z.end());}
        CHECK(x==y);a->reset();a->noteOn(60,127);CHECK(render(*a,12000)==x);
        a->allSoundOff();CHECK(rms(render(*a,4096))==0.0);
    });
    std::printf("%d passed, %d failed\n", passed, failed);
    return failed == 0 ? 0 : 1;
}
