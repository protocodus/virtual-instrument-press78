#include "Press78Engine.h"
#include "Press78OutputBus.h"
#include "mode00_command_fixture.h"
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
void* operator new(std::size_t n) { if(tracking)++allocations; if(void* p=std::malloc(n?n:1))return p;throw std::bad_alloc(); }
void* operator new[](std::size_t n){return ::operator new(n);}
void operator delete(void* p)noexcept{std::free(p);} void operator delete[](void* p)noexcept{std::free(p);}
#if defined(__cpp_sized_deallocation)
void operator delete(void* p,std::size_t)noexcept{std::free(p);}void operator delete[](void* p,std::size_t)noexcept{std::free(p);}
#endif
namespace press78 {
struct Press78AllocationTestAccess {
 static auto allocator(const Press78Engine& e){return e.allocator_;}
 static constexpr std::size_t historySize(){return Press78Engine::kHistory;}
 static auto voice(const Press78Engine& e,int i){return e.voices_[i];}
 static auto count(const Press78Engine& e,int n,int s=0){return e.heldInputCounts_[s][n];}
 static int tails(const Press78Engine& e){int n=0;for(const auto& t:e.tails_)n+=t.remaining>0;return n;}
 static int longestTail(const Press78Engine& e){int n=0;for(const auto& t:e.tails_)n=std::max(n,t.remaining);return n;}
 static auto phaseState(const Press78Engine& e,int i){const auto& v=e.voices_[i];return std::array<double,12>{{v.modPhase,v.carrierPhase,v.prev1,v.prev2,v.lfoPhase,v.modEnvelope.attenuation,v.carrierEnvelope.attenuation,static_cast<double>(v.ticks),static_cast<double>(v.age),v.velocity,v.modGain,v.carrierGain}};}
};
}
namespace {
using E=press78::Press78Engine;using A=press78::Press78AllocationTestAccess;
int passed=0,failed=0,fixtureEvents=0,fixtureChecks=0;
#define CHECK(x) do{if(!(x))throw std::runtime_error(std::string("line ")+std::to_string(__LINE__)+": " #x);}while(false)
template<class F>void test(const char* name,F f){try{f();++passed;std::printf("PASS %s\n",name);}catch(const std::exception& e){tracking=false;++failed;std::printf("FAIL %s: %s\n",name,e.what());}}
press78::Controls controls(int allocation=1,int polyphony=12){press78::Controls c;c.allocationModel=allocation;c.polyphony=polyphony;c.sustainMode=1;c.masterGain=1;c.outputCircuit=false;c.toneCutoffHz=0;c.outputLimit=false;c.dcBlock=false;return c;}
auto engine(int allocation=1,int polyphony=12){auto e=std::make_unique<E>();e->setControls(controls(allocation,polyphony));auto p=press78::initPatch();p.carrier.rr=15;e->setPatch(p);return e;}
void advance(E& e,int n=256){e.process(nullptr,nullptr,static_cast<std::size_t>(n));}
bool same(const press78::Mode00Allocator& a,const press78::Mode00Allocator& b){return a.ranks==b.ranks&&a.notes==b.notes&&a.sources==b.sources&&a.valid==b.valid&&a.keyed==b.keyed&&a.pending==b.pending&&a.held==b.held&&a.pool==b.pool;}
void invariants(const E& e){const auto a=A::allocator(e);CHECK(e.activeVoices()<=static_cast<std::size_t>(e.controls().polyphony));for(int s=0;s<2;++s)for(int n=0;n<128;++n)CHECK(a.held[s][n]==(A::count(e,n,s)!=0));for(int i=0;i<12;++i){auto v=A::voice(e,i);if(v.active){CHECK(i<e.controls().polyphony);CHECK(a.valid[i]);CHECK(v.note==a.notes[i]);CHECK(v.source==a.sources[i]);}}}
}
int main(){
 test("history capacity covers all causal taps at rate clock and wrap boundaries",[]{CHECK(A::historySize()==128);std::size_t checked=0;for(double chip:{E::kInternalRate,E::kYm3420Rate})for(double rate:{8000.,8001.,44100.,48000.,96000.,192000.})for(double ppm:{-30000.,-10000.,0.,10000.,30000.}){double position=0;for(int i=0;i<4096;++i){const auto latest=static_cast<std::int64_t>(std::floor(position));const auto next=latest+1;const auto base=static_cast<std::int64_t>(std::floor(position-E::kResamplerDelay*chip/E::kInternalRate));for(int j=0;j<64;++j){const auto tick=base+j-31;CHECK(tick<next);CHECK(tick>=next-static_cast<std::int64_t>(A::historySize()));++checked;}CHECK(position>=0);position+=chip/rate*(1+ppm*1e-6);}}CHECK(checked==15728640);});
 test("default compatibility and bounded selector",[]{press78::Controls c;CHECK(c.allocationModel==0);auto e=engine(0);CHECK(e->effectiveAllocationModel()==0);c.allocationModel=-99;CHECK(press78::sanitizeControls(c).allocationModel==0);c.allocationModel=99;CHECK(press78::sanitizeControls(c).allocationModel==1);});
 test("all published Mode00 command fixture events exactly",[]{
  for(const auto& c:allocation_fixture::cases){press78::Mode00Allocator a;for(int i=0;i<12;++i){a.ranks[i]=static_cast<std::uint8_t>(c.ranks[i]);a.notes[i]=c.notes[i];}
   for(int i=0;i<c.size;++i){const auto& e=c.events[i];auto d=e.kind==1?a.noteOn(e.note,0):e.kind==0?a.noteOff(e.note,0):a.service(e.count);int pitch=e.kind==1?d.slot:-1;
    CHECK(pitch==e.pitch);++fixtureChecks;CHECK(d.keyCount==e.keyCount);++fixtureChecks;for(int k=0;k<d.keyCount;++k)CHECK(d.keys[k]==e.keys[k]);++fixtureChecks;
    for(int k=0;k<12;++k){CHECK(a.ranks[k]==e.ranks[k]);CHECK(a.notes[k]==e.notes[k]);CHECK(a.pending[k]==e.pending[k]);}fixtureChecks+=3;++fixtureEvents;
   }
  }CHECK(fixtureEvents==251);CHECK(fixtureChecks==1506);
 });
 test("unsigned rank floors deterministic ties and long event aging",[]{press78::Mode00Allocator a;a.ranks.fill(128);a.ranks[3]=a.ranks[8]=0;auto d=a.noteOn(60,0);CHECK(d.slot==3);CHECK(a.ranks[3]==254);CHECK(a.ranks[8]==0);CHECK(a.ranks[0]==128);a.ranks[0]=0;a.ranks[1]=128;a.ranks[2]=1;a.ranks[3]=129;a.ranks[4]=255;a.age();CHECK(a.ranks[0]==0&&a.ranks[1]==128&&a.ranks[2]==0&&a.ranks[3]==128&&a.ranks[4]==254);for(int i=0;i<4096;++i){a.noteOff(60,0);a.noteOn(60,0);a.service(1);}CHECK(a.find(60,0)>=0);});
 test("held duplicate is a complete edge no-op even after future patch load",[]{auto e=engine();e->noteOn(60,100);advance(*e);auto p=e->patch();p.carrier.mul=7;e->setPatch(p,false);auto a=A::allocator(*e);auto v=A::phaseState(*e,0);int tails=A::tails(*e);e->noteOn(60,127);CHECK(same(a,A::allocator(*e)));CHECK(v==A::phaseState(*e,0));CHECK(A::tails(*e)==tails);CHECK(e->activeVoices()==1);CHECK(A::count(*e,60)==1);});
 test("velocity zero and redundant offs preserve logical edge policy",[]{auto e=engine();e->noteOn(60,127);e->noteOn(60,0);CHECK(!A::voice(*e,0).held);CHECK(A::voice(*e,0).released);CHECK(A::count(*e,60)==0);auto a=A::allocator(*e);e->noteOff(60);CHECK(same(a,A::allocator(*e)));});
 test("MIDI and CV same pitch have independent ownership",[]{auto e=engine();e->noteOn(60,100,0);e->noteOn(60,100,1);CHECK(e->activeVoices()==2);e->noteOn(60,127,0);CHECK(e->activeVoices()==2);e->noteOff(60,0);CHECK(!A::voice(*e,0).held);CHECK(A::voice(*e,1).held);e->noteOff(60,1);CHECK(!A::voice(*e,1).held);invariants(*e);});
 test("unsupported Original source IDs are rejected without aliasing",[]{auto e=engine();e->noteOn(60,100);auto a=A::allocator(*e);auto v=A::phaseState(*e,0);for(int s:{-1,2,17,std::numeric_limits<int>::min(),std::numeric_limits<int>::max()}){e->noteOn(60,100,s);e->noteOff(60,s);}CHECK(same(a,A::allocator(*e)));CHECK(v==A::phaseState(*e,0));CHECK(e->activeVoices()==1);});
 test("silent legal patches still allocate keys ranks and retained caches",[]{for(int kind=0;kind<3;++kind){auto e=engine();auto p=e->patch();if(kind<2)p.carrier.tl=kind?127:99;else p.carrier.ar=0;e->setPatch(p);e->noteOn(60,100);CHECK(e->activeVoices()==0);auto a=A::allocator(*e);CHECK(a.find(60,0)==0&&a.ranks[0]==254&&a.held[0][60]);CHECK(A::count(*e,60)==1);auto c=e->controls();c.allocationModel=0;e->setControls(c);advance(*e);CHECK(e->effectiveAllocationModel()==1);e->setPatch(press78::initPatch(),true);e->noteOn(60,127);CHECK(e->activeVoices()==0);CHECK(same(a,A::allocator(*e)));e->noteOff(60);CHECK(e->effectiveAllocationModel()==0);}});
 test("live mute edits preserve logical cache and do not retrigger a held key",[]{auto e=engine();e->noteOn(60,127);advance(*e);auto a=A::allocator(*e);auto p=e->patch();p.carrier.tl=127;e->setPatch(p,true);CHECK(same(a,A::allocator(*e)));auto phase=A::phaseState(*e,0);e->noteOn(60,100);CHECK(phase==A::phaseState(*e,0));p.carrier.tl=0;e->setPatch(p,true);CHECK(same(a,A::allocator(*e)));CHECK(A::voice(*e,0).held);});
 test("retired envelopes keep cache and held-input ownership",[]{auto e=engine();auto p=e->patch();p.carrier.d2r=63;e->setPatch(p);e->noteOn(60,127);advance(*e,512);CHECK(e->activeVoices()==0);CHECK(A::allocator(*e).find(60,0)==0);CHECK(A::count(*e,60)==1);e->noteOn(60,127);CHECK(e->activeVoices()==0);e->noteOff(60);p.carrier.d2r=0;e->setPatch(p);e->noteOn(60,127);CHECK(A::allocator(*e).find(60,0)==0);CHECK(A::voice(*e,0).active);});
 test("release retrigger reuses cached slot and existing fade guard",[]{auto e=engine();auto p=e->patch();p.carrier.rr=8;e->setPatch(p);e->noteOn(60,100);advance(*e);e->noteOff(60);advance(*e,16);e->noteOn(60,111);CHECK(e->activeVoices()==1);CHECK(A::allocator(*e).find(60,0)==0);CHECK(A::longestTail(*e)==48);CHECK(A::voice(*e,0).held);});
 test("each reduced pool prefers a released slot before held ranks",[]{for(int n=1;n<=12;++n){auto e=engine(1,n);for(int i=0;i<n;++i)e->noteOn(48+i,100);CHECK(e->activeVoices()==static_cast<std::size_t>(n));int slot=n/2;e->noteOff(48+slot);e->noteOn(90,100);CHECK(A::allocator(*e).find(90,0)==slot);CHECK(e->activeVoices()==static_cast<std::size_t>(n));invariants(*e);}});
 test("live pool shrink enlarge retains stolen key latches without respawn",[]{auto e=engine();for(int i=0;i<12;++i)e->noteOn(60+i,100);auto c=e->controls();c.polyphony=3;e->setControls(c);CHECK(e->activeVoices()==3);CHECK(A::tails(*e)==9);for(int i=3;i<12;++i)CHECK(!A::allocator(*e).valid[i]);c.polyphony=12;e->setControls(c);CHECK(e->activeVoices()==3);e->noteOn(70,127);CHECK(e->activeVoices()==3);e->noteOff(70);e->noteOn(70,127);CHECK(e->activeVoices()==4);CHECK(A::allocator(*e).find(70,0)==3);e->noteOff(71);CHECK(A::voice(*e,3).held);invariants(*e);});
 test("Legacy duplicate ownership defers mode through natural retirement",[]{auto e=engine(0);auto p=e->patch();p.carrier.d2r=63;e->setPatch(p);e->noteOn(60,100);e->noteOn(60,100);advance(*e,512);CHECK(!e->activeVoices());CHECK(A::count(*e,60)==2);auto c=e->controls();c.allocationModel=1;e->setControls(c);CHECK(e->effectiveAllocationModel()==0);e->noteOff(60);CHECK(e->effectiveAllocationModel()==0);e->noteOff(60);CHECK(e->effectiveAllocationModel()==1);});
 test("stolen but still held key defers allocation mode after audio ends",[]{auto e=engine(1,1);e->noteOn(60,100);e->noteOn(62,100);e->noteOff(62);advance(*e,1024);CHECK(!e->activeVoices());CHECK(!A::tails(*e));CHECK(A::count(*e,60)==1);auto c=e->controls();c.allocationModel=0;e->setControls(c);CHECK(e->effectiveAllocationModel()==1);e->noteOff(60);CHECK(e->effectiveAllocationModel()==0);});
 test("model request cancellation and fade-tail deferral",[]{auto e=engine(1,1);e->noteOn(60,100);advance(*e);e->noteOn(62,100);e->noteOff(60);e->noteOff(62);auto c=e->controls();c.allocationModel=0;e->setControls(c);CHECK(e->effectiveAllocationModel()==1);c.allocationModel=1;e->setControls(c);advance(*e,1024);CHECK(e->effectiveAllocationModel()==1);e->noteOn(64,100);e->noteOn(65,100);e->noteOff(64);e->noteOff(65);c.allocationModel=0;e->setControls(c);advance(*e,1);CHECK(e->effectiveAllocationModel()==1);CHECK(A::longestTail(*e)==47);advance(*e,1024);CHECK(e->effectiveAllocationModel()==0);});
 test("allNotesOff clears silent stolen and active ownership but keeps fades",[]{auto e=engine(1,1);e->noteOn(60,100);e->noteOn(62,100);auto p=e->patch();p.carrier.tl=127;e->setPatch(p);e->noteOn(64,100);CHECK(A::tails(*e)>0);auto c=e->controls();c.allocationModel=0;e->setControls(c);e->allNotesOff();for(int n:{60,62,64})CHECK(A::count(*e,n)==0);CHECK(A::tails(*e)>0);CHECK(e->effectiveAllocationModel()==1);advance(*e,1024);CHECK(e->effectiveAllocationModel()==0);});
 test("reset and allSoundOff clear allocation state and adopt requested mode",[]{for(bool panic:{false,true}){auto e=engine(1,1);e->noteOn(60,100);e->noteOn(62,100);auto c=e->controls();c.allocationModel=0;e->setControls(c);if(panic)e->allSoundOff();else e->reset();CHECK(!e->activeVoices()&&!A::tails(*e));CHECK(e->effectiveAllocationModel()==0);for(int n:{60,62})CHECK(A::count(*e,n)==0);c.allocationModel=1;e->setControls(c);e->noteOn(60,100);CHECK(e->activeVoices()==1);}});
 test("pitch sustain patch and repeated control snapshots preserve ownership",[]{auto e=engine();e->noteOn(60,100);auto a=A::allocator(*e);auto c=e->controls();c.pitchModel=1;c.sustainMode=0;c.masterTuneCents=5;c.pitchBendSemitones=1;e->setControls(c);e->sustainController(127);auto p=e->patch();p.feedback=4;e->setPatch(p,true);for(int i=0;i<4;++i)e->setControls(c);CHECK(same(a,A::allocator(*e)));CHECK(A::count(*e,60)==1);});
 test("split processing preserves both audio and allocation state",[]{auto a=engine(),b=engine();a->noteOn(67,111);b->noteOn(67,111);std::array<float,1024>x{},y{};a->process(x.data(),nullptr,x.size());b->process(y.data(),nullptr,17);b->process(y.data()+17,nullptr,y.size()-17);CHECK(x==y);CHECK(same(A::allocator(*a),A::allocator(*b)));});
 test("noise requests remain inert in Original allocation",[]{auto a=engine(),b=engine();auto c=b->controls();c.noiseRms=std::numeric_limits<double>::infinity();c.noiseModel=99;b->setControls(c);CHECK(b->controls().noiseRms==0&&b->controls().noiseModel==0);a->noteOn(60,100);b->noteOn(60,100);std::array<float,2048>x{},y{};a->process(x.data(),nullptr,x.size());b->process(y.data(),nullptr,y.size());CHECK(x==y);});
 test("bounded deterministic input stream preserves ownership and capacity",[]{auto e=engine();unsigned state=0x780680;for(int i=0;i<4096;++i){state=state*1664525u+1013904223u;int n=36+int((state>>8)%60),source=int((state>>20)&1);if(state&1)e->noteOn(n,1+int((state>>1)%127),source);else e->noteOff(n,source);if(i%127==0){auto c=e->controls();c.polyphony=1+int((state>>12)%12);e->setControls(c);}if(i%251==0)e->allNotesOff();invariants(*e);advance(*e,3);}});
 test("render and event path allocate no dynamic memory",[]{auto e=engine();std::array<float,64>l{},r{};allocations=0;tracking=true;for(int i=0;i<128;++i){e->noteOn(48+i%24,100,i%2);e->noteOff(48+(i+7)%24,i%2);if(i%17==0)e->allNotesOff();e->process(l.data(),r.data(),64);}tracking=false;CHECK(allocations==0);for(float v:l)CHECK(std::isfinite(v));});
 test("output bus exposes selector at three rates without nonfinite audio",[]{for(double rate:{44100.,48000.,96000.}){auto e=std::make_unique<press78::Press78OutputBus>();e->prepare(rate);e->setControls(controls());e->setPatch(press78::initPatch());CHECK(e->effectiveAllocationModel()==1);e->noteOn(60,100);std::array<float,1024>l{},r{};e->process(l.data(),r.data(),l.size());for(float v:l)CHECK(std::isfinite(v));e->allNotesOff();}});
 std::printf("Allocation groups passed=%d failed=%d fixture_events=%d fixture_field_checks=%d engine_bytes=%zu bus_bytes=%zu\n",passed,failed,fixtureEvents,fixtureChecks,sizeof(E),sizeof(press78::Press78OutputBus));return failed?1:0;
}
