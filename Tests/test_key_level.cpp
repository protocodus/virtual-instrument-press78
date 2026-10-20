#include "Press78Engine.h"
#include "FirmwareLevel.h"
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
namespace { bool tracking=false;std::size_t allocations=0; }
void* operator new(std::size_t n){if(tracking)++allocations;if(void*p=std::malloc(n?n:1))return p;throw std::bad_alloc();}
void* operator new[](std::size_t n){return ::operator new(n);}
void operator delete(void*p)noexcept{std::free(p);} void operator delete[](void*p)noexcept{std::free(p);}
#if defined(__cpp_sized_deallocation)
void operator delete(void*p,std::size_t)noexcept{std::free(p);} void operator delete[](void*p,std::size_t)noexcept{std::free(p);}
#endif
namespace {
using press78::Press78Engine;namespace fl=press78::firmware_level;
constexpr double tau=6.283185307179586476925286766559;
int passed=0,failed=0;
#define REQUIRE(x) do{if(!(x))throw std::runtime_error(std::string("line ")+std::to_string(__LINE__)+": " #x);}while(false)
template<class F>void test(const char*n,F f){try{f();++passed;std::printf("PASS %s\n",n);}catch(const std::exception&e){tracking=false;++failed;std::printf("FAIL %s: %s\n",n,e.what());}}
// These contracts predate the envelope Reverb, which holds a release ~1.7 s
// past the idle commit they time; it is off so the level law stands alone.
press78::Controls clean(int model=1){press78::Controls c;c.keyLevelModel=model;c.pitchModel=1;c.masterGain=1;c.outputCircuit=false;c.toneCutoffHz=0;c.dcBlock=false;c.outputLimit=false;c.envelopeReverb=false;return c;}
std::unique_ptr<Press78Engine> engine(press78::Controls c=clean(),int sr=48000){auto e=std::make_unique<Press78Engine>();e->prepare(sr);e->setControls(c);e->setPatch(press78::initPatch());return e;}
std::vector<float> render(Press78Engine&e,std::size_t n){std::vector<float>y(n);e.process(y.data(),nullptr,n);return y;}
void near(double x,double y,double tol=1e-6){REQUIRE(std::abs(x-y)<tol);}
double amplitude(int command){return command>=99?0:std::pow(10.,-command*.75/20);}
}
int main(){
 test("all LKS bytes obey note pairs, clamped endpoints and zero center",[]{
  for(int lks=0;lks<256;++lks){
   for(int n=0;n<26;++n)REQUIRE(fl::offset(n,lks)==fl::offset(24,lks));
   for(int n=24;n<128;n+=2)REQUIRE(fl::offset(n,lks)==fl::offset(n+1,lks));
   REQUIRE(fl::offset(60,lks)==0&&fl::offset(61,lks)==0);
   for(int n=102;n<128;++n)REQUIRE(fl::offset(n,lks)==fl::offset(102,lks));
   REQUIRE(fl::offset(-999,lks)==fl::offset(0,lks));REQUIRE(fl::offset(999,lks)==fl::offset(127,lks));
   for(int n=0;n<128;++n){const int x=fl::offset(n,lks);for(int tl=0;tl<128;++tl){
    const int q=fl::command(tl,n,lks);REQUIRE(q>=0&&q<=127);
    if(tl+x<0)REQUIRE(q==0);else if(tl+x>127)REQUIRE(q==127);else REQUIRE(q-tl==x);
   }}
  }
 });
 test("independent original-command witnesses and boundary shapes",[]{
  REQUIRE(fl::command(99,36,0x11)==80);REQUIRE(fl::command(99,60,0x11)==99);REQUIRE(fl::command(99,84,0x11)==93);
  REQUIRE(fl::command(127,36,0x11)==108);REQUIRE(fl::command(127,60,0x11)==127);REQUIRE(fl::command(127,84,0x11)==121);
  for(int n=0;n<128;++n){REQUIRE(fl::offset(n,0)==0);if(n<60)REQUIRE(fl::offset(n,15)==35-2*(std::max(n-24,0)/2));else REQUIRE(fl::offset(n,0x80)==std::min((n-60)/2,21));}
  REQUIRE(fl::command(0,36,0x11)==0);REQUIRE(fl::command(127,36,15)==127);
  REQUIRE(fl::offset(59,1)==-2&&fl::offset(60,1)==0);REQUIRE(fl::offset(101,0x80)==20&&fl::offset(102,0x80)==21);
 });
 test("firmware amplitude uses final command including stored99 unmute",[]{
  for(int model:{0,1})for(int note:{36,60,84}){
   auto c=clean(model);auto e=engine(c);auto p=press78::initPatch();p.carrier.tl=99;p.carrier.lksLo=1;p.carrier.lksHi=1;e->setPatch(p);e->noteOn(note,127);
   const int code=fl::command(99,note,0x11);REQUIRE(e->activeVoices()==(model==1&&code<99?1u:0u));
   const auto y=render(*e,1024);double phase=0;const double step=tau*press78::firmware_pitch::frequency(note)/48000;
   for(int i=0;i<992;++i){phase=std::fmod(phase+step,tau);near(y[i+32],model==1?.8*amplitude(code)*std::sin(phase):0,1e-9);}
  }
 });
 test("negative offsets saturate at unity and upper endpoint stays flat",[]{
  for(int note:{0,24,25,36,102,103,127}){
   auto e=engine();auto p=press78::initPatch();p.carrier.tl=1;p.carrier.lksLo=1;p.carrier.lksHi=1;e->setPatch(p);e->noteOn(note,127);auto y=render(*e,2048);
   double phase=0,step=tau*press78::firmware_pitch::frequency(note)/48000;int q=fl::command(1,note,0x11);
   for(int i=0;i<2016;++i){phase=std::fmod(phase+step,tau);near(y[i+32],.8*amplitude(q)*std::sin(phase));REQUIRE(std::abs(y[i+32])<=.800001);}
  }
 });
 test("carrier live TL and LKS edit preserves oscillator and envelope trajectory",[]{
  auto a=engine(),b=engine();auto p=press78::initPatch();p.carrier.tl=10;p.carrier.d1r=28;p.carrier.d1l=4;
  a->setPatch(p);b->setPatch(p);a->noteOn(84,127);b->noteOn(84,127);REQUIRE(render(*a,512)==render(*b,512));
  p.carrier.tl=20;p.carrier.lksHi=1;a->setPatch(p,true);
  auto ya=render(*a,2048),yb=render(*b,2048);double ratio=amplitude(14)/amplitude(10);
  for(int i=0;i<2048;++i)near(ya[i],yb[i]*(i<32?1:ratio),2e-7);
 });
 test("modulator live TL and LKS edit preserves both phases",[]{
  auto e=engine();auto p=press78::initPatch();p.modulator.tl=40;p.modulator.lksHi=1;p.modulator.mul=2;p.carrier.tl=10;e->setPatch(p);e->noteOn(84,127);
  auto y=render(*e,512);p.modulator.tl=50;p.modulator.lksHi=8;e->setPatch(p,true);auto z=render(*e,512);y.insert(y.end(),z.begin(),z.end());
  double cm=0,cc=0,step=tau*press78::firmware_pitch::frequency(84)/48000;
  for(int i=0;i<992;++i){cm=std::fmod(cm+step*2,tau);cc=std::fmod(cc+step,tau);double m=std::sin(cm)*amplitude(i<512?34:62);near(y[i+32],std::sin(cc+8*3.14159265358979323846*m)*amplitude(10)*.8,2e-6);}
 });
 test("model switch does not change held or releasing audio and commits on idle",[]{
  auto c=clean(0);auto a=engine(c),b=engine(c);auto p=press78::initPatch();p.carrier.tl=10;p.carrier.lksHi=10;a->setPatch(p);b->setPatch(p);a->noteOn(84,127);b->noteOn(84,127);REQUIRE(render(*a,128)==render(*b,128));
  c.keyLevelModel=1;a->setControls(c);REQUIRE(a->effectiveKeyLevelModel()==0);REQUIRE(render(*a,2048)==render(*b,2048));a->noteOff(84);b->noteOff(84);REQUIRE(render(*a,128)==render(*b,128));REQUIRE(a->effectiveKeyLevelModel()==0);
  REQUIRE(render(*a,48000)==render(*b,48000));REQUIRE(a->effectiveKeyLevelModel()==1);
 });
 test("requested law waits for isolated steal tail",[]{
  auto c=clean(0);c.polyphony=1;auto e=engine(c);e->noteOn(60,127);e->process(nullptr,nullptr,100);auto p=press78::initPatch();p.carrier.rr=15;e->setPatch(p);e->noteOn(64,127);e->noteOff(64);e->process(nullptr,nullptr,12);REQUIRE(e->activeVoices()==0);
  c.keyLevelModel=1;e->setControls(c);REQUIRE(e->effectiveKeyLevelModel()==0);e->process(nullptr,nullptr,35);REQUIRE(e->effectiveKeyLevelModel()==0);e->process(nullptr,nullptr,2);REQUIRE(e->effectiveKeyLevelModel()==1);
 });
 test("reset soundoff and startup commit requested law with old defaultzero",[]{
  press78::Controls defaults;REQUIRE(defaults.keyLevelModel==0);auto c=clean(0);auto e=engine(c);e->noteOn(60,100);c.keyLevelModel=1;e->setControls(c);e->reset();REQUIRE(e->effectiveKeyLevelModel()==1);e->noteOn(60,100);c.keyLevelModel=0;e->setControls(c);e->allSoundOff();REQUIRE(e->effectiveKeyLevelModel()==0);
  auto p=press78::initPatch();p.carrier.tl=99;p.carrier.lksLo=1;e->setPatch(p);c.keyLevelModel=1;e->setControls(c);e->noteOn(36,127);REQUIRE(e->activeVoices()==1);
 });
 test("law requests preserve Original pitch bend and host tuning",[]{
  auto c=clean(0);c.midiPitchBend=127*128;c.midiBendRange=2;c.masterTuneCents=3.125;c.hostTuneCents=1.7;auto a=engine(c),b=engine(c);a->noteOn(68,127);b->noteOn(68,127);REQUIRE(render(*a,128)==render(*b,128));c.keyLevelModel=1;a->setControls(c);REQUIRE(render(*a,4096)==render(*b,4096));REQUIRE(a->effectivePitchModel()==1&&a->effectiveKeyLevelModel()==0);
 });
 test("all host rates chunking null outputs and retired noise remain deterministic",[]{
  for(int sr:{22050,44100,48000,96000,192000}){
   auto c=clean();c.outputCircuit=true;c.chorusMode=1;c.chorusMix=.8;auto a=engine(c,sr);c.noiseModel=1;c.noiseRms=.1;auto b=engine(c,sr);auto p=press78::initPatch();p.carrier.tl=10;p.carrier.lksHi=10;a->setPatch(p);b->setPatch(p);a->noteOn(84,127);b->noteOn(84,127);auto y=render(*a,4096);std::vector<float>z(4096);
   for(std::size_t n=0;n<z.size();){auto k=std::min<std::size_t>(37,z.size()-n);b->process(z.data()+n,nullptr,k);n+=k;}REQUIRE(y==z);REQUIRE(b->controls().noiseRms==0&&b->controls().noiseModel==0);REQUIRE(b->latencySamples()==static_cast<int>(std::ceil(32.*sr/48000)));
   auto idle=engine(c,sr);for(float x:render(*idle,1024))REQUIRE(x==0);
  }
 });
 test("sanitization and live key edits allocate nothing",[]{
  auto c=clean();c.keyLevelModel=-999;REQUIRE(press78::sanitizeControls(c).keyLevelModel==0);c.keyLevelModel=999;REQUIRE(press78::sanitizeControls(c).keyLevelModel==1);
  auto e=engine();auto p=press78::initPatch();p.carrier.tl=10;e->setPatch(p);for(int n=0;n<13;++n)e->noteOn(48+n,100);allocations=0;tracking=true;
  for(int i=0;i<256;++i){c.keyLevelModel=i&1;e->setControls(c);p.modulator.lksLo=i&15;p.carrier.lksHi=(i>>4)&15;e->setPatch(p,true);e->process(nullptr,nullptr,64);}tracking=false;REQUIRE(allocations==0);REQUIRE(sizeof(Press78Engine)<192*1024);
 });
 std::printf("%d passed, %d failed\n",passed,failed);return failed?1:0;
}
