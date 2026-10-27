// U4 parameter-extremes matrix over the plug-in processor, through the shared
// portfolio harness (Tests/ParameterMatrix.h is a byte-identical copy of the
// master; change it in reason-rack-extensions).
//
//   Press78ParameterMatrixTests [--jobs N] [--rotation] [--shard K/N]
//                               [--case LABEL] [--count] [--list]
//
// The shared command line (U9): --rotation runs each case at one rate and
// block size instead of all nine, --shard K/N runs the cases whose index
// modulo N is K (numbered from 0), --case runs only the case a FAIL line
// names, and --count and --list print the cases and parameters.

#include "PluginProcessor.h"
#include "ParameterMatrix.h"
#include "DSP/HardwareCharacter.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <string>

namespace
{
using protocodus::matrix::Case;
using protocodus::matrix::Limits;

// The envelope law in Source/DSP/Press78Engine.cpp: an operator at rate r
// covers its 96 dB range in 48 * 2^(-r/4) seconds. Key rate scaling only
// speeds it up above middle C, which the matrix chord (60, 64, 67) starts on.
double fullRangeSeconds (double rate) { return 48.0 * std::pow (2.0, -rate / 4.0); }

class Press78Device final : public protocodus::matrix::JuceDevice
{
public:
    Press78Device() : JuceDevice (std::make_unique<Press78AudioProcessor>())
    {
        for (auto* parameter : processor->getParameters())
            if (parameter->isAutomatable())
                if (auto* ranged = dynamic_cast<juce::RangedAudioParameter*> (parameter))
                    columns[ranged->paramID.toStdString()] = { automatable++, ranged };
    }

    Limits LimitsFor (const Case& c) const override
    {
        Limits limits;
        double release = 0.0, gain = 0.0;
        bool limited = true, dcBlocked = true, louderRelease = false;
        // Automation ramps between the case and its base, so each limit takes
        // whichever of the two asks more of it.
        for (const auto* row : { &c.values, &c.base })
        {
            release = std::max (release, releaseSeconds (*row));
            gain = std::max (gain, value (*row, "masterGain"));
            limited = limited && value (*row, "outputLimit") >= 0.5;
            dcBlocked = dcBlocked && value (*row, "dcBlock") >= 0.5;
            louderRelease = louderRelease || tremolo (*row);
        }

        // Output protection bounds every sample to +/-1. Without it, three
        // voices (plus up to three stolen-voice tails) of carrier level 0.8,
        // a stereo width of up to 2 and the output circuit's gain stay below
        // this, scaled by the master gain.
        limits.ceiling = limited ? 1.0001f : static_cast<float> (std::max (1.0, 12.0 * gain));
        // Half-sine and squared waves carry DC that only the DC filter removes.
        if (! dcBlocked)
            limits.dcLimit = limits.ceiling;
        for (const auto* row : { &c.values, &c.base })
            if (silentWhileHeld (*row, limits.silenceFloor))
                limits.soundsWhileHeld = false;
        // An AM LFO can put the held window in a trough and the release on a
        // crest, so such a case waits for silence instead of comparing levels.
        constexpr double longTailSeconds = 6.0;
        limits.releaseSeconds = release <= longTailSeconds || louderRelease ? release : -1.0;
        return limits;
    }

private:
    struct Column { std::size_t index; juce::RangedAudioParameter* parameter; };

    // A row's value of one parameter in its own units. A parameter the rows
    // leave out (not automatable) keeps the processor's current value.
    double value (const std::vector<float>& row, const std::string& id) const
    {
        const auto found = columns.find (id);
        if (found == columns.end())
            return 0.0;
        const auto& column = found->second;
        const float normalised = column.index < row.size() ? row[column.index] : column.parameter->getValue();
        return column.parameter->convertFrom0to1 (normalised);
    }
    int integer (const std::vector<float>& row, const std::string& id) const
    {
        return static_cast<int> (std::lround (value (row, id)));
    }

    // The harness restores the case row by the first block at/after 0.75 s
    // (at most 512/44100 s later), before note-off at 0.8 s. Thus release
    // uses a restored endpoint, not a mixture of rate/sustain/clock rows.
    // Start at 0 dB attenuation, the longest possible remaining release.
    // The selected model uses the ordinary RR/SRR until the 18 dB knee,
    // then the slower of that rate and native RR4. RKS cannot slow either
    // segment for this harness's chord (60, 64, 67).
    double releaseSeconds (const std::vector<float>& row) const
    {
        const int code = integer (row, "sustain") != 0 ? integer (row, "car_srr") : integer (row, "car_rr");
        const double ordinary = fullRangeSeconds (4 * code + 2);
        const double rr4 = fullRangeSeconds (4 * 4 + 2);
        constexpr double kneeFraction = press78::hardware_character::kReleaseKneeDb / 96.0;
        const double envelope = kneeFraction * ordinary
            + (1.0 - kneeFraction) * std::max (ordinary, rr4);
        // Bound the entire reconstruction support (twice its nominal
        // latency), plus two ticks for envelope/tick endpoint rounding.
        constexpr double reconstruction = (2.0 * press78::Press78Engine::kResamplerDelay + 2.0)
            / press78::Press78Engine::kInternalRate;
        const double slowestClock = 1.0
            + (value (row, "clockOffsetPpm") - value (row, "clockDriftPpm")) * 1.0e-6;
        // Keep the existing chorus, 10 Hz DC filter and output-circuit
        // settling allowance; the absolute silence threshold is unchanged.
        return (envelope + reconstruction) / slowestClock + 0.3;
    }

    bool tremolo (const std::vector<float>& row) const
    {
        return integer (row, "ams") > 0 && value (row, "tremoloDepth") > 0.0
            && (integer (row, "car_amEnable") != 0 || integer (row, "mod_amEnable") != 0);
    }

    // The held chord may be silent before note-off by design: a carrier that
    // never attacks, or one whose level, less what its envelope has decayed
    // by the start of the held window, is within twice the silence floor. The
    // loudest voice is the chord's last note (67 at velocity 127, so a level
    // factor of 1), 0.45 s after its note-on when the window opens. Level is
    // 0.8 at TL 0, 0.75 dB per TL step, times master gain. The envelope
    // follows Envelope::next(): attack from 96 dB, exponential in dB, to
    // 1/1000 in 8 * 2^(-AR/4) s; D1 at d1r down to D1L * 3 dB (D1L 15 is
    // 93 dB); then D2 at d2r. Key scaling, which is small a fifth above
    // middle C, is left out.
    bool silentWhileHeld (const std::vector<float>& row, float silenceFloor) const
    {
        const int tl = integer (row, "car_tl"), ar = integer (row, "car_ar");
        if (tl >= 99 || ar == 0)
            return true;
        constexpr double sinceNoteOn = 0.45;
        const double attackSeconds = ar >= 63 ? 0.0 : 8.0 * std::pow (2.0, -ar / 4.0);
        double attenuation = 0.0;
        if (sinceNoteOn < attackSeconds)
            attenuation = 96.0 * std::pow (1000.0, -sinceNoteOn / attackSeconds);
        else
        {
            const double t = sinceNoteOn - attackSeconds;
            const auto dbPerSecond = [] (int rate) { return rate == 0 ? 0.0 : 96.0 / fullRangeSeconds (rate); };
            const int d1l = integer (row, "car_d1l");
            const double target = d1l == 15 ? 93.0 : 3.0 * d1l;
            const double d1 = dbPerSecond (integer (row, "car_d1r")), d2 = dbPerSecond (integer (row, "car_d2r"));
            if (target == 0.0)
                attenuation = d2 * t;
            else if (d1 > 0.0)
                attenuation = d1 * t <= target ? d1 * t : target + d2 * (t - target / d1);
        }
        const double levelDb = 20.0 * std::log10 (0.8 * std::max (value (row, "masterGain"), 1.0e-9)) - 0.75 * tl;
        return attenuation >= 96.0 || levelDb - attenuation < 20.0 * std::log10 (2.0 * silenceFloor);
    }

    std::size_t automatable = 0;
    std::map<std::string, Column> columns;
};
} // namespace

int main (int argc, char** argv)
{
    juce::ScopedJuceInitialiser_GUI juce;
    return protocodus::matrix::Main (argc, argv, [] { return std::make_unique<Press78Device>(); });
}
