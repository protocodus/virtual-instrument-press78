"""Frozen effective stereo transfer, not an identified PSS-780 BBD circuit.

The input is a proposed recorded mid channel. Global branch FIR coefficients
were fitted only on the six v3 training presets. A fixed bounded blend applies
their correction in 100-4000Hz and returns toward v3 outside that band.

This OFFLINE function uses two-sided FIR context: provide >=32ms input history
and future context when cropping clips. It adds no output delay. A real-time
implementation must delay BOTH mid and side by the required lookahead; this
module is not a zero-latency real-time BBD implementation.
"""
from functools import lru_cache
from pathlib import Path
import json
import numpy as np
from scipy import signal
from .calibrated_chorus import delay_seconds

PROFILE_PATH = Path(__file__).with_name('v4_effective_stereo_profile.json')


@lru_cache(maxsize=1)
def load_profile():
    return json.loads(PROFILE_PATH.read_text())


@lru_cache(maxsize=16)
def correction_kernel(sample_rate):
    """Zero-phase blend with nonnegative frequency response at most one.

The autocorrelation of a real FIR has response |H|² after compensating its
known center. Normalize against a dense frequency-grid maximum, then leave a
small conservative margin. This bounds blending, not total stereo path gain.
"""
    sr = float(sample_rate)
    if not np.isfinite(sr) or sr < 12000:
        raise ValueError('Sample rate must be finite and at least 12kHz')
    p = load_profile()['correction_blend']
    half = round(p['prototype_half_duration_seconds']*sr)
    h = signal.firwin(2*half+1, p['band_hz'], fs=sr, pass_zero=False, window='hann')
    _, response = signal.freqz(h, worN=262144)
    h /= np.max(abs(response)) * (1+1e-6)
    return np.convolve(h, h[::-1])


def _shift(x, samples):
    n = len(x)
    integer = round(samples)
    if abs(samples-integer) < 1e-10:
        y = np.zeros_like(x)
        if integer == 0: return x.copy()
        if abs(integer) >= n: return y
        if integer > 0: y[integer:] = x[:-integer]
        else: y[:integer] = x[-integer:]
        return y
    return np.interp(np.arange(n)-samples, np.arange(n), x, left=0., right=0.)


def process_refined_chorus(mono, sr, start_seconds=0.):
    """Return Nx2 stereo, retaining the input as arithmetic mid, no gain fit.

Use absolute decoded-video seconds for the frozen capture phase. For an
original performance, any continuous time base is valid but not a measured
hardware reset phase. No polynomial distortion or captured noise is added.
    """
    x = np.asarray(mono, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('Finite mono samples required')
    if not np.isfinite(start_seconds): raise ValueError('Finite start time required')
    kernel = correction_kernel(sr)
    if not len(x): return np.empty((0, 2))
    p = load_profile(); v3 = p['v3_profile']
    samples = np.arange(len(x))
    t = start_seconds+samples/float(sr)
    delay = delay_seconds(t, v3)
    if np.any(delay < 0): raise ValueError('Noncausal v3 delay')
    wet = np.interp(samples-delay*sr, samples, x, left=0., right=0.)
    baseline = v3['wet_gain']*wet+v3['mid_leak_gain']*x
    fitted = np.zeros_like(x)
    for source, coefficients in ((wet, p['wet_coefficients']), (x, p['mid_coefficients'])):
        for lag, coefficient in zip(p['tap_seconds'], coefficients):
            fitted += coefficient*_shift(source, lag*sr)
    correction = signal.oaconvolve(fitted-baseline, kernel, mode='same')
    side = baseline+correction
    return np.column_stack((x+side, x-side))
