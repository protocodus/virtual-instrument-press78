#pragma once
#include "FixedOutputBus.h"
namespace press78::fixed_bus_research {
// Software output protection only. This is not Yamaha/DAC distortion.
class GuardedOutputBus : public FixedOutputBus {
public:
    void prepare(double rate) noexcept { FixedOutputBus::prepare(rate);clearCounts(); }
    void reset() noexcept { FixedOutputBus::reset();clearCounts(); }
    static float protectedSample(float value,bool enabled) noexcept {
        if(!std::isfinite(value))return 0;
        return enabled?std::max(-1.f,std::min(1.f,value)):value;
    }
    void process(float* left,float* right,std::size_t frames) noexcept {
        if(sampleRate()==48000.) { FixedOutputBus::process(left,right,frames);return; }
        for(std::size_t i=0;i<frames;++i) {
            float l,r;FixedOutputBus::process(&l,&r,1);
            l=protect(l);r=protect(r);
            if(left)left[i]=l;if(right)right[i]=r;
        }
    }
    std::uint64_t clippedChannels() const noexcept{return clipped_;}
    std::uint64_t nonfiniteFaults() const noexcept{return nonfinite_;}
    double maximumClipDelta() const noexcept{return delta_;}
private:
    std::uint64_t clipped_=0,nonfinite_=0;
    double delta_=0;
    void clearCounts() noexcept{clipped_=nonfinite_=0;delta_=0;}
    float protect(float value) noexcept {
        if(!std::isfinite(value)){++nonfinite_;return 0;}
        const auto result=protectedSample(value,controls().outputLimit);
        if(result!=value){++clipped_;delta_=std::max(delta_,std::abs(static_cast<double>(value)-result));}
        return result;
    }
};
static_assert(sizeof(GuardedOutputBus)<=196608,"Guarded prototype exceeds192KiB");
}
