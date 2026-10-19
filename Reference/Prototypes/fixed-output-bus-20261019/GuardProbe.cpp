#include "GuardedOutputBus.h"
#include "RecordedChorusProfile.h"
#include <iostream>
#include <iomanip>
#include <vector>
#include <cstdlib>
#include <new>
#include <stdexcept>
#include <cstring>
static std::size_t allocations=0;
void* operator new(std::size_t n){++allocations;if(auto*p=std::malloc(n))return p;throw std::bad_alloc();}
void* operator new[](std::size_t n){return ::operator new(n);}void operator delete(void*p) noexcept{std::free(p);}void operator delete[](void*p) noexcept{std::free(p);}
using namespace press78;using namespace press78::fixed_bus_research;
void require(bool yes,const char*message){if(!yes)throw std::runtime_error(message);}
template<class E> void setup(E&e,double rate,int mode){e.prepare(rate);Controls c;c.masterGain=mode==0?.01:2;c.outputLimit=mode!=2&&mode!=4;c.drive=mode==0||mode>=3?0:1;c.outputCircuit=false;c.dcBlock=false;c.toneCutoffHz=0;c.chorusMode=1;c.chorusMix=1;c.stereoWidth=2;c.chorusRateHz=RecordedChorusProfile::rateHz;c.chorusDepthMs=RecordedChorusProfile::depthMs;c.clockDriftPpm=20;c.pitchModel=1;c.sustainMode=1;e.setControls(c);auto p=initPatch();p.carrier.tl=0;p.modulator.tl=0;p.feedback=7;p.carrier.wave=2;e.setPatch(p);for(int i=0;i<12;++i)e.noteOn(48+i,127);}
int main(){try{std::cout<<std::setprecision(17);require(GuardedOutputBus::protectedSample(1.1f,true)==1,"+clip");require(GuardedOutputBus::protectedSample(-2.f,true)==-1,"-clip");require(GuardedOutputBus::protectedSample(1.1f,false)==1.1f,"unlimited");require(GuardedOutputBus::protectedSample(std::numeric_limits<float>::infinity(),false)==0,"finitefault");
for(float v:{-1.f,1.f,std::nextafter(1.f,0.f),std::nextafter(-1.f,0.f)})require(GuardedOutputBus::protectedSample(v,true)==v,"insidebound unchanged");
require(GuardedOutputBus::protectedSample(std::nextafter(1.f,2.f),true)==1,"nextafter positive");
require(GuardedOutputBus::protectedSample(std::nextafter(-1.f,-2.f),true)==-1,"nextafter negative");
std::cout<<"{\"row_statistics_scope\":\"first_one_second_before_separate_toggle_assertions\",\"sizeof_wrapper\":"<<sizeof(GuardedOutputBus)<<",\"rows\":[";bool first=true;
for(double rate:{8000.,11025.,16000.,22050.,24000.,32000.,44100.,44117.,48000.,88200.,96000.,176400.,192000.})for(int mode=0;mode<5;++mode){
    FixedOutputBus raw;GuardedOutputBus guard;setup(raw,rate,mode);setup(guard,rate,mode);std::array<float,127>l{},r{},a{},b{};double rawPeak=0,peak=0;bool exact=true;std::size_t n=0;
    while(n<static_cast<std::size_t>(rate)){auto count=std::min<std::size_t>(127,static_cast<std::size_t>(rate)-n);auto old=allocations;raw.process(l.data(),r.data(),count);guard.process(a.data(),b.data(),count);require(old==allocations,"allocation");for(std::size_t i=0;i<count;++i){rawPeak=std::max(rawPeak,std::max(std::abs(double(l[i])),std::abs(double(r[i]))));peak=std::max(peak,std::max(std::abs(double(a[i])),std::abs(double(b[i]))));require(std::isfinite(a[i])&&std::isfinite(b[i]),"finite");exact &= std::memcmp(&a[i],&l[i],4)==0&&std::memcmp(&b[i],&r[i],4)==0;require(a[i]==GuardedOutputBus::protectedSample(l[i],mode!=2&&mode!=4)&&b[i]==GuardedOutputBus::protectedSample(r[i],mode!=2&&mode!=4),"exact declared protection");}n+=count;}
    const auto firstClips=guard.clippedChannels();const auto firstDelta=guard.maximumClipDelta();
    // Explicit host-boundary limit toggles: old SRC history is also protected immediately.
    for(bool enabled:{false,true}) {auto c=raw.controls();c.outputLimit=enabled;raw.setControls(c);guard.setControls(c);raw.process(l.data(),r.data(),127);guard.process(a.data(),b.data(),127);for(int i=0;i<127;++i)require(a[i]==GuardedOutputBus::protectedSample(l[i],enabled)&&b[i]==GuardedOutputBus::protectedSample(r[i],enabled),"toggle timing/history");}
    if(mode==0||mode==2||mode==4||rate==48000)require(exact,"required exact output");if(mode!=2&&mode!=4)require(peak<=1,"output bound");require(raw.latencySamples()==guard.latencySamples(),"latency");
    if(!first)std::cout<<",";first=false;std::cout<<"{\"rate\":"<<rate<<",\"scenario\":"<<mode<<",\"raw_peak\":"<<rawPeak<<",\"protected_peak\":"<<peak<<",\"exact_raw\":"<<(exact?"true":"false")<<",\"clipped_channels\":"<<firstClips<<",\"maximum_clip_delta\":"<<firstDelta<<",\"finite_faults\":"<<guard.nonfiniteFaults()<<"}";
}
for(double rate:{8000.,44100.,44117.,48000.,96000.,192000.,44100.5,48000.25}) {
    GuardedOutputBus a,b,c;setup(a,rate,3);setup(b,rate,3);setup(c,rate,3);
    std::array<float,127>al{},ar{},bl{},br{},scratch{};
    a.process(al.data(),ar.data(),127);b.process(bl.data(),br.data(),64);b.process(bl.data()+64,br.data()+64,63);
    require(std::memcmp(al.data(),bl.data(),sizeof(al))==0&&std::memcmp(ar.data(),br.data(),sizeof(ar))==0,"guard split bytes");
    c.process(scratch.data(),scratch.data(),127);require(std::memcmp(scratch.data(),ar.data(),sizeof(ar))==0,"guard alias bytes");
    c.process(nullptr,nullptr,127);a.process(al.data(),ar.data(),127);c.process(scratch.data(),nullptr,127);a.process(al.data(),ar.data(),127);require(std::memcmp(scratch.data(),al.data(),sizeof(al))==0,"guard null advancement");
    const auto frame=a.hostFrame(),count=a.clippedChannels();a.process(nullptr,nullptr,0);require(a.hostFrame()==frame&&a.clippedChannels()==count,"guard zero count");
    a.allSoundOff();a.process(al.data(),ar.data(),127);for(int i=0;i<127;++i)require(al[i]==0&&ar[i]==0,"guard panic");a.reset();require(a.hostFrame()==0&&a.clippedChannels()==0,"guard reset");
}
std::cout<<"],\"passed\":true,\"audio_allocations\":0}\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
