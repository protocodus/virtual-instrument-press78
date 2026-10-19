#include "GuardedOutputBus.h"
#include <cassert>
#include <cstring>
#include <iostream>
int main(){using press78::fixed_bus_research::GuardedOutputBus;int cases=0;
for(bool enabled:{false,true}){
for(float bad:{std::numeric_limits<float>::infinity(),-std::numeric_limits<float>::infinity(),std::numeric_limits<float>::quiet_NaN()}){assert(GuardedOutputBus::protectedSample(bad,enabled)==0);++cases;}
for(float value:{-0.f,0.f,-1.f,1.f,std::nextafter(1.f,0.f),std::nextafter(-1.f,0.f)}){float result=GuardedOutputBus::protectedSample(value,enabled);assert(std::memcmp(&value,&result,4)==0);++cases;}}
std::cout<<"{\"passed\":true,\"cases\":"<<cases<<",\"scope\":\"NaN,bothinfinities,signedzero,finitebounds; pureprotector\"}\n";}
