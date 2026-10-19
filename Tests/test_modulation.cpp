#include "Press78Engine.h"

#include <algorithm>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <new>
#include <stdexcept>
#include <string>
#include <vector>

namespace { bool tracking = false; std::size_t allocations = 0; }
void* operator new(std::size_t size) {
    if (tracking) ++allocations;
    if (void* p = std::malloc(size ? size : 1)) return p;
    throw std::bad_alloc();
}
void* operator new[](std::size_t size) { return ::operator new(size); }
void operator delete(void* p) noexcept { std::free(p); }
void operator delete[](void* p) noexcept { std::free(p); }
#if defined(__cpp_sized_deallocation)
void operator delete(void* p, std::size_t) noexcept { std::free(p); }
void operator delete[](void* p, std::size_t) noexcept { std::free(p); }
#endif

namespace {
constexpr double pi = 3.1415926535897932384626433832795;
using press78::Press78Engine;
struct Pitch { double seconds, cents; };
int passed = 0, failed = 0;
#define REQUIRE(x) do { if (!(x)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " #x); } while (false)

template<class F> void test(const char* name, F body) {
    try { body(); ++passed; std::printf("PASS %s\n", name); }
    catch (const std::exception& e) { tracking = false; ++failed; std::printf("FAIL %s: %s\n", name, e.what()); }
}
press78::Controls clearOutput() {
    press78::Controls c; // Exercise the product modulation defaults.
    c.masterGain = 1; c.outputCircuit = false; c.envelopeReverb = false; c.toneCutoffHz = 0;
    c.outputLimit = false; c.dcBlock = false;
    return c;
}
press78::Patch sine(int pms, int delay = 0) {
    auto p = press78::initPatch();
    p.vibrato = true; p.pms = pms; p.vibratoDelay = delay;
    return p;
}
std::unique_ptr<Press78Engine> engine(int sr, const press78::Patch& patch,
                                    const press78::Controls& c = clearOutput()) {
    auto e = std::make_unique<Press78Engine>(); e->prepare(sr);
    e->setControls(c); e->setPatch(patch); return e;
}
std::vector<float> render(Press78Engine& e, std::size_t frames) {
    std::vector<float> y(frames); e.process(y.data(), nullptr, frames); return y;
}

// Observe audio only. Carrier crossing intervals estimate the average pitch
// during each440Hz cycle; this never reads phase/LFO/envelope internals.
std::vector<Pitch> pitch(const std::vector<float>& audio, int sr) {
    std::vector<Pitch> result;
    double previous = -1;
    for (std::size_t i = 1; i < audio.size(); ++i) {
        REQUIRE(std::isfinite(audio[i]));
        if (audio[i-1] <= 0 && audio[i] > 0) {
            const double fraction = -static_cast<double>(audio[i-1]) / (audio[i] - audio[i-1]);
            const double crossing = (static_cast<double>(i - 1) + fraction) / sr;
            if (previous >= 0) {
                const double frequency = 1 / (crossing - previous);
                result.push_back({(crossing + previous) / 2, 1200 * std::log2(frequency / 440)});
            }
            previous = crossing;
        }
    }
    return result;
}
double value(const std::vector<Pitch>& curve, double t) {
    const auto end = std::lower_bound(curve.begin(), curve.end(), t,
        [](const Pitch& p, double seconds) { return p.seconds < seconds; });
    REQUIRE(end != curve.begin() && end != curve.end());
    const auto& a = *(end - 1); const auto& b = *end;
    return a.cents + (b.cents - a.cents) * (t - a.seconds) / (b.seconds - a.seconds);
}
std::vector<double> pitchCrossings(const std::vector<Pitch>& curve) {
    std::vector<double> result;
    for (std::size_t i = 1; i < curve.size(); ++i) {
        const auto& a = curve[i-1]; const auto& b = curve[i];
        if (a.seconds > .2 && a.cents <= 0 && b.cents > 0)
            result.push_back(a.seconds - a.cents * (b.seconds - a.seconds) / (b.cents - a.cents));
    }
    return result;
}
double harmonic(const std::vector<Pitch>& curve, double begin, double end,
                double frequency, int number) {
    std::complex<double> area{};
    Pitch previous{begin, value(curve, begin)};
    const auto phasor = [=](Pitch p) {
        return p.cents * std::polar(1.0, -2 * pi * frequency * number * p.seconds);
    };
    const auto integrate = [&](Pitch p) {
        area += .5 * (p.seconds - previous.seconds) * (phasor(previous) + phasor(p));
        previous = p;
    };
    for (const auto p : curve) if (p.seconds > begin && p.seconds < end) integrate(p);
    integrate({end, value(curve, end)});
    return 2 * std::abs(area) / (end - begin);
}
double difference(const std::vector<Pitch>& a, const std::vector<Pitch>& b, double shift) {
    double energy = 0; int count = 0;
    for (const auto p : a) if (p.seconds > .12 && p.seconds < .85) {
        const double d = p.cents - value(b, p.seconds + shift); energy += d*d; ++count;
    }
    REQUIRE(count > 250); return std::sqrt(energy / count);
}
} // namespace

int main() {
    test("audible PMS3/PMS6 depth, triangle spectrum and5.24Hz period at48/96k", [] {
        // Fourier fundamental -> triangle peak; third/fundamental independently
        // distinguishes the intended shape from a sine. Tolerances include
        // cycle averaging and linear crossing interpolation, not hardware fit.
        for (const int sr : {48000, 96000}) {
            double peaks[2]{};
            for (int index = 0; index < 2; ++index) {
                auto e = engine(sr, sine(index == 0 ? 3 : 6)); e->noteOn(69, 127);
                const auto curve = pitch(render(*e, static_cast<std::size_t>(sr * 4)), sr);
                const auto crossings = pitchCrossings(curve); REQUIRE(crossings.size() >= 18);
                const double begin = crossings.front(), end = crossings.back();
                const double rate = (crossings.size() - 1) / (end - begin);
                const double first = harmonic(curve, begin, end, rate, 1);
                const double third = harmonic(curve, begin, end, rate, 3);
                peaks[index] = first * pi*pi / 8;
                std::printf("MEASURE sr=%d PMS=%d rate=%.8f peak=%.6f third_ratio=%.6f\n",
                            sr, index == 0 ? 3 : 6, rate, peaks[index], third / first);
                REQUIRE(std::abs(rate - 5.24) < .002);
                REQUIRE(third / first > .10 && third / first < .12);
                REQUIRE(std::abs(peaks[index] - (index == 0 ? 12.5 : 100)) < (index == 0 ? .2 : 1.0));
            }
            REQUIRE(std::abs(peaks[1] / peaks[0] - 8) < .08);
        }
    });
    test("global modulation continues across silence and a fresh note, reset mode restarts", [] {
        constexpr int sr = 48000;
        constexpr std::size_t gap = 16656; //347ms, deliberately not an LFO period.
        for (const bool global : {false, true}) {
            auto c = clearOutput();
            if (!global) c.globalLfo = false; // The other branch tests the product default.
            auto held = engine(sr, sine(6), c), silent = engine(sr, sine(6), c);
            held->noteOn(69, 127);
            const auto reference = render(*held, sr + gap);
            silent->process(nullptr, nullptr, 9600);
            silent->noteOn(72, 127); silent->process(nullptr, nullptr, 1200);
            silent->allSoundOff(); silent->process(nullptr, nullptr, gap - 10800);
            REQUIRE(silent->activeVoices() == 0);
            silent->noteOn(69, 127); const auto restarted = render(*silent, sr);
            if (!global) {
                REQUIRE(std::equal(restarted.begin(), restarted.end(), reference.begin()));
            } else {
                const auto a = pitch(restarted, sr), b = pitch(reference, sr);
                const double continuous = difference(a, b, static_cast<double>(gap) / sr);
                const double reset = difference(a, b, 0);
                std::printf("MEASURE global continuity_RMSE=%.6f reset_RMSE=%.6f cents\n", continuous, reset);
                REQUIRE(continuous < .4); REQUIRE(reset > 15);
            }
        }
    });
    test("PMS0 leaves the rendered tone unchanged under both LFO modes", [] {
        auto p = sine(0, 17); auto off = p; off.vibrato = false;
        auto a = engine(48000, p), b = engine(48000, off);
        auto c = clearOutput(); c.globalLfo = false; c.triangleLfo = false; c.lfoRateHz = 13.7;
        auto d = engine(48000, p, c);
        a->noteOn(69, 127); b->noteOn(69, 127); d->noteOn(69, 127);
        const auto reference = render(*b, 48000);
        REQUIRE(render(*a, reference.size()) == reference);
        REQUIRE(render(*d, reference.size()) == reference);
    });
    test("legacy20-code vibrato gate remains200ms with declared output latency", [] {
        auto p = sine(6, 20); auto off = p; off.vibrato = false;
        auto a = engine(48000, p), b = engine(48000, off);
        a->noteOn(69, 127); b->noteOn(69, 127);
        const auto x = render(*a, 14400), y = render(*b, 14400);
        const auto expected = static_cast<std::size_t>(.200 * 48000 + a->latencySamples());
        std::size_t first = 0;
        while (first < x.size() && x[first] == y[first]) ++first;
        std::printf("MEASURE delay first_difference=%zu expected=%zu frames\n", first, expected);
        REQUIRE(first >= expected && first <= expected + 2);
    });
    test("modulated AM/PM rendering is block invariant and realtime paths do not allocate", [] {
        auto p = sine(6, 7); p.carrier.amEnable = true; p.ams = 2;
        auto a = engine(48000, p), b = engine(48000, p);
        std::vector<float> full(32000), pieces(32000);
        const auto run = [&](Press78Engine& e, std::vector<float>& out, bool split) {
            auto c = clearOutput(); std::size_t block = 1;
            for (std::size_t event = 0; event < out.size(); event += 8000) {
                if (event == 0 || event == 16000) e.noteOn(69, 127);
                if (event == 8000) e.noteOff(69);
                if (event == 24000) { c.globalLfo = false; c.triangleLfo = false; e.setControls(c); }
                std::size_t cursor = event;
                while (cursor < event + 8000) {
                    const auto n = std::min(split ? block : std::size_t{8000}, event + 8000 - cursor);
                    e.process(out.data() + cursor, nullptr, n); cursor += n;
                    block = block * 7 % 257 + 1;
                }
            }
        };
        run(*a, full, false); allocations = 0; tracking = true;
        run(*b, pieces, true); tracking = false;
        REQUIRE(allocations == 0); REQUIRE(full == pieces);
    });
    std::printf("modulation_contracts_passed=%d failed=%d\n", passed, failed);
    return failed == 0 ? 0 : 1;
}
