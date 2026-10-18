#include "Press78Engine.h"
#include "RecordedChorus.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace press78 {
namespace {
constexpr double pi = 3.14159265358979323846264338327950288;
constexpr double tau = 2.0 * pi;
constexpr double pmDepth[8] = {0.0, 3.4, 6.7, 10.0, 14.0, 20.0, 40.0, 80.0};
constexpr double amDepth[4] = {0.0, 1.4, 5.9, 11.8};
constexpr double rateScaling[4] = {0.0, 0.0625, 0.125, 0.25};

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
double step(const Operator& op, int note) noexcept {
    const double base = 440.0 * std::pow(2.0, (note - 69) / 12.0);
    const double ratio = op.mul == 0 ? 0.5 : static_cast<double>(op.mul);
    const double cents = (op.dt2 ? 600.0 : 0.0) + op.dt1 * 1.5;
    return tau * base * ratio * std::pow(2.0, cents / 1200.0) / Press78Engine::kInternalRate;
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
    c.velocitySensitivity = bounded(c.velocitySensitivity, 0, 2, 1);
    c.velocityToModulation = bounded(c.velocityToModulation, 0, 2, 0);
    c.modulationAmount = bounded(c.modulationAmount, 0, 2, 1);
    c.polyphony = std::clamp(c.polyphony, 1, 12);
    c.lfoRateHz = bounded(c.lfoRateHz, 0, 30, 6.1);
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

void Press78Engine::Envelope::configure(const Operator& op, int midi, bool sustain) noexcept {
    const double ar = rate(op.ar, op.rks, midi);
    const double d1r = rate(op.d1r, op.rks, midi), d2r = rate(op.d2r, op.rks, midi);
    const double rr = rate(4 * (sustain ? op.srr : op.rr) + 2, op.rks, midi);
    disabled = ar == 0.0;
    instantAttack = ar >= 63.0;
    attackMul = std::exp(-std::log(1000.0) / std::max(1.0, kInternalRate * 8.0 * std::pow(2.0, -ar / 4.0)));
    decay1 = d1r == 0.0 ? 0.0 : 96.0 / (kInternalRate * 48.0 * std::pow(2.0, -d1r / 4.0));
    decay2 = d2r == 0.0 ? 0.0 : 96.0 / (kInternalRate * 48.0 * std::pow(2.0, -d2r / 4.0));
    release = 96.0 / (kInternalRate * 48.0 * std::pow(2.0, -rr / 4.0));
    target = op.d1l == 15 ? 93.0 : op.d1l * 3.0;
}

double Press78Engine::Envelope::next(bool released) noexcept {
    if (disabled || finished) return 0.0;
    if (released) stage = 3;
    if (stage == 0) {
        attenuation = instantAttack ? 0.0 : attenuation * attackMul;
        if (attenuation <= 0.096) { attenuation = 0.0; stage = 1; }
    } else if (stage == 1) {
        // Preserve the frozen model's one D1 step even when target is zero.
        attenuation += decay1;
        if (attenuation >= target) stage = 2;
    } else if (stage == 2) attenuation += decay2;
    else attenuation += release;
    if (attenuation >= 96.0) {
        if (stage != 0) finished = true;
        return 0.0;
    }
    return std::pow(10.0, -std::max(0.0, attenuation) / 20.0);
}

void Press78Engine::Voice::configure(const Patch& p, int midi, int vel, std::uint64_t serial) noexcept {
    *this = Voice{};
    note = midi; velocity = vel / 127.0; age = serial;
    active = true; held = true;
    updatePatch(p);
}

void Press78Engine::Voice::updatePatch(const Patch& p) noexcept {
    patch = p;
    modEnvelope.configure(p.modulator, note, p.sustain);
    carrierEnvelope.configure(p.carrier, note, p.sustain);
    modStep = step(p.modulator, note); carrierStep = step(p.carrier, note);
    modGain = level(p.modulator, note); carrierGain = level(p.carrier, note) * 0.8;
    feedback = p.feedback == 0 ? 0.0 : 4.0 * pi * std::pow(2.0, p.feedback - 7);
}

double Press78Engine::Voice::next(const Controls& c, double pitchMultiplier, double globalLfo) noexcept {
    if (!active) return 0.0;
    const double em = modEnvelope.next(released), ec = carrierEnvelope.next(released);
    if (carrierEnvelope.finished || (carrierEnvelope.disabled && released)) {
        active = false; return 0.0;
    }
    double lfo = c.globalLfo ? globalLfo : std::sin(lfoPhase);
    if (c.triangleLfo) lfo = 2.0 / pi * std::asin(std::clamp(lfo, -1.0, 1.0));
    const double delay = std::round(patch.vibratoDelay * 0.01 * c.lfoDelayScale * kInternalRate);
    const double cents = patch.vibrato && static_cast<double>(ticks) >= delay ? pmDepth[patch.pms] * c.vibratoDepth * lfo : 0.0;
    const double pitch = pitchMultiplier * std::pow(2.0, cents / 1200.0);
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
        * ec * carrierGain * std::pow(velocity, c.velocitySensitivity) * amC;
    lfoPhase = std::fmod(lfoPhase + tau * c.lfoRateHz / kInternalRate, tau);
    ++ticks;
    return y;
}

Press78Engine::Press78Engine() noexcept : patch_(initPatch()) { prepare(48000.0); }

void Press78Engine::prepare(double sampleRate) noexcept {
    sampleRate_ = bounded(sampleRate, 8000.0, 192000.0, 48000.0);
    buildResampler();
    analog_.prepare(sampleRate_);
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
    position_ = 0.0; nextTick_ = 0; hostTime_ = 0.0;
    globalLfoPhase_ = 0.0; chorusPhase_ = 0.0;
    gain_ = controls_.masterGain; pitchMultiplier_ = targetPitch_;
    voiceControls_ = controls_;
    currentToneCoefficient_ = toneCoefficient_;
    circuitMix_ = controls_.outputCircuit ? 1.0 : 0.0;
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
    patch_ = sanitizePatch(patch);
    if (updateActive) for (auto& voice : voices_) if (voice.active) voice.updatePatch(patch_);
}

void Press78Engine::setChorusTime(double seconds) noexcept {
    seconds = bounded(seconds, -1e6, 1e6, 0.0);
    chorusPhase_ = std::fmod(tau * chorusRate_ * seconds, tau);
    if (chorusPhase_ < 0.0) chorusPhase_ += tau;
}

void Press78Engine::setControls(const Controls& controls) noexcept {
    controls_ = sanitizeControls(controls);
    targetPitch_ = std::pow(2.0, (controls_.pitchBendSemitones * 100.0 + controls_.masterTuneCents) / 1200.0);
    toneCoefficient_ = controls_.toneCutoffHz == 0.0 ? 0.0
        : 1.0 - std::exp(-tau * std::min(controls_.toneCutoffHz, sampleRate_ * 0.45) / sampleRate_);
    if (!hasProcessed_) {
        gain_ = controls_.masterGain; pitchMultiplier_ = targetPitch_; voiceControls_ = controls_;
        currentToneCoefficient_ = toneCoefficient_;
        circuitMix_ = controls_.outputCircuit ? 1.0 : 0.0;
        recordedChorusMix_ = static_cast<double>(controls_.chorusMode);
        drive_ = controls_.drive; chorusMix_ = controls_.chorusMix;
        chorusRate_ = controls_.chorusRateHz; chorusDepth_ = controls_.chorusDepthMs;
        width_ = controls_.stereoWidth;
    }
    while (activeVoices() > static_cast<std::size_t>(controls_.polyphony)) {
        Voice* victim = nullptr;
        for (auto& v : voices_) if (v.active && (!victim || v.age < victim->age)) victim = &v;
        if (!victim) break;
        auto* tail = &tails_[0];
        for (auto& t : tails_) if (t.remaining < tail->remaining) tail = &t;
        tail->voice = *victim; tail->remaining = 48; victim->active = false;
    }
}

void Press78Engine::noteOn(int note, int velocity, int source) noexcept {
    note = std::clamp(note, 0, 127);
    if (velocity <= 0) { noteOff(note, source); return; }
    velocity = std::min(velocity, 127);
    if (patch_.carrier.tl >= 99 || patch_.carrier.ar == 0) return;
    Voice* target = nullptr;
    if (activeVoices() < static_cast<std::size_t>(controls_.polyphony)) {
        for (auto& v : voices_) if (!v.active) { target = &v; break; }
    }
    if (!target) {
        for (auto& v : voices_) if (v.active && (!target || v.age < target->age)) target = &v;
        if (!target) target = &voices_[0];
        auto* tail = &tails_[0];
        for (auto& t : tails_) if (t.remaining < tail->remaining) tail = &t;
        tail->voice = *target; tail->remaining = 48;
    }
    target->configure(patch_, note, velocity, ++serial_);
    target->source = source;
}

void Press78Engine::noteOff(int note, int source) noexcept {
    note = std::clamp(note, 0, 127);
    Voice* target = nullptr;
    for (auto& v : voices_) if (v.active && v.held && v.note == note && v.source == source && (!target || v.age < target->age)) target = &v;
    if (target) { target->held = false; target->released = !pedal_; }
}

void Press78Engine::sustainPedal(bool down) noexcept {
    pedal_ = down;
    if (!down) for (auto& v : voices_) if (v.active && !v.held) v.released = true;
}

void Press78Engine::allNotesOff() noexcept {
    for (auto& v : voices_) if (v.active) { v.held = false; v.released = !pedal_; }
}

void Press78Engine::allSoundOff() noexcept {
    for (auto& v : voices_) v.active = false;
    for (auto& t : tails_) t.remaining = 0;
    history_.fill(0.0); delay_.fill(0.0);
    analog_.reset();
    tone1_ = tone2_ = 0.0;
    dcInputL_ = dcInputR_ = dcOutputL_ = dcOutputR_ = 0.0;
    pedal_ = false;
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
    // A causal, normalized Blackman-windowed sinc. Nominal48k integer samples
    // are passed exactly (apart from the explicit32-tick delay). Downsampling
    // rolls off before the host Nyquist; it is not the Python offline FIR.
    const double cutoff = sampleRate_ >= kInternalRate ? 1.0 : sampleRate_ / kInternalRate * 0.94;
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
    // Tune smoothing is clocked with the envelopes/operators. Clock offset
    // changes the arrival of these ticks, including feedback and the LFO.
    constexpr double smooth = 0.00415800184511004; // 1-exp(-1/(48000*.005)).
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
    const double global = std::sin(globalLfoPhase_);
    double sum = 0.0;
    for (auto& voice : voices_) if (voice.active) sum += voice.next(voiceControls_, pitchMultiplier_, global);
    for (auto& tail : tails_) if (tail.remaining > 0) {
        sum += tail.voice.next(voiceControls_, pitchMultiplier_, global) * (tail.remaining - 1) / 47.0;
        --tail.remaining;
    }
    globalLfoPhase_ = std::fmod(globalLfoPhase_ + tau * voiceControls_.lfoRateHz / kInternalRate, tau);
    return sum;
}

double Press78Engine::historyAt(std::int64_t tick) const noexcept {
    if (tick < 0 || tick >= nextTick_ || tick < nextTick_ - static_cast<std::int64_t>(kHistory)) return 0.0;
    return history_[static_cast<std::size_t>(tick) % kHistory];
}

double Press78Engine::resampled(double position) const noexcept {
    const double center = position - kResamplerDelay;
    const auto base = static_cast<std::int64_t>(std::floor(center));
    const double fraction = center - std::floor(center);
    if (sampleRate_ >= kInternalRate && fraction < 1e-12) return historyAt(base);
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
    // Always advance the related-hardware small-signal circuit, including
    // during bypass, so re-enabling it does not expose stale filter memory.
    const double circuit = analog_.process(mono);
    circuitMix_ += ((controls_.outputCircuit ? 1.0 : 0.0) - circuitMix_) * gainSmoothing_;
    mono += circuitMix_ * (circuit - mono);
    currentToneCoefficient_ += (toneCoefficient_ - currentToneCoefficient_) * gainSmoothing_;
    drive_ += (controls_.drive - drive_) * gainSmoothing_;
    chorusMix_ += (controls_.chorusMix - chorusMix_) * gainSmoothing_;
    chorusRate_ += (controls_.chorusRateHz - chorusRate_) * gainSmoothing_;
    chorusDepth_ += (controls_.chorusDepthMs - chorusDepth_) * gainSmoothing_;
    recordedChorusMix_ += (static_cast<double>(controls_.chorusMode) - recordedChorusMix_) * gainSmoothing_;
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
    double side = 0.5 * (a - b) * chorusMix_ * width_;
    // Mode0 retains the original arithmetic path exactly. The recorded mode
    // is an effective transfer, not the physical BBD or the acausal v4 FIR.
    if (recordedChorusMix_ > 0.0) {
        const double delay = RecordedChorus::delayMilliseconds(chorusPhase_, chorusDepth_) * 0.001 * sampleRate_;
        const double recorded = RecordedChorus::side(mono, readDelay(delay)) * chorusMix_ * width_;
        side += recordedChorusMix_ * (recorded - side);
    }
    left = mono + side; right = mono - side;
    delayWrite_ = (delayWrite_ + 1) % kDelaySize;
    chorusPhase_ = std::fmod(chorusPhase_ + tau * chorusRate_ / sampleRate_, tau);
    if (controls_.dcBlock) {
        const double l = left - dcInputL_ + dcCoefficient_ * dcOutputL_;
        const double r = right - dcInputR_ + dcCoefficient_ * dcOutputR_;
        dcInputL_ = left; dcInputR_ = right; dcOutputL_ = l; dcOutputR_ = r;
        left = l; right = r;
    } else { dcInputL_ = left; dcInputR_ = right; dcOutputL_ = dcOutputR_ = 0.0; }
    gain_ += (controls_.masterGain - gain_) * gainSmoothing_;
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
        position_ += kInternalRate / sampleRate_ * (1.0 + ppm * 1e-6);
        hostTime_ += 1.0 / sampleRate_;
    }
    hasProcessed_ = true;
}
} // namespace press78
