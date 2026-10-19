// Appended to a strictly generated copy of native Press78Engine.cpp by run.py.
// There is no second oscillator, envelope, allocator, resampler or output model.
#include "FactoryVoices.h"
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
struct Event { int frame, kind, value, velocity; };
void add(std::vector<Event>& events, double seconds, int kind, int value, int velocity=0) {
    events.push_back({static_cast<int>(seconds*48000), kind, value, velocity});
}
std::vector<Event> sequence(int fixture) {
    std::vector<Event> e;
    if (fixture==65 || fixture==93 || fixture==97) {
        const int first=fixture==65?40:(fixture==93?48:60);
        add(e,0,0,fixture);
        add(e,.25,1,first,110);add(e,1.75,2,first);
        add(e,7.25,1,first+12,110);add(e,8.75,2,first+12);
    } else if (fixture==100) {
        add(e,.25,0,99);add(e,.25,1,45,96);add(e,1.25,2,45);
        for(int n:{45,52,57})add(e,2.25,1,n,127);
        for(int n:{45,52,57})add(e,3.75,2,n);
        add(e,5,0,79);add(e,5,1,28,127);add(e,5.5,2,28);
        add(e,6,1,31,127);add(e,6.5,2,31);
        for(int n:{28,35,40})add(e,7,1,n,127);
        for(int n:{28,35,40})add(e,8.5,2,n);
        add(e,9.5,0,93);
        for(int n:{48,55,60,64})add(e,9.5,1,n,127);
        for(int n:{48,55,60,64})add(e,11.5,2,n);
    } else require(fixture==101,"Unknown fixture"); // no-note silence witness
    return e;
}
}

namespace press78 {
// Existing research friend only; does not change the production class layout.
struct Press78SustainTestAccess {
    static void contracts() {
        using H=research::AssumedEnvelope;
        Operator op;op.ar=63;op.rr=8;op.srr=2;op.rks=2;
        EnvelopePairParity(op);
        Envelope base;base.configure(op,48,false);base.disabled=false;base.attenuation=17.99;base.stage=3;
        require(!H::engaged(base,true,true),"Knee engages too early");
        base.attenuation=18;
        require(H::engaged(base,true,true),"Knee did not engage");
        require(!H::engaged(base,true,false),"Knee outside Reverb");
        auto held=base;held.stage=2;
        require(!H::engaged(held,false,true),"Knee while still held");
        require(H::engaged(base,false,true),"Entered release stage was not preserved");
        const double raw=base.release;
        auto capped=base;auto expected=base;auto cap=base;auto capOp=op;capOp.rr=capOp.srr=4;
        cap.updateRelease(capOp,48,false);
        expected.release=std::min(expected.release,cap.release);
        const double actual=H::next(capped,op,48,true,true);
        require(actual==expected.next(true)&&capped.attenuation==expected.attenuation,"Native cap parity");
        require(capped.release==raw,"Temporary cap changed stored rate");
        op.rr=2;base=Envelope{};base.configure(op,48,false);base.disabled=false;base.attenuation=18;base.stage=3;
        capped=base;require(H::next(capped,op,48,true,true)==base.next(true),"Slower release accelerated");
        auto& O=research::OutputHypothesis::process;
        require(O(0)==0,"Output adds DC at zero");
        require(std::abs((O(1e-7)-O(-1e-7))/2e-7-1)<1e-10,"Output slope not unity");
        double prev=O(-10);
        for(int i=1;i<=2000;++i) {
            const double y=O(-10+i*.01);
            require(std::isfinite(y)&&y>prev,"Nonmonotonic output transfer");
            require(y<research::OutputHypothesis::positiveLimit()&&y>research::OutputHypothesis::negativeLimit(),"Output outside headroom");
            prev=y;
        }
        std::cout<<"{\"reverb_off_exact\":true,\"knee_gate\":true,\"native_rate_scaling\":true,\"rate_restored\":true,\"slower_rate_preserved\":true,\"output_zero_unity_monotonic_bounded\":true}\n";
    }
private:
    using Envelope=Press78Engine::Envelope;
    static void EnvelopePairParity(const Operator& op) {
        Envelope a,b;a.configure(op,72,true);b=a;
        for(int i=0;i<100000;++i) {
            const bool released=i>=1000;
            const bool knee=research::AssumedEnvelope::engaged(b,released,false);
            require(a.next(released)==research::AssumedEnvelope::next(b,op,72,released,knee),"Reverb OFF differs");
            require(a.attenuation==b.attenuation&&a.stage==b.stage&&a.finished==b.finished&&a.release==b.release,"Reverb OFF state differs");
        }
    }
};
}

int main(int argc,char** argv) {
    try {
        if(argc==2 && std::string(argv[1])=="contracts") {press78::Press78SustainTestAccess::contracts();return 0;}
        require(argc==3,"renderer fixture block | contracts");
        const int fixture=std::stoi(argv[1]),block=std::stoi(argv[2]);
        require(block>0&&block<=4096,"Invalid block");
        press78::Press78Engine engine;engine.prepare(48000);
        press78::Controls c;c.masterGain=.5;c.pitchModel=1;c.sustainMode=1;c.clockOffsetPpm=c.clockDriftPpm=0;
        c.outputCircuit=true;c.toneCutoffHz=0;c.dcBlock=true;c.outputLimit=false;c.drive=0;c.chorusMix=0;
        engine.setControls(c);engine.reset();
        const auto events=sequence(fixture);
        constexpr int frames=14*48000;
        std::array<float,4096> l{},r{};
        std::array<float,8192> interleaved{};
        std::size_t index=0,maxActive=0;int frame=0;double peak=0;
        while(frame<frames) {
            while(index<events.size()&&events[index].frame==frame) {
                const auto e=events[index++];
                if(e.kind==0) {auto p=press78::factoryPatch(static_cast<unsigned>(e.value));p.sustain=false;engine.setPatch(p);}
                else if(e.kind==1)engine.noteOn(e.value,e.velocity);
                else engine.noteOff(e.value);
                maxActive=std::max(maxActive,engine.activeVoices());
            }
            const int next=index<events.size()?events[index].frame:frames;
            const int n=std::min({block,frames-frame,next-frame});
            require(n>0,"Scheduler failed to advance");
            engine.process(l.data(),r.data(),static_cast<std::size_t>(n));
            for(int i=0;i<n;++i) {
                require(std::isfinite(l[i])&&std::isfinite(r[i]),"Nonfinite audio");
                interleaved[2*i]=l[i];interleaved[2*i+1]=r[i];
                peak=std::max({peak,std::abs(static_cast<double>(l[i])),std::abs(static_cast<double>(r[i]))});
            }
            require(std::fwrite(interleaved.data(),sizeof(float)*2,static_cast<std::size_t>(n),stdout)==static_cast<std::size_t>(n),"Short stdout write");
            frame+=n;
        }
        require(index==events.size(),"Not all events consumed");
        std::cerr<<"{\"frames\":"<<frame<<",\"events\":"<<index<<",\"max_active_voices\":"<<maxActive<<",\"peak\":"<<peak<<"}\n";
        return std::ferror(stdout)?2:0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
