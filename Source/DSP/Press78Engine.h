#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include "AnalogOutput.h"

// Independently written port of the documented PSS-780 behavioral experiment.
// This is not a bit-exact YM3420/OPU emulator. No Yamaha firmware is included.
namespace press78 {

struct Operator {
    int mul = 1;       // 0 means 1/2; otherwise integer ratio 1..15.
    int dt1 = 0;       // -7..7; behavioral law: 1.5 cents/step.
    int tl = 0;        // 0..127 attenuation; values >=99 mute the operator.
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
    int midiPitchBend = -1;            // -1: standalone semitones; else14-bit raw.
    int midiBendRange = 2;             // 0..24; original positive spans1..12.
    // Original: masterTune rounds to3.125c before lookup (hardware +/-50c;
    // larger plugin spans are creative). Host calibration remains continuous.
    double hostTuneCents = 0.0;        // Nonpersisted host master tuning.
    double velocitySensitivity = 1.0; // carrier velocity exponent, 0..2.
    double velocityToModulation = 0.0;// modulator velocity exponent, 0..2.
    double modulationAmount = 1.0;    // 0..2 times the baseline FM index (8*pi).
    int polyphony = 12;               // 1..12. Reductions fade the oldest voices.
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
    bool outputCircuit = true;        // Related PSS480 small-signal circuit model.
    double toneCutoffHz = 14000.0;     // 20..0.9*Nyquist; 0 bypasses filter.
    double drive = 0.0;               // 0..1 creative tanh saturation; 0 bypass.
    int chorusMode = 0;              // 0 Studio legacy;1 recorded effective v3.
    double chorusMix = 0.0;           // 0..1, scales the selected stereo side.
    double chorusRateHz = 0.65;       // 0.05..8.
    double chorusDepthMs = 2.0;       // 0..8. Studio12ms; recorded measured harmonic law.
    double stereoWidth = 1.0;         // 0..2; dry mono midpoint is preserved.
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
    static constexpr double kInternalRate = 48000.0; // Modeling choice, not OPU fact.
    static constexpr int kResamplerDelay = 32;       // Internal samples.

    Press78Engine() noexcept;
    void prepare(double sampleRate) noexcept; // 8000..192000; resets state.
    void reset() noexcept;
    // Program changes snapshot future voices. Explicit live edit preserves
    // oscillator/envelope state and updates the sounding voices' coefficients.
    void setPatch(const Patch&, bool updateActiveVoices = false) noexcept;
    void setControls(const Controls&) noexcept;
    // Research fixture only: set a capture epoch for the continuous chorus
    // LFO (seconds, bounded+/-1e6). Call after prepare/setControls, not per block.
    // Does not reset signal history; reset() restores ordinary zero epoch.
    void setChorusTime(double seconds) noexcept;
    void noteOn(int note, int velocity, int source = 0) noexcept;
    void noteOff(int note, int source = 0) noexcept; // Oldest held match; source0=MIDI,1=CV.
    void sustainPedal(bool down) noexcept;
    void allNotesOff() noexcept;
    void allSoundOff() noexcept;
    // Null outputs still advance time. If outputs alias, the right channel wins.
    void process(float* left, float* right, std::size_t frames) noexcept;
    std::size_t activeVoices() const noexcept;
    double sampleRate() const noexcept { return sampleRate_; }
    // Nominal-clock resampler latency; effects add their own wet-only delay.
    // Clock variation also scales the32-tick delay (less than3.1% at limits).
    int latencySamples() const noexcept;
    const Patch& patch() const noexcept { return patch_; }
    const Controls& controls() const noexcept { return controls_; }
    // A requested law change waits until voices and steal tails are idle.
    int effectivePitchModel() const noexcept { return effectivePitchModel_; }

private:
    struct Envelope {
        double attenuation = 96.0, attackMul = 0.0, decay1 = 0.0;
        double decay2 = 0.0, release = 0.0, target = 0.0;
        int stage = 0;
        bool instantAttack = false, disabled = true, finished = false;
        void configure(const Operator&, int midi, bool sustain) noexcept;
        double next(bool released) noexcept;
    };
    struct Voice {
        Patch patch{};
        Envelope modEnvelope{}, carrierEnvelope{};
        double modPhase = 0.0, carrierPhase = 0.0;
        double prev1 = 0.0, prev2 = 0.0, lfoPhase = 0.0;
        double modStep = 0.0, carrierStep = 0.0;
        double modGain = 0.0, carrierGain = 0.0, feedback = 0.0;
        double velocity = 1.0;
        std::uint64_t age = 0, ticks = 0;
        int note = 60, source = 0;
        bool active = false, held = false, released = false;
        void configure(const Patch&, int midi, int vel, std::uint64_t serial) noexcept;
        void updatePatch(const Patch&) noexcept;
        void updateOriginalPitch(int steps) noexcept;
        double next(const Controls&, double pitchMultiplier, double globalLfo) noexcept;
    };
    struct Tail { Voice voice{}; int remaining = 0; };
    static constexpr std::size_t kHistory = 256;
    static constexpr std::size_t kDelaySize = 4096;
    static constexpr int kSincTaps = 64;
    static constexpr int kSincPhases = 256;
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
    double globalLfoPhase_ = 0.0, chorusPhase_ = 0.0;
    double gain_ = 0.25, pitchMultiplier_ = 1.0, targetPitch_ = 1.0;
    double tone1_ = 0.0, tone2_ = 0.0, toneCoefficient_ = 0.0;
    double currentToneCoefficient_ = 0.0, drive_ = 0.0, chorusMix_ = 0.0;
    double circuitMix_ = 1.0;
    double recordedChorusMix_ = 0.0;  // Smoothed mode blend; no history reset.
    double chorusRate_ = 0.65, chorusDepth_ = 2.0, width_ = 1.0;
    double dcInputL_ = 0.0, dcInputR_ = 0.0, dcOutputL_ = 0.0, dcOutputR_ = 0.0;
    double dcCoefficient_ = 0.0, gainSmoothing_ = 0.0;
    std::int64_t nextTick_ = 0;
    std::uint64_t serial_ = 0;
    std::size_t delayWrite_ = 0;
    bool pedal_ = false, hasProcessed_ = false;
    int effectivePitchModel_ = 0, pitchSteps_ = 0;
    bool pitchIdle() const noexcept;
    void applyPendingPitchModel() noexcept;
    void updatePitchControls() noexcept;
    void buildResampler() noexcept;
    double synthesizeTick() noexcept;
    double resampled(double position) const noexcept;
    double historyAt(std::int64_t tick) const noexcept;
    double readDelay(double samples) const noexcept;
    void output(double mono, double& left, double& right) noexcept;
};
} // namespace press78
