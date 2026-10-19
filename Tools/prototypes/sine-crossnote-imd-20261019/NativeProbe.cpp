#include "Press78Engine.h"
#include "RecordedChorusProfile.h"
#include <array>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("native_probe dry|circuit|chorus|both output.f32");
 const std::string mode=argv[1];const bool circuit=mode=="circuit"||mode=="both",chorus=mode=="chorus"||mode=="both";
 if(mode!="dry"&&mode!="circuit"&&mode!="chorus"&&mode!="both")throw std::runtime_error("unknown mode");
 auto e=std::make_unique<press78::Press78Engine>();e->prepare(48000);
 auto p=press78::initPatch();p.carrier.ar=63;p.carrier.d1r=0;p.carrier.d1l=0;p.carrier.d2r=0;p.carrier.rks=0;p.carrier.tl=0;p.carrier.rr=8;
 p.modulator.tl=127;p.vibrato=false;p.sustain=false;p.feedback=0;e->setPatch(p);
 press78::Controls c;c.masterGain=.1;c.outputCircuit=circuit;c.chorusMode=1;c.chorusMix=chorus?1:0;c.chorusRateHz=press78::RecordedChorusProfile::rateHz;c.chorusDepthMs=press78::RecordedChorusProfile::depthMs;c.pitchModel=0;c.drive=0;c.toneCutoffHz=0;c.dcBlock=false;c.outputLimit=false;c.noiseRms=0;
 e->setControls(c);e->setChorusTime(8723419.0/48000.0);
 for(int note:{39,75,79,87})e->noteOn(note,127);
 std::ofstream out(argv[2],std::ios::binary);std::array<float,128>l{},r{};
 for(int pos=0;pos<48000;pos+=128){const int n=std::min(128,48000-pos);e->process(l.data(),r.data(),n);for(int i=0;i<n;++i){out.write(reinterpret_cast<char*>(&l[i]),4);out.write(reinterpret_cast<char*>(&r[i]),4);}}
 if(!out)throw std::runtime_error("output write failed");std::cout<<"{\"frames\":48000,\"latency_samples\":"<<e->latencySamples()<<",\"noise\":false,\"nonlinear_stage\":false}\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
