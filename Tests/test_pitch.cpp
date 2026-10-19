#include "Press78Engine.h"
#include "FirmwarePitch.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
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
using press78::Press78Engine;
namespace fp = press78::firmware_pitch;
constexpr double tau = 6.283185307179586476925286766559;
int passed = 0, failed = 0;
#define REQUIRE(x) do { if (!(x)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " #x); } while (false)
template<class F> void test(const char* name, F body) {
    try { body(); ++passed; std::printf("PASS %s\n", name); }
    catch (const std::exception& e) { tracking = false; ++failed; std::printf("FAIL %s: %s\n", name, e.what()); }
}
press78::Controls clean(int model = 1) {
    press78::Controls c;
    c.pitchModel = model; c.masterGain = 1; c.outputCircuit = false;
    c.toneCutoffHz = 0; c.dcBlock = false; c.outputLimit = false;
    return c;
}
std::unique_ptr<Press78Engine> engine(const press78::Controls& c = clean(), int sr = 48000) {
    auto e = std::make_unique<Press78Engine>(); e->prepare(sr);
    e->setControls(c); e->setPatch(press78::initPatch()); return e;
}
std::vector<float> render(Press78Engine& e, std::size_t count) {
    std::vector<float> y(count); e.process(y.data(), nullptr, count); return y;
}
double frequency(const std::vector<float>& y, int sr) {
    double first = -1, last = -1; int count = 0;
    for (std::size_t i = static_cast<std::size_t>(sr / 5); i < y.size(); ++i)
        if (y[i-1] <= 0 && y[i] > 0) {
            const double t = i - 1 - static_cast<double>(y[i-1]) / (y[i] - y[i-1]);
            if (first < 0) first = t;
            last = t; ++count;
        }
    REQUIRE(count > 20);
    return (count - 1) * sr / (last - first);
}
void near(double x, double y, double tolerance) { REQUIRE(std::abs(x - y) < tolerance); }
} // namespace

int main() {
    test("functional command words and all converter boundaries", [] {
        constexpr int semitones[12] = {2394,2537,2688,2847,3017,3196,3386,3588,3801,4027,4266,4520};
        for (int i = 0; i < 384; ++i) {
            const int expected = i == 257 ? 3838 : static_cast<int>(std::floor(2394.41 * std::pow(2., i / 384.) + .5));
            REQUIRE(fp::words[i] == expected);
        }
        for (int i = 0; i < 12; ++i) REQUIRE(fp::words[i*32] == semitones[i]);
        for (int n = 0; n < 128; ++n) for (int fraction = 0; fraction < 32; ++fraction)
            for (int voice = 0; voice < 12; ++voice) {
                int block = n / 12 - 1;
                const int index = (n % 12) * 32 + fraction;
                int word = index == 257 ? 3838 : static_cast<int>(std::floor(2394.41 * std::pow(2., index / 384.) + .5));
                if (n >= 117) { word = 8054; block = 7; }
                else if (n < 12) { word /= 2; block = 0; }
                else if (n >= 108) { word *= 2; block = 7; }
                const auto writes = fp::commands(n, fraction, voice);
                const int mark = (voice % 2) * 128;
                REQUIRE(writes[0].address == 0x228 + voice / 2);
                REQUIRE(writes[1].address == 0x230 + voice / 2);
                REQUIRE(writes[2].address == 0x238 + voice / 2);
                REQUIRE(writes[0].value == (mark | ((word >> 6) & 31)));
                REQUIRE(writes[1].value == (mark | (word & 63)));
                REQUIRE(writes[2].value == (mark | ((word >> 6) & 96) | (block << 2)));
            }
    });
    test("bend61/62 duplicate, asymmetric endpoints and all14-bit lower-bit invariance", [] {
        for (int range = 0; range <= 24; ++range) {
            REQUIRE(fp::bendSteps(61, range) == fp::bendSteps(62, range));
            REQUIRE(fp::bendSteps(0, range) == -range * 32);
            REQUIRE(fp::bendSteps(64, range) == 0);
            REQUIRE(fp::bendSteps(127, range) == range * 32);
            for (int raw = 0; raw < 16384; ++raw) {
                int high = raw / 128;
                if (high == 62) high = 61;
                if (high == 127) high = 128;
                REQUIRE(fp::bendSteps(raw >> 7, range) == static_cast<int>(std::trunc(range * (high - 64) / 2.)));
            }
        }
        auto c = clean(); c.midiPitchBend = 61*128; c.midiBendRange = 2;
        auto a = engine(c); c.midiPitchBend = 62*128+127; auto b = engine(c);
        a->noteOn(68,127); b->noteOn(68,127);
        REQUIRE(render(*a,4096) == render(*b,4096));
    });
    test("Original pure tones match declared grid at44.1/48/96k and extend keyboard", [] {
        for (int sr : {44100,48000,96000}) for (int note : {39,60,68,77,87}) {
            auto e = engine(clean(),sr); e->noteOn(note,127);
            near(frequency(render(*e,sr),sr),fp::frequency(note),.001);
        }
        REQUIRE(fp::frequency(127) > fp::frequency(126)); // no hardware high clamp
        REQUIRE(fp::extendedWord(-1).block == -2);
        REQUIRE(fp::extendedWord(-1).word == fp::words[383]);
        auto e = engine(); e->noteOn(0,127); e->noteOn(127,127);
        for (float x : render(*e,4096)) REQUIRE(std::isfinite(x));
    });
    test("Original fine tune reaches irregular Ab fraction and host tune stays continuous", [] {
        const double expected[3] = {415.35496711730957,419.39814885457355,416.88481966654456};
        for (int fine = 0; fine < 3; ++fine) {
            auto c = clean(); c.masterTuneCents = fine * 3.125;
            auto e = engine(c); e->noteOn(68,127);
            near(frequency(render(*e,48000),48000),expected[fine],.001);
        }
        auto c = clean(); c.masterTuneCents = 1.5; auto a = engine(c);
        c.masterTuneCents = 0; auto b = engine(c);
        a->noteOn(68,127); b->noteOn(68,127); REQUIRE(render(*a,4096) == render(*b,4096));
        c.hostTuneCents = 1.5; auto d = engine(c); d->noteOn(68,127);
        near(frequency(render(*d,48000),48000),expected[0]*std::pow(2.,1.5/1200),.001);
    });
    test("Original raw bend replaces standalone bend without double application", [] {
        auto c = clean(); c.pitchBendSemitones = 12; c.midiPitchBend = 8192;
        auto e = engine(c); e->noteOn(69,127);
        near(frequency(render(*e,48000),48000),440.0511582692464,.001);
        c.midiPitchBend = -1; auto a = engine(c); a->noteOn(69,127);
        near(frequency(render(*a,48000),48000),fp::frequency(69,384),.001);
    });
    test("Original live bend preserves phase rather than resetting oscillator", [] {
        auto c = clean(); auto e = engine(c); e->noteOn(68,127);
        auto y = render(*e,512); c.masterTuneCents = 3.125; e->setControls(c);
        const auto end = render(*e,256); y.insert(y.end(),end.begin(),end.end());
        const double a = tau*fp::frequency(68)/48000, b = tau*fp::frequency(68,1)/48000;
        double phase = 0;
        for (int tick = 0; tick < 736; ++tick) {
            phase = std::fmod(phase+(tick < 512 ? a:b),tau);
            near(y[tick+32],.8*std::sin(phase),1e-6);
        }
    });
    test("Original bend updates both new voice and phase-preserved steal tail", [] {
        auto c = clean(); c.polyphony=1; auto e=engine(c); e->noteOn(68,127);
        auto y=render(*e,100); e->noteOn(70,127);
        auto part=render(*e,16); y.insert(y.end(),part.begin(),part.end());
        c.masterTuneCents=3.125; e->setControls(c);
        part=render(*e,100); y.insert(y.end(),part.begin(),part.end());
        double oldPhase=0,newPhase=0;
        for (int tick=0;tick<184;++tick) {
            oldPhase=std::fmod(oldPhase+tau*fp::frequency(68,tick<116?0:1)/48000,tau);
            if (tick>=100) newPhase=std::fmod(newPhase+tau*fp::frequency(70,tick<116?0:1)/48000,tau);
            const double expected=tick<100?.8*std::sin(oldPhase)
                :.8*std::sin(newPhase)+(tick<148?.8*std::sin(oldPhase)*(147-tick)/47.:0.);
            near(y[tick+32],expected,2e-6);
        }
    });
    test("law changes defer for held/releasing voices and commit after idle/reset/soundoff", [] {
        auto c=clean(0); auto e=engine(c); e->noteOn(69,127); e->process(nullptr,nullptr,64);
        c.pitchModel=1; e->setControls(c); REQUIRE(e->effectivePitchModel()==0);
        e->noteOff(69); e->process(nullptr,nullptr,64); REQUIRE(e->effectivePitchModel()==0);
        e->process(nullptr,nullptr,48000); REQUIRE(e->effectivePitchModel()==1);
        e->noteOn(69,127); c.pitchModel=0;e->setControls(c); REQUIRE(e->effectivePitchModel()==1);
        e->reset(); REQUIRE(e->effectivePitchModel()==0);
        e->noteOn(69,127); c.pitchModel=1;e->setControls(c); e->allSoundOff(); REQUIRE(e->effectivePitchModel()==1);
    });
    test("law changes wait for final steal tail even when main voice is gone", [] {
        auto c=clean(0); c.polyphony=1; auto e=engine(c);
        e->noteOn(60,127);e->process(nullptr,nullptr,100);
        auto p=press78::initPatch();p.carrier.rr=15;e->setPatch(p);
        e->noteOn(64,127);e->noteOff(64);e->process(nullptr,nullptr,12);
        REQUIRE(e->activeVoices()==0);
        c.pitchModel=1;e->setControls(c);REQUIRE(e->effectivePitchModel()==0);
        e->process(nullptr,nullptr,35);REQUIRE(e->effectivePitchModel()==0);
        e->process(nullptr,nullptr,2);REQUIRE(e->effectivePitchModel()==1);
    });
    test("Original split blocks, null outputs and legacy noise fields are deterministic", [] {
        auto c=clean(); c.chorusMode=1;c.chorusMix=.8;c.outputCircuit=true;
        auto a=engine(c,44100);c.noiseModel=1;c.noiseRms=.05;auto b=engine(c,44100);
        a->noteOn(60,100);b->noteOn(60,100);
        const auto whole=render(*a,10000);std::vector<float> split(10000);
        for(std::size_t n=0;n<split.size();){const auto k=std::min<std::size_t>(37,split.size()-n);b->process(split.data()+n,nullptr,k);n+=k;}
        REQUIRE(whole==split);REQUIRE(b->controls().noiseRms==0);REQUIRE(b->controls().noiseModel==0);
        auto idle=engine(c);for(float x:render(*idle,2048))REQUIRE(x==0);
    });
    test("Equal ignores Original metadata and preserves continuous tune and bend", [] {
        auto c=clean(0);c.masterTuneCents=1.7;c.pitchBendSemitones=.37;auto a=engine(c);
        c.midiPitchBend=0;c.midiBendRange=24;auto b=engine(c);
        a->noteOn(69,127);b->noteOn(69,127);const auto y=render(*a,48000);
        REQUIRE(y==render(*b,48000));near(frequency(y,48000),440*std::pow(2.,38.7/1200),.001);
        c.hostTuneCents=1.3;c.masterTuneCents=.4;auto d=engine(c);d->noteOn(69,127);REQUIRE(y==render(*d,48000));
    });
    test("sanitization and live Original control updates allocate nothing", [] {
        auto c=clean();c.pitchModel=99;c.midiPitchBend=99999;c.midiBendRange=99;c.hostTuneCents=std::numeric_limits<double>::quiet_NaN();
        const auto safe=press78::sanitizeControls(c);REQUIRE(safe.pitchModel==1&&safe.midiPitchBend==16383&&safe.midiBendRange==24&&safe.hostTuneCents==0);
        auto e=engine();for(int n=0;n<13;++n)e->noteOn(48+n,100);
        allocations=0;tracking=true;
        for(int i=0;i<128;++i){c=clean();c.midiPitchBend=i*128;c.masterTuneCents=(i%17-8)*3.125;e->setControls(c);e->process(nullptr,nullptr,64);}
        tracking=false;REQUIRE(allocations==0);REQUIRE(sizeof(Press78Engine)<192*1024);
    });
    std::printf("%d passed, %d failed\n",passed,failed);
    return failed?1:0;
}
