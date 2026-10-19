// Independent diagnostic after the frozen estimator failed; no source audio.
#include "Press78Engine.h"
#include "RecordedChorusProfile.h"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <memory>
#include <string>
#include <vector>
std::vector<double> render(const std::string&mode,const std::vector<int>&notes){
 auto e=std::make_unique<press78::Press78Engine>();e->prepare(48000);auto p=press78::initPatch();p.carrier.ar=63;p.carrier.d1r=0;p.carrier.d1l=0;p.carrier.d2r=0;p.carrier.rks=0;p.carrier.tl=0;p.carrier.rr=8;p.modulator.tl=127;p.feedback=0;p.vibrato=false;p.sustain=false;e->setPatch(p);
 press78::Controls c;c.masterGain=.1;c.outputCircuit=mode=="circuit"||mode=="both";c.chorusMode=1;c.chorusMix=mode=="chorus"||mode=="both"?1:0;c.chorusRateHz=press78::RecordedChorusProfile::rateHz;c.chorusDepthMs=press78::RecordedChorusProfile::depthMs;c.pitchModel=0;c.toneCutoffHz=0;c.drive=0;c.dcBlock=false;c.outputLimit=false;c.noiseRms=0;e->setControls(c);e->setChorusTime(8723419.0/48000.0);for(int n:notes)e->noteOn(n,127);
 std::vector<float>l(48000),r(48000);for(int p=0;p<48000;p+=128){auto count=std::min(128,48000-p);e->process(l.data()+p,r.data()+p,count);}std::vector<double>x(96000);for(int i=0;i<48000;++i){x[2*i]=l[i];x[2*i+1]=r[i];}return x;
}
int main(){std::cout<<"{\"controls\":[";bool comma=false;for(auto mode:{"dry","circuit","chorus","both"}){
 auto mixed=render(mode,{39,75,79,87});std::vector<double>sum(mixed.size());for(int n:{39,75,79,87}){auto x=render(mode,{n});for(std::size_t i=0;i<x.size();++i)sum[i]+=x[i];}double error=0,energy=0,maxerror=0;for(std::size_t i=0;i<sum.size();++i){double d=mixed[i]-sum[i];error+=d*d;energy+=mixed[i]*mixed[i];maxerror=std::max(maxerror,std::abs(d));}if(comma)std::cout<<',';comma=true;std::cout<<"{\"mode\":\""<<mode<<"\",\"relative_rms_error\":"<<std::sqrt(error/energy)<<",\"max_absolute_error\":"<<maxerror<<",\"passed_1e_minus6\":"<<(std::sqrt(error/energy)<1e-6?"true":"false")<<'}';}std::cout<<"],\"source_pcm_read\":false}\n";}
