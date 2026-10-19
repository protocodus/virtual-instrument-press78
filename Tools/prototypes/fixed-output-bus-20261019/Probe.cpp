#include "FixedOutputBus.h"
#include "FactoryVoices.h"
#include "RecordedChorusProfile.h"
#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <new>
#include <stdexcept>
#include <string>
#include <vector>
static std::size_t allocations=0;
void* operator new(std::size_t n){++allocations;if(auto*p=std::malloc(n))return p;throw std::bad_alloc();}
void* operator new[](std::size_t n){return ::operator new(n);}
void operator delete(void*p) noexcept{std::free(p);} void operator delete[](void*p) noexcept{std::free(p);}
using press78::fixed_bus_research::FixedOutputBus;
using press78::fixed_bus_research::OutputSRC;
using press78::fixed_bus_research::physicalPosition;
void require(bool yes,const char* message){if(!yes)throw std::runtime_error(message);}
constexpr double rates[]={8000,11025,16000,22050,24000,32000,44100,44117,48000,88200,96000,176400,192000};
press78::Controls controls(int variant=0){
    press78::Controls c;c.masterGain=variant==0?1:.25;c.outputCircuit=variant!=0;
    c.toneCutoffHz=variant==0?0:14000;c.dcBlock=variant!=0;c.outputLimit=variant!=0;
    c.pitchModel=1;c.sustainMode=variant%2;c.chorusMode=1;c.chorusMix=variant==0?0:1;
    c.chorusRateHz=press78::RecordedChorusProfile::rateHz;c.chorusDepthMs=press78::RecordedChorusProfile::depthMs;
    c.clockOffsetPpm=variant==2?1234:0;c.clockDriftPpm=variant==3?20:0;c.drive=variant==4?1:0;return c;
}
template<class E> void event(E&e,int index,int variant=0){
    auto c=controls(variant);auto p=press78::initPatch();p.carrier.tl=8;p.modulator.tl=24;p.feedback=5;
    switch(index){
    case 0:e.setPatch(p);e.setControls(c);e.setChorusTime(-32./48000.);e.noteOn(65,127);break;
    case 1:for(int n=0;n<15;++n)e.noteOn(48+n,100,n%2);break;
    case 2:e.sustainController(1);e.noteOff(65);e.noteOff(50,0);break;
    case 3:c.masterGain=.7;c.pitchBendSemitones=.25;c.drive=.8;e.setControls(c);p.carrier.tl=16;e.setPatch(p,true);break;
    case 4:e.sustainController(127);e.allNotesOff();break;
    case 5:e.sustainController(0);e.noteOn(72,100,1);break;
    case 6:e.allSoundOff();break;
    case 7:e.noteOn(60,120);break;
    }
}
const double times[]={0,.10003,.23007,.41011,.65013,.81017,1.11019,1.31023};
void write(const std::string&path,const std::vector<float>&x){std::ofstream f(path,std::ios::binary);f.write(reinterpret_cast<const char*>(x.data()),x.size()*4);require(bool(f),"write");}
std::vector<float> read(const std::string&path){std::ifstream f(path,std::ios::binary|std::ios::ate);require(bool(f),"open input");auto n=f.tellg();require(n>=0&&n%8==0,"stereo input size");std::vector<float>x(static_cast<std::size_t>(n)/4);f.seekg(0);f.read(reinterpret_cast<char*>(x.data()),n);return x;}
template<class E> std::vector<float> render(double rate,int variant,std::size_t block){
    E e;e.prepare(rate);std::vector<float>result(static_cast<std::size_t>(2*rate)*2),l(block),r(block);
    std::size_t cursor=0,ev=0;
    while(cursor<result.size()/2){
        while(ev<8&&static_cast<std::size_t>(std::llround(times[ev]*rate))==cursor)event(e,static_cast<int>(ev++),variant);
        auto end=ev<8?static_cast<std::size_t>(std::llround(times[ev]*rate)):result.size()/2;
        auto n=std::min(block,std::min(end,result.size()/2)-cursor);require(n>0,"zero render block");
        e.process(l.data(),r.data(),n);for(std::size_t i=0;i<n;++i){result[2*(cursor+i)]=l[i];result[2*(cursor+i)+1]=r[i];}cursor+=n;
    }return result;
}
void selftest(){
    int checks=0;std::size_t identityBytes=0;
    for(int variant=0;variant<5;++variant)for(auto block:{1,64,127}){
        const auto a=render<press78::Press78Engine>(48000,variant,block),b=render<FixedOutputBus>(48000,variant,block);
        require(a.size()==b.size()&&std::memcmp(a.data(),b.data(),a.size()*sizeof(float))==0,"48k identity");identityBytes+=a.size()*4;++checks;
    }
    for(double rate:rates){
        const auto a=render<FixedOutputBus>(rate,3,64),b=render<FixedOutputBus>(rate,3,127);
        require(a.size()==b.size()&&std::memcmp(a.data(),b.data(),a.size()*sizeof(float))==0,"split blocks");++checks;
        FixedOutputBus e;e.prepare(rate);event(e,0);std::vector<float>zero(73),l(73),r(73);e.process(l.data(),r.data(),73);
        const auto frame=e.hostFrame();const auto pos=physicalPosition(frame,rate);const auto before=e.nextPhysicalFrame();
        e.setControls(e.controls());require(e.nextPhysicalFrame()==(rate==48000?frame:pos.ceil),"flush actual index");require(before<=e.nextPhysicalFrame(),"no backwards source index");++checks;
        const auto next=e.nextPhysicalFrame();e.process(nullptr,nullptr,0);require(next==e.nextPhysicalFrame()&&frame==e.hostFrame(),"zero frame");
        e.allSoundOff();e.process(l.data(),r.data(),73);require(l==zero&&r==zero,"immediate panic silence");++checks;
        auto count=allocations;e.noteOn(60,100);e.setControls(e.controls());e.sustainController(1);e.noteOff(60);e.process(l.data(),r.data(),73);e.allNotesOff();e.sustainPedal(false);e.allSoundOff();require(allocations==count,"audio/event allocation");++checks;
        e.reset();require(e.hostFrame()==0&&e.nextPhysicalFrame()==0,"reset counters");e.process(l.data(),r.data(),73);require(l==zero&&r==zero,"reset silence");++checks;
        FixedOutputBus nullEngine,full,alias;for(auto*p:{&nullEngine,&full,&alias}){p->prepare(rate);event(*p,0,3);}full.process(l.data(),r.data(),73);alias.process(zero.data(),zero.data(),73);require(zero==r,"rightwins alias");nullEngine.process(nullptr,nullptr,73);nullEngine.process(zero.data(),nullptr,73);full.process(l.data(),r.data(),73);require(zero==l,"null outputs advance");++checks;
        for(std::uint64_t seconds:{0ULL,1ULL,86400ULL,604800ULL})for(int offset=0;offset<16;++offset){
            const auto frame=seconds*static_cast<std::uint64_t>(rate)+offset;
            const auto p=physicalPosition(frame,rate);const auto numerator=static_cast<unsigned long long>(frame)*48000ULL;
            const auto denominator=static_cast<unsigned long long>(rate);
            require(p.floor==numerator/denominator&&p.ceil==(numerator+denominator-1)/denominator,"exact rational long timestamp");++checks;
        }
    }
    for(double rate:{8000.,11025.,16000.,22050.,24000.,32000.,44100.,44117.,48000.,88200.,96000.,176400.,192000.,44100.5,48000.25}) {
        FixedOutputBus e;e.prepare(rate);std::vector<std::uint64_t> boundaries;
        for(double t:{0.,.1,.12345,1.})for(int offset=0;offset<16;++offset)
            boundaries.push_back(static_cast<std::uint64_t>(std::llround(t*rate))+offset);
        std::sort(boundaries.begin(),boundaries.end());
        for(auto frame:boundaries) {
            e.process(nullptr,nullptr,static_cast<std::size_t>(frame-e.hostFrame()));
            const auto mul=rate==44100.5?2ULL:(rate==48000.25?4ULL:1ULL);
            const auto den=static_cast<std::uint64_t>(rate*mul),num=frame*48000ULL*mul;
            const auto expected=(num+den-1)/den;
            const auto before=e.nextPhysicalFrame();
            e.noteOn(60,100);e.noteOff(60);e.sustainPedal(true);e.sustainController(0);
            e.setPatch(e.patch(),true);e.setControls(e.controls());e.setChorusTime(.25);
            e.allNotesOff();e.allSoundOff();
            require(e.nextPhysicalFrame()==(rate==48000?frame:expected),"allmutator actual causal index");
            require(before<=e.nextPhysicalFrame(),"mutator produced backwards");++checks;
        }
    }
    for(double rate:{44100.5,48000.25})for(std::uint64_t seconds:{0ULL,1ULL,86400ULL,604800ULL})for(int offset=0;offset<16;++offset){
        const auto frame=static_cast<std::uint64_t>(seconds*rate)+offset;const auto pos=physicalPosition(frame,rate);
        const auto multiplier=rate==44100.5?2ULL:4ULL;const auto denominator=static_cast<std::uint64_t>(rate*multiplier);
        const auto num=frame*48000ULL*multiplier;
        require(pos.floor==num/denominator&&pos.ceil==(num+denominator-1)/denominator,"fractional rational timestamp");++checks;
    }
    for(double rate:{-1.,0.,7999.,192001.,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()}){FixedOutputBus e;e.prepare(rate);require(e.sampleRate()>=8000&&e.sampleRate()<=192000,"invalid rate");++checks;}
    std::cout<<"{\"passed\":true,\"checks\":"<<checks<<",\"identity_bytes\":"<<identityBytes<<",\"sizeof_engine\":"<<sizeof(press78::Press78Engine)<<",\"sizeof_wrapper\":"<<sizeof(FixedOutputBus)<<",\"render_event_allocations\":0}\n";
}
void component(const std::string&in,const std::string&out,double rate){
    auto x=read(in);const auto frames=static_cast<std::size_t>(std::floor((x.size()/2)*rate/48000.));std::vector<float>y(frames*2);OutputSRC src;src.prepare(rate);
    for(std::size_t i=0;i<frames;++i){auto pos=physicalPosition(i,rate);while(src.nextIndex()<=pos.floor){auto j=src.nextIndex();src.push(x[2*j],x[2*j+1]);}auto v=src.read(pos);y[2*i]=v[0];y[2*i+1]=v[1];}write(out,y);
}
void coefficients(double rate,const std::string&out){
    OutputSRC src;src.prepare(rate);auto fs=static_cast<std::uint64_t>(rate);require(fs==rate,"coefficients integral rate");auto phases=fs/std::gcd(fs,48000ULL);auto taps=2*src.halfDelay()+1;
    std::ofstream f(out,std::ios::binary);std::uint64_t header[]={phases,static_cast<std::uint64_t>(taps),static_cast<std::uint64_t>(src.halfDelay())};f.write(reinterpret_cast<char*>(header),sizeof(header));std::vector<double>c(taps);double minSum=2,maxSum=0,maxL1=0;
    for(std::uint64_t n=0;n<phases;++n){const auto pos=physicalPosition(n,rate);double total=0;for(int j=0;j<taps;++j){c[j]=src.coefficient(j-src.halfDelay()-pos.fraction);total+=c[j];}minSum=std::min(minSum,total);maxSum=std::max(maxSum,total);double l1=0;for(auto&v:c){v/=total;l1+=std::abs(v);}maxL1=std::max(maxL1,l1);f.write(reinterpret_cast<char*>(c.data()),c.size()*8);}require(bool(f),"coeff output");std::cout<<"{\"minimum_sum\":"<<minSum<<",\"maximum_sum\":"<<maxSum<<",\"maximum_l1\":"<<maxL1<<"}\n";
}
void full(double rate,const std::string&out,const std::string&reference){
    const auto y=render<FixedOutputBus>(rate,3,64);write(out,y);
    press78::Press78Engine e;e.prepare(48000.);std::vector<float>x((96000+2400)*2);std::size_t ev=0;
    for(std::size_t frame=0;frame<x.size()/2;++frame){
        while(ev<8){const auto host=static_cast<std::uint64_t>(std::llround(times[ev]*rate));const auto den=static_cast<std::uint64_t>(rate);const auto when=(host*48000ULL+den-1)/den;if(when!=frame)break;event(e,static_cast<int>(ev++),3);}
        e.process(&x[2*frame],&x[2*frame+1],1);
    }write(reference,x);
}
void perf(){
    std::cout<<"[";bool first=true;
    for(double rate:rates)for(int voices:{1,12}){FixedOutputBus e;e.prepare(rate);auto c=controls(3);e.setControls(c);for(int i=0;i<voices;++i)e.noteOn(48+i,127);std::array<float,64>l{},r{};std::vector<double>wall;double total=0;
        const int blocks=static_cast<int>(rate/64);for(int b=0;b<blocks;++b){auto start=std::chrono::steady_clock::now();e.process(l.data(),r.data(),64);auto stop=std::chrono::steady_clock::now();double t=std::chrono::duration<double>(stop-start).count();wall.push_back(t);total+=t;}
        std::sort(wall.begin(),wall.end());if(!first)std::cout<<",";first=false;std::cout<<"{\"rate\":"<<rate<<",\"voices\":"<<voices<<",\"wall_fraction\":"<<total/(blocks*64/rate)<<",\"p99_seconds\":"<<wall[wall.size()*99/100]<<",\"max_seconds\":"<<wall.back()<<"}";
    }std::cout<<"]\n";
}
int main(int argc,char**argv){try{std::cout<<std::setprecision(17);require(argc>1,"mode");std::string mode=argv[1];if(mode=="selftest")selftest();else if(mode=="src"&&argc==5)component(argv[2],argv[3],std::stod(argv[4]));else if(mode=="coeff"&&argc==4)coefficients(std::stod(argv[2]),argv[3]);else if(mode=="full"&&argc==5)full(std::stod(argv[2]),argv[3],argv[4]);else if(mode=="perf")perf();else throw std::runtime_error("arguments");return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
