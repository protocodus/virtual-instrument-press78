// Offline benchmark fixture. Not compiled into the Rack Extension.
#include "Press78Engine.h"
#if __has_include("RecordedChorus.h")
#include "RecordedChorus.h"
#define PRESS78_HAS_RECORDED_CHORUS 1
#endif
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
struct Event { std::size_t frame; std::string kind, raw; int note=0, velocity=0, source=0; };
void u16(std::ostream& f, std::uint16_t v) { for(int i=0;i<2;++i) f.put(static_cast<char>((v>>(8*i))&255)); }
void u32(std::ostream& f, std::uint32_t v) { for(int i=0;i<4;++i) f.put(static_cast<char>((v>>(8*i))&255)); }
void sample(std::ostream& f, float v) { std::uint32_t b;std::memcpy(&b,&v,4);u32(f,b); }
std::array<std::uint8_t,33> raw(const std::string& text) {
    if(text.size()!=66) throw std::runtime_error("Patch must contain 33 hex bytes");
    const auto nibble=[](char c) { if(c>='0'&&c<='9')return c-'0'; if(c>='a'&&c<='f')return c-'a'+10; throw std::runtime_error("Invalid hex"); };
    std::array<std::uint8_t,33> b{};
    for(std::size_t i=0;i<b.size();++i)b[i]=static_cast<std::uint8_t>((nibble(text[2*i])<<4)|nibble(text[2*i+1]));
    return b;
}
}

int main(int argc,char** argv) {
    try {
        if(argc!=6)throw std::runtime_error("Usage: hardware_sequence events.txt output.wav frames rate raw|dry|legacy|recorded");
        const auto frames=static_cast<std::size_t>(std::stoull(argv[3]));
        const int rate=std::stoi(argv[4]);const std::string mode=argv[5];
        if(rate!=48000 || frames>48000*600 || frames==0)throw std::runtime_error("Benchmark fixture requires 48k and at most 600seconds");
        press78::Controls c;c.masterGain=1.;c.toneCutoffHz=0.;c.dcBlock=false;c.outputLimit=false;c.outputCircuit=mode!="raw";
        if(mode=="legacy")c.chorusMix=1.;
#ifdef PRESS78_HAS_RECORDED_CHORUS
        else if(mode=="recorded") {
            c.chorusMode=1;c.chorusMix=1.;
            c.chorusRateHz=press78::RecordedChorusProfile::rateHz;
            c.chorusDepthMs=press78::RecordedChorusProfile::depthMs;
        }
#endif
        else if(mode!="raw"&&mode!="dry")throw std::runtime_error("Unknown output mode");
        std::ifstream input(argv[1]);if(!input)throw std::runtime_error("Cannot open events");
        std::vector<Event> events;
        Event e;
        while(input>>e.frame>>e.kind) {
            if(e.kind=="patch")input>>e.raw;
            else if(e.kind=="on")input>>e.note>>e.velocity>>e.source;
            else if(e.kind=="off")input>>e.note>>e.source;
            else throw std::runtime_error("Unknown event type");
            if(!input || e.frame>frames || (!events.empty()&&e.frame<events.back().frame))throw std::runtime_error("Invalid event ordering");
            events.push_back(e);
        }
        if(!input.eof())throw std::runtime_error("Invalid event file");
        auto engine=std::make_unique<press78::Press78Engine>();engine->prepare(rate);engine->setControls(c);
        double chorusEpoch=0.;
#ifdef PRESS78_HAS_RECORDED_CHORUS
        if(mode=="recorded") {
            // Removing the fixed FM delay must not advance capture LFO phase.
            // This epoch comes from declared latency, never from audio fitting.
            chorusEpoch=-static_cast<double>(engine->latencySamples())/rate;
            engine->setChorusTime(chorusEpoch);
        }
#endif
        std::ofstream out(argv[2],std::ios::binary);if(!out)throw std::runtime_error("Cannot open output");
        const auto bytes=static_cast<std::uint32_t>(frames*8);
        out.write("RIFF",4);u32(out,36+bytes);out.write("WAVEfmt ",8);u32(out,16);u16(out,3);u16(out,2);u32(out,rate);u32(out,rate*8);u16(out,8);u16(out,32);out.write("data",4);u32(out,bytes);
        std::array<float,128> left{},right{};std::size_t cursor=0,idx=0;double peak=0;
        while(cursor<frames) {
            while(idx<events.size()&&events[idx].frame==cursor) {
                const auto& x=events[idx++];
                if(x.kind=="patch")engine->setPatch(press78::decodeVoice(raw(x.raw)),false);
                else if(x.kind=="on")engine->noteOn(x.note,x.velocity,x.source);
                else engine->noteOff(x.note,x.source);
            }
            const auto next=idx<events.size()?events[idx].frame:frames;
            const auto count=std::min<std::size_t>(128,std::min(next,frames)-cursor);
            engine->process(left.data(),right.data(),count);
            for(std::size_t i=0;i<count;++i) {
                if(!std::isfinite(left[i])||!std::isfinite(right[i]))throw std::runtime_error("Nonfinite output");
                sample(out,left[i]);sample(out,right[i]);peak=std::max(peak,std::max(std::abs(static_cast<double>(left[i])),std::abs(static_cast<double>(right[i]))));
            }
            cursor+=count;
        }
        if(!out)throw std::runtime_error("Cannot write output");
        std::cout<<"{\"frames\":"<<frames<<",\"sample_rate\":"<<rate<<",\"latency_samples\":"<<engine->latencySamples()<<",\"mode\":\""<<mode<<"\",\"peak\":"<<peak<<",\"events\":"<<events.size()<<",\"chorus_epoch_seconds\":"<<chorusEpoch<<",\"chorus_rate_hz\":"<<c.chorusRateHz<<",\"chorus_depth_ms\":"<<c.chorusDepthMs<<"}\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
