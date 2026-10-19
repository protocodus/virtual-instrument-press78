// Protocol: design-frozen.json. Synthetic inputs only; no ROM/media decoding.
#include "../../../Source/DSP/Press78Engine.cpp"
#include "CommandAudioConsumer.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <new>
#include <string>
#include <vector>

static bool countAllocations=false;
static std::size_t allocations=0;
void* operator new(std::size_t size) { if(countAllocations) ++allocations; if(void* p=std::malloc(size?size:1)) return p; throw std::bad_alloc(); }
void* operator new[](std::size_t size) { return ::operator new(size); }
void operator delete(void* p) noexcept { std::free(p); }
void operator delete[](void* p) noexcept { std::free(p); }
void operator delete(void* p,std::size_t) noexcept { std::free(p); }
void operator delete[](void* p,std::size_t) noexcept { std::free(p); }

using Consumer=press78::research::CommandAudioConsumer;
using Commands=press78::research::Mode00CompleteCommands;
using Access=press78::Press78SustainTestAccess;
static std::uint64_t assertions=0;
static void check(bool ok,const char* what) { ++assertions; if(!ok) { std::cerr<<"FAIL "<<what<<" at assertion "<<assertions<<"\n"; std::exit(1); } }
static void ok(Consumer::Status status) { check(status==Consumer::Status::Ok,"accepted consumer event"); }
static Commands::WorkingPatch working(int table=0,int rr=8) {
    Commands::WorkingPatch p;
    p.bytes[0]=p.bytes[1]=1;
    p.bytes[2]=24;p.bytes[3]=20;
    p.bytes[6]=p.bytes[7]=63;
    p.bytes[10]=p.bytes[11]=static_cast<std::uint8_t>(table<<6);
    p.bytes[12]=p.bytes[13]=static_cast<std::uint8_t>(rr);
    p.bytes[14]=8;
    p.bytes[19]=p.bytes[20]=5;
    return p;
}
static press78::Patch native(const Commands::WorkingPatch& p) {
    std::array<std::uint8_t,33> b{};
    std::copy(p.bytes.begin(),p.bytes.end(),b.begin()+1);
    return press78::decodeVoice(b);
}
static Consumer::Status initialize(Consumer& c,Commands::WorkingPatch p=working(),int effects=0,
                                    press78::Controls controls={}) {
    Commands::Snapshot s;
    s.controllers.volumeIndex=9;s.front.patch=p;s.front.effects=static_cast<std::uint8_t>(effects);
    return c.initialize(Commands::Target::PSS780,s,controls,48000,
        Consumer::ReverbPolicy::StoreReverbBitWithoutAudioEffect);
}
static void load(Consumer& c,const Commands::WorkingPatch& p=working()) { ok(initialize(c,p));ok(c.selectProgram(p,0)); }
static Consumer::Plan raw(std::initializer_list<Consumer::Write> words) {
    Consumer::Plan p;p.count=words.size();std::copy(words.begin(),words.end(),p.writes.begin());return p;
}
static Consumer::Notes notes(const Consumer& c) { return c.frontend().state().allocator.notes; }
static void equalPlan(const Consumer::Plan& p,std::initializer_list<Consumer::Write> expected) {
    check(p.count==expected.size(),"exact command count");std::size_t i=0;
    for(const auto word:expected) { check(p.writes[i].address==word.address,"exact address order");check(p.writes[i++].value==word.value,"exact value order"); }
}
static bool sameDynamics(const Access::Dynamics& a,const Access::Dynamics& b,bool coefficients=true) {
    return a.modPhase==b.modPhase && a.carrierPhase==b.carrierPhase && a.prev1==b.prev1 && a.prev2==b.prev2
      && a.modAttenuation==b.modAttenuation && a.carrierAttenuation==b.carrierAttenuation
      && a.ticks==b.ticks && a.note==b.note && a.modStage==b.modStage && a.carrierStage==b.carrierStage
      && a.active==b.active && a.held==b.held && a.released==b.released
      && a.modFinished==b.modFinished && a.carrierFinished==b.carrierFinished
      && (!coefficients || (a.modRelease==b.modRelease && a.carrierRelease==b.carrierRelease
           && a.modStep==b.modStep && a.carrierStep==b.carrierStep && a.modGain==b.modGain && a.carrierGain==b.carrierGain));
}
static bool sameImage(const Consumer::Image& a,const Consumer::Image& b) {
    for(int i=0;i<12;++i) {
        const auto& x=a.slots[i];const auto& y=b.slots[i];
        if(x.mod!=y.mod || x.car!=y.car || x.feedback!=y.feedback || x.pmsAms!=y.pmsAms
           || x.pitchHigh!=y.pitchHigh || x.pitchLow!=y.pitchLow || x.pitchBlock!=y.pitchBlock || x.valid!=y.valid || x.keyed!=y.keyed) return false;
    }return true;
}
static bool sameFrontend(const Commands::Snapshot& a,const Commands::Snapshot& b) {
    const auto& x=a.front;const auto& y=b.front;const auto& u=x.allocator;const auto& v=y.allocator;
    return x.patch.bytes==y.patch.bytes && x.cachedPrograms==y.cachedPrograms && x.program==y.program && x.effects==y.effects
      && u.ranks==v.ranks && u.notes==v.notes && u.sources==v.sources && u.valid==v.valid && u.keyed==v.keyed
      && u.pending==v.pending && u.held==v.held && u.pool==v.pool && a.vibratoDelay==b.vibratoDelay
      && a.controllers.volumeIndex==b.controllers.volumeIndex && a.controllers.bendHigh==b.controllers.bendHigh
      && a.controllers.bendSpan==b.controllers.bendSpan && a.controllers.fineSteps==b.controllers.fineSteps;
}
static void equalAudio(Consumer& a,Consumer& b,std::size_t count=257) {
    std::array<float,257> al{},ar{},bl{},br{};check(count<=al.size(),"bounded comparison");
    a.process(al.data(),ar.data(),count);b.process(bl.data(),br.data(),count);
    for(std::size_t i=0;i<count;++i) { check(al[i]==bl[i],"unchanged next left audio");check(ar[i]==br[i],"unchanged next right audio"); }
}
static void rejection(Consumer& c,const Consumer::Plan& p,Consumer::Notes n,Consumer::Status expected) {
    auto unchanged=std::make_unique<Consumer>(c);
    const auto epochs=c.epochs();const auto last=c.lastPlan();
    check(c.applyRaw(p,n)==expected,"expected raw rejection");
    check(sameImage(c.image(),unchanged->image()),"atomic image");
    check(sameFrontend(c.frontend().snapshot(),unchanged->frontend().snapshot()),"atomic frontend");
    check(c.epochs()==epochs,"atomic epoch count");
    check(c.lastPlan().count==last.count,"atomic last trace count");
    for(std::size_t i=0;i<last.count;++i) {check(c.lastPlan().writes[i].address==last.writes[i].address,"atomic trace address");check(c.lastPlan().writes[i].value==last.writes[i].value,"atomic trace value");}
    for(int i=0;i<12;++i) check(sameDynamics(Access::dynamics(c.engine(),i),Access::dynamics(unchanged->engine(),i)),"atomic native slot");
    equalAudio(c,*unchanged);
}
static void commandTests() {
    auto c=std::make_unique<Consumer>();
    check(c->noteOn(36)==Consumer::Status::NotReady,"explicit initialization required");
    Commands::Snapshot s;s.controllers.volumeIndex=9;
    check(c->initialize(Commands::Target::PSS780,s,{},48000,Consumer::ReverbPolicy::Unspecified)==Consumer::Status::InvalidInitialization,"explicit reverb policy required");
    auto badControls=press78::Controls{};badControls.pitchModel=1;
    check(initialize(*c,working(),0,badControls)==Consumer::Status::InvalidInitialization,"no second pitch transform");
    s.front.allocator.notes[0]=36;
    check(c->initialize(Commands::Target::PSS780,s,{},48000,Consumer::ReverbPolicy::StoreReverbBitWithoutAudioEffect)==Consumer::Status::InvalidInitialization,"no invented warm boot");
    ok(initialize(*c));
    check(c->serviceKeyOn()==Consumer::Status::Ok,"empty service has no writes");
    auto fresh=std::make_unique<Consumer>(*c);
    // Missing preload must reject the entire frontend transaction, including
    // its already-previewed note/allocator mutation.
    const auto before=c->frontend().snapshot();
    ok(c->noteOn(36)); // Note preparation is legal; it has no key-on yet.
    check(c->serviceKeyOn()==Consumer::Status::MissingRegisters,"key-on rejects missing fields");
    check(c->frontend().state().allocator.pending[0]==1,"pending allocation unconsumed on rejection");
    check(!c->image().slots[0].keyed,"missing key-on remains off");
    check(fresh->frontend().state().allocator.notes[0]==0 && before.front.allocator.notes[0]==0,"fresh state explicit");
    c=std::make_unique<Consumer>();load(*c);
    check(c->lastPlan().count==168,"full program reload count");
    check(c->image().slots[0].valid==((1u<<14)-1),"program parameters known, pitch unknown");
    ok(c->noteOn(36));
    equalPlan(c->lastPlan(),{{0x2e0,8},{0x2e8,8},{0x208,0},{0x260,24},{0x268,20},{0x228,5},{0x230,26},{0x238,40},{0x2e8,15}});
    check(!c->image().slots[0].keyed,"note waits for service");
    check(c->image().slots[0].car[5]==15,"intermediate RR15 retained");
    check(Consumer::fnum(c->image().slots[0])==2394 && Consumer::block(c->image().slots[0])==2,"actual pitch word decode");
    ok(c->serviceKeyOn());equalPlan(c->lastPlan(),{{0x218,0},{0x2e8,8},{0x208,24}});
    check(c->image().slots[0].keyed,"key edge committed");
    check(Access::slotPatch(c->engine(),0).carrier.rr==8,"service restores raw RR");
    check(Access::slotPatch(c->engine(),0).vibratoDelay==0,"native VDT bypassed");
    check(Access::slotPatch(c->engine(),0).carrier.lksHi==0,"no duplicate LKS");
    std::array<float,123> l{},r{};c->process(l.data(),r.data(),l.size());
    auto prior=Access::dynamics(c->engine(),0);
    ok(c->applyRaw(raw({{0x208,24}}),notes(*c)));
    check(sameDynamics(prior,Access::dynamics(c->engine(),0)),"key1 to key1 preserves state");
    ok(c->noteOff(36));equalPlan(c->lastPlan(),{{0x2e0,8},{0x2e8,8},{0x208,0}});
    const auto released=Access::dynamics(c->engine(),0);
    check(released.released && !released.held && released.active,"keyoff enters release without panic");
    check(released.modPhase==prior.modPhase && released.prev1==prior.prev1,"keyoff preserves phase and feedback");
    ok(c->noteOn(36));ok(c->serviceKeyOn());
    const auto reset=Access::dynamics(c->engine(),0);
    check(reset.modPhase==0 && reset.carrierPhase==0 && reset.prev1==0 && reset.prev2==0 && reset.ticks==0,"genuine off/on inherits configure reset");
    for(int note=37;note<=48;++note) {ok(c->noteOn(note));ok(c->serviceKeyOn());}
    check(c->engine().activeVoices()==12 && Access::tailsEmpty(c->engine()),"twelve fixed slots, no steal tails");
    for(int slot=0;slot<12;++slot) {
        check(c->image().slots[slot].valid==Consumer::kComplete,"all fixed slots loaded");
        check(Access::dynamics(c->engine(),slot).note==c->frontend().state().allocator.notes[slot],"source mapped note for inherited RKS");
    }
    // Legal operation on a copy must reject atomically when raw-image damage
    // prevents keyon, rather than committing a second frontend state.
    auto malformed=raw({{0x260,17},{0x207,0}});
    rejection(*c,malformed,notes(*c),Consumer::Status::UnsupportedPlan);
    for(int value=0;value<256;++value) {
        const bool good=(value&128)==0 && (value&7)<6 && ((value&24)==0 || (value&24)==24)
                      && ((value&96)==0 || (value&96)==96);
        if(!good) rejection(*c,raw({{0x208,static_cast<std::uint8_t>(value)}}),notes(*c),Consumer::Status::UnsupportedPlan);
    }
    for(const auto word : {Consumer::Write{0x218,4},Consumer::Write{0x220,0},Consumer::Write{0x228,32},Consumer::Write{0x230,64},Consumer::Write{0x238,1},Consumer::Write{0x246,0},Consumer::Write{0x2ff,0},Consumer::Write{0x327,0}})
        rejection(*c,raw({{0x268,0},word}),notes(*c),Consumer::Status::UnsupportedPlan);
    auto over=raw({{0x260,0}});over.count=205;rejection(*c,over,notes(*c),Consumer::Status::UnsupportedPlan);
    auto status=raw({{0x260,0}});status.status=Commands::Status::UnsupportedState;rejection(*c,status,notes(*c),Consumer::Status::UnsupportedPlan);
    auto badNotes=notes(*c);badNotes[11]=127;rejection(*c,raw({{0x260,0}}),badNotes,Consumer::Status::UnsupportedMetadata);
    auto unchanged=std::make_unique<Consumer>(*c);
    check(c->sustainController(128)==Consumer::Status::RejectedFrontend,"unsupported controller rejected");
    check(sameFrontend(c->frontend().snapshot(),unchanged->frontend().snapshot()),"controller atomic frontend");equalAudio(*c,*unchanged);
    check(Access::tailsEmpty(c->engine()),"never creates source allocator tails");
}
static void liveTests() {
    for(int table=0;table<4;++table) {
        auto c=std::make_unique<Consumer>();auto w=working(table,4);load(*c,w);ok(c->noteOn(48));ok(c->serviceKeyOn());
        std::array<float,300> l{},r{};c->process(l.data(),r.data(),l.size());
        auto d=Access::dynamics(c->engine(),0);
        ok(c->applyRaw(raw({{0x260,127},{0x268,127}}),notes(*c)));
        const auto muted=Access::dynamics(c->engine(),0);
        check(sameDynamics(d,muted,false),"TL127 does not reset native state");
        check(muted.modGain==0 && muted.carrierGain==0,"TL127 follows inherited endpoint");
        ok(c->applyRaw(raw({{0x260,24},{0x268,20},{0x2c0,static_cast<std::uint8_t>(((table+1)%4)<<6)}}),notes(*c)));
        check(sameDynamics(d,Access::dynamics(c->engine(),0),false),"live TL/wave preserves state");
        check(Access::slotPatch(c->engine(),0).modulator.wave==(table+1)%4,"live wave decoded");
        ok(c->noteOff(48));c->process(l.data(),r.data(),l.size());d=Access::dynamics(c->engine(),0);
        ok(c->sustainController(1));const auto sr=Access::dynamics(c->engine(),0);
        check(sameDynamics(d,sr,false),"CC64 preserves release state");
        check(sr.carrierRelease!=d.carrierRelease && Access::slotPatch(c->engine(),0).carrier.rr==5,"raw nonzero CC64 uses SRR once");
        ok(c->sustainController(0));check(Access::dynamics(c->engine(),0).carrierRelease==d.carrierRelease,"zero CC64 restores RR");
        check(!Access::slotPatch(c->engine(),0).sustain,"no second sustain choice");
        // Same accepted word sequence split across plans has exactly equal
        // subsequent audio: no invented bus interval between ordered writes.
        auto split=std::make_unique<Consumer>(*c);
        ok(c->applyRaw(raw({{0x260,31},{0x268,27},{0x2e8,7}}),notes(*c)));
        ok(split->applyRaw(raw({{0x260,31}}),notes(*split)));ok(split->applyRaw(raw({{0x268,27}}),notes(*split)));ok(split->applyRaw(raw({{0x2e8,7}}),notes(*split)));
        equalAudio(*c,*split);
    }
    // Frontend delay counts service invocations, not a guessed time period.
    auto w=working();w.bytes[15]=0x33;w.bytes[21]=2;w.bytes[23]=128;
    auto c=std::make_unique<Consumer>();load(*c,w);ok(c->noteOn(36));ok(c->serviceKeyOn());
    check(c->frontend().vibratoDelay()[0]==4 && c->image().slots[0].pmsAms==3,"PMS initially gated, AMS retained");
    std::array<float,1000> l{},r{};c->process(l.data(),r.data(),l.size());
    check(c->frontend().vibratoDelay()[0]==4 && Access::slotPatch(c->engine(),0).pms==0,"samples do not advance firmware delay");
    for(int i=0;i<3;++i) {ok(c->serviceVibrato());check(c->lastPlan().count==0,"no early PMS word");}
    const auto d=Access::dynamics(c->engine(),0);ok(c->serviceVibrato());
    equalPlan(c->lastPlan(),{{0x218,0x33}});check(c->frontend().vibratoDelay()[0]==0,"exact fourth invocation expires");
    check(sameDynamics(d,Access::dynamics(c->engine(),0)),"PMS write preserves full dynamics");
    check(Access::slotPatch(c->engine(),0).pms==3 && Access::slotPatch(c->engine(),0).vibratoDelay==0,"one frontend PMS gate");
    // Store-only Reverb is explicit. The raw high bit is retained, but it
    // cannot invent an envelope change or an additional audio effect.
    auto noReverb=std::make_unique<Consumer>(*c);
    ok(c->applyRaw(raw({{0x260,152},{0x268,148}}),notes(*c)));
    check(c->reverbAudioUnsupported() && !noReverb->reverbAudioUnsupported(),"Reverb bit exposed as unsupported audio");
    equalAudio(*c,*noReverb);
    // PSS780 program selection keys off old voices, then TL127 reloads. Verify
    // output/chorus memories survive by comparing the first delayed output
    // sample before any newly muted synthesis can reach the 32-tick output.
    auto outputControls=press78::Controls{};outputControls.chorusMix=.5;
    c=std::make_unique<Consumer>();ok(initialize(*c,working(),0,outputControls));ok(c->selectProgram(working(),0));ok(c->noteOn(36));ok(c->serviceKeyOn());
    c->process(l.data(),r.data(),l.size());auto old=std::make_unique<Consumer>(*c);
    const auto prior=Access::dynamics(c->engine(),0);ok(c->selectProgram(working(2),1));
    const auto post=Access::dynamics(c->engine(),0);
    check(prior.modPhase==post.modPhase && prior.prev1==post.prev1 && prior.ticks==post.ticks,"program TL127 preserves phase/history");
    check(post.released && post.active && post.carrierGain==0,"program mute without panic");
    float al=0,ar=0,bl=0,br=0;c->process(&al,&ar,1);old->process(&bl,&br,1);
    check(al==bl && ar==br && al!=0,"program does not clear output/circuit/chorus history");
}
struct Audio { std::vector<float> left,right;explicit Audio(std::size_t n):left(n),right(n){} };
static Audio render(bool command,int table,bool overlap,std::size_t chunk) {
    constexpr std::size_t length=96000;
    Audio out(length);
    auto w=working(table,overlap?4:8);if(overlap) w.bytes[2]=127;
    auto c=std::make_unique<Consumer>();auto baseline=std::make_unique<press78::Press78Engine>();
    if(command) load(*c,w);
    else {auto controls=press78::Controls{};controls.pitchModel=1;baseline->setControls(controls);baseline->prepare(48000);baseline->setPatch(native(w));}
    const std::array<std::size_t,4> times=overlap?std::array<std::size_t,4>{{0,14400,15360,31200}}:std::array<std::size_t,4>{{0,16800,36000,52800}};
    std::size_t event=0,frame=0;
    while(frame<length) {
        if(event<4 && frame==times[event]) {
            const int note=overlap?36:event<2?36:48;
            if(command) {if(event%2==0) {ok(c->noteOn(note));ok(c->serviceKeyOn());}else ok(c->noteOff(note));}
            else if(event%2==0) baseline->noteOn(note,127);else baseline->noteOff(note);
            ++event;
        }
        const std::size_t next=event<4?times[event]:length;
        const std::size_t n=std::min({chunk,length-frame,next-frame});check(n!=0,"render progress");
        if(command) c->process(out.left.data()+frame,out.right.data()+frame,n);
        else baseline->process(out.left.data()+frame,out.right.data()+frame,n);
        frame+=n;
    }return out;
}
static std::uint64_t compare(const Audio& a,const Audio& b,bool requireEqual) {
    std::uint64_t different=0;check(a.left.size()==b.left.size(),"audio length");
    for(std::size_t i=0;i<a.left.size();++i) {
        check(std::isfinite(a.left[i]) && std::isfinite(a.right[i]) && std::isfinite(b.left[i]) && std::isfinite(b.right[i]),"finite audio");
        const bool equal=a.left[i]==b.left[i] && a.right[i]==b.right[i];different+=!equal;
        if(requireEqual) check(equal,"exact shipping/fixed-slot equivalence");
    }return different;
}
static void writeWav(const std::string& path,const Audio& a) {
    std::ofstream f(path,std::ios::binary);check(static_cast<bool>(f),"WAV destination");
    const auto u16=[&](std::uint16_t x){f.put(static_cast<char>(x));f.put(static_cast<char>(x>>8));};
    const auto u32=[&](std::uint32_t x){u16(static_cast<std::uint16_t>(x));u16(static_cast<std::uint16_t>(x>>16));};
    f.write("RIFF",4);u32(static_cast<std::uint32_t>(36+a.left.size()*8));f.write("WAVEfmt ",8);u32(16);u16(3);u16(2);u32(48000);u32(384000);u16(8);u16(32);f.write("data",4);u32(static_cast<std::uint32_t>(a.left.size()*8));
    for(std::size_t i=0;i<a.left.size();++i) for(const auto x:{a.left[i],a.right[i]}) {std::uint32_t bits=0;std::memcpy(&bits,&x,4);u32(bits);}
    check(static_cast<bool>(f),"WAV write");
}
static std::pair<double,double> metrics(const Audio& a) {double sum=0,peak=0;for(std::size_t i=0;i<a.left.size();++i) for(const double x:{a.left[i],a.right[i]}) {sum+=x*x;peak=std::max(peak,std::abs(x));}return {std::sqrt(sum/(2*a.left.size())),peak};}
int main(int argc,char** argv) {
    commandTests();liveTests();
    std::array<std::uint64_t,5> differences{};
    for(int table=0;table<4;++table) {const auto a=render(false,table,false,256);const auto b=render(true,table,false,256);differences[table]=compare(a,b,true);}
    const auto a=render(false,0,true,256),b=render(true,0,true,256);differences[4]=compare(a,b,false);check(differences[4]>0,"declared overlap policy differs");
    const auto chunked=render(true,0,true,1);check(compare(b,chunked,true)==0,"chunk invariance at same epochs");
    auto c=std::make_unique<Consumer>();load(*c);std::array<float,4096> l{},r{};
    countAllocations=true;
    const auto on=c->noteOn(36),service=c->serviceKeyOn();c->process(l.data(),r.data(),l.size());const auto cc=c->sustainController(1),off=c->noteOff(36),vib=c->serviceVibrato(),program=c->selectProgram(working(3),1);
    c->process(l.data(),r.data(),l.size());countAllocations=false;
    ok(on);ok(service);ok(cc);ok(off);ok(vib);ok(program);check(allocations==0,"no observed command/process new allocations");
    std::cout<<"{\"assertions\":"<<assertions<<",\"allocations_during_measured_operations\":"<<allocations<<",\"frame_differences\":[";
    for(std::size_t i=0;i<5;++i) std::cout<<(i?",":"")<<differences[i];
    std::cout<<"],\"overlap_A_rms\":"<<std::setprecision(17)<<metrics(a).first<<",\"overlap_A_peak\":"<<metrics(a).second<<",\"overlap_B_rms\":"<<metrics(b).first<<",\"overlap_B_peak\":"<<metrics(b).second<<",\"consumer_bytes\":"<<sizeof(Consumer)<<"}\n";
    if(argc==2) {
        // Only this opt-in branch writes the five frozen short render pairs.
        for(int caseId=0;caseId<5;++caseId) {
            const bool overlap=caseId==4;const int table=overlap?0:caseId;
            const auto aa=render(false,table,overlap,256),bb=render(true,table,overlap,256);
            const auto prefix=std::string(argv[1])+"/0"+std::to_string(caseId+1)+"/";
            writeWav(prefix+"A.wav",aa);writeWav(prefix+"B.wav",bb);
        }
    }
}
