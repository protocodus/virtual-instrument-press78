"""Frozen recording-calibrated stereo transfer, separate from BBD circuit model.

This accepts an already generated/filtered mono signal as a proposed mid channel.
It predicts side from a globally modulated effective delay and fixed leakage.
It does not identify physical BBD clock, reconstruction filter, or DAC behavior.
"""
from pathlib import Path
from collections.abc import Mapping
import json
import numpy as np

PROFILE_PATH=Path(__file__).with_name('video_chorus_profile.json')

def load_profile():
    return json.loads(PROFILE_PATH.read_text())

def delay_seconds(times,profile=None):
    p=profile if profile is not None else load_profile()
    d=p['delay_ms'];phase=2*np.pi*p['lfo_hz']*np.asarray(times,dtype=float)
    return .001*(d['mean']+d['sin_1']*np.sin(phase)+d['cos_1']*np.cos(phase)
                 +d['sin_2']*np.sin(2*phase)+d['cos_2']*np.cos(2*phase))

def process_calibrated_chorus(mono,sample_rate,*,start_seconds=0.,profile=None):
    """Return samples x 2 stereo without peak normalization.

    start_seconds controls the single global LFO phase. Use absolute reference
    time for comparisons, or any continuous time base for a new performance.
    A standalone clip has zero input history; prepend at least 3ms when slicing
    a continuous render, then trim. This function preserves its proposed input
    as the arithmetic mid channel, by construction, not as a hardware claim.
    Calibration concerns 100–4000Hz; behavior outside that band is extrapolated.
    """
    x=np.asarray(mono,dtype=float)
    if x.ndim!=1:raise ValueError('Expected mono samples, not an existing stereo signal')
    if not np.isfinite(sample_rate) or sample_rate<=0:raise ValueError('sample_rate must be positive')
    if not np.isfinite(start_seconds) or not np.all(np.isfinite(x)):raise ValueError('Inputs must be finite')
    p=profile if profile is not None else load_profile()
    t=start_seconds+np.arange(len(x))/sample_rate
    d=delay_seconds(t,p)
    if np.any(d<0):raise ValueError('Profile has noncausal negative delay')
    wet=np.interp(t-d,t,x,left=0.,right=0.) if len(x) else x.copy()
    side=p['wet_gain']*wet+p['mid_leak_gain']*x
    return np.column_stack((x+side,x-side))
