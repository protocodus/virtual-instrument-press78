#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include "AnalogOutput.h"
#include "AmplifierCircuit.h"
#include "ChorusCircuit.h"
#include "FirmwareAllocation.h"

// Independently written port of the documented PSS-780 behavioral experiment.
// This is not a bit-exact YM3420/OPU emulator. No Yamaha firmware is included.
namespace press78 {

struct Operator {
    int mul = 1;       // 0 means 1/2; otherwise integer ratio 1..15.
    int dt1 = 0;       // -7..7; behavioral law: 1.5 cents/step.
    int tl = 0;        // 0..127; the selected key-level law precedes the final 99 mute.
    int lksHi = 0, lksLo = 0, rks = 0;
    int ar = 63, d1r = 0, d2r = 0, d1l = 0;
    int rr = 10, srr = 5;
    int wave = 0;      // sine, signed squared sine, half sine, squared half sine.
    bool amEnable = false, dt2 = false; // DT2 adds 600 cents in this model.
};

struct Patch {
    Operator modulator{}, carrier{};
    int feedback = 0, pms = 0, ams = 0, vibratoDelay = 0;
    bool vibrato = false, sustain = false;
    // Retained for provenance/import round trips; unknown bytes have no effect.
    std::array<std::uint8_t, 33> rawData{};
};

Patch decodeVoice(const std::array<std::uint8_t, 33>& bytes) noexcept;
Patch sanitizePatch(Patch patch) noexcept;
Patch initPatch() noexcept; // Independently defined sine, no factory data needed.

struct Controls {
    double masterGain = 0.25;          // 0..2, applied after synthesis/effects.
    double pitchBendSemitones = 0.0;   // -48..48.
    double masterTuneCents = 0.0;      // -1200..1200.
    // Equal0 preserves the legacy continuous pitch law. Original1 uses the
    // verified firmware command table plus an empirical downstream grid law.
    int pitchModel = 0;
    // Legacy0 keeps the earlier key-level curves. Original1 uses the PSS-780
    // program's signed per-key TL offsets and saturation; 0.75 dB per code and
    // the final 99 mute remain the existing model.
    int keyLevelModel = 0;
    int midiPitchBend = -1;            // -1: standalone semitones; else14-bit raw.
    int midiBendRange = 2;             // 0..24; original positive spans1..12.
    // Original: masterTune rounds to3.125c before lookup (hardware +/-50c;
    // larger plugin spans are creative). Host calibration remains continuous.
    double hostTuneCents = 0.0;        // Nonpersisted host master tuning.
    double velocitySensitivity = 1.0; // carrier velocity exponent, 0..2.
    double velocityToModulation = 0.0;// modulator velocity exponent, 0..2.
    double modulationAmount = 1.0;    // 0..2 times the baseline FM index (8*pi).
    int polyphony = 12;               // 1..12; Original uses a first-N slot pool.
    // Legacy0 takes free voices, then steals the oldest. Original1 is the
    // PSS-780 program's Mode 00 allocation, with MIDI and CV as two sources.
    int allocationModel = 0;
    // Legacy0 holds released keys under the pedal. Original1 selects RR/SRR
    // immediately; it uses the existing approximate envelope timing law.
    int sustainMode = 0;
    // Legacy0 scales the carrier by (velocity/127)^velocitySensitivity.
    // Original1 uses the PSS-780 Mode 99 carrier velocity table, its dB scaled
    // by velocitySensitivity. Velocity to FM keeps the legacy law in both.
    int velocityCurve = 0;
    // PSS-780 Portamento effect: speed 1 (slow)..5 (fast), panel default 3.
    // The glide law is the keyboard program's; its service period is estimated.
    bool portamento = false;
    int portamentoSpeed = 3;
    // User-selected envelope-Reverb estimate, default on in both hosts.
    // Native reference callers may disable it; this is not a new host parameter.
    // Carrier EG >=18dB during release caps both operators at native RR4/RKS.
    bool envelopeReverb = true;
    double lfoRateHz = 5.24;            // 0..30, shared by AM and PM.
    double vibratoDepth = 1.0;         // 0..4 multiplier of the patch PMS law.
    double tremoloDepth = 1.0;         // 0..4 multiplier of the patch AMS law.
    double lfoDelayScale = 1.0;        // 0..4 times the patch delay.
    bool triangleLfo = true;
    bool globalLfo = true;            // false preserves per-note Python phase.
    double clockOffsetPpm = 0.0;       // -20000..20000, explicitly hypothetical.
    // Clock modulation retains the nominal reconstruction cutoff. Upward
    // shifts can alias near-Nyquist energy; this is not an alias-free warper.
    double clockDriftPpm = 0.0;        // 0..10000 sinusoidal excursion.
    double clockDriftRateHz = 0.1;     // 0.001..2; common digital timebase only.
    bool outputCircuit = true;        // Selected shared headroom + sibling filter.
    double toneCutoffHz = 14000.0;     // 20..0.9*Nyquist; 0 bypasses filter.
    double drive = 0.0;               // 0..1 creative tanh saturation; 0 bypass.
    int chorusMode = 0;              // 0 Studio legacy;1 recorded effective v3.
    // Legacy0 keeps the recorded fit's full-band wet signal. Sibling1 band-
    // limits it through the PSS-270 BBD wet-path filters (ChorusCircuit.h).
    int chorusCircuit = 0;
    double chorusMix = 0.0;           // 0..1, scales the selected stereo side.
    double chorusRateHz = 0.65;       // 0.05..8.
    double chorusDepthMs = 2.0;       // 0..8. Studio12ms; recorded measured harmonic law.
    double stereoWidth = 1.0;         // 0..2; dry mono midpoint is preserved.
    // 0 Preamp keeps the signal at the top of the volume slider, as before;
    // 1 AUX and 2 Phones add the amplifier and that jack (AmplifierCircuit.h).
    int outputJack = 0;
    // 0 Ideal keeps the amplifier linear, as before; 1 Batteries and 2 Adaptor
    // clip AUX and Phones at the AN7148's swing on that supply's rail.
    int powerSupply = 0;
    // Legacy0 ticks the chip core at 48 kHz, a modelling choice. YM3420_1
    // ticks it at the chip's own rate, so FM partials above its Nyquist fold
    // back where the hardware's do. Applied once voices are idle.
    int chipRate = 0;
    // Deprecated compatibility fields for old patches/callers. Sanitization
    // always sets both to zero; the instrument generates no additive noise.
    int noiseModel = 0;
    double noiseRms = 0.0;
    bool dcBlock = true;              // 10Hz output DC removal.
    bool outputLimit = true;          // transparent below .9, smooth bound +/-1.
};

Controls sanitizeControls(Controls controls) noexcept;

class Press78Engine {
public:
    static constexpr std::size_t kMaxVoices = 12;
    static constexpr double kInternalRate = 48000.0; // Legacy chip rate: a modeling choice, not OPU fact.
    // The PSS-780's 5.5 MHz OPU clock over 96. PSS-680 recordings (the same
    // YM3420) place 205 alias lines in 63 notes at 96 x fs = 5.4992 MHz, within
    // 150 ppm of that clock; dividers 95 or 97 would need a 1 % clock error.
    // At this rate 2^20 x f0/fs falls within 0.2 of an integer for the
    // measured notes: a 20-bit phase step per sample (research 2026-10-20).
    static constexpr double kYm3420Rate = 5.5e6 / 96.0;
    // Legacy ticks. Either chip rate delays by this time, 32/48000 s, so the
    // reported latency does not depend on Controls::chipRate.
    static constexpr int kResamplerDelay = 32;

    Press78Engine() noexcept;
    void prepare(double sampleRate) noexcept; // 8000..192000; resets state.
    void reset() noexcept;
    // Program changes snapshot future voices and seed Original Sustain from
    // the patch flag, without retimbring existing voices. A live edit preserves
    // the controller override unless the Sustain flag actually changes.
    void setPatch(const Patch&, bool updateActiveVoices = false) noexcept;
    void setControls(const Controls&) noexcept;
    // Research fixture only: set a capture epoch for the continuous chorus
    // LFO (seconds, bounded+/-1e6). Call after prepare/setControls, not per block.
    // Does not reset signal history; reset() restores ordinary zero epoch.
    void setChorusTime(double seconds) noexcept;
    void noteOn(int note, int velocity, int source = 0) noexcept;
    void noteOff(int note, int source = 0) noexcept; // Oldest held match; source0=MIDI,1=CV.
    void sustainPedal(bool down) noexcept;
    // An actual CC64 message, not a continuously replayed host-state snapshot.
    // Legacy threshold is64; Original enables SRR for every nonzero value.
    void sustainController(int rawValue) noexcept;
    void allNotesOff() noexcept;
    void allSoundOff() noexcept;
    // Null outputs still advance time. If outputs alias, the right channel wins.
    void process(float* left, float* right, std::size_t frames) noexcept;
    std::size_t activeVoices() const noexcept;
    double sampleRate() const noexcept { return sampleRate_; }
    // Nominal-clock resampler latency; effects add their own wet-only delay.
    // Clock variation also scales the 32/48000 s delay (less than 3.1% at limits).
    int latencySamples() const noexcept;
    double chipRate() const noexcept { return chipRate_; }
    const Patch& patch() const noexcept { return patch_; }
    const Controls& controls() const noexcept { return controls_; }
    // A requested law change waits until voices and steal tails are idle.
    int effectivePitchModel() const noexcept { return effectivePitchModel_; }
    int effectiveSustainMode() const noexcept { return effectiveSustainMode_; }
    int effectiveKeyLevelModel() const noexcept { return effectiveKeyLevelModel_; }
    int effectiveAllocationModel() const noexcept { return effectiveAllocationModel_; }
    int effectiveChipRate() const noexcept { return effectiveChipRate_; }

private:
    friend struct Press78SustainTestAccess;
    friend struct Press78PortamentoTestAccess;
    friend struct Press78AllocationTestAccess;
    friend struct Press78ChipRateTestAccess;
    struct Envelope {
        double attenuation = 96.0, attackMul = 0.0, decay1 = 0.0;
        double decay2 = 0.0, release = 0.0, reverbRelease = 0.0, target = 0.0;
        int stage = 0;
        bool instantAttack = false, disabled = true, finished = false;
        void configure(const Operator&, int midi, bool sustain, double tickRate) noexcept;
        void updateRelease(const Operator&, int midi, bool sustain, double tickRate) noexcept;
        double next(bool released, bool reverbKnee = false) noexcept;
    };
    struct Voice {
        Patch patch{};
        Envelope modEnvelope{}, carrierEnvelope{};
        double modPhase = 0.0, carrierPhase = 0.0;
        double prev1 = 0.0, prev2 = 0.0, lfoPhase = 0.0;
        double modStep = 0.0, carrierStep = 0.0;
        double modGain = 0.0, carrierGain = 0.0, feedback = 0.0;
        double velocity = 1.0;      // velocity/127, the modulator's law.
        double velocityLevel = 1.0; // Carrier level at sensitivity 1.
        // Portamento offset and per-service step in 1/256 semitone, as the
        // firmware keeps them; the oscillators hear offset>>3 (1/32 semitone).
        int glideOffset = 0, glideStep = 0, glideSteps = 0;
        double glideMultiplier = 1.0; // Equal model only.
        std::uint64_t age = 0, ticks = 0;
        double tickRate = kInternalRate; // Fixed while the voice sounds.
        int note = 60, source = 0;
        bool active = false, held = false, released = false;
        void configure(const Patch&, int midi, int vel, std::uint64_t serial, int keyLevelModel, double rate) noexcept;
        void updatePatch(const Patch&, int keyLevelModel) noexcept;
        void updateRelease(bool sustain) noexcept;
        void updateOriginalPitch(int steps) noexcept;
        double next(const Controls&, double pitchMultiplier, double globalLfo) noexcept;
    };
    struct Tail { Voice voice{}; int remaining = 0; };
    // The sinc reader needs at most the latest 64 ticks after fill; 128 keeps
    // every one and leaves room for the allocator in the instance budget.
    static constexpr std::size_t kHistory = 128;
    static constexpr std::size_t kDelaySize = 4096;
    static constexpr int kSincTaps = 64;
    static constexpr int kSincPhases = 256;
    static_assert(kHistory >= kResamplerDelay * kYm3420Rate / kInternalRate + 34, "History must retain every causal sinc tap");
    std::array<Voice, kMaxVoices> voices_{};
    std::array<Tail, kMaxVoices> tails_{};
    std::array<double, kHistory> history_{};
    std::array<std::array<double, kSincTaps>, kSincPhases + 1> sinc_{};
    std::array<double, kDelaySize> delay_{};
    Patch patch_{};
    Controls controls_{};
    Controls voiceControls_{};
    AnalogOutput analog_{};
    double sampleRate_ = 48000.0, position_ = 0.0, hostTime_ = 0.0;
    double chipRate_ = kInternalRate, resamplerDelay_ = kResamplerDelay, tickSmoothing_ = 0.0;
    int portamentoServiceTicks_ = 0, fadeTicks_ = 48, effectiveChipRate_ = 0;
    double globalLfoPhase_ = 0.0, chorusPhase_ = 0.0;
    double gain_ = 0.25, pitchMultiplier_ = 1.0, targetPitch_ = 1.0;
    double tone1_ = 0.0, tone2_ = 0.0, toneCoefficient_ = 0.0;
    double currentToneCoefficient_ = 0.0, drive_ = 0.0, chorusMix_ = 0.0;
    double circuitMix_ = 1.0, chorusCircuitMix_ = 0.0;
    ChorusCircuit chorusCircuit_{};
    double auxMix_ = 0.0, phonesMix_ = 0.0;
    AmplifierCircuit amplifier_{};
    double recordedChorusMix_ = 0.0;  // Smoothed mode blend; no history reset.
    double chorusRate_ = 0.65, chorusDepth_ = 2.0, width_ = 1.0;
    double dcInputL_ = 0.0, dcInputR_ = 0.0, dcOutputL_ = 0.0, dcOutputR_ = 0.0;
    double dcCoefficient_ = 0.0, gainSmoothing_ = 0.0;
    std::int64_t nextTick_ = 0;
    std::uint64_t serial_ = 0;
    std::size_t delayWrite_ = 0;
    bool pedal_ = false, hasProcessed_ = false;
    bool originalSustain_ = false;
    int effectivePitchModel_ = 0, pitchSteps_ = 0;
    int effectiveSustainMode_ = 0, effectiveKeyLevelModel_ = 0;
    int effectiveAllocationModel_ = 0;
    Mode00Allocator allocator_{};
    // Held inputs per source and note, so a law change waits for every key
    // to lift even after its voice was stolen or its envelope finished.
    std::array<std::array<std::uint32_t, 128>, 2> heldInputCounts_{};
    bool allocationIdle() const noexcept;
    void applyPendingAllocationModel() noexcept;
    void clearAllocationState() noexcept;
    bool silent(int note) const noexcept;
    void startVoice(Voice&, int note, int velocity, int source) noexcept;
    void fadeVoice(Voice&) noexcept;
    void originalNoteOn(int note, int velocity, int source) noexcept;
    void originalNoteOff(int note, int source) noexcept;
    // Last note-on per source (0 = none yet: the firmware does not glide then).
    std::array<int, 2> lastNote_{};
    int portamentoCountdown_ = 0;
    void servicePortamento() noexcept;
    void applyGlide(Voice& voice) noexcept;
    bool pitchIdle() const noexcept;
    void applyPendingPitchModel() noexcept;
    void applyPendingSustainMode() noexcept;
    void applyPendingKeyLevelModel() noexcept;
    void applyPendingChipRate() noexcept;
    void setChipRate(int model) noexcept;
    void refreshOriginalRelease() noexcept;
    void updatePitchControls() noexcept;
    void buildResampler() noexcept;
    double synthesizeTick() noexcept;
    double resampled(double position) const noexcept;
    double historyAt(std::int64_t tick) const noexcept;
    double readDelay(double samples) const noexcept;
    void output(double mono, double& left, double& right) noexcept;
};
} // namespace press78
