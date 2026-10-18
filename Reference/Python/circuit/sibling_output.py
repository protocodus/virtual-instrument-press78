"""PSS-270 mixer dry-input superposition for bounded sibling experiments.

This adds the dry response of the documented passive mixer to the v3 wet
response, without assuming the missing PSS-780 routing is identical. Upstream
signal and BBD-pin voltage mapping remain explicit experiment assumptions.
"""
import numpy as np
from scipy import signal
from .pss270_chorus import build_post_bbd, discrete_sos


def build_dry_branch():
    """Excite the dry coupling capacitor; ground the BBD output source.

    Reuse the same source node for numerical reduction, rerouting only the two
    coupling capacitors. The ideal-source shunt load has no effect on transfer.
    All physical resistor loading, cross-coupling and opamp dynamics remain.
    """
    c, nodes = build_post_bbd()
    vi, wi, di = (c.index(n) for n in ('bbd_out', 'wet_ac', 'dry_ac'))
    # BBD source end of 0.1 uF now AC-ground; other end unchanged.
    c.C[vi, vi] -= .1e-6
    c.C[vi, wi] += .1e-6
    c.C[wi, vi] += .1e-6
    # Dry end of 4.7 uF now driven instead of AC-ground.
    c.C[vi, vi] += 4.7e-6
    c.C[vi, di] -= 4.7e-6
    c.C[di, vi] -= 4.7e-6
    for part in c.parts:
        if part['name'] == 'P270_BBD_COUPLE':
            part['a'] = '0'
        elif part['name'] == 'P270_DRY_COUPLE':
            part['a'] = 'bbd_out'
    return c, nodes


def process_dry_branch(audio, sample_rate):
    x = np.asarray(audio, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('Finite mono voltage required')
    c, nodes = build_dry_branch()
    return np.column_stack([signal.sosfilt(discrete_sos(c, sample_rate, nodes[s]), x)
                            for s in ('left', 'right')])


def dry_reference_gain():
    """One fixed 1 kHz gain used solely to express auditions in model units."""
    c, nodes = build_dry_branch()
    v = np.linalg.solve(c.G + 2j*np.pi*1000*c.C, c.B)
    return float(abs(v[c.index(nodes['left']), 0]))
