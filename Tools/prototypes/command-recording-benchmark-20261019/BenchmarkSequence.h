#pragma once
// Research schedule/parser only. Frozen design fixes the conditional epoch law.
#include <array>
#include <algorithm>
#include <cstdint>
#include <cstddef>
#include <istream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace press78::research::recording {
struct Event {
    std::size_t frame=0;
    std::string kind;
    std::array<std::uint8_t,33> raw{};
    int note=0,velocity=0,channel=-1,program=-1;
};
inline std::array<std::uint8_t,33> parseRaw(const std::string& text) {
    if(text.size()!=66) throw std::runtime_error("Expected33 raw bytes");
    const auto nibble=[](char c) {if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;throw std::runtime_error("Invalid lowercase hex");};
    std::array<std::uint8_t,33> out{};
    for(std::size_t i=0;i<33;++i) out[i]=static_cast<std::uint8_t>(16*nibble(text[2*i])+nibble(text[2*i+1]));
    if(out[0]>4 || out[32]!=0) throw std::runtime_error("Unsupported bank metadata/padding");
    return out;
}
inline std::vector<Event> readEvents(std::istream& input,std::size_t total) {
    std::vector<Event> events;std::string line;int program=-1;
    while(std::getline(input,line)) {
        std::istringstream row(line);Event event;std::string extra;
        if(!(row>>event.frame>>event.kind)) throw std::runtime_error("Malformed event row");
        if(event.kind=="patch") {std::string hex;if(!(row>>hex))throw std::runtime_error("Missing raw patch");event.raw=parseRaw(hex);event.program=++program;}
        else if(event.kind=="on") {if(!(row>>event.note>>event.velocity>>event.channel))throw std::runtime_error("Incomplete on row");}
        else if(event.kind=="off") {if(!(row>>event.note>>event.channel))throw std::runtime_error("Incomplete off row");}
        else throw std::runtime_error("Unknown event kind");
        if(row>>extra) throw std::runtime_error("Trailing event fields");
        if(event.frame>=total || (!events.empty()&&event.frame<events.back().frame))throw std::runtime_error("Frame outside ordered render domain");
        if(event.kind!="patch" && (event.note<36 || event.note>96 || event.channel<0 || event.channel>1 || (event.kind=="on"&&(event.velocity<1 || event.velocity>127))))
            throw std::runtime_error("Unsupported conditional MIDI input");
        events.push_back(event);
    }
    if(!input.eof())throw std::runtime_error("Event read failed");
    return events;
}
// Tick first; entire equal-frame group in supplied order; one key service after
// the complete group, including off-only/patch-only. Never service per chunk.
// The caller owns process(), making pure scheduler tests audio-free.
template<class Sink>
void runSchedule(const std::vector<Event>& events,std::size_t total,std::size_t block,Sink& sink) {
    if(!total || !block || block>4096)throw std::runtime_error("Unsupported frame/block bounds");
    std::size_t frame=0,index=0,nextGrid=240;
    while(frame<total) {
        if(frame==nextGrid) {sink.vibrato(frame);nextGrid+=240;}
        bool group=false;
        while(index<events.size() && events[index].frame==frame) {sink.event(frame,index,events[index]);++index;group=true;}
        if(group)sink.keyService(frame);
        const auto nextEvent=index<events.size()?events[index].frame:total;
        const auto limit=std::min({total,nextEvent,nextGrid});
        if(limit<=frame)throw std::runtime_error("Nonprogressing or unordered schedule");
        const auto count=std::min(block,limit-frame);sink.process(frame,count);frame+=count;
    }
    if(index!=events.size())throw std::runtime_error("Unconsumed source events");
}
} // namespace press78::research::recording
