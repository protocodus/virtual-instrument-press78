#pragma once
// Research only. Include unchanged Source/DSP/Press78Engine.cpp once in the
// executable that uses this header. design-frozen.json defines the boundaries.
#include "../../../Source/DSP/Press78Engine.h"
#include "../mode00-complete-command-20261019/Mode00CompleteCommands.h"
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace press78 {
// Deliberate use of an existing private research seam; no shipping source edit.
struct Press78SustainTestAccess {
    struct Dynamics {
        double modPhase, carrierPhase, prev1, prev2, modAttenuation, carrierAttenuation;
        double modRelease, carrierRelease, modStep, carrierStep, modGain, carrierGain;
        std::uint64_t ticks;
        int note, modStage, carrierStage;
        bool active, held, released, modFinished, carrierFinished;
    };
    static Dynamics dynamics(const Press78Engine& e, std::size_t s) noexcept {
        const auto& v = e.voices_[s];
        return {v.modPhase,v.carrierPhase,v.prev1,v.prev2,v.modEnvelope.attenuation,
            v.carrierEnvelope.attenuation,v.modEnvelope.release,v.carrierEnvelope.release,
            v.modStep,v.carrierStep,v.modGain,v.carrierGain,v.ticks,v.note,
            v.modEnvelope.stage,v.carrierEnvelope.stage,v.active,v.held,v.released,
            v.modEnvelope.finished,v.carrierEnvelope.finished};
    }
    static const Patch& slotPatch(const Press78Engine& e, std::size_t s) noexcept { return e.voices_[s].patch; }
    static bool tailsEmpty(const Press78Engine& e) noexcept {
        for (const auto& t : e.tails_) if (t.remaining) return false;
        return true;
    }
    static void key(Press78Engine& e, std::size_t s, bool on, const Patch& p,
                    int originalMappedNote, double frequency) noexcept {
        auto& v = e.voices_[s];
        if (on) {
            // Existing reset/configure is an inherited hypothesis, not a chip fact.
            v.configure(p, originalMappedNote, 127, ++e.serial_);
            applySteps(v, frequency);
        } else { v.held = false; v.released = true; }
    }
    static void coefficients(Press78Engine& e, std::size_t s, const Patch& p,
                             double frequency) noexcept {
        auto& v = e.voices_[s];
        if (!v.active) return;
        // updatePatch updates coefficients, retaining envelope/phase/history.
        v.updatePatch(p);
        applySteps(v, frequency);
    }
private:
    static void applySteps(Press78Engine::Voice& v, double frequency) noexcept {
        // Same operation order as shipping originalStep; only base frequency is
        // obtained from actual three-word registers rather than a second lookup.
        constexpr double twoPi = 6.28318530717958647692528676655900576;
        const auto opStep = [frequency](const Operator& op) noexcept {
            const double ratio = op.mul == 0 ? .5 : static_cast<double>(op.mul);
            const double cents = (op.dt2 ? 600.0 : 0.0) + op.dt1 * 1.5;
            return twoPi * frequency * ratio * std::pow(2.0, cents / 1200.0)
                / Press78Engine::kInternalRate;
        };
        v.modStep = opStep(v.patch.modulator); v.carrierStep = opStep(v.patch.carrier);
    }
};
} // namespace press78

namespace press78::research {
class CommandAudioConsumer {
public:
    using Commands = Mode00CompleteCommands;
    using Plan = Commands::Plan;
    using Write = Commands::RegisterWrite;
    using Notes = std::array<int,12>;
    enum class ReverbPolicy { Unspecified, StoreReverbBitWithoutAudioEffect };
    enum class Status { Ok, NotReady, InvalidInitialization, RejectedFrontend,
                        UnsupportedPlan, MissingRegisters, UnsupportedMetadata };
    struct Slot {
        std::array<std::uint8_t,6> mod{}, car{};
        std::uint8_t feedback = 0, pmsAms = 0, pitchHigh = 0, pitchLow = 0, pitchBlock = 0;
        std::uint32_t valid = 0;
        bool keyed = false;
    };
    struct Image { std::array<Slot,12> slots{}; };
    static constexpr std::uint32_t kComplete = (1u << 17) - 1;

    // A silent empty logical snapshot, explicitly NOT the original CPU boot.
    Status initialize(Commands::Target target, const Commands::Snapshot& snapshot,
                      const Controls& controls, double sampleRate, ReverbPolicy policy) noexcept {
        if (ready_ || policy != ReverbPolicy::StoreReverbBitWithoutAudioEffect
            || !controlsSupported(controls) || !std::isfinite(sampleRate)
            || sampleRate < 8000 || sampleRate > 192000 || !empty(snapshot.front.allocator))
            return Status::InvalidInitialization;
        Commands prospective;
        if (prospective.restore(target,snapshot) != Commands::Status::Ok)
            return Status::InvalidInitialization;
        for (const auto delay : snapshot.vibratoDelay) if (delay) return Status::InvalidInitialization;
        frontend_ = prospective;
        engine_.setControls(controls);
        engine_.prepare(sampleRate);
        policy_ = policy; ready_ = true;
        return Status::Ok;
    }
    Status noteOn(int note, int velocity = 127) noexcept { return event([=](Commands& c) { return c.noteOn(note,velocity); }); }
    Status noteOff(int note) noexcept { return event([=](Commands& c) { return c.noteOff(note); }); }
    Status serviceKeyOn() noexcept { return event([](Commands& c) { return c.serviceKeyOn(); }); }
    Status serviceVibrato() noexcept { return event([](Commands& c) { return c.serviceVibrato(); }); }
    Status sustainController(int value) noexcept { return event([=](Commands& c) { return c.sustainController(value); }); }
    Status selectProgram(const Commands::WorkingPatch& patch, std::uint8_t program) noexcept {
        return event([&](Commands& c) { return c.selectProgram(patch,program); });
    }
    // Explicit research boundary for ordered raw plans, including malformed-plan
    // tests. This changes no allocator. Notes are original mapped cache notes,
    // used solely by inherited native RKS; the chip's keycode remains unknown.
    Status applyRaw(const Plan& plan, const Notes& notes) noexcept {
        if (!ready_) return Status::NotReady;
        Image staged = image_;
        const auto status = preflight(staged,plan,notes);
        if (status != Status::Ok) return status;
        for (std::size_t i=0;i<plan.count;++i) apply(image_,plan.writes[i],notes,true);
        last_ = plan; ++epochs_;
        return Status::Ok;
    }
    void process(float* left,float* right,std::size_t frames) noexcept {
        if (ready_) engine_.process(left,right,frames);
    }
    bool ready() const noexcept { return ready_; }
    const Commands& frontend() const noexcept { return frontend_; }
    const Image& image() const noexcept { return image_; }
    const Plan& lastPlan() const noexcept { return last_; }
    const Press78Engine& engine() const noexcept { return engine_; }
    std::uint64_t epochs() const noexcept { return epochs_; }
    bool reverbAudioUnsupported() const noexcept {
        for (const auto& s : image_.slots)
            if (((s.valid & 2) && (s.mod[1] & 128)) || ((s.valid & (1u<<7)) && (s.car[1] & 128))) return true;
        return false;
    }
    static int fnum(const Slot& s) noexcept { return (s.pitchLow & 63) | ((s.pitchHigh & 31)<<6) | ((s.pitchBlock & 96)<<6); }
    static int block(const Slot& s) noexcept { return (s.pitchBlock>>2)&7; }
    static double frequency(const Slot& s) noexcept {
        // This is exactly the existing empirical downstream grid hypothesis,
        // not a measured OPU clock or a recovered phase-increment algorithm.
        return std::floor(std::ldexp(static_cast<double>(fnum(s)),block(s)-3))
            * (5500000.0/(6.0*16777216.0));
    }
    static Patch patch(const Slot& s) noexcept {
        Patch p;
        const auto decode=[](const std::array<std::uint8_t,6>& b) noexcept {
            Operator op;
            const int dt=b[0]>>4;
            op.mul=b[0]&15; op.dt1=(dt&8)?-(dt&7):dt&7;
            op.tl=b[1]&127; op.lksHi=op.lksLo=0;
            op.ar=b[2]&63; op.rks=b[2]>>6;
            op.d1r=b[3]&63; op.dt2=(b[3]&64)!=0; op.amEnable=(b[3]&128)!=0;
            op.d2r=b[4]&63; op.wave=b[4]>>6;
            op.d1l=b[5]>>4; op.rr=b[5]&15; op.srr=op.rr;
            return op;
        };
        p.modulator=decode(s.mod); p.carrier=decode(s.car);
        p.feedback=(s.feedback>>3)&7; p.pms=(s.pmsAms>>4)&7; p.ams=s.pmsAms&3;
        p.vibrato=true; p.vibratoDelay=0; p.sustain=false;
        return p;
    }
private:
    Commands frontend_{}; // Sole committed allocator/effect/cache owner.
    Press78Engine engine_{};
    Image image_{};
    Plan last_{};
    std::uint64_t epochs_=0;
    ReverbPolicy policy_=ReverbPolicy::Unspecified;
    bool ready_=false;
    static bool empty(const Mode00Allocator& a) noexcept {
        if (a.pool!=12 || a.held[0].any() || a.held[1].any()) return false;
        for (int s=0;s<12;++s) if (a.notes[s] || a.sources[s] || a.ranks[s] || a.pending[s] || a.keyed[s] || !a.valid[s]) return false;
        return true;
    }
    static bool controlsSupported(const Controls& c) noexcept {
        const auto range=[](double x,double low,double high) noexcept { return std::isfinite(x) && x>=low && x<=high; };
        return c.polyphony==12 && c.pitchModel==0 && c.sustainMode==0 && c.midiPitchBend==-1
            && c.pitchBendSemitones==0 && c.masterTuneCents==0 && c.hostTuneCents==0
            && c.clockOffsetPpm==0 && c.clockDriftPpm==0 && c.noiseModel==0 && c.noiseRms==0
            && range(c.masterGain,0,2) && range(c.velocitySensitivity,0,2)
            && range(c.velocityToModulation,0,2) && range(c.modulationAmount,0,2)
            && range(c.lfoRateHz,0,30) && range(c.vibratoDepth,0,4) && range(c.tremoloDepth,0,4)
            && range(c.lfoDelayScale,0,4) && range(c.clockDriftRateHz,.001,2)
            && (c.toneCutoffHz==0 || range(c.toneCutoffHz,20,86400)) && range(c.drive,0,1)
            && (c.chorusMode==0 || c.chorusMode==1) && range(c.chorusMix,0,1)
            && range(c.chorusRateHz,.05,8) && range(c.chorusDepthMs,0,8) && range(c.stereoWidth,0,2);
    }
    template<class F> Status event(F operation) noexcept {
        if (!ready_) return Status::NotReady;
        auto prospective=frontend_;
        const auto plan=operation(prospective);
        if (plan.status!=Commands::Status::Ok) return Status::RejectedFrontend;
        const auto status=applyRaw(plan,prospective.state().allocator.notes);
        if (status==Status::Ok) frontend_=prospective;
        return status;
    }
    Status preflight(Image& staged,const Plan& p,const Notes& notes) noexcept {
        if (p.status!=Commands::Status::Ok || p.count>p.writes.size()) return Status::UnsupportedPlan;
        for (const auto n:notes) if (n!=0 && (n<36 || n>96)) return Status::UnsupportedMetadata;
        for (std::size_t i=0;i<p.count;++i) {
            const auto status=apply(staged,p.writes[i],notes,false);
            if (status!=Status::Ok) return status;
        }
        return Status::Ok;
    }
    Status apply(Image& image,Write word,const Notes& notes,bool audible) noexcept {
        const int address=word.address,value=word.value;
        if (address==0x208) {
            const int pair=value&7;
            if ((value&128) || pair>5 || ((value&24)!=0 && (value&24)!=24)
                || ((value&96)!=0 && (value&96)!=96)) return Status::UnsupportedPlan;
            // Validate both paired edges before applying either native edge.
            for (int odd=0;odd<2;++odd) {
                const int slot=2*pair+odd;
                const bool on=(value & (odd?96:24))!=0;
                const auto& s=image.slots[slot];
                if (on && !s.keyed && (s.valid!=kComplete || notes[slot]<36 || notes[slot]>96)) return Status::MissingRegisters;
            }
            for (int odd=0;odd<2;++odd) {
                const int slot=2*pair+odd;
                const bool on=(value & (odd?96:24))!=0;
                auto& s=image.slots[slot];
                if (s.keyed!=on && audible)
                    Press78SustainTestAccess::key(engine_,slot,on,patch(s),notes[slot],frequency(s));
                s.keyed=on;
            }
            return Status::Ok;
        }
        int slot=-1;
        if (address>=0x240 && address<=0x2fd) {
            const int group=(address-0x240)/32, offset=(address-0x240)%32;
            const int pair=offset&7, odd=offset/16, carrier=(offset&8)?1:0;
            if (group>5 || pair>5) return Status::UnsupportedPlan;
            slot=2*pair+odd;
            auto& s=image.slots[slot];
            (carrier?s.car:s.mod)[group]=word.value;
            s.valid|=1u<<(group+6*carrier);
        } else {
            int field=-1,base=0,mask=0;
            if (address>=0x218 && address<=0x21d) { field=13;base=0x218;mask=0x73; }
            else if (address>=0x220 && address<=0x225) { field=12;base=0x220;mask=0x78; if ((value&0x47)!=0x40) return Status::UnsupportedPlan; }
            else if (address>=0x228 && address<=0x22d) { field=14;base=0x228;mask=0x1f; }
            else if (address>=0x230 && address<=0x235) { field=15;base=0x230;mask=0x3f; }
            else if (address>=0x238 && address<=0x23d) { field=16;base=0x238;mask=0x7c; }
            else return Status::UnsupportedPlan;
            if (value & ~(mask|128)) return Status::UnsupportedPlan;
            slot=2*(address-base)+(value>>7);
            auto& s=image.slots[slot];
            if (field==12) s.feedback=word.value;
            if (field==13) s.pmsAms=word.value;
            if (field==14) s.pitchHigh=word.value;
            if (field==15) s.pitchLow=word.value;
            if (field==16) s.pitchBlock=word.value;
            s.valid|=1u<<field;
        }
        const auto& s=image.slots[slot];
        if (audible && s.valid==kComplete)
            Press78SustainTestAccess::coefficients(engine_,slot,patch(s),frequency(s));
        return Status::Ok;
    }
};
} // namespace press78::research
