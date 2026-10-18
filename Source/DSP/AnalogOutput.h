#pragma once
#include <array>
#include <cmath>

namespace press78 {
// Generated from the frozen Python MNA: PSS480 buffer/preamp, volume-pot top.
// Related-hardware surrogate, not a recovered PSS780 analog board or DAC.
// Six stable SOS implement trapezoidal integration of the linear circuit.
class AnalogOutput {
public:
    void prepare(double sampleRate) noexcept {
        const double ratio=sampleRate/48000.0;
        for(unsigned n=0;n<6;++n) {
            const auto& s=reference_[n];
            std::array<double,6> t{};
            if(sampleRate==48000.0)t=s;
            else for(unsigned j=0;j<2;++j) {
                const unsigned k=j*3;
                const double p=s[k]+s[k+1]+s[k+2];
                const double q=2.0*(s[k]-s[k+2])*ratio;
                const double r=(s[k]-s[k+1]+s[k+2])*ratio*ratio;
                t[k]=p+q+r;t[k+1]=2.0*(p-r);t[k+2]=p-q+r;
            }
            for(unsigned j=0;j<6;++j)sections_[n][j]=t[j]/t[3];
        }
        reset();
    }
    void reset() noexcept {for(auto& pair:state_)pair={0.0,0.0};}
    double process(double input) noexcept {
        for(unsigned n=0;n<6;++n) {
            const auto& s=sections_[n];auto& z=state_[n];
            const double output=s[0]*input+z[0];
            z[0]=s[1]*input-s[4]*output+z[1];
            z[1]=s[2]*input-s[5]*output;
            input=output;
        }
        return input;
    }
private:
    inline static constexpr std::array<std::array<double,6>,6> reference_{{
        {{-0.15630321445278808,-0.31260760361041695,-0.15630438916646072,1,-0.021595474976414133,0.00011659113454449005}},
        {{1,2,1,1,0.63244408460683266,-0.353671851682403}},
        {{1,1.9901466706493385,0.99014674464605468,1,1.9803083725103126,0.98040531255861096}},
        {{1,-1.9958376186008548,0.99584194995558706,1,-1.9958363777513919,0.99584071168939581}},
        {{1,-1.0087161022968898,0.010774701674926697,1,-1.9958390522814606,0.99584338065338618}},
        {{1,-2.0000000000002078,1.0000000000002078,1,-0.0092480660558986738,-0.98898866376056971}}
    }};
    std::array<std::array<double,6>,6> sections_{};
    std::array<std::array<double,2>,6> state_{};
};
} // namespace press78
