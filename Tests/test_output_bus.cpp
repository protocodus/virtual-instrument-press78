#include "Press78OutputBus.h"
#include "FactoryVoices.h"
#include "output_bus_latency_cases.h"
#include "RecordedChorusProfile.h"
#include "../Tools/prototypes/fixed-output-bus-20261019/GuardedOutputBus.h"
#include <array>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <new>
#include <stdexcept>
#include <vector>
namespace { std::size_t allocationCount=0; }
void* operator new(std::size_t n){++allocationCount;if(void*p=std::malloc(n))return p;throw std::bad_alloc();}
void* operator new[](std::size_t n){return ::operator new(n);}
void operator delete(void*p) noexcept{std::free(p);}void operator delete[](void*p) noexcept{std::free(p);}
void operator delete(void*p,std::size_t) noexcept{std::free(p);}void operator delete[](void*p,std::size_t) noexcept{std::free(p);}
namespace {
using press78::Press78OutputBus;using Prototype=press78::fixed_bus_research::GuardedOutputBus;
void check(bool value,const char*message){if(!value)throw std::runtime_error(message);}
constexpr std::array<double,15> rates{{8000,11025,16000,22050,24000,32000,44100,44117,48000,88200,96000,176400,192000,44100.5,48000.25}};
press78::Controls controls(int profile){press78::Controls c;if(profile==0)return c;c.pitchModel=1;c.sustainMode=1;c.clockDriftPpm=20;c.chorusMode=1;c.chorusMix=1;c.chorusRateHz=press78::RecordedChorusProfile::rateHz;c.chorusDepthMs=press78::RecordedChorusProfile::depthMs;if(profile>=2){c.masterGain=2;c.outputCircuit=false;c.toneCutoffHz=0;c.dcBlock=false;c.stereoWidth=2;c.outputLimit=profile!=3;}if(profile==4){c.clockOffsetPpm=1234;c.clockDriftPpm=900;}return c;}
press78::Patch patch(int profile){if(profile<2)return press78::decodeVoice(press78::kFactoryVoices[profile?93:97].bytes);auto p=press78::initPatch();p.carrier.tl=0;p.modulator.tl=0;p.feedback=7;p.carrier.wave=2;return p;}
// Same fixed host events for both implementations, including live edits,
// coincident MIDI/CV notes, rawpedal state, polyphony changes and panic.
template<class E> void apply(E&e,int which,int profile){auto c=controls(profile);auto p=patch(profile);switch(which){
case 0:e.setPatch(p);e.setControls(c);e.setChorusTime(-32./48000.);for(int i=0;i<12;++i)e.noteOn(48+i,127,i%2);e.noteOn(60,100,1);break;
case 1:e.sustainController(1);e.noteOff(60,1);e.noteOff(50,0);break;
case 2:c.masterGain=.75;c.polyphony=7;c.pitchBendSemitones=.25;e.setControls(c);p.carrier.tl=12;e.setPatch(p,true);break;
case 3:e.sustainController(0);e.allNotesOff();e.noteOn(72,100);break;
case 4:c.outputLimit=!c.outputLimit;e.setControls(c);e.setPatch(p,false);break;
case 5:e.allSoundOff();break;
case 6:e.noteOn(65,120);e.sustainPedal(true);break;
case 7:e.noteOff(65);e.sustainPedal(false);break;
}}
constexpr double times[]={0,.03103,.07407,.11011,.13013,.17017,.19019,.22023};
template<class E> std::vector<float> render(double rate,int profile,int block){E e;e.prepare(rate);const auto frames=static_cast<std::size_t>(std::llround(.35*rate));std::vector<float>out(frames*2);std::array<float,127>l{},r{};std::size_t cursor=0,ev=0;while(cursor<frames){while(ev<8&&static_cast<std::size_t>(std::llround(times[ev]*rate))==cursor)apply(e,static_cast<int>(ev++),profile);auto end=ev<8?static_cast<std::size_t>(std::llround(times[ev]*rate)):frames;auto n=std::min<std::size_t>(block,std::min(end,frames)-cursor);check(n>0,"fixture advance");e.process(l.data(),r.data(),n);for(std::size_t i=0;i<n;++i){out[2*(cursor+i)]=l[i];out[2*(cursor+i)+1]=r[i];}cursor+=n;}return out;}
bool bytesEqual(const std::vector<float>&a,const std::vector<float>&b){return a.size()==b.size()&&std::memcmp(a.data(),b.data(),a.size()*sizeof(float))==0;}
}
int main(){try{std::size_t checks=0,comparedBytes=0;
check(sizeof(Press78OutputBus)<=196608,"instance budget");++checks;
check(std::memcmp(press78::output_bus_detail::kKernel.data(),press78::fixed_bus_research::kKernel.data(),sizeof(press78::output_bus_detail::kKernel))==0,"frozen kernel byte identity");++checks;
// Every grid phase a tabulated host rate reaches, and the row read() picks for it, is the coefficient() row bit for bit.
{namespace d=press78::output_bus_detail;for(const auto& [rate,table]:{std::pair{44100.,&d::kPhaseTable44100},{88200.,&d::kPhaseTable176400},{176400.,&d::kPhaseTable176400},{96000.,&d::kPhaseTable192000},{192000.,&d::kPhaseTable192000}}){d::OutputSRC src;src.prepare(rate);const auto& t=*table;check(t.taps==2*src.halfDelay()+1,"phase table taps");std::vector<bool> seen(t.phases);for(std::uint64_t frame=0;frame<static_cast<std::uint64_t>(rate);++frame){const auto pos=d::physicalPosition(frame,rate);const auto p=static_cast<int>(pos.fraction*t.phases+.5);check(p<t.phases,"phase index");if(seen[p])continue;seen[p]=true;for(int j=0;j<t.taps;++j){const double c=src.coefficient(static_cast<double>(j-src.halfDelay())-pos.fraction);check(std::memcmp(&c,t.rows+p*t.taps+j,sizeof c)==0,"phase rows equal coefficient()");}}if(rate==table->rate)for(bool b:seen)check(b,"every phase reached");++checks;}}
for(double rate:rates)for(int profile=0;profile<5;++profile){auto a=render<Press78OutputBus>(rate,profile,64),b=render<Prototype>(rate,profile,127);check(bytesEqual(a,b),"production/prototype output bytes");comparedBytes+=a.size()*sizeof(float);++checks;if(rate==48000){auto old=render<press78::Press78Engine>(rate,profile,127);check(bytesEqual(a,old),"48k legacy bytes");++checks;}}
for(double rate:rates){Press78OutputBus e;e.prepare(rate);apply(e,0,1);std::array<float,64>l{},r{},s{};auto before=allocationCount;e.process(l.data(),r.data(),64);e.sustainController(127);e.noteOff(48);e.setControls(e.controls());e.setPatch(e.patch(),true);e.allNotesOff();e.process(nullptr,nullptr,64);e.allSoundOff();e.process(l.data(),r.data(),64);check(allocationCount==before,"render/event allocation");for(auto v:l)check(v==0,"panic clears outerhistory");for(auto v:r)check(v==0,"panic stereo");++checks;
const int half=static_cast<int>(std::ceil(96/std::min(1.,rate/48000.)));const auto expected=rate==48000?32:static_cast<int>(std::ceil((32.+half)*rate/48000.));check(e.latencySamples()==expected,"latency");++checks;e.reset();check(e.hostFrame()==0&&e.nextPhysicalFrame()==0&&e.clippedChannels()==0,"reset counters");++checks;
Press78OutputBus a,b,c;for(auto*p:{&a,&b,&c}){p->prepare(rate);apply(*p,0,1);}a.process(l.data(),r.data(),64);b.process(s.data(),s.data(),64);check(std::memcmp(s.data(),r.data(),sizeof(s))==0,"alias rightwins");c.process(nullptr,nullptr,64);a.process(l.data(),r.data(),64);c.process(s.data(),nullptr,64);check(std::memcmp(s.data(),l.data(),sizeof(s))==0,"null advances");++checks;
for(std::uint64_t frame:{0ULL,1ULL,4800ULL,480000ULL,29030551201ULL}){auto a=press78::output_bus_detail::physicalPosition(frame,rate);auto b=press78::fixed_bus_research::physicalPosition(frame,rate);check(a.floor==b.floor&&a.ceil==b.ceil&&std::memcmp(&a.fraction,&b.fraction,sizeof(double))==0,"position equivalence");++checks;}}
for(double rate:{-1.,0.,7999.,192001.,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()}){Press78OutputBus a;Prototype b;a.prepare(rate);b.prepare(rate);check(a.sampleRate()==b.sampleRate()&&a.latencySamples()==b.latencySamples(),"invalid rates");++checks;}
for(const auto& c:kOutputLatencyCases){Press78OutputBus e;e.prepare(c.rate);check(e.latencySamples()==c.frames,"independent exact latency oracle");++checks;}
for(bool enabled:{false,true})for(float value:{-0.f,0.f,-1.f,1.f,std::nextafter(1.f,2.f),std::nextafter(-1.f,-2.f),2.f,-2.f,std::numeric_limits<float>::infinity(),-std::numeric_limits<float>::infinity(),std::numeric_limits<float>::quiet_NaN()}){auto a=Press78OutputBus::protectedSample(value,enabled),b=Prototype::protectedSample(value,enabled);check(std::memcmp(&a,&b,4)==0,"protection edgebytes");++checks;}
std::cout<<"{\"passed\":true,\"checks\":"<<checks<<",\"production_prototype_compared_bytes\":"<<comparedBytes<<",\"sizeof_output_bus\":"<<sizeof(Press78OutputBus)<<",\"shared_kernel_bytes\":"<<sizeof(press78::output_bus_detail::kKernel)<<",\"render_event_allocations\":0}\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
