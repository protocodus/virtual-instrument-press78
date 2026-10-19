#!/usr/bin/env python3
"""Frozen, research-only tonal-line extraction on retained EditingFun supports.

No downloads, production changes, gate inference or hardware envelope fitting.
The protocol and this implementation must be bound before any evaluation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.io import wavfile
from scipy import signal

ROOT = Path(__file__).resolve().parents[1]
RATE = 48000
WINDOWS = {'short': (0., .1), 'extended': (.05, .35)}
OFFSETS = (-175., -125., -75., 75., 125., 175.)


def binding(path):
    path = Path(path)
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


def clean(value):
    if isinstance(value, dict): return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [clean(v) for v in value]
    if isinstance(value, np.ndarray): return clean(value.tolist())
    if isinstance(value, (np.bool_,)): return bool(value)
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


def write(path, value):
    path.write_text(json.dumps(clean(value), indent=2) + '\n')


def frequency(y):
    # One fixed selection from the full union, never optimized for decay fit.
    n = len(y); nfft = 32 * n
    spectrum = np.abs(np.fft.rfft((y-np.mean(y))*np.hanning(n), nfft))
    ff = np.fft.rfftfreq(nfft, 1/RATE)
    ids = np.flatnonzero((ff >= 180) & (ff <= 2000))
    k = int(ids[np.argmax(spectrum[ids])])
    a, b, c = np.log(np.maximum(spectrum[k-1:k+2], 1e-300))
    delta = .5*(a-c)/(a-2*b+c)
    return float((k+np.clip(delta, -.5, .5))*RATE/nfft)


def local(y, center, bounds, frequency_hz, width):
    lo, hi = [round(v*RATE) for v in bounds]
    at = round(center*RATE); half = round(width*RATE/2)
    start, end = max(lo, at-half), min(hi, at+half)
    t = np.arange(start, end)/RATE
    u = (t-center)/width
    w = .5+.5*np.cos(2*np.pi*u)
    cols = [np.ones(len(t)), u]
    for h in range(1, 4):
        cs, sn = np.cos(2*np.pi*h*frequency_hz*t), np.sin(2*np.pi*h*frequency_hz*t)
        for power in (0, 1, 2): cols.extend([u**power*cs, u**power*sn])
    x = np.asarray(cols).T
    sw = np.sqrt(w)
    a = x*sw[:, None]
    coefficients, _, _, sv = np.linalg.lstsq(a, y[start:end]*sw, rcond=None)
    condition = float(sv[0]/sv[-1])
    residual = y[start:end]-x@coefficients
    z = coefficients[2]-1j*coefficients[3]
    off = []
    for offset in OFFSETS:
        f = frequency_hz+offset
        if f < 20 or f >= RATE/2 or min(abs(f-h*frequency_hz) for h in range(1,4)) < 50:
            continue
        q = np.column_stack([np.cos(2*np.pi*f*t), np.sin(2*np.pi*f*t)])
        v = np.linalg.lstsq(q*sw[:, None], residual*sw, rcond=None)[0]
        off.append({'frequency_hz':f, 'residual_line_peak':float(np.hypot(*v))})
    maximum = max((v['residual_line_peak'] for v in off), default=np.inf)
    return {'time':center, 'support_frames':[start,end], 'amplitude':float(abs(z)),
            'phase':float(np.angle(z)), 'condition':condition,
            'offband':off, 'line_above_residual_probe_db':float(20*np.log10(max(abs(z),1e-300)/max(maximum,1e-300))),
            'weighted_residual_fraction':float(np.sum(w*residual**2)/max(np.sum(w*y[start:end]**2),1e-300))}


def fit(rows):
    t = np.array([r['time'] for r in rows]); levels=20*np.log10(np.maximum([r['amplitude'] for r in rows],1e-300))
    x=t-t.mean(); slope=float(x@(levels-levels.mean())/(x@x))
    errors=levels-(levels.mean()+slope*x)
    denom=float(np.sum((levels-levels.mean())**2))
    phase=np.unwrap([r['phase'] for r in rows])
    changes=np.diff(phase)/(2*np.pi*np.diff(t))
    return {'slope_db_per_second':slope, 'r_squared':1-float(errors@errors)/max(denom,1e-300),
            'max_residual_db':float(np.max(abs(errors))),
            'residual_frequency_span_hz':float(np.ptp(changes)),
            'minimum_line_above_residual_probe_db':min(r['line_above_residual_probe_db'] for r in rows),
            'max_condition':max(r['condition'] for r in rows), 'rows':rows}


def measure(y, fixed_frequency=None):
    f=frequency(y) if fixed_frequency is None else fixed_frequency
    result={'frequency_hz':f,'frequency_eligible':180<=f<=2000,'windows':{}}
    for kind, bounds in WINDOWS.items():
        centers=np.linspace(*bounds, round((bounds[1]-bounds[0])/.005)+1)
        variants={str(width):fit([local(y, c, bounds, f, width) for c in centers]) for width in (.02,.04)}
        main=variants['0.04']; other=variants['0.02']
        difference=abs(main['slope_db_per_second']-other['slope_db_per_second'])
        gates={'frequency':result['frequency_eligible'], 'finite_unclipped':bool(np.all(np.isfinite(y)) and np.max(abs(y))<.98),
               'conditioning':max(v['max_condition'] for v in variants.values())<=1e10,
               'linear':all(v['r_squared']>=.99 and v['max_residual_db']<=.5 for v in variants.values()),
               'decaying':all(-120<=v['slope_db_per_second']<=-1 for v in variants.values()),
               'projection_width_agreement':difference<=1.,
               'phase_stationary':all(v['residual_frequency_span_hz']<=2 for v in variants.values()),
               'residual_probe_separation':all(v['minimum_line_above_residual_probe_db']>=20 for v in variants.values())}
        result['windows'][kind]={'variants':variants,'slope_width_difference_db_per_second':difference,
                                'gates':gates,'qualified_tonal_line':all(gates.values())}
    return result


def control(case, speech):
    t=np.arange(round(.35*RATE))/RATE
    envelope=.5*10**(-case['decay']*(t+.05)/20)
    phase=2*np.pi*case['frequency']*t+case['phase']
    y=envelope*(np.sin(phase)+.15*np.sin(2*phase+.3)+.07*np.sin(3*phase-.4))
    if case['kind']=='speech':
        b=np.resize(speech,len(t)).copy(); b/=np.sqrt(np.mean(b*b))
        y+=b*(envelope[0]/np.sqrt(2))*10**(case['speech_relative_rms_db']/20)
    if case['kind']=='nearby-tone': y+=.35*envelope*np.sin(phase+2*np.pi*.7*t+1)
    if case['kind']=='dynamic-gain':y*=10**(12*t/20)
    # Explicitly retained, deterministic PCM16 conversion; no dither.
    return np.clip(np.rint(y*32768),-32768,32767)/32768


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();p=json.loads(args.protocol.read_text());out=args.out.resolve()
    out.relative_to(ROOT/'build');assert not out.exists() and out!=ROOT/'build'
    assert p['implementation']==binding(Path(__file__))
    for row in p['bindings']:assert binding(ROOT/row['path'])==row
    out.mkdir(parents=True);started=time.monotonic()
    write(out/'started.json',{'protocol':binding(args.protocol.resolve()),'implementation':binding(Path(__file__))})
    rate,raw=wavfile.read(ROOT/p['wave']['path'],mmap=True);assert rate==RATE and raw.shape[1]==2 and raw.dtype==np.float32
    # Only the already-declared speech reference is selected for controls here.
    speech=raw[:round(.2*RATE)].astype(float).mean(axis=1)
    controls=[]
    for case in p['controls']:
        y=control(case,speech);m=measure(y)
        truth=-case['decay']+(12 if case['kind']=='dynamic-gain' else 0)
        evaluations=[]
        for kind,row in m['windows'].items():
            error=abs(row['variants']['0.04']['slope_db_per_second']-truth)
            required=case['kind']=='clean'
            passed=(row['qualified_tonal_line'] and error<=.5) if required else (not row['qualified_tonal_line'] or error<=1.)
            evaluations.append({'window':kind,'truth_captured_line_slope':truth,'absolute_error':error,'required_qualification':required,'passed':passed})
        controls.append({'case':case,'measurements':m,'evaluations':evaluations})
    positives=[c for c in controls if c['case']['kind'] in ('clean','speech')]
    qualified=all(v['passed'] for c in positives for v in c['evaluations'])
    write(out/'controls.json',{'passed':qualified,'controls':controls})
    source=[]
    if qualified:
        # Target samples are first selected only after controls pass.
        lo,hi=round(10.1*RATE),round(10.45*RATE)
        union=raw[lo:hi].astype(float); f=frequency(union.mean(axis=1))
        for name,y in [('mid',union.mean(axis=1)),('left',union[:,0]),('right',union[:,1])]:
            source.append({'channel':name,'absolute_union_seconds':[70.10,70.45],
                           'measurements':measure(y,f)})
    result={'schema':'press78.editingfun-tonal-result.v1','protocol':binding(args.protocol.resolve()),
            'implementation':binding(Path(__file__)),'control_qualification':qualified,'control_count':len(controls),
            'control_evaluations':sum(len(c['evaluations']) for c in controls),
            'required_evaluations':sum(len(c['evaluations']) for c in positives),
            'failed_required_evaluations':[{'id':c['case']['id'],**v} for c in positives for v in c['evaluations'] if not v['passed']],
            'real_target_measured':bool(source),'source':source,
            'display31':'All12 prior rows remain rejected for range-edge crop; not decoded or remeasured.',
            'scope':'Selected captured tonal-line slope only. Offband probes measure residual interference, not an independent noise floor. Unknown gates, overlapping notes, effect state and gain dynamics prevent physical EG inference.',
            'controls_artifact':binding(out/'controls.json'),'elapsed_seconds':time.monotonic()-started}
    write(out/'result.json',result)
    print(json.dumps({'passed':qualified,'controls':len(controls),'failed_required':len(result['failed_required_evaluations']),'real_target_measured':bool(source)}))


if __name__=='__main__': main()
