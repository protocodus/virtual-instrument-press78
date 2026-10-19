#include "Press78Engine.h"
#include "FactoryVoices.h"
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
namespace { bool tracking=false; std::size_t allocations=0; }
void* operator new(std::size_t n) { if(tracking) ++allocations; if(void* p=std::malloc(n?n:1)) return p; throw std::bad_alloc(); }
void* operator new[](std::size_t n) { return ::operator new(n); }
void operator delete(void* p) noexcept {std::free(p);}
void operator delete[](void* p) noexcept {std::free(p);}
#if defined(__cpp_sized_deallocation)
void operator delete(void* p,std::size_t) noexcept {std::free(p);}
void operator delete[](void* p,std::size_t) noexcept {std::free(p);}
#endif
namespace press78 {
struct Press78SustainTestAccess {
 static auto voice(const Press78Engine& e,int i=0) {return e.voices_[i];}
 static auto tail(const Press78Engine& e,int i=0) {return e.tails_[i];}
 static bool latch(const Press78Engine& e) {return e.originalSustain_;}
 static auto continuous(const Press78Engine::Voice& v) {
  const auto& a=v.modEnvelope;const auto& b=v.carrierEnvelope;
  return std::array<double,27>{{v.modPhase,v.carrierPhase,v.prev1,v.prev2,v.lfoPhase,v.modStep,v.carrierStep,v.modGain,v.carrierGain,v.feedback,v.velocity,a.attenuation,a.attackMul,a.decay1,a.decay2,a.target,b.attenuation,b.attackMul,b.decay1,b.decay2,b.target,static_cast<double>(v.ticks),static_cast<double>(v.age),static_cast<double>(v.note),static_cast<double>(v.source),static_cast<double>(a.stage),static_cast<double>(b.stage)}};
 }
 static auto flags(const Press78Engine::Voice& v) {
  return std::array<bool,9>{{v.active,v.held,v.released,v.modEnvelope.instantAttack,v.modEnvelope.disabled,v.modEnvelope.finished,v.carrierEnvelope.instantAttack,v.carrierEnvelope.disabled,v.carrierEnvelope.finished}};
 }
};
}
namespace {
using E=press78::Press78Engine;using A=press78::Press78SustainTestAccess;
int passed=0,failed=0;
#define CHECK(x) do{if(!(x))throw std::runtime_error(std::string("line ")+std::to_string(__LINE__)+": " #x);}while(false)
template<class F>void test(const char* name,F f){try{f();++passed;std::printf("PASS %s\n",name);}catch(const std::exception& e){tracking=false;++failed;std::printf("FAIL %s: %s\n",name,e.what());}}
press78::Patch patch(bool sustain=false){auto p=press78::initPatch();p.sustain=sustain;p.modulator.rr=7;p.modulator.srr=3;p.carrier.rr=7;p.carrier.srr=5;return p;}
press78::Controls controls(int mode=1){press78::Controls c;c.sustainMode=mode;c.outputCircuit=false;c.envelopeReverb=false;c.masterGain=1;c.toneCutoffHz=0;c.outputLimit=false;c.dcBlock=false;return c;}
auto engine(int mode=1,bool sustain=false){auto e=std::make_unique<E>();e->setControls(controls(mode));e->setPatch(patch(sustain));return e;}
void advance(E& e,int n=257){e.process(nullptr,nullptr,n);}
template<class V>void unchanged(const V& a,const V& b){CHECK(A::continuous(a)==A::continuous(b));CHECK(A::flags(a)==A::flags(b));}
double rr(E& e,int slot=0){return A::voice(e,slot).carrierEnvelope.release;}
}
int main(){
 test("legacy default and bounded sustain selector",[]{press78::Controls c;CHECK(c.sustainMode==0);c.sustainMode=-99;CHECK(press78::sanitizeControls(c).sustainMode==0);c.sustainMode=99;CHECK(press78::sanitizeControls(c).sustainMode==1);});
 test("all raw CC values preserve distinct Legacy and Original semantics",[]{
  auto a=engine(),b=engine(0);
  for(int x=0;x<128;++x){a->reset();b->reset();a->noteOn(60,127);b->noteOn(60,127);double normal=rr(*a);a->sustainController(x);b->sustainController(x);CHECK(rr(*a)==normal/(x?4.:1.));a->noteOff(60);b->noteOff(60);CHECK(A::voice(*a).released);CHECK(A::voice(*b).released==(x<64));}
 });
 test("late CC zero clears sustain-enabled factory and invalid raw clamps",[]{
  auto e=engine(1,true);e->noteOn(60,127);double slow=rr(*e);e->sustainController(0);CHECK(rr(*e)==slow*4);CHECK(!A::latch(*e));e->sustainController(std::numeric_limits<int>::max());CHECK(rr(*e)==slow);e->sustainController(std::numeric_limits<int>::min());CHECK(rr(*e)==slow*4);
 });
 test("CC refresh preserves phase feedback envelope stage age and flags",[]{
  for(bool released:{false,true}){auto e=engine();e->noteOn(67,111);advance(*e);if(released){e->noteOff(67);advance(*e,19);}auto old=A::voice(*e);e->sustainController(1);auto slow=A::voice(*e);unchanged(old,slow);CHECK(slow.carrierEnvelope.release==old.carrierEnvelope.release/4);CHECK(slow.modEnvelope.release==old.modEnvelope.release/16);e->sustainController(0);unchanged(old,A::voice(*e));CHECK(rr(*e)==old.carrierEnvelope.release);}
 });
 test("released envelope slope changes without attenuation restart",[]{
  auto e=engine();e->noteOn(60,127);advance(*e);e->noteOff(60);advance(*e,101);auto a=A::voice(*e);e->sustainController(127);auto b=A::voice(*e);unchanged(a,b);advance(*e,100);auto z=A::voice(*e);CHECK(z.released);CHECK(std::abs((z.carrierEnvelope.attenuation-b.carrierEnvelope.attenuation)-b.carrierEnvelope.release*(z.ticks-b.ticks))<1e-12);
 });
 test("repeated live snapshots preserve override and explicit flag edits replace it",[]{
  auto e=engine(1,true);e->noteOn(60,127);advance(*e);e->sustainController(0);double fast=rr(*e);auto p=e->patch();p.feedback=2;e->setPatch(p,true);CHECK(rr(*e)==fast);CHECK(!A::latch(*e));p.sustain=false;e->setPatch(p,true);CHECK(rr(*e)==fast);p.sustain=true;auto before=A::voice(*e);e->setPatch(p,true);CHECK(A::latch(*e));CHECK(rr(*e)==fast/4);unchanged(before,A::voice(*e));
 });
 test("future program seeding leaves cached voices and keyoff selection unchanged",[]{
  auto e=engine();e->noteOn(60,127);advance(*e);double old=rr(*e);auto p=patch(true);p.carrier.rr=10;p.carrier.srr=4;e->setPatch(p,false);CHECK(A::latch(*e));CHECK(rr(*e)==old);e->noteOff(60);CHECK(rr(*e)==old);e->noteOn(62,127);CHECK(rr(*e,1)==old/8);e->sustainController(0);CHECK(rr(*e)==old);CHECK(rr(*e,1)==old*8);CHECK(A::voice(*e).patch.carrier.rr==7);
 });
 test("explicit same-patch program load seeds future state after CC override",[]{
  auto e=engine(1,true);e->sustainController(0);e->noteOn(60,127);double fast=rr(*e);e->setPatch(e->patch(),false);CHECK(A::latch(*e));CHECK(rr(*e)==fast);e->noteOn(62,127);CHECK(rr(*e,1)==fast/4);
 });
 test("allNotesOff releases immediately while original pedal remains enabled",[]{
  auto e=engine();e->sustainController(127);for(int n=60;n<65;++n)e->noteOn(n,127);e->allNotesOff();for(int i=0;i<5;++i){CHECK(!A::voice(*e,i).held);CHECK(A::voice(*e,i).released);}CHECK(A::latch(*e));
 });
 test("reset and allSoundOff reseed patch state and clear sounding voices",[]{
  for(bool flag:{false,true}){auto e=engine(1,flag);e->sustainController(flag?0:127);e->noteOn(60,127);e->reset();CHECK(!e->activeVoices());CHECK(A::latch(*e)==flag);e->noteOn(60,127);e->sustainController(flag?0:127);e->allSoundOff();CHECK(!e->activeVoices());CHECK(A::latch(*e)==flag);}
 });
 test("sustain mode changes wait for held voices deferred release and fade tails",[]{
  auto e=engine(0);auto p=patch();p.carrier.rr=15;e->setPatch(p);e->noteOn(60,127);e->sustainPedal(true);e->noteOff(60);auto c=e->controls();c.sustainMode=1;e->setControls(c);advance(*e,500);CHECK(e->effectiveSustainMode()==0);CHECK(!A::voice(*e).released);e->sustainPedal(false);advance(*e,1000);CHECK(e->activeVoices()==0);CHECK(e->effectiveSustainMode()==1);
  e->noteOn(60,127);c=e->controls();c.polyphony=1;e->setControls(c);e->noteOn(62,127);c.sustainMode=0;e->setControls(c);CHECK(e->effectiveSustainMode()==1);e->allSoundOff();CHECK(e->effectiveSustainMode()==0);
 });
 test("pending handover waits for a live fade after the replacement voice ends",[]{
  auto e=engine();auto c=e->controls();c.polyphony=1;e->setControls(c);e->noteOn(60,127);advance(*e);e->noteOn(62,127);e->noteOff(62);c.sustainMode=0;e->setControls(c);advance(*e,1);CHECK(e->activeVoices()==0);CHECK(A::tail(*e).remaining==47);CHECK(e->effectiveSustainMode()==1);advance(*e,46);CHECK(A::tail(*e).remaining==1);CHECK(e->effectiveSustainMode()==1);advance(*e,3);CHECK(e->effectiveSustainMode()==0);
 });
 test("raw controller updates steal fade coefficient without restarting its life",[]{
  auto e=engine();auto c=e->controls();c.polyphony=1;e->setControls(c);e->noteOn(60,127);advance(*e);e->noteOn(62,127);auto a=A::tail(*e);CHECK(a.remaining==48);e->sustainController(1);auto b=A::tail(*e);CHECK(b.remaining==48);unchanged(a.voice,b.voice);CHECK(b.voice.carrierEnvelope.release==a.voice.carrierEnvelope.release/4);advance(*e,70);CHECK(A::tail(*e).remaining==0);CHECK(e->activeVoices()==1);
 });
 test("MIDI and CV same-note noteoffs remain independent",[]{auto e=engine();e->noteOn(60,127,0);e->noteOn(60,127,1);e->sustainController(63);e->noteOff(60,0);CHECK(A::voice(*e,0).released);CHECK(A::voice(*e,1).held);e->noteOff(60,1);CHECK(A::voice(*e,1).released);});
 test("all release nibbles key scaling and MIDI boundary coefficients agree with frozen law",[]{
  auto e=engine(),reference=engine(0);
  for(int rate=0;rate<16;++rate)for(int slow=0;slow<16;++slow)for(int rks=0;rks<4;++rks)for(int note:{0,60,127}){
   auto p=patch();p.carrier.rr=rate;p.carrier.srr=slow;p.carrier.rks=rks;e->allSoundOff();reference->allSoundOff();e->setPatch(p);e->noteOn(note,127);reference->setPatch(p);reference->noteOn(note,127);CHECK(rr(*e)==rr(*reference));e->sustainController(1);reference->allSoundOff();p.sustain=true;reference->setPatch(p);reference->noteOn(note,127);CHECK(rr(*e)==rr(*reference));
  }
 });
 test("bool API and raw127/0 produce byte-identical renders in both modes",[]{
  for(int mode:{0,1}){auto a=engine(mode),b=engine(mode);a->noteOn(60,127);b->noteOn(60,127);a->sustainPedal(true);b->sustainController(127);a->noteOff(60);b->noteOff(60);std::array<float,1024>x{},y{};a->process(x.data(),nullptr,x.size());b->process(y.data(),nullptr,y.size());CHECK(x==y);a->sustainPedal(false);b->sustainController(0);a->process(x.data(),nullptr,x.size());b->process(y.data(),nullptr,y.size());CHECK(x==y);}
 });
 test("original control and render path allocates nothing",[]{auto e=engine();for(int n=48;n<60;++n)e->noteOn(n,127);std::array<float,64>l{},r{};allocations=0;tracking=true;for(int i=0;i<128;++i){e->sustainController(i);e->process(l.data(),r.data(),64);if(i==31)e->allNotesOff();}tracking=false;CHECK(allocations==0);for(float x:l)CHECK(std::isfinite(x));});
 std::printf("Sustain groups passed=%d failed=%d\n",passed,failed);return failed?1:0;
}
