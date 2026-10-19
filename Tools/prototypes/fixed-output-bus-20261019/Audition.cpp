#include "GuardedOutputBus.h"
#include "FactoryVoices.h"
#include "RecordedChorusProfile.h"
#include <fstream>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

namespace {
void u32(std::ostream& f,std::uint32_t x) { for(int b=0;b<4;++b)f.put(static_cast<char>((x>>(8*b))&255)); }
void u16(std::ostream& f,unsigned x) { f.put(static_cast<char>(x&255));f.put(static_cast<char>((x>>8)&255)); }
void wav(const std::string& path,const std::vector<float>& l,const std::vector<float>& r,int fs) {
    std::ofstream f(path,std::ios::binary);if(!f)throw std::runtime_error("WAV open");
    f.write("RIFF",4);u32(f,36+static_cast<std::uint32_t>(l.size()*8));f.write("WAVEfmt ",8);u32(f,16);
    u16(f,3);u16(f,2);u32(f,fs);u32(f,fs*8);u16(f,8);u16(f,32);f.write("data",4);u32(f,static_cast<std::uint32_t>(l.size()*8));
    for(std::size_t i=0;i<l.size();++i)for(float v:{l[i],r[i]}){std::uint32_t bits;std::memcpy(&bits,&v,4);u32(f,bits);}
    if(!f)throw std::runtime_error("WAV write");
}
struct Event {double time;int note,velocity;};
constexpr Event events[]={{.25,60,100},{1.5,60,0},{2.25,48,95},{2.25,55,100},{2.25,60,105},
    {3.75,48,0},{3.75,55,0},{3.75,60,0},{4.25,67,100},{4.75,67,0}};
template<class Engine> void render(const std::string& path,int fs,int preset) {
    auto engine=std::make_unique<Engine>();engine->prepare(fs);
    auto c=press78::Controls{};c.pitchModel=1;c.sustainMode=1;c.clockDriftPpm=20;
    c.chorusMode=1;c.chorusMix=1;c.chorusRateHz=press78::RecordedChorusProfile::rateHz;
    c.chorusDepthMs=press78::RecordedChorusProfile::depthMs;
    engine->setPatch(press78::decodeVoice(press78::kFactoryVoices.at(static_cast<std::size_t>(preset)).bytes));engine->setControls(c);
    const auto frames=static_cast<std::size_t>(fs)*7;
    std::vector<float> l(frames),r(frames);std::size_t cursor=0,event=0;
    while(cursor<frames){
        while(event<std::size(events)&&cursor==static_cast<std::size_t>(std::llround(events[event].time*fs))){
            const auto& e=events[event++];if(e.velocity)engine->noteOn(e.note,e.velocity);else engine->noteOff(e.note);
        }
        const auto boundary=event<std::size(events)?static_cast<std::size_t>(std::llround(events[event].time*fs)):frames;
        const auto count=std::min<std::size_t>(128,boundary-cursor);
        engine->process(l.data()+cursor,r.data()+cursor,count);cursor+=count;
    }
    wav(path,l,r,fs);double peak=0;for(std::size_t i=0;i<frames;++i)peak=std::max({peak,std::abs(double(l[i])),std::abs(double(r[i]))});
    std::cout<<"{\"rate\":"<<fs<<",\"preset\":"<<preset<<",\"latency_samples\":"<<engine->latencySamples()<<",\"peak\":"<<peak<<"}\n";
}
}
int main(int argc,char** argv){try{
    if(argc!=5)throw std::runtime_error("mode output rate preset");
    const std::string mode=argv[1];const int fs=std::stoi(argv[3]),preset=std::stoi(argv[4]);
    if((fs!=44100&&fs!=48000&&fs!=96000)||(preset!=65&&preset!=93&&preset!=97))throw std::runtime_error("Frozen fixture only");
    if(mode=="old")render<press78::Press78Engine>(argv[2],fs,preset);
    else if(mode=="candidate")render<press78::fixed_bus_research::GuardedOutputBus>(argv[2],fs,preset);
    else throw std::runtime_error("Bad mode");return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
