# Local supply response and signal-dependent fidelity

The user's lo-fi requirement remains part of the instrument objective: preserve authentic DAC, distortion, component and power behavior while excluding artificial noise. The current b13 noise removal leaves FM feedback, output filtering, chorus, clock controls, creative Drive and output protection intact. The latter two are still explicitly creative/safety transfers; the engine has no calibrated YM3420 nonlinear transfer or voltage-dependent analog/clock coupling. It would be misleading to describe all requested character as already reproduced.

This change adds a real component to the **research circuit model**, without changing the instrument's sound or reinstalling its Rack build. The [Python module](../../Tools/reference/circuit/supply.py) models the sibling OPU's local supply response to externally specified voltage and current changes. It generates no excitation, noise or audio modulation. The [receipt](local-supply-model-2026-10-19.json) retains numerical validation, source hashes and scope.

## Circuit and physical ports

The [original scanner's Yamaha PSS-480 schematic](https://forum.mamedev.org/download/file.php?id=323), drawing KEC-11861, was visually rechecked at the OPU/buffer crop. A 47 ohm resistor connects +5A to **AVDD41**, with 470 uF from that local node to AGND43. VDD40 and VDD39 use +5D. This is a local supply subnetwork from the readable sibling drawing, not the missing PSS-680/780 analog foldout. The internal function and signal-dependent current of this analog rail remain unknown.

For changes relative to an unspecified steady operating point, the ideal network obeys:

```
C d(deltaVlocal)/dt = (deltaVupstream - deltaVlocal)/R - deltaIload
Hsource(s) = 1 / (1 + sRC)
Zload(s)   = -R / (1 + sRC)
```

A positive load-current change lowers the local rail. Nominal R/C give a 22.09 ms time constant and 7.20484 Hz corner. An upstream voltage fluctuation and a changing chip load are separate inputs. Neither input is generated from oscillator activity or voice count by this model.

| Prescribed excitation | Ideal local-network response |
|---|---|
| 50 Hz upstream ripple | −16.916 dB voltage transfer |
| 100 Hz upstream ripple | −22.870 dB voltage transfer |
| 120 Hz upstream ripple | −24.447 dB voltage transfer |
| Extra 1 mA load for 1 ms | −2.080 mV at the interval end |
| Extra 1 mA load for 10 ms | −17.112 mV at the interval end |
| Extra 1 mA held to steady state | −47 mV |

These are unit sensitivities, not measured ripple or load amounts. In particular, −22.870 dB is **not** a PSRR specification or measured audio sideband. Unknown rail sensitivity could affect DAC gain, offset, headroom or timing in different ways; this network alone cannot select any of them.

The module uses the exact continuous solution within each constant-input interval. It does not impose a host-rate bilinear pole, so splitting an interval preserves elapsed physical time. R/C alternatives are explicit scenarios; no undocumented tolerance distribution or random aging is assigned. Capacitor ESR/leakage, supply-return impedance, regulator dropout and upstream adapter/battery behavior remain outside this local model. The separately documented mixer choke/bias and upstream +9 power-amplifier branches must not be replaced with this same pole.

## Checks and remaining evidence

Run:

```sh
python3 Tools/check_supply.py --output build/local-supply-20261019/validation.json
```

All nine checks pass, including under `python3 -S` without site packages. CMake registers the same check as `Press78.LocalSupply`; a fresh local CTest run passes. A separate one-node AC Kirchhoff solve agrees to floating-point precision; an independent RK4 integration of prescribed source/load transitions differs by at most 3.82e-17 V. Additional checks cover steady load, cancellation, elapsed-time partitioning, source/load impedance distinction and invalid inputs. With zero initial state and zero excitation, output is exactly zero. Independent review rechecked the rail tracing, equations, step/corner responses and source bindings. These establish implementation agreement with the stated ideal circuit, not target-instrument fidelity.

Before this can affect production audio, the missing discriminators are the target rail topology, actual operating/load changes, output tap, signal volts and the relevant voltage-to-audio or clock transfer. The exact manual's high-level/chord distortion warning remains useful evidence, but it does not locate the nonlinear stage. Existing Drive cannot supply those missing measurements. No hiss, dither, mains oscillator, random supply movement, bit corruption or generic saturation is added by this work.

A new [firsthand PSR sample-pack lead](https://zlovecraft.bandcamp.com/album/rs-sample-pack-xvii-psr), released January 29, 2026, lists isolated bass/lead samples and identifies YM3420/YM3419. Its author describes recording through modern Focusrite ISA preamps. It supplies no exact instrument model, raw patch, gate log or calibrated level chain. The paid download was not acquired; no audio was measured or fitted from this page. It is an additional source lead, without resolving the DAC or supply transfer.
