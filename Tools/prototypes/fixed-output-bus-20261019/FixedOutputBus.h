// Isolated engineering prototype. Not a hardware sample-rate assertion.
#pragma once
#include "Press78Engine.h"
#include "KernelTable.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>

namespace press78::fixed_bus_research {
struct GridPosition {
    std::uint64_t floor = 0, ceil = 0;
    double fraction = 0;
};
inline double validRate(double fs) noexcept {
    return std::isfinite(fs) ? std::max(8000.,std::min(192000.,fs)) : 48000.;
}
inline GridPosition physicalPosition(std::uint64_t frame, double fs) noexcept {
    fs=validRate(fs);
    if(fs==std::floor(fs)) {
        const auto rate=static_cast<std::uint64_t>(fs);
        const auto seconds=frame/rate, remainder=frame%rate;
        // Decompose before multiply. Saturation only beyond >12million years.
        if(seconds>(std::numeric_limits<std::uint64_t>::max()-48000)/48000)
            return {std::numeric_limits<std::uint64_t>::max()-1,std::numeric_limits<std::uint64_t>::max()-1,0};
        const auto product=remainder*48000, quotient=product/rate, rem=product%rate;
        const auto lower=seconds*48000+quotient;
        return {lower,lower+(rem!=0),static_cast<double>(rem)/static_cast<double>(rate)};
    }
    static_assert(sizeof(double)==8 && std::numeric_limits<double>::is_iec559
                  && std::numeric_limits<double>::digits==53,"Requires IEEE754 binary64");
    std::uint64_t bits=0;std::memcpy(&bits,&fs,8);
    const auto denominator=(bits&((1ULL<<52)-1))|(1ULL<<52);
    const auto exponent=static_cast<unsigned>((bits>>52)&2047);
    const auto shift=1075U-exponent; // 35..40 for supported positive rates.
    const auto lowProduct=(frame&0xffffffffULL)*48000ULL;
    const auto highProduct=(frame>>32)*48000ULL;
    const auto productLow=lowProduct+(highProduct<<32);
    const auto productHigh=(highProduct>>32)+(productLow<lowProduct);
    const auto high=(productHigh<<shift)|(productLow>>(64-shift));
    const auto low=productLow<<shift;
    std::uint64_t remainder=0,quotient=0;bool overflow=false;
    for(int bit=127;bit>=0;--bit) {
        const auto digit=bit>=64?((high>>(bit-64))&1ULL):((low>>bit)&1ULL);
        remainder=(remainder<<1)|digit; // <54bits, fits uint64.
        if(remainder>=denominator) {
            remainder-=denominator;
            if(bit>=64)overflow=true;else quotient|=1ULL<<bit;
        }
    }
    if(overflow || quotient>=std::numeric_limits<std::uint64_t>::max()-1)
        return {std::numeric_limits<std::uint64_t>::max()-1,std::numeric_limits<std::uint64_t>::max()-1,0};
    return {quotient,quotient+(remainder!=0),static_cast<double>(remainder)/static_cast<double>(denominator)};
}

class OutputSRC {
public:
    static constexpr std::size_t kHistory=2048;
    void prepare(double fs) noexcept {
        rate_=validRate(fs); ratio_=std::min(1.,rate_/48000.);
        half_=static_cast<int>(std::ceil(96./ratio_)); reset();
    }
    void reset() noexcept { clearHistory(); next_=0; }
    void clearHistory() noexcept { history_.fill({{0,0}}); }
    void push(float left,float right) noexcept {
        history_[next_%kHistory]={{left,right}}; ++next_;
    }
    std::uint64_t nextIndex() const noexcept { return next_; }
    int halfDelay() const noexcept { return half_; }
    double ratio() const noexcept { return ratio_; }
    double coefficient(double distance) const noexcept {
        const double u=std::abs(ratio_*distance)*1024.;
        if(u>98304.)return 0.;
        const auto i=static_cast<std::size_t>(u);
        if(i>=98304)return ratio_*static_cast<double>(kKernel[98304]);
        const double fraction=u-static_cast<double>(i);
        return ratio_*(static_cast<double>(kKernel[i])+(static_cast<double>(kKernel[i+1])-kKernel[i])*fraction);
    }
    std::array<float,2> read(GridPosition pos) const noexcept {
        // pos - halfDelay is center; highest required index never exceeds floor(pos).
        double left=0,right=0,total=0;
        for(int relative=-half_;relative<=half_;++relative) {
            const double c=coefficient(static_cast<double>(relative)-pos.fraction);
            total+=c;
            const auto behind=static_cast<std::uint64_t>(half_-relative);
            if(pos.floor<behind)continue;
            const auto index=pos.floor-behind;
            if(index>=next_ || next_-index>kHistory)continue;
            const auto& value=history_[index%kHistory];
            left+=c*value[0];right+=c*value[1];
        }
        return {{static_cast<float>(left/total),static_cast<float>(right/total)}};
    }
private:
    std::array<std::array<float,2>,kHistory> history_{};
    std::uint64_t next_=0;
    double rate_=48000.,ratio_=1.;
    int half_=96;
};

class FixedOutputBus {
public:
    FixedOutputBus() noexcept { prepare(48000.); }
    void prepare(double fs) noexcept {
        rate_=validRate(fs); direct_=rate_==48000.; engine_.prepare(48000.);
        src_.prepare(rate_); frame_=0;
    }
    void reset() noexcept { engine_.reset();src_.reset();frame_=0; }
    void setPatch(const Patch& p,bool live=false) noexcept { flushPast();engine_.setPatch(p,live); }
    void setControls(const Controls& c) noexcept { flushPast();engine_.setControls(c); }
    void setChorusTime(double time) noexcept { flushPast();engine_.setChorusTime(time); }
    void noteOn(int note,int velocity,int source=0) noexcept { flushPast();engine_.noteOn(note,velocity,source); }
    void noteOff(int note,int source=0) noexcept { flushPast();engine_.noteOff(note,source); }
    void sustainPedal(bool value) noexcept { flushPast();engine_.sustainPedal(value); }
    void sustainController(int value) noexcept { flushPast();engine_.sustainController(value); }
    void allNotesOff() noexcept { flushPast();engine_.allNotesOff(); }
    void allSoundOff() noexcept { flushPast();engine_.allSoundOff();src_.clearHistory(); }
    void process(float* left,float* right,std::size_t count) noexcept {
        if(direct_) { engine_.process(left,right,count);frame_+=count;return; }
        for(std::size_t i=0;i<count;++i) {
            const auto pos=physicalPosition(frame_,rate_);
            while(src_.nextIndex()<=pos.floor)produce();
            const auto y=src_.read(pos);
            if(left)left[i]=y[0];if(right)right[i]=y[1];
            ++frame_;
        }
    }
    std::size_t activeVoices() const noexcept { return engine_.activeVoices(); }
    double sampleRate() const noexcept { return rate_; }
    double nominalLatencySeconds() const noexcept { return (32.+(direct_?0:src_.halfDelay()))/48000.; }
    int latencySamples() const noexcept {
        if(direct_)return engine_.latencySamples();
        // Exact ceil(nominalTicks*hostRate/48000), including binary64 rates.
        // Intermediate bounds: numerator<2^63, denominator<2^56.
        std::uint64_t bits=0;std::memcpy(&bits,&rate_,8);
        const auto significand=(bits&((1ULL<<52)-1))|(1ULL<<52);
        const auto shift=1075U-static_cast<unsigned>((bits>>52)&2047);
        const auto numerator=significand*static_cast<std::uint64_t>(32+src_.halfDelay());
        const auto denominator=48000ULL<<shift;
        return static_cast<int>(numerator/denominator+(numerator%denominator!=0));
    }
    const Patch& patch() const noexcept { return engine_.patch(); }
    const Controls& controls() const noexcept { return engine_.controls(); }
    int effectivePitchModel() const noexcept { return engine_.effectivePitchModel(); }
    int effectiveSustainMode() const noexcept { return engine_.effectiveSustainMode(); }
    // Research diagnostics: real generated index, not the intended timestamp.
    std::uint64_t nextPhysicalFrame() const noexcept { return direct_?frame_:src_.nextIndex(); }
    std::uint64_t hostFrame() const noexcept { return frame_; }
private:
    Press78Engine engine_{};
    OutputSRC src_{};
    double rate_=48000.;
    std::uint64_t frame_=0;
    bool direct_=true;
    void produce() noexcept { float left,right;engine_.process(&left,&right,1);src_.push(left,right); }
    void flushPast() noexcept {
        if(direct_)return;
        const auto pos=physicalPosition(frame_,rate_);
        while(src_.nextIndex()<pos.ceil)produce();
    }
};
static_assert(sizeof(FixedOutputBus)<=196608,"Research prototype exceeds192KiB instance budget");
}
