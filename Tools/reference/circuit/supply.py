"""Incremental PSS-480 OPU local supply, not a PSS-780 audio transfer.

KEC-11861 shows +5A -> 47 ohm -> AVDD41, with 470 uF to
AGND43. This models that local network alone, relative to an unspecified
operating point. Inputs are externally supplied changes in upstream volts
and chip load amperes; there is no noise, oscillator, audio follower or
invented load generator. No DAC voltage sensitivity is asserted.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class LocalSupply:
    """Ideal R/C nominal values; alternatives are explicit scenarios.

    Does not model capacitor ESR/leakage, regulator dropout, shared return
    impedance, the mixer choke/bias network or the upstream +9 amplifier.
    A positive current delta means increased load and reduces the local rail.
    """
    resistance_ohm: float = 47.0
    capacitance_farad: float = 470e-6

    def __post_init__(self):
        for value in (self.resistance_ohm, self.capacitance_farad):
            if not math.isfinite(value) or value <= 0:
                raise ValueError('Finite positive R and C required')
        if (not math.isfinite(self.time_constant_seconds)
                or self.time_constant_seconds <= 0):
            raise ValueError('Representable positive RC product required')

    @property
    def time_constant_seconds(self):
        return self.resistance_ohm * self.capacitance_farad

    def transfer(self, frequency_hz):
        """Return (dVlocal/dVupstream, dVlocal/dIload) at continuous f.

        The second complex quantity is in ohms and includes the minus sign.
        This is not an audio gain, PSRR measurement or clock sensitivity.
        """
        if not math.isfinite(frequency_hz) or frequency_hz < 0:
            raise ValueError('Finite nonnegative frequency required')
        omega_tau = 2 * math.pi * frequency_hz * self.time_constant_seconds
        source = (0j if math.isinf(omega_tau)
                  else 1 / complex(1, omega_tau))
        return source, -self.resistance_ohm * source

    def advance(self, local_delta_v, upstream_delta_v, load_delta_a,
                duration_seconds):
        """Exact end state for one constant-input interval (zero-order hold).

        All voltages/currents are deltas, not absolute supply measurements.
        The caller specifies the physical excitation. Zero excitation and
        zero initial state stay exactly zero, for any interval length.
        """
        values = (local_delta_v, upstream_delta_v, load_delta_a,
                  duration_seconds)
        if not all(math.isfinite(value) for value in values):
            raise ValueError('Finite state, excitation and duration required')
        if duration_seconds < 0:
            raise ValueError('Nonnegative duration required')
        if duration_seconds == 0:
            return local_delta_v
        target = upstream_delta_v - self.resistance_ohm * load_delta_a
        if not math.isfinite(target):
            raise ValueError('Representable target voltage required')
        amount = -math.expm1(-duration_seconds / self.time_constant_seconds)
        # Convex form avoids overflow of (target - initial) for opposite signs.
        result = (1 - amount) * local_delta_v + amount * target
        if not math.isfinite(result):
            raise ValueError('Representable output voltage required')
        return result
