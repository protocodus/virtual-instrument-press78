"""Prospectively bound engineering audition; never a hardware fidelity score."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import scipy
from scipy.io import wavfile
from scipy.signal import resample_poly, stft

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v): p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def bind(out):
    if out.exists(): raise ValueError('Do not overwrite a frozen design')
    paths = sorted((ROOT/'Source/DSP').glob('*.h')) + [ROOT/'Source/DSP/Press78Engine.cpp']
    paths += [HERE/x for x in ['FixedOutputBus.h','GuardedOutputBus.h','KernelTable.h','Audition.cpp','run_audition.py']]
    design = {'schema':'press78.fixed-output-audition.v1','scope':'Host-rate consistency against unchanged b13 48k model; NOT hardware accuracy.',
      'presets':[65,93,97],'rates':[44100,48000,96000],'duration_seconds':7,
      'events':[[.25,60,100],[1.5,60,0],[2.25,48,95],[2.25,55,100],[2.25,60,105],[3.75,48,0],[3.75,55,0],[3.75,60,0],[4.25,67,100],[4.75,67,0]],
      'controls':'NativeRender --real defaults: Original pitch/Sustain, 20ppm hypothetical clock drift, recorded chorus, analog filter, gain .25, tone14k, DC/limit enabled; no added noise/drive.',
      'score_window_seconds':[.25,6.75], 'analysis_and_listening_rate':48000,
      'alignment':'Remove ONLY declared candidate extra SRC delay:105 ticks at44.1k,96 at96k. Common32tick base delay retained. No fitted lag/gain/pitch.',
      'resample':'scipy.signal.resample_poly, Kaiser beta12, padtype constant; float64 analysis.',
      'level':'Unity post-render gain for all clips; no normalization.',
      'metrics':'Stereo/channel NRMSE; STFT1024/hop256 joint log magnitude RMS over reference bins >-60dB relative global peak,100..16000Hz. No perceptual or hardware interpretation.',
      'prospective_checks':'All six non48 preset/rate candidate NRMSEs lower than old; all three48 renders byte-identical; all raw output finite. Retain all adverse results.',
      'sources':{str(p.relative_to(ROOT)):digest(p) for p in paths},
      'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}}
    save(out,design)
def metrics(y,reference):
    a,b=[int(x*48000) for x in [.25,6.75]]; x=y[a:b];r=reference[a:b]
    relative=np.sqrt(np.sum((x-r)**2,axis=0)/np.maximum(np.sum(r*r,axis=0),1e-30))
    joint=float(np.sqrt(np.sum((x-r)**2)/max(np.sum(r*r),1e-30)))
    f,_,zr=stft(r,fs=48000,nperseg=1024,noverlap=768,axis=0,boundary=None,padded=False)
    _,_,zy=stft(x,fs=48000,nperseg=1024,noverlap=768,axis=0,boundary=None,padded=False)
    ar=np.abs(zr);ay=np.abs(zy); mask=(ar>ar.max()*1e-3)&((f>=100)&(f<=16000))[:,None,None]
    delta=20*np.log10(np.maximum(ay[mask],1e-30)/ar[mask])
    return {'channel_nrmse':relative.tolist(),'joint_nrmse':joint,'joint_stft_logmag_rms_db':float(np.sqrt(np.mean(delta*delta))),'qualified_stft_bins':int(mask.sum())}
def run(design_path,out):
    d=json.loads(design_path.read_text())
    for p,h in d['sources'].items():
        if digest(ROOT/p)!=h: raise ValueError('Changed binding: '+p)
    if out.exists() or not out.resolve().is_relative_to((ROOT/'build').resolve()): raise ValueError('Fresh build directory required')
    out.mkdir(parents=True);save(out/'design.json',d)
    command=['c++','-std=c++17','-O3','-Wall','-Wextra','-Wpedantic','-I'+str(HERE),'-I'+str(ROOT/'Source/DSP'),str(HERE/'Audition.cpp'),str(ROOT/'Source/DSP/Press78Engine.cpp'),'-o',str(out/'audition')]
    compile_result=subprocess.run(command,capture_output=True,text=True)
    (out/'compile.log').write_text(compile_result.stdout+compile_result.stderr);compile_result.check_returncode()
    rows=[];audio={};metadata=[];links=[]
    for preset in d['presets']:
        for rate in d['rates']:
            for mode in ['old','candidate']:
                name=f'pss{preset}-{rate}-{mode}';path=out/(name+'-native.wav')
                result=subprocess.run([str(out/'audition'),mode,str(path),str(rate),str(preset)],capture_output=True,text=True,check=True)
                meta=json.loads(result.stdout);meta.update(mode=mode,path=path.name,sha256=digest(path));metadata.append(meta)
                sr,raw=wavfile.read(path);assert sr==rate and raw.shape==(rate*7,2) and np.isfinite(raw).all()
                y=raw.astype(np.float64)
                if rate!=48000:
                    divisor=math.gcd(rate,48000);y=resample_poly(y,48000//divisor,rate//divisor,axis=0,window=('kaiser',12.),padtype='constant')
                delay=(105 if rate==44100 else 96) if mode=='candidate' and rate!=48000 else 0
                if delay:y=np.pad(y[delay:],((0,delay),(0,0)))
                audio[preset,rate,mode]=y
                audition=out/(name+'.wav');wavfile.write(audition,48000,y.astype(np.float32));links.append((preset,rate,mode,audition.name))
        ref=audio[preset,48000,'old']
        for rate in d['rates']:
            for mode in ['old','candidate']:
                rows.append({'preset':preset,'rate':rate,'mode':mode,**metrics(audio[preset,rate,mode],ref)})
    exact=[{'preset':p,'exact':np.array_equal(audio[p,48000,'old'],audio[p,48000,'candidate'])} for p in d['presets']]
    pairs=[]
    for p in d['presets']:
        for rate in [44100,96000]:
            old=next(x for x in rows if (x['preset'],x['rate'],x['mode'])==(p,rate,'old'))
            new=next(x for x in rows if (x['preset'],x['rate'],x['mode'])==(p,rate,'candidate'))
            pairs.append({'preset':p,'rate':rate,'old_nrmse':old['joint_nrmse'],'candidate_nrmse':new['joint_nrmse'],'lower':new['joint_nrmse']<old['joint_nrmse']})
    receipt={'schema':'press78.fixed-output-audition-result.v1','design_sha256':digest(design_path),'renderer_sha256':digest(out/'audition'),'compile_command':command,
      'passed':all(x['exact'] for x in exact) and all(x['lower'] for x in pairs),'48k_identity':exact,'comparisons':pairs,'metrics':rows,'native_files':metadata,
      'scope':d['scope'],'listening_alignment':d['alignment'],'no_noise_added':True}
    save(out/'result.json',receipt)
    parts=['<!doctype html><meta charset="utf-8"><title>Press78 host-rate audition</title><style>body{background:#25282b;color:#eee;font:16px system-ui;max-width:1000px;margin:40px auto}table{width:100%;border-collapse:collapse}td,th{padding:12px;border-bottom:1px solid #555}audio{width:260px}small{color:#b8d6d8}</style><h1>Press78 · output consistency</h1><p>Musical models, not hardware recordings. Same phrase and gain. A = b13; B = candidate. Only declared extra conversion delay removed. 48k reference remains unchanged.</p><table><tr><th>Preset / host rate</th><th>A · b13</th><th>B · candidate</th></tr>']
    for p in d['presets']:
        for rate in d['rates']:
            parts.append(f'<tr><td>PSS {p} / {rate} Hz</td>'+''.join(f'<td><audio controls preload="none" src="pss{p}-{rate}-{m}.wav"></audio></td>' for m in ['old','candidate'])+'</tr>')
    parts.append('</table><p><small>No normalization, added noise or hardware-fidelity claim. Detailed metrics: <a href="result.json">result.json</a>.</small></p>')
    (out/'report.html').write_text(''.join(parts));print(json.dumps({'passed':receipt['passed'],'comparisons':pairs}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['bind','run']);ap.add_argument('design',type=Path);ap.add_argument('--out',type=Path);args=ap.parse_args()
    if args.action=='bind':bind(args.design)
    else:
        if args.out is None:ap.error('--out required')
        run(args.design,args.out)
