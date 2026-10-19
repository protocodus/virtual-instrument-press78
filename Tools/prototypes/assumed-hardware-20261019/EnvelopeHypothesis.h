#pragma once

// Research-only scenario, not an identified YM3420 law. See envelope-notes.md
// and Docs/research/reverb-release-evidence.md for the TX81Z analogy and limits.
#include "../../../Source/DSP/Press78Engine.h"
#include <algorithm>
#include <cmath>

namespace press78::research {

struct AssumedEnvelope {
    // Assumed absolute carrier EG attenuation, before either operator advances.
    // This excludes TL, velocity, AM, output gain and note-off-relative decay.
    static constexpr double kCarrierKneeDb = 18.0;

    template<class Envelope>
    static bool engaged(const Envelope& carrier, bool released,
                        bool researchReverbEnabled) noexcept {
        // The native EG remains in stage 3 once entered, even if a subsequent
        // direct caller passes released=false. Preserve that native behavior.
        return researchReverbEnabled && (released || carrier.stage == 3)
            && std::isfinite(carrier.attenuation)
            && carrier.attenuation >= kCarrierKneeDb;
    }

    template<class Envelope>
    static double next(Envelope& envelope, const Operator& op, int midi,
                       bool released, bool carrierKneeEngaged) noexcept {
        if (!carrierKneeEngaged || (!released && envelope.stage != 3)
            || envelope.disabled || envelope.finished)
            return envelope.next(released);

        const double ordinaryRelease = envelope.release;
        auto capEnvelope = envelope;
        auto capOperator = op;
        capOperator.rr = 4;
        capOperator.srr = 4;
        // Use the unchanged native RR transform, note and RKS. The copy is a
        // coefficient scratch value only; it never clocks a second envelope.
        // At RKS0 this is native RR4 = 45.254834 dB/s, not the earlier RR x3
        // experiment's 15.084945 dB/s. No base timing multiplier is applied.
        capEnvelope.updateRelease(capOperator, midi, false);
        envelope.release = std::min(ordinaryRelease, capEnvelope.release);
        const double value = envelope.next(released);
        // Keep the authoritative ordinary coefficient for live RR/SRR/RKS
        // updates and explicit Reverb-off continuation on the following tick.
        envelope.release = ordinaryRelease;
        return value;
    }
};

} // namespace press78::research
