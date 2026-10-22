#include "Press78Engine.h"
#include "RecordedChorus.h"
#include "FirmwarePitch.h"
#include "FirmwareLevel.h"
#include "HardwareCharacter.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace press78 {
namespace {
constexpr double pi = 3.14159265358979323846264338327950288;
constexpr double tau = 2.0 * pi;
// Recording-calibrated OPU hypothesis: PMS3 is about12.5 cents, with
// doubling depth per sensitivity step. Unobserved levels remain hypotheses.
constexpr double pmDepth[8] = {0.0, 3.125, 6.25, 12.5, 25.0, 50.0, 100.0, 200.0};
constexpr double amDepth[4] = {0.0, 1.4, 5.9, 11.8};
constexpr double rateScaling[4] = {0.0, 0.0625, 0.125, 0.25};
// PSS-780 program (xg503b0-132, read 2026-10-20): Portamento starts a slot at
// the previous note-on's pitch, offset (previous-new)*256 in 1/256 semitone,
// and each main-loop pass adds (new-previous)<<speed until the offset crosses
// zero. Every glide thus takes 2^(8-speed) passes whatever the interval:
// 128, 64, 32, 16, 8 for speeds 1..5. The pass is not timer-paced and was not
// measured; 2.5 ms (speed 3 = 80 ms) is an estimate, the one unrecovered value.
constexpr double kPortamentoServiceSeconds = 0.0025;

// PSS-780 program (xg503b0-132, bank2 $7890, read 2026-10-20): in Mode 99 a
// note's carrier TL gains a velocity addend of 31 codes below velocity 3,
// falling by one code at each of these velocities to 0 from 118. The
// keyboard's own Mode 00 ignores velocity. A TL code is 0.75 dB, as level()
// assumes. The firmware saturates TL+addend at 127, >95 dB down; not modeled.
constexpr int kMode99VelocitySteps[31] = {3, 4, 5, 6, 7, 9, 10, 12, 13, 15, 17, 19, 22, 24, 27, 30,
                                          34, 37, 41, 46, 51, 56, 62, 68, 74, 80, 87, 94, 102, 111, 118};

double mode99VelocityLevel(int velocity) noexcept {
    int addend = 31;
    for (const int step : kMode99VelocitySteps) if (velocity >= step) --addend;
    return std::pow(10.0, -addend * 0.75 / 20.0);
}

// The firmware shifts the glide offset right three times into the
// 1/32-semitone pitch coordinate, rounding toward minus infinity.
int heardGlideSteps(int offset) noexcept { return offset >= 0 ? offset / 8 : -((7 - offset) / 8); }

double bounded(double x, double low, double high, double fallback) noexcept {
    return std::isfinite(x) ? std::clamp(x, low, high) : fallback;
}
double rate(int value, int scaling, int note) noexcept {
    if (value == 0) return 0.0;
    return std::clamp(value + (note - 60) * rateScaling[scaling], 0.25, 63.0);
}
double level(const Operator& op, int midi) noexcept {
    if (op.tl >= 99) return 0.0;
    const int value = midi >= 60 ? op.lksHi : op.lksLo;
    double distance = std::abs(midi - 60), slope = 0.0;
    if (midi >= 60) {
        constexpr double slopes[16] = {0, -3, -2, -1, 1, 2, 3, 5, 6, 8, 10, 3, 4.5, 6.5, 8.5, 10.5};
        slope = slopes[value];
        if (value >= 11) distance = 36.0 * std::pow(distance / 36.0, 1.5);
    } else {
        slope = value == 0 ? 0.0 : (value < 8 ? value - 8 : value - 7);
    }
    return std::min(4.0, std::pow(10.0, -(op.tl * 0.75 + slope * distance * 0.0625) / 20.0));
}
double firmwareLevel(const Operator& op, int midi) noexcept {
    const int command = firmware_level::command(op.tl, midi, (op.lksHi << 4) | op.lksLo);
    // The signed lookup and saturation are the keyboard program's.
    // This decibel transfer and silence boundary remain the existing model.
    return command >= 99 ? 0.0 : std::pow(10.0, -(command * 0.75) / 20.0);
}
double step(const Operator& op, int note, double rate) noexcept {
    const double base = 440.0 * std::pow(2.0, (note - 69) / 12.0);
    const double ratio = op.mul == 0 ? 0.5 : static_cast<double>(op.mul);
    const double cents = (op.dt2 ? 600.0 : 0.0) + op.dt1 * 1.5;
    return tau * base * ratio * std::pow(2.0, cents / 1200.0) / rate;
}
double originalStep(const Operator& op, int note, int steps, double rate) noexcept {
    const double base = firmware_pitch::frequency(note, steps);
    const double ratio = op.mul == 0 ? 0.5 : static_cast<double>(op.mul);
    const double cents = (op.dt2 ? 600.0 : 0.0) + op.dt1 * 1.5;
    return tau * base * ratio * std::pow(2.0, cents / 1200.0) / rate;
}
double wave(double phase, int shape) noexcept {
    const double s = std::sin(phase);
    if (shape >= 2 && s < 0.0) return 0.0;
    return shape == 1 || shape == 3 ? s * std::abs(s) : s;
}
Operator sanitize(Operator op) noexcept {
    op.mul = std::clamp(op.mul, 0, 15);
    op.dt1 = std::clamp(op.dt1, -7, 7);
    op.tl = std::clamp(op.tl, 0, 127);
    op.lksHi = std::clamp(op.lksHi, 0, 15);
    op.lksLo = std::clamp(op.lksLo, 0, 15);
    op.rks = std::clamp(op.rks, 0, 3);
    op.ar = std::clamp(op.ar, 0, 63);
    op.d1r = std::clamp(op.d1r, 0, 63);
    op.d2r = std::clamp(op.d2r, 0, 63);
    op.d1l = std::clamp(op.d1l, 0, 15);
    op.rr = std::clamp(op.rr, 0, 15);
    op.srr = std::clamp(op.srr, 0, 15);
    op.wave = std::clamp(op.wave, 0, 3);
    return op;
}
double softBound(double x) noexcept {
    const double a = std::abs(x);
    return a <= 0.9 ? x : std::copysign(0.9 + 0.1 * std::tanh((a - 0.9) / 0.1), x);
}
} // namespace

Patch decodeVoice(const std::array<std::uint8_t, 33>& b) noexcept {
    Patch patch;
    patch.rawData = b;
    for (int k = 0; k < 2; ++k) {
        auto& op = k == 0 ? patch.modulator : patch.carrier;
        const int dt = b[1 + k] >> 4;
        op.mul = b[1 + k] & 15;
        op.dt1 = (dt & 8) != 0 ? -(dt & 7) : dt & 7;
        op.tl = b[3 + k] & 127;
        op.lksHi = b[5 + k] >> 4; op.lksLo = b[5 + k] & 15;
        op.rks = b[7 + k] >> 6; op.ar = b[7 + k] & 63;
        op.amEnable = (b[9 + k] & 128) != 0; op.dt2 = (b[9 + k] & 64) != 0;
        op.d1r = b[9 + k] & 63;
        op.wave = b[11 + k] >> 6; op.d2r = b[11 + k] & 63;
        op.d1l = b[13 + k] >> 4; op.rr = b[13 + k] & 15;
        op.srr = b[20 + k] & 15;
    }
    patch.feedback = (b[15] >> 3) & 7;
    patch.pms = (b[16] >> 4) & 7; patch.ams = b[16] & 3;
    patch.vibratoDelay = b[22] & 127;
    patch.vibrato = (b[24] & 128) != 0; patch.sustain = (b[24] & 64) != 0;
    return patch;
}

Patch sanitizePatch(Patch p) noexcept {
    p.modulator = sanitize(p.modulator); p.carrier = sanitize(p.carrier);
    p.feedback = std::clamp(p.feedback, 0, 7);
    p.pms = std::clamp(p.pms, 0, 7); p.ams = std::clamp(p.ams, 0, 3);
    p.vibratoDelay = std::clamp(p.vibratoDelay, 0, 127);
    return p;
}

Patch initPatch() noexcept {
    Patch p;
    p.modulator.tl = 127;
    return p;
}

Controls sanitizeControls(Controls c) noexcept {
    c.masterGain = bounded(c.masterGain, 0, 2, 0.25);
    c.pitchBendSemitones = bounded(c.pitchBendSemitones, -48, 48, 0);
    c.masterTuneCents = bounded(c.masterTuneCents, -1200, 1200, 0);
    c.hostTuneCents = bounded(c.hostTuneCents, -1200, 1200, 0);
    c.pitchModel = std::clamp(c.pitchModel, 0, 1);
    c.keyLevelModel = std::clamp(c.keyLevelModel, 0, 1);
    c.midiPitchBend = std::clamp(c.midiPitchBend, -1, 16383);
    c.midiBendRange = std::clamp(c.midiBendRange, 0, 24);
    c.velocitySensitivity = bounded(c.velocitySensitivity, 0, 2, 1);
    c.velocityToModulation = bounded(c.velocityToModulation, 0, 2, 0);
    c.modulationAmount = bounded(c.modulationAmount, 0, 2, 1);
    c.polyphony = std::clamp(c.polyphony, 1, 12);
    c.allocationModel = std::clamp(c.allocationModel, 0, 1);
    c.chorusCircuit = std::clamp(c.chorusCircuit, 0, 1);
    c.outputJack = std::clamp(c.outputJack, 0, 2);
    c.powerSupply = std::clamp(c.powerSupply, 0, 2);
    c.power = std::clamp(c.power, 1, 101);
    c.chipRate = std::clamp(c.chipRate, 0, 1);
    c.sustainMode = std::clamp(c.sustainMode, 0, 1);
    c.velocityCurve = std::clamp(c.velocityCurve, 0, 1);
    c.portamentoSpeed = std::clamp(c.portamentoSpeed, 1, 5);
    c.lfoRateHz = bounded(c.lfoRateHz, 0, 30, 5.24);
    c.vibratoDepth = bounded(c.vibratoDepth, 0, 4, 1);
    c.tremoloDepth = bounded(c.tremoloDepth, 0, 4, 1);
    c.lfoDelayScale = bounded(c.lfoDelayScale, 0, 4, 1);
    c.clockOffsetPpm = bounded(c.clockOffsetPpm, -20000, 20000, 0);
    c.clockDriftPpm = bounded(c.clockDriftPpm, 0, 10000, 0);
    c.clockDriftRateHz = bounded(c.clockDriftRateHz, 0.001, 2, 0.1);
    c.toneCutoffHz = bounded(c.toneCutoffHz, 0, 86400, 14000);
    if (c.toneCutoffHz > 0) c.toneCutoffHz = std::max(20.0, c.toneCutoffHz);
    c.drive = bounded(c.drive, 0, 1, 0);
    c.chorusMode = std::clamp(c.chorusMode, 0, 1);
    c.chorusMix = bounded(c.chorusMix, 0, 1, 0);
    c.chorusRateHz = bounded(c.chorusRateHz, 0.05, 8, 0.65);
    c.chorusDepthMs = bounded(c.chorusDepthMs, 0, 8, 2);
    c.stereoWidth = bounded(c.stereoWidth, 0, 2, 1);
    // Retained only for source/patch compatibility. No artificial-noise path
    // exists, including when an older caller requests nonzero or invalid values.
    c.noiseRms = 0.0;
    c.noiseModel = 0;
    return c;
}

void Press78Engine::Envelope::configure(const Operator& op, int midi, bool sustain, double tickRate) noexcept {
    const double ar = rate(op.ar, op.rks, midi);
    const double d1r = rate(op.d1r, op.rks, midi), d2r = rate(op.d2r, op.rks, midi);
    disabled = ar == 0.0;
    instantAttack = ar >= 63.0;
    attackMul = std::exp(-std::log(1000.0) / std::max(1.0, tickRate * 8.0 * std::pow(2.0, -ar / 4.0)));
    decay1 = d1r == 0.0 ? 0.0 : 96.0 / (tickRate * 48.0 * std::pow(2.0, -d1r / 4.0));
    decay2 = d2r == 0.0 ? 0.0 : 96.0 / (tickRate * 48.0 * std::pow(2.0, -d2r / 4.0));
    updateRelease(op, midi, sustain, tickRate);
    target = op.d1l == 15 ? 93.0 : op.d1l * 3.0;
}

void Press78Engine::Envelope::updateRelease(const Operator& op, int midi, bool sustain, double tickRate) noexcept {
    const double rr = rate(4 * (sustain ? op.srr : op.rr) + 2, op.rks, midi);
    release = 96.0 / (tickRate * 48.0 * std::pow(2.0, -rr / 4.0));
    // Selected B uses each operator's unchanged native RR4/RKS transform.
    // Precompute at configuration/rate edits, not with pow/copies every tick.
    const double capRate = rate(4 * 4 + 2, op.rks, midi);
    reverbRelease = 96.0 / (tickRate * 48.0 * std::pow(2.0, -capRate / 4.0));
}

double Press78Engine::Envelope::next(bool released, bool reverbKnee) noexcept {
    if (disabled || finished) return 0.0;
    if (released) stage = 3;
    if (stage == 0) {
        attenuation = instantAttack ? 0.0 : attenuation * attackMul;
        if (attenuation <= 0.096) { attenuation = 0.0; stage = 1; }
    } else {
        // An already reached D1L has no D1 interval. Test it before stepping,
        // so a zero-height D1 neither adds attenuation nor delays D2. This is
        // a behavioral endpoint correction, not a recovered OPU tick law.
        if (stage == 1 && attenuation >= target) stage = 2;
        if (stage == 1) {
            attenuation += decay1;
            if (attenuation >= target) stage = 2;
        } else if (stage == 2) attenuation += decay2;
        else attenuation += reverbKnee ? std::min(release, reverbRelease) : release;
    }
    if (attenuation >= 96.0) {
        if (stage != 0) finished = true;
        return 0.0;
    }
    return std::pow(10.0, -std::max(0.0, attenuation) / 20.0);
}

void Press78Engine::Voice::configure(const Patch& p, int midi, int vel, std::uint64_t serial, int keyLevelModel, double rate) noexcept {
    *this = Voice{};
    note = midi; velocity = vel / 127.0; age = serial; tickRate = rate;
    active = true; held = true;
    updatePatch(p, keyLevelModel);
}

void Press78Engine::Voice::updatePatch(const Patch& p, int keyLevelModel) noexcept {
    patch = p;
    modEnvelope.configure(p.modulator, note, p.sustain, tickRate);
    carrierEnvelope.configure(p.carrier, note, p.sustain, tickRate);
    modStep = step(p.modulator, note, tickRate); carrierStep = step(p.carrier, note, tickRate);
    if (keyLevelModel == 1) {
        modGain = firmwareLevel(p.modulator, note);
        carrierGain = firmwareLevel(p.carrier, note) * 0.8;
    } else {
        modGain = level(p.modulator, note); carrierGain = level(p.carrier, note) * 0.8;
    }
    feedback = p.feedback == 0 ? 0.0 : 4.0 * pi * std::pow(2.0, p.feedback - 7);
}

void Press78Engine::Voice::updateOriginalPitch(int steps) noexcept {
    // Only coefficients change: oscillator phase, feedback, envelope and age
    // survive bends/fine edits, including voices in the steal fade.
    modStep = originalStep(patch.modulator, note, steps + glideSteps, tickRate);
    carrierStep = originalStep(patch.carrier, note, steps + glideSteps, tickRate);
}

void Press78Engine::Voice::updateRelease(bool sustain) noexcept {
    modEnvelope.updateRelease(patch.modulator, note, sustain, tickRate);
    carrierEnvelope.updateRelease(patch.carrier, note, sustain, tickRate);
}

double Press78Engine::Voice::next(const Controls& c, double pitchMultiplier, double globalLfo) noexcept {
    if (!active) return 0.0;
    // User-selected sibling-inspired pseudo-Reverb. One pre-step carrier
    // snapshot gates both operators; TL, velocity and gain do not move the knee.
    // 18dB/RR4 are assumed choices, not an identified PSS-780 Reverb algorithm.
    const bool knee = c.envelopeReverb && (released || carrierEnvelope.stage == 3)
        && std::isfinite(carrierEnvelope.attenuation)
        && carrierEnvelope.attenuation >= hardware_character::kReleaseKneeDb;
    const double em = modEnvelope.next(released, knee), ec = carrierEnvelope.next(released, knee);
    if (carrierEnvelope.finished || (carrierEnvelope.disabled && released)) {
        active = false; return 0.0;
    }
    double lfo = c.globalLfo ? globalLfo : std::sin(lfoPhase);
    if (c.triangleLfo) lfo = 2.0 / pi * std::asin(std::clamp(lfo, -1.0, 1.0));
    const double delay = std::round(patch.vibratoDelay * 0.01 * c.lfoDelayScale * tickRate);
    const double cents = patch.vibrato && static_cast<double>(ticks) >= delay ? pmDepth[patch.pms] * c.vibratoDepth * lfo : 0.0;
    const double pitch = pitchMultiplier * glideMultiplier * std::pow(2.0, cents / 1200.0);
    modPhase = std::fmod(modPhase + modStep * pitch, tau);
    carrierPhase = std::fmod(carrierPhase + carrierStep * pitch, tau);
    const double am = amDepth[patch.ams] * c.tremoloDepth;
    const double amM = patch.modulator.amEnable ? std::pow(10.0, -am * (lfo + 1.0) / 40.0) : 1.0;
    const double amC = patch.carrier.amEnable ? std::pow(10.0, -am * (lfo + 1.0) / 40.0) : 1.0;
    // The two delayed modulator outputs include envelope, TL, and AM exactly
    // as in the Python hypothesis. No unverified fixed-point table is added.
    const double mod = wave(modPhase + feedback * (prev1 + prev2) * 0.5, patch.modulator.wave)
        * em * modGain * std::pow(velocity, c.velocityToModulation) * amM;
    prev2 = prev1; prev1 = mod;
    const double y = wave(carrierPhase + 8.0 * pi * c.modulationAmount * mod, patch.carrier.wave)
        * ec * carrierGain * std::pow(velocityLevel, c.velocitySensitivity) * amC;
    lfoPhase = std::fmod(lfoPhase + tau * c.lfoRateHz / tickRate, tau);
    ++ticks;
    return y;
}

Press78Engine::Press78Engine() noexcept : patch_(initPatch()) { prepare(48000.0); }

void Press78Engine::prepare(double sampleRate) noexcept {
    sampleRate_ = bounded(sampleRate, 8000.0, 192000.0, 48000.0);
    setChipRate(controls_.chipRate);
    analog_.prepare(sampleRate_);
    chorusCircuit_.prepare(sampleRate_);
    amplifier_.prepare(sampleRate_);
    gainSmoothing_ = 1.0 - std::exp(-1.0 / (sampleRate_ * 0.005));
    dcCoefficient_ = std::exp(-tau * 10.0 / sampleRate_);
    setControls(controls_);
    reset();
}

void Press78Engine::reset() noexcept {
    for (auto& v : voices_) v = Voice{};
    for (auto& t : tails_) t = Tail{};
    history_.fill(0.0); delay_.fill(0.0);
    analog_.reset();
    chorusCircuit_.reset();
    amplifier_.reset();
    position_ = 0.0; nextTick_ = 0; hostTime_ = 0.0;
    globalLfoPhase_ = 0.0; chorusPhase_ = 0.0;
    lastNote_ = {}; portamentoCountdown_ = 0;
    effectivePitchModel_ = controls_.pitchModel;
    effectiveSustainMode_ = controls_.sustainMode;
    effectiveKeyLevelModel_ = controls_.keyLevelModel;
    effectiveAllocationModel_ = controls_.allocationModel;
    if (effectiveChipRate_ != controls_.chipRate) setChipRate(controls_.chipRate);
    clearAllocationState();
    originalSustain_ = patch_.sustain;
    updatePitchControls();
    gain_ = controls_.masterGain; pitchMultiplier_ = targetPitch_;
    voiceControls_ = controls_;
    currentToneCoefficient_ = toneCoefficient_;
    circuitMix_ = controls_.outputCircuit ? 1.0 : 0.0;
    chorusCircuitMix_ = static_cast<double>(controls_.chorusCircuit);
    auxMix_ = controls_.outputJack == 1 ? 1.0 : 0.0;
    phonesMix_ = controls_.outputJack == 2 ? 1.0 : 0.0;
    recordedChorusMix_ = static_cast<double>(controls_.chorusMode);
    drive_ = controls_.drive; chorusMix_ = controls_.chorusMix;
    chorusRate_ = controls_.chorusRateHz; chorusDepth_ = controls_.chorusDepthMs;
    width_ = controls_.stereoWidth;
    tone1_ = tone2_ = 0.0;
    dcInputL_ = dcInputR_ = dcOutputL_ = dcOutputR_ = 0.0;
    delayWrite_ = 0; serial_ = 0;
    pedal_ = false; hasProcessed_ = false;
}

void Press78Engine::setPatch(const Patch& patch, bool updateActive) noexcept {
    const bool flagChanged = patch.sustain != patch_.sustain;
    patch_ = sanitizePatch(patch);
    if (!updateActive || flagChanged) originalSustain_ = patch_.sustain;
    if (updateActive) for (auto& voice : voices_) if (voice.active) {
        voice.updatePatch(patch_, effectiveKeyLevelModel_);
        if (effectivePitchModel_ == 1) voice.updateOriginalPitch(pitchSteps_);
        if (effectiveSustainMode_ == 1) voice.updateRelease(originalSustain_);
    }
    // Steal fades retain their old patch, but an explicit live Sustain edit
    // also updates their rate. These short fades are a plugin click guard.
    if (updateActive && flagChanged) refreshOriginalRelease();
}

void Press78Engine::setChorusTime(double seconds) noexcept {
    seconds = bounded(seconds, -1e6, 1e6, 0.0);
    chorusPhase_ = std::fmod(tau * chorusRate_ * seconds, tau);
    if (chorusPhase_ < 0.0) chorusPhase_ += tau;
}

void Press78Engine::setControls(const Controls& controls) noexcept {
    controls_ = sanitizeControls(controls);
    applyPendingChipRate();
    applyPendingAllocationModel();
    applyPendingKeyLevelModel();
    applyPendingPitchModel();
    applyPendingSustainMode();
    updatePitchControls();
    toneCoefficient_ = controls_.toneCutoffHz == 0.0 ? 0.0
        : 1.0 - std::exp(-tau * std::min(controls_.toneCutoffHz, sampleRate_ * 0.45) / sampleRate_);
    const int source = controls_.powerSupply == 0 ? 0 : controls_.powerSupply == 2 || controls_.power > 100 ? 2 : 1;
    amplifier_.setSupply(source, (100 - std::min(controls_.power, 100)) / 99.0);
    if (!hasProcessed_) {
        gain_ = controls_.masterGain; pitchMultiplier_ = targetPitch_; voiceControls_ = controls_;
        currentToneCoefficient_ = toneCoefficient_;
        circuitMix_ = controls_.outputCircuit ? 1.0 : 0.0;
        chorusCircuitMix_ = static_cast<double>(controls_.chorusCircuit);
        auxMix_ = controls_.outputJack == 1 ? 1.0 : 0.0;
        phonesMix_ = controls_.outputJack == 2 ? 1.0 : 0.0;
        amplifier_.snapSupply();
        recordedChorusMix_ = static_cast<double>(controls_.chorusMode);
        drive_ = controls_.drive; chorusMix_ = controls_.chorusMix;
        chorusRate_ = controls_.chorusRateHz; chorusDepth_ = controls_.chorusDepthMs;
        width_ = controls_.stereoWidth;
    }
    if (effectiveAllocationModel_ == 1) {
        if (allocator_.pool != controls_.polyphony) {
            for (std::size_t i = static_cast<std::size_t>(controls_.polyphony); i < kMaxVoices; ++i)
                if (voices_[i].active) fadeVoice(voices_[i]);
            allocator_.setPolyphony(controls_.polyphony);
        }
    } else while (activeVoices() > static_cast<std::size_t>(controls_.polyphony)) {
        Voice* victim = nullptr;
        for (auto& v : voices_) if (v.active && (!victim || v.age < victim->age)) victim = &v;
        if (!victim) break;
        fadeVoice(*victim);
    }
}

void Press78Engine::noteOn(int note, int velocity, int source) noexcept {
    note = std::clamp(note, 0, 127);
    if (velocity <= 0) { noteOff(note, source); return; }
    velocity = std::min(velocity, 127);
    applyPendingAllocationModel();
    applyPendingKeyLevelModel();
    if (effectiveAllocationModel_ == 1) { originalNoteOn(note, velocity, source); return; }
    if (Mode00Allocator::validSource(source)) {
        auto& count = heldInputCounts_[source][note];
        if (count != std::numeric_limits<std::uint32_t>::max()) ++count;
    }
    if (silent(note)) return;
    Voice* target = nullptr;
    if (activeVoices() < static_cast<std::size_t>(controls_.polyphony)) {
        for (auto& v : voices_) if (!v.active) { target = &v; break; }
    }
    if (!target) {
        for (auto& v : voices_) if (v.active && (!target || v.age < target->age)) target = &v;
        if (!target) target = &voices_[0];
        fadeVoice(*target);
    }
    startVoice(*target, note, velocity, source);
}

bool Press78Engine::silent(int note) const noexcept {
    const bool muted = effectiveKeyLevelModel_ == 0 ? patch_.carrier.tl >= 99
        : firmware_level::command(patch_.carrier.tl, note,
            (patch_.carrier.lksHi << 4) | patch_.carrier.lksLo) >= 99;
    return muted || patch_.carrier.ar == 0;
}

void Press78Engine::startVoice(Voice& target, int note, int velocity, int source) noexcept {
    applyPendingChipRate();
    applyPendingPitchModel();
    applyPendingSustainMode();
    target.configure(patch_, note, velocity, ++serial_, effectiveKeyLevelModel_, chipRate_);
    target.velocityLevel = controls_.velocityCurve == 1 ? mode99VelocityLevel(velocity) : target.velocity;
    auto& previous = lastNote_[source == 1 ? 1 : 0];
    if (controls_.portamento && previous != 0) {
        target.glideOffset = (previous - note) * 256;
        target.glideStep = (note - previous) * (1 << controls_.portamentoSpeed);
        applyGlide(target);
    }
    previous = note;
    if (effectivePitchModel_ == 1) target.updateOriginalPitch(pitchSteps_);
    if (effectiveSustainMode_ == 1) target.updateRelease(originalSustain_);
    target.source = source;
}

void Press78Engine::fadeVoice(Voice& voice) noexcept {
    auto* tail = &tails_[0];
    for (auto& t : tails_) if (t.remaining < tail->remaining) tail = &t;
    tail->voice = voice; tail->remaining = fadeTicks_; voice.active = false;
}

void Press78Engine::originalNoteOn(int note, int velocity, int source) noexcept {
    if (!Mode00Allocator::validSource(source)) return;
    const auto event = allocator_.noteOn(note, source);
    if (!event.edge) return;
    heldInputCounts_[source][note] = 1;
    if (event.slot < 0) return;
    auto& target = voices_[static_cast<std::size_t>(event.slot)];
    if (target.active) fadeVoice(target);
    // A silent patch still owns its key, cache and rank. Do not start an
    // inaudible voice or mistake envelope retirement for a free input.
    if (!silent(note)) startVoice(target, note, velocity, source);
    (void)allocator_.service(1); // Immediate delivery; no CPU timing is modelled.
}

void Press78Engine::originalNoteOff(int note, int source) noexcept {
    if (!Mode00Allocator::validSource(source)) return;
    const auto event = allocator_.noteOff(note, source);
    if (!event.edge) return;
    heldInputCounts_[source][note] = 0;
    if (event.slot >= 0) {
        auto& target = voices_[static_cast<std::size_t>(event.slot)];
        if (target.active && target.note == note && target.source == source) {
            target.held = false;
            target.released = effectiveSustainMode_ == 1 || !pedal_;
        }
    }
    applyPendingAllocationModel();
}

void Press78Engine::noteOff(int note, int source) noexcept {
    note = std::clamp(note, 0, 127);
    if (effectiveAllocationModel_ == 1) { originalNoteOff(note, source); return; }
    if (Mode00Allocator::validSource(source)) {
        auto& count = heldInputCounts_[source][note];
        if (count) --count;
    }
    Voice* target = nullptr;
    for (auto& v : voices_) if (v.active && v.held && v.note == note && v.source == source && (!target || v.age < target->age)) target = &v;
    if (target) {
        target->held = false;
        // Program loads are future-only in this instrument. Keep this voice's
        // cached selection until an actual CC or explicit live Sustain edit.
        target->released = effectiveSustainMode_ == 1 || !pedal_;
    }
    applyPendingAllocationModel();
}

void Press78Engine::sustainPedal(bool down) noexcept {
    sustainController(down ? 127 : 0);
}

void Press78Engine::sustainController(int rawValue) noexcept {
    rawValue = std::clamp(rawValue, 0, 127);
    pedal_ = rawValue >= 64;
    originalSustain_ = rawValue != 0;
    if (effectiveSustainMode_ == 1) refreshOriginalRelease();
    else if (!pedal_) for (auto& v : voices_) if (v.active && !v.held) v.released = true;
}

void Press78Engine::allNotesOff() noexcept {
    if (effectiveAllocationModel_ == 1) allocator_.allNotesOff();
    for (auto& source : heldInputCounts_) source.fill(0);
    for (auto& v : voices_) if (v.active) {
        v.held = false;
        v.released = effectiveSustainMode_ == 1 || !pedal_;
    }
    applyPendingAllocationModel();
}

void Press78Engine::allSoundOff() noexcept {
    for (auto& v : voices_) v.active = false;
    for (auto& t : tails_) t.remaining = 0;
    history_.fill(0.0); delay_.fill(0.0);
    analog_.reset();
    chorusCircuit_.reset();
    amplifier_.reset();
    tone1_ = tone2_ = 0.0;
    dcInputL_ = dcInputR_ = dcOutputL_ = dcOutputR_ = 0.0;
    pedal_ = false;
    originalSustain_ = patch_.sustain;
    clearAllocationState();
    applyPendingChipRate();
    applyPendingAllocationModel();
    applyPendingKeyLevelModel();
    applyPendingPitchModel();
    applyPendingSustainMode();
}

void Press78Engine::clearAllocationState() noexcept {
    allocator_.reset(controls_.polyphony);
    for (auto& source : heldInputCounts_) source.fill(0);
}

bool Press78Engine::allocationIdle() const noexcept {
    if (!pitchIdle()) return false;
    for (const auto& source : heldInputCounts_) for (auto count : source) if (count) return false;
    return true;
}

void Press78Engine::applyPendingAllocationModel() noexcept {
    if (effectiveAllocationModel_ == controls_.allocationModel || !allocationIdle()) return;
    effectiveAllocationModel_ = controls_.allocationModel;
    clearAllocationState();
}

void Press78Engine::applyGlide(Voice& voice) noexcept {
    voice.glideSteps = heardGlideSteps(voice.glideOffset);
    if (effectivePitchModel_ == 1) voice.updateOriginalPitch(pitchSteps_);
    else voice.glideMultiplier = std::pow(2.0, voice.glideSteps / 384.0);
}

void Press78Engine::servicePortamento() noexcept {
    for (auto& voice : voices_) {
        if (!voice.active || voice.glideStep == 0) continue;
        const int before = voice.glideOffset;
        voice.glideOffset += voice.glideStep;
        if ((before < 0) != (voice.glideOffset < 0)) voice.glideOffset = voice.glideStep = 0;
        if (heardGlideSteps(voice.glideOffset) != voice.glideSteps) applyGlide(voice);
    }
}

bool Press78Engine::pitchIdle() const noexcept {
    for (const auto& voice : voices_) if (voice.active) return false;
    for (const auto& tail : tails_) if (tail.remaining > 0) return false;
    return true;
}

void Press78Engine::applyPendingPitchModel() noexcept {
    if (effectivePitchModel_ == controls_.pitchModel || !pitchIdle()) return;
    effectivePitchModel_ = controls_.pitchModel;
    updatePitchControls();
    // There are no oscillators to glide between laws. Starting the next voice
    // with the previous law's bend multiplier would otherwise double bend it.
    pitchMultiplier_ = targetPitch_;
}

void Press78Engine::applyPendingKeyLevelModel() noexcept {
    if (effectiveKeyLevelModel_ != controls_.keyLevelModel && pitchIdle())
        effectiveKeyLevelModel_ = controls_.keyLevelModel;
}

void Press78Engine::applyPendingChipRate() noexcept {
    if (effectiveChipRate_ != controls_.chipRate && pitchIdle()) setChipRate(controls_.chipRate);
}

void Press78Engine::setChipRate(int model) noexcept {
    effectiveChipRate_ = model;
    chipRate_ = model == 1 ? kYm3420Rate : kInternalRate;
    resamplerDelay_ = kResamplerDelay * chipRate_ / kInternalRate;
    // 5 ms control smoothing; the legacy literal (5 ms to 1 ppm) stays bit for bit.
    tickSmoothing_ = model == 1 ? 1.0 - std::exp(-1.0 / (chipRate_ * 0.005)) : 0.00415800184511004;
    portamentoServiceTicks_ = static_cast<int>(std::lround(kPortamentoServiceSeconds * chipRate_));
    fadeTicks_ = static_cast<int>(std::lround(0.001 * chipRate_)); // 1 ms steal fade.
    // A switch waits for silence, so the history the new table reads is
    // near zero and the delay's 6.2-tick jump cannot be heard.
    buildResampler();
}

void Press78Engine::applyPendingSustainMode() noexcept {
    if (effectiveSustainMode_ != controls_.sustainMode && pitchIdle())
        effectiveSustainMode_ = controls_.sustainMode;
}

void Press78Engine::refreshOriginalRelease() noexcept {
    if (effectiveSustainMode_ != 1) return;
    for (auto& voice : voices_) if (voice.active) voice.updateRelease(originalSustain_);
    for (auto& tail : tails_) if (tail.remaining > 0) tail.voice.updateRelease(originalSustain_);
}

void Press78Engine::updatePitchControls() noexcept {
    if (effectivePitchModel_ == 0) {
        const double tune = controls_.masterTuneCents + controls_.hostTuneCents;
        // Preserve the legacy addition order and5ms continuous smoothing.
        targetPitch_ = std::pow(2.0, (controls_.pitchBendSemitones * 100.0 + tune) / 1200.0);
        return;
    }
    const int bend = controls_.midiPitchBend < 0
        ? static_cast<int>(std::lround(controls_.pitchBendSemitones * 32.0))
        : firmware_pitch::bendSteps(controls_.midiPitchBend >> 7, controls_.midiBendRange);
    const int steps = bend + static_cast<int>(std::lround(controls_.masterTuneCents / 3.125));
    if (steps != pitchSteps_) {
        pitchSteps_ = steps;
        for (auto& voice : voices_) if (voice.active) voice.updateOriginalPitch(steps);
        for (auto& tail : tails_) if (tail.remaining > 0) tail.voice.updateOriginalPitch(steps);
    }
    targetPitch_ = std::pow(2.0, controls_.hostTuneCents / 1200.0);
}

std::size_t Press78Engine::activeVoices() const noexcept {
    std::size_t n = 0;
    for (const auto& v : voices_) if (v.active) ++n;
    return n;
}

int Press78Engine::latencySamples() const noexcept {
    return static_cast<int>(std::ceil(kResamplerDelay * sampleRate_ / kInternalRate));
}

void Press78Engine::buildResampler() noexcept {
    // A causal, normalized Blackman-windowed sinc. Legacy 48k integer samples
    // are passed exactly (apart from the explicit 32-tick delay). Downsampling
    // rolls off before the host Nyquist; it is not the Python offline FIR.
    const double cutoff = sampleRate_ >= chipRate_ ? 1.0 : sampleRate_ / chipRate_ * 0.94;
    for (int p = 0; p <= kSincPhases; ++p) {
        const double frac = static_cast<double>(p) / kSincPhases;
        double sum = 0.0;
        for (int j = 0; j < kSincTaps; ++j) {
            const double x = (j - 31) - frac;
            const double z = pi * x * cutoff;
            const double s = std::abs(z) < 1e-12 ? 1.0 : std::sin(z) / z;
            const double window = std::abs(x) >= 32.0 ? 0.0 : 0.42 + 0.5 * std::cos(pi * x / 32.0) + 0.08 * std::cos(tau * x / 32.0);
            sinc_[p][j] = cutoff * s * window;
            sum += sinc_[p][j];
        }
        for (double& x : sinc_[p]) x /= sum;
    }
}

double Press78Engine::synthesizeTick() noexcept {
    applyPendingChipRate();
    applyPendingAllocationModel();
    applyPendingKeyLevelModel();
    applyPendingPitchModel();
    applyPendingSustainMode();
    // Tune smoothing is clocked with the envelopes/operators. Clock offset
    // changes the arrival of these ticks, including feedback and the LFO.
    const double smooth = tickSmoothing_;
    pitchMultiplier_ += (targetPitch_ - pitchMultiplier_) * smooth;
    voiceControls_.modulationAmount += (controls_.modulationAmount - voiceControls_.modulationAmount) * smooth;
    voiceControls_.velocitySensitivity += (controls_.velocitySensitivity - voiceControls_.velocitySensitivity) * smooth;
    voiceControls_.velocityToModulation += (controls_.velocityToModulation - voiceControls_.velocityToModulation) * smooth;
    voiceControls_.vibratoDepth += (controls_.vibratoDepth - voiceControls_.vibratoDepth) * smooth;
    voiceControls_.tremoloDepth += (controls_.tremoloDepth - voiceControls_.tremoloDepth) * smooth;
    voiceControls_.lfoRateHz += (controls_.lfoRateHz - voiceControls_.lfoRateHz) * smooth;
    voiceControls_.lfoDelayScale = controls_.lfoDelayScale;
    voiceControls_.triangleLfo = controls_.triangleLfo;
    voiceControls_.globalLfo = controls_.globalLfo;
    voiceControls_.envelopeReverb = controls_.envelopeReverb;
    if (--portamentoCountdown_ <= 0) {
        portamentoCountdown_ = portamentoServiceTicks_;
        servicePortamento();
    }
    const double global = std::sin(globalLfoPhase_);
    double sum = 0.0;
    for (auto& voice : voices_) if (voice.active) sum += voice.next(voiceControls_, pitchMultiplier_, global);
    for (auto& tail : tails_) if (tail.remaining > 0) {
        sum += tail.voice.next(voiceControls_, pitchMultiplier_, global) * (tail.remaining - 1) / (fadeTicks_ - 1.0);
        --tail.remaining;
    }
    globalLfoPhase_ = std::fmod(globalLfoPhase_ + tau * voiceControls_.lfoRateHz / chipRate_, tau);
    return sum;
}

double Press78Engine::historyAt(std::int64_t tick) const noexcept {
    if (tick < 0 || tick >= nextTick_ || tick < nextTick_ - static_cast<std::int64_t>(kHistory)) return 0.0;
    return history_[static_cast<std::size_t>(tick) % kHistory];
}

double Press78Engine::resampled(double position) const noexcept {
    const double center = position - resamplerDelay_;
    const auto base = static_cast<std::int64_t>(std::floor(center));
    const double fraction = center - std::floor(center);
    if (sampleRate_ >= chipRate_ && fraction < 1e-12) return historyAt(base);
    const double phase = fraction * kSincPhases;
    const int p = std::min(kSincPhases - 1, static_cast<int>(phase));
    const double mix = phase - p;
    double value = 0.0;
    for (int j = 0; j < kSincTaps; ++j) {
        const double coefficient = sinc_[p][j] + mix * (sinc_[p + 1][j] - sinc_[p][j]);
        value += historyAt(base + j - 31) * coefficient;
    }
    return value;
}

double Press78Engine::readDelay(double samples) const noexcept {
    samples = std::clamp(samples, 1.0, static_cast<double>(kDelaySize - 2));
    const auto whole = static_cast<std::size_t>(samples);
    const double fraction = samples - static_cast<double>(whole);
    const auto a = (delayWrite_ + kDelaySize - whole) % kDelaySize;
    const auto b = (a + kDelaySize - 1) % kDelaySize;
    return delay_[a] + fraction * (delay_[b] - delay_[a]);
}

void Press78Engine::output(double mono, double& left, double& right) noexcept {
    // Always advance the selected headroom and related-hardware small-signal
    // circuit, including during bypass, to avoid stale filter memory.
    // A sagging +5 V narrows the mixer's window (AmplifierCircuit.h). A tenth
    // of it stays past the point where the keyboard would have reset.
    const double above = std::max(0.1 * hardware_character::kHeadroom, hardware_character::kHeadroom - amplifier_.mixerLossAbove());
    const double below = std::max(0.1 * hardware_character::kHeadroom, hardware_character::kHeadroom - amplifier_.mixerLossBelow());
    const double circuit = analog_.process(hardware_character::output(mono, above, below));
    circuitMix_ += ((controls_.outputCircuit ? 1.0 : 0.0) - circuitMix_) * gainSmoothing_;
    mono += circuitMix_ * (circuit - mono);
    currentToneCoefficient_ += (toneCoefficient_ - currentToneCoefficient_) * gainSmoothing_;
    drive_ += (controls_.drive - drive_) * gainSmoothing_;
    chorusMix_ += (controls_.chorusMix - chorusMix_) * gainSmoothing_;
    chorusRate_ += (controls_.chorusRateHz - chorusRate_) * gainSmoothing_;
    chorusDepth_ += (controls_.chorusDepthMs - chorusDepth_) * gainSmoothing_;
    recordedChorusMix_ += (static_cast<double>(controls_.chorusMode) - recordedChorusMix_) * gainSmoothing_;
    chorusCircuitMix_ += (static_cast<double>(controls_.chorusCircuit) - chorusCircuitMix_) * gainSmoothing_;
    width_ += (controls_.stereoWidth - width_) * gainSmoothing_;
    if (controls_.toneCutoffHz != 0.0) {
        tone1_ += currentToneCoefficient_ * (mono - tone1_);
        tone2_ += currentToneCoefficient_ * (tone1_ - tone2_);
        mono = tone2_;
    } else { tone1_ = tone2_ = mono; }
    if (drive_ > 0.0) {
        // Crossfade from the exact bypass to saturation so tiny drive values
        // approach the dry signal continuously instead of a hard tanh switch.
        const double amount = 1.0 + 15.0 * drive_;
        mono += drive_ * (std::tanh(mono * amount) / amount - mono);
    }
    delay_[delayWrite_] = mono;
    const double depth = chorusDepth_ * 0.001 * sampleRate_;
    const double base = 0.012 * sampleRate_;
    const double a = readDelay(base + depth * std::sin(chorusPhase_));
    const double b = readDelay(base + depth * std::sin(chorusPhase_ + pi * 0.5));
    double side = 0.5 * (a - b) * chorusMix_ * width_, sideRight = side;
    // The sibling wet-path filters always run, so switching them or the mode
    // never replays stale filter memory.
    const double recordedMs = RecordedChorus::delayMilliseconds(chorusPhase_, chorusDepth_);
    double filteredRight = 0.0;
    const double filtered = chorusCircuit_.process(
        readDelay((recordedMs * 0.001 - chorusCircuit_.delaySeconds()) * sampleRate_), filteredRight);
    // Mode0 retains the original arithmetic path exactly. The recorded mode
    // is an effective transfer, not the physical BBD or the acausal v4 FIR.
    if (recordedChorusMix_ > 0.0) {
        const double plain = readDelay(recordedMs * 0.001 * sampleRate_);
        const double wet = plain + chorusCircuitMix_ * (filtered - plain);
        const double wetRight = plain + chorusCircuitMix_ * (filteredRight - plain);
        const double recorded = RecordedChorus::side(mono, wet) * chorusMix_ * width_;
        const double recordedRight = RecordedChorus::side(mono, wetRight) * chorusMix_ * width_;
        sideRight += recordedChorusMix_ * (recordedRight - sideRight);
        side += recordedChorusMix_ * (recorded - side);
    }
    left = mono + side; right = mono - sideRight;
    delayWrite_ = (delayWrite_ + 1) % kDelaySize;
    chorusPhase_ = std::fmod(chorusPhase_ + tau * chorusRate_ / sampleRate_, tau);
    if (controls_.dcBlock) {
        const double l = left - dcInputL_ + dcCoefficient_ * dcOutputL_;
        const double r = right - dcInputR_ + dcCoefficient_ * dcOutputR_;
        dcInputL_ = left; dcInputR_ = right; dcOutputL_ = l; dcOutputR_ = r;
        left = l; right = r;
    } else { dcInputL_ = left; dcInputR_ = right; dcOutputL_ = dcOutputR_ = 0.0; }
    auxMix_ += ((controls_.outputJack == 1 ? 1.0 : 0.0) - auxMix_) * gainSmoothing_;
    phonesMix_ += ((controls_.outputJack == 2 ? 1.0 : 0.0) - phonesMix_) * gainSmoothing_;
    gain_ += (controls_.masterGain - gain_) * gainSmoothing_;
    amplifier_.process(left, right, auxMix_, phonesMix_, 0.5 * gain_);
    left *= gain_; right *= gain_;
    if (controls_.outputLimit) { left = softBound(left); right = softBound(right); }
    // Parameter clamps already bound the model. This last guard protects the
    // host if an unforeseen numerical fault occurs; it is not per-patch gain.
    if (!std::isfinite(left)) left = 0.0;
    if (!std::isfinite(right)) right = 0.0;
}

void Press78Engine::process(float* left, float* right, std::size_t frames) noexcept {
    if (frames == 0) return;
    for (std::size_t i = 0; i < frames; ++i) {
        while (static_cast<double>(nextTick_) <= position_) {
            history_[static_cast<std::size_t>(nextTick_) % kHistory] = synthesizeTick();
            ++nextTick_;
        }
        double l, r;
        output(resampled(position_), l, r);
        if (left) left[i] = static_cast<float>(l);
        if (right) right[i] = static_cast<float>(r);
        const double ppm = controls_.clockOffsetPpm + controls_.clockDriftPpm * std::sin(tau * controls_.clockDriftRateHz * hostTime_);
        position_ += chipRate_ / sampleRate_ * (1.0 + ppm * 1e-6);
        hostTime_ += 1.0 / sampleRate_;
    }
    hasProcessed_ = true;
}
} // namespace press78
