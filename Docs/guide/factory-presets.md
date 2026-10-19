# Press78 factory sounds

The factory bank contains 100 original sounds named `PSS 00` through `PSS 99`, 50 newly authored modern sounds, and an independent Init patch. The original sounds keep their b14 parameters.

Use Reason’s standard patch browser. Original `PSS` sounds remain at the bank root; the new sounds are under `Modern`, grouped by Bass, Donk, Pluck, Lead, Pad and FX. All patches retain the output-circuit model and output protection; no added noise is used.

New Reason devices open **BASS - Vowel Engine**, a throaty, rhythmic low bass. Start around MIDI notes 30–42; harder hits add growl, and the mod wheel adds slow pitch wobble. The same unchanged preset is available under `Modern → Bass`. Choose `Init` at the bank root for a clean sine starting point. Existing saved sounds retain their settings. This default selection applies to the Rack Extension; the JUCE plug-in still starts with Init.

The mod wheel adds pitch vibrato. Velocity shapes level and, on these modern sounds, the FM intensity. Pitch bend is configured per patch. LFO rates are free running; they do not follow the project tempo automatically.

The ranges below use MIDI note numbers to avoid octave-name differences between hosts. Most sounds work outside them, but these are the intended playing registers.

## Bass · 12 sounds

| Preset | MIDI range | Sound and playing response |
|---|---:|---|
| BASS - Low Gravity | 28–52 | Round centered sub with a brief soft FM strike and a slowly fading body. No chorus keeps the bottom focused. Velocity: Harder notes add a small rounded attack; the body stays predominantly sine. Wheel: Adds a subtle slow pitch shimmer, leaving the centered low end intact. |
| BASS - Rubber Relay | 31–55 | A two-to-one FM attack contracts into a rounded, lightly saturated bass body for syncopated short notes. Velocity: Velocity opens the rubbery strike considerably while keeping the tail warmer. Wheel: Adds restrained vibrato for held accents. |
| BASS - Split Current | 29–53 | Slightly offset operator tuning and feedback make a moving Reese-like spectrum; a shallow stereo delay widens its edge. Velocity: Harder playing adds more metallic motion without removing the sustained body. Wheel: Introduces gentle pitch movement; it does not change the FM ratio. |
| BASS - Vowel Engine | 30–54 | Three-to-one half-wave FM moves under a per-note amplitude LFO, producing a throaty rhythmic growl over a stable carrier. Velocity: Velocity raises the growl intensity; softer hits expose more of the carrier. Wheel: Adds slow pitch wobble at the same rate as the growl movement. |
| BASS - Alloy Teeth | 31–55 | A seven-to-one modulator puts a hard metallic edge above a short, solid bass envelope. Velocity: Soft hits are rounded; hard hits reveal the upper metallic strike. Wheel: Adds a small pitch flutter for accent notes. |
| BASS - Acid Fuse | 30–55 | Squared-sine operators and strong feedback produce a rasping opening that quickly closes into a narrow pulsing body. Velocity: High velocity brightens the opening rasp; the envelope closes without a filter sweep. Wheel: Adds a narrow fast vibrato; pitch bend gives the larger slides. |
| BASS - Pulse Stencil | 30–54 | Half-squared FM is pulsed by a four-hertz modulator-only LFO, while the low carrier remains continuously present. Velocity: Velocity adds bite to each timbral pulse rather than muting the bass between pulses. Wheel: Adds a modest four-hertz pitch wobble to the pulsing texture. |
| BASS - Hollow Stack | 31–57 | A clean three-to-one sine pair gives an odd-harmonic hollow character with a rounded onset and compact release. Velocity: Velocity moves the tone from almost pure to hollow and woody. Wheel: Adds gentle vibrato for the ends of longer phrases. |
| BASS - Undergrid | 36–60 | A half-rate modulator creates a subharmonic beneath the carrier; its bright attack falls away into a low rubbery tail. Velocity: Harder hits emphasize the subharmonic growl; play an octave above a conventional sub line. Wheel: Adds mild pitch motion without changing the half-rate relationship. |
| BASS - Wire Tension | 32–55 | An offset coarse-tuned modulator leaves an inharmonic wire-like edge around a centered carrier; the edge decays before the body. Velocity: Low velocity gives a clean body; higher velocity reveals the inharmonic attack. Wheel: Adds restrained vibrato suitable for single-note accents. |
| BASS - Pluck Circuit | 30–58 | A fast three-to-one FM pluck with a sustained low residual, voiced for repeated sixteenth-note bass patterns. Velocity: Velocity strongly controls the pluck brightness and moderately controls level. Wheel: Adds vibrato mainly to held residual notes; short plucks stay focused. |
| BASS - Slow Crush | 30–54 | Feedback-rich half-wave FM opens over the first few tens of milliseconds, then moves slowly under a timbral LFO. Velocity: Velocity changes how far the crushed texture opens after the initial low onset. Wheel: Adds slow pitch motion aligned with the timbral LFO. |

## Donk · 8 sounds

| Preset | MIDI range | Sound and playing response |
|---|---:|---|
| DONK - Concrete Knock | 36–60 | A classic short two-to-one FM knock: bright opening, rapidly falling index and a round percussive carrier. Velocity: Harder hits increase the initial knock; the body remains short at every velocity. Wheel: Adds a subtle pitch quiver during the decay. |
| DONK - Hollow Impact | 38–62 | A three-to-one FM thud with a hollow middle and a tighter carrier envelope than Concrete Knock. Velocity: Velocity adds a woody ring to the front of the hit. Wheel: Introduces very small pitch movement; the short body remains percussive. |
| DONK - Glass Hammer | 40–64 | A seven-to-one FM flash falls quickly into a squared-sine body, giving a glassy top without a long bell tail. Velocity: Higher velocity adds glass to the attack; soft notes are rounder and darker. Wheel: Adds a light vibrato to the remaining glassy body. |
| DONK - Timber Trigger | 36–60 | A half-sine modulator gives a woody asymmetric knock with a softer, rounded decay after the first impact. Velocity: Velocity sharpens the wooden impact while leaving the later body mellow. Wheel: Adds a slight vibrato for pitched percussion fills. |
| DONK - Sub Mallet | 48–72 | A half-rate carrier makes a low octave mallet with a brief brighter strike. Play higher than the other donks for a comparable bass register. Velocity: Hard hits emphasize the mallet strike; soft hits become a low rounded pulse. Wheel: Adds very gentle pitch movement to the lower octave. |
| DONK - Laser Knuckle | 38–62 | A coarse-detuned high-ratio strike collapses into a clean short carrier, creating a laser-like metallic click without a pitch envelope. Velocity: Velocity exposes the inharmonic laser edge; lower values leave a cleaner donk. Wheel: Adds a controlled pitch quiver to the brief body. |
| DONK - Rebound | 36–60 | Four-to-one FM drops quickly to a lower index that persists beneath a two-stage carrier decay, giving a knock followed by a rounded after-ring. Velocity: Velocity changes both the knock and the residual FM ring. Wheel: Adds restrained vibrato to the after-ring. |
| DONK - Scrap Bounce | 38–62 | Five-to-one half-squared feedback FM produces a gritty top that decays faster than its compact squared-sine bass body. Velocity: Hard hits add a rough metallic front; softer playing makes the body more rounded. Wheel: Adds a light pitch flutter for accent hits. |

## Pluck · 12 sounds

| Preset | MIDI range | Sound and playing response |
|---|---:|---|
| PLUCK - Kinetic Tine | 48–84 | A crisp harmonic tine with a rounded body for arpeggios and open chords. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.24 Hz vibrato, about 5.5 cents at full wheel; wheel-down has no pitch LFO. |
| PLUCK - Velvet Mallet | 45–81 | A soft woody strike with a short low-mid body and restrained high harmonics. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.24 Hz vibrato, about 3.5 cents at full wheel; wheel-down has no pitch LFO. |
| PLUCK - Glass Thread | 48–79 | An inharmonic glass strike with a clear fundamental and a delicate ringing tail. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.24 Hz vibrato, about 3.9 cents at full wheel; wheel-down has no pitch LFO. |
| PLUCK - Rubber Relay | 36–76 | A tight rubbery twang with a bright snap that settles quickly into a round body. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.24 Hz vibrato, about 7.0 cents at full wheel; wheel-down has no pitch LFO. |
| PLUCK - Copper Drop | 43–79 | A compact metallic strike with a dark fundamental; leave space for the ring. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.24 Hz vibrato, about 5.0 cents at full wheel; wheel-down has no pitch LFO. |
| PLUCK - Pixel Chord | 48–84 | A bright compact keyboard pluck with a hollow edge for rhythmic chords. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.24 Hz vibrato, about 5.5 cents at full wheel; wheel-down has no pitch LFO. |
| PLUCK - Prism Keys | 48–84 | A clean bright key strike with a longer rounded body for melodic chord voicings. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.24 Hz vibrato, about 4.5 cents at full wheel; wheel-down has no pitch LFO. |
| PLUCK - Bamboo Pulse | 43–81 | A hollow woody pluck with a pointed attack for sparse syncopated patterns. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.24 Hz vibrato, about 5.6 cents at full wheel; wheel-down has no pitch LFO. |
| PLUCK - Chrome Pin | 48–76 | A short high-metal click over a pitched body for melodic percussion accents. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.24 Hz vibrato, about 3.5 cents at full wheel; wheel-down has no pitch LFO. |
| PLUCK - Soft Circuit | 36–81 | A rounded slightly gritty pluck with a soft upper edge and solid low register. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.24 Hz vibrato, about 5.5 cents at full wheel; wheel-down has no pitch LFO. |
| PLUCK - Magnet Bell | 45–81 | A bell-like harmonic pluck with a lightly beating metallic edge and clear pitch center. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.24 Hz vibrato, about 3.8 cents at full wheel; wheel-down has no pitch LFO. |
| PLUCK - Afterimage | 48–84 | A wide digital pluck with a bright front edge and a softer gently moving body. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 4.8 Hz vibrato, about 5.0 cents at full wheel; wheel-down has no pitch LFO. |

## Lead · 8 sounds

| Preset | MIDI range | Sound and playing response |
|---|---:|---|
| LEAD - Neon Wire | 48–84 | A focused monophonic lead with a bright nasal edge that rounds off after the attack. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.6 Hz vibrato, about 15.1 cents at full wheel; wheel-down has no pitch LFO. |
| LEAD - Signal Silk | 43–84 | A smooth softly bright polyphonic synth for melodies or close chord voicings. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.1 Hz vibrato, about 7.3 cents at full wheel; wheel-down has no pitch LFO. |
| LEAD - Vector Reed | 43–84 | A reedy lead with a hollow body and a clear articulate attack. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.4 Hz vibrato, about 12.0 cents at full wheel; wheel-down has no pitch LFO. |
| LEAD - Pixel Brass | 43–79 | A compact poly synth with a short FM bloom and a brassy rounded sustain. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.2 Hz vibrato, about 12.4 cents at full wheel; wheel-down has no pitch LFO. |
| LEAD - Spline Solo | 36–84 | A rounded monophonic lead with a slightly beating upper edge and wide bend range. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.8 Hz vibrato, about 12.0 cents at full wheel; wheel-down has no pitch LFO. |
| LEAD - Meteor Square | 43–81 | A dense bright digital lead that also works as a short polyphonic synth stab. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.5 Hz vibrato, about 12.5 cents at full wheel; wheel-down has no pitch LFO. |
| LEAD - Glass Current | 48–84 | A clear sustained synth with high glassy partials and a stable sine-like center. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 5.7 Hz vibrato, about 8.1 cents at full wheel; wheel-down has no pitch LFO. |
| LEAD - Amber Hook | 43–84 | A warm forward lead with a short brassy transient and mellow sustained tone. Velocity: Velocity shapes level and FM brightness; lighter playing softens the attack. Wheel: Adds 4.9 Hz vibrato, about 12.5 cents at full wheel; wheel-down has no pitch LFO. |

## Pad · 6 sounds

| Preset | MIDI range | Sound and playing response |
|---|---:|---|
| PAD - Afterglow | 48–84 | Soft opening harmonics with a rounded fundamental and a long stereo tail. Velocity: Soft strikes stay muted; hard strikes reveal the opening harmonics. Wheel: Slow, restrained vibrato for long chords. |
| PAD - Glass Tides | 52–88 | An airy 3:2 operator interval with slowly settling glass overtones. Velocity: Velocity moves the glass partials forward. Wheel: Adds shimmer to a sustained chord. |
| PAD - Velvet Circuit | 43–79 | A dark squared-sine pad with a gentle breath-like amplitude movement. Velocity: Hard playing adds edge without a sharp attack. Wheel: A gentle pitch movement above the slow amplitude cycle. |
| PAD - Prism Choir | 48–81 | Smooth vocal-like formants made from asymmetric operators and a slow index bloom. Velocity: Harder notes open the vowel-like harmonics. Wheel: Push forward for an animated, singing chord. |
| PAD - Neon Suspension | 48–84 | Bright suspended harmonics with a stable body and widening stereo movement. Velocity: Velocity brings out the bright fifth-related partials. Wheel: Expressive vibrato on long upper notes. |
| PAD - Low Orbit | 36–67 | A slow, low-register drone with beating noninteger overtones and a firm center. Velocity: Velocity changes the density of the beating partials. Wheel: Subtle motion for held drones. |

## FX · 4 sounds

| Preset | MIDI range | Sound and playing response |
|---|---:|---|
| FX - Ion Drop | 36–76 | A short metallic FM laser whose upper partials collapse into a resonant tail. Velocity: Soft hits are hollow; hard hits launch dense metallic partials. Wheel: Adds wide vibrato to sustained retriggers. |
| FX - Broken Beacon | 48–88 | A ringing, inharmonic beacon with a regular tremolo pulse and a long tail. Velocity: Velocity controls the inharmonic strike. Wheel: Bends the ringing beacon into a moving alarm. |
| FX - Phase Flare | 36–76 | An aggressive feedback stab with fading high-frequency energy and a compact tail. Velocity: Hard strikes increase the crunch and spectral density. Wheel: Fast pitch agitation for repeated fills. |
| FX - Gravity Well | 28–60 | A swelling low drone with changing index and slow, exaggerated pitch movement. Velocity: Velocity opens the low, moving texture. Wheel: Increases the depth of the slow pitch orbit. |

These are original Protocodus sound designs made from the editable engine; the modern bank does not copy the PSS factory recipes. The accompanying audio catalog uses the native Rack wrapper and fixed demonstration performances. No per-file normalization is applied.
