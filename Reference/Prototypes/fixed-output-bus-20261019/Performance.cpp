#include "GuardedOutputBus.h"
#include "RecordedChorusProfile.h"
#include <chrono>
#include <iostream>
#include <iomanip>
#include <vector>
using namespace press78;using namespace press78::fixed_bus_research;
int main(){std::cout<<std::setprecision(17)<<"{\"sizeof_guarded\":"<<sizeof(GuardedOutputBus)<<",\"rows\":[";bool first=true;double worst=0;
for(double rate:{8000.,11025.,16000.,22050.,24000.,32000.,44100.,44117.,48000.,88200.,96000.,176400.,192000.,44100.5,48000.25})for(int voices:{1,12}){GuardedOutputBus e;e.prepare(rate);Controls c;c.pitchModel=1;c.sustainMode=1;c.clockDriftPpm=20;c.chorusMode=1;c.chorusMix=1;c.chorusRateHz=RecordedChorusProfile::rateHz;c.chorusDepthMs=RecordedChorusProfile::depthMs;e.setControls(c);auto p=initPatch();p.carrier.tl=6;p.modulator.tl=24;p.feedback=5;e.setPatch(p);for(int i=0;i<voices;++i)e.noteOn(48+i,127);
std::array<float,64>l{},r{};std::vector<double>wall;auto blocks=static_cast<int>(rate/64);wall.reserve(blocks);double total=0;
for(int i=0;i<blocks;++i){auto a=std::chrono::steady_clock::now();e.process(l.data(),r.data(),64);auto b=std::chrono::steady_clock::now();double t=std::chrono::duration<double>(b-a).count();total+=t;wall.push_back(t);}std::sort(wall.begin(),wall.end());double fraction=total/(blocks*64/rate);worst=std::max(worst,fraction);
if(!first)std::cout<<",";first=false;std::cout<<"{\"rate\":"<<rate<<",\"voices\":"<<voices<<",\"wall_fraction\":"<<fraction<<",\"p99_seconds\":"<<wall[wall.size()*99/100]<<",\"max_seconds\":"<<wall.back()<<",\"block_seconds\":"<<64/rate<<",\"nominal_latency_seconds\":"<<e.nominalLatencySeconds()<<",\"declared_latency_frames\":"<<e.latencySamples()<<"}";
}std::cout<<"],\"worst_mean_wall_fraction\":"<<worst<<",\"research_sanity_gate_passed\":"<<(worst<.5?"true":"false")<<",\"scope\":\"SinglelocalO2run; nohardrealtime/nativeReasonclaim\"}\n";}
