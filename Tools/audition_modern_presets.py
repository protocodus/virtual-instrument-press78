#!/usr/bin/env python3
"""Render modern .repatch files through the real CPress78 wrapper and typed SDK5 MOM.

Writes a new, immutable run directory. Numerical QA is not subjective listening,
hardware calibration, an actual Reason session, or a host performance benchmark.
Requires NumPy/SciPy and a locally available verified SDK5/native source tree.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import html
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import numpy as np
from scipy.io import wavfile
from scipy.signal import welch

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEVICE = ROOT.parent / 'reason-rack-extension/press78-20261018/Examples/Press78'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def ratio_db(a, b=1):
    return 20 * math.log10(max(float(a), 1e-15) / max(float(b), 1e-15))


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64)**2)))


def load_helper():
    spec = importlib.util.spec_from_file_location('modern_bank', ROOT/'Tools/modern_bank.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_patch(path, voice, controls):
    tree = ET.parse(path)
    root = tree.getroot()
    properties = root.find('Properties')
    if root.tag != 'JukeboxPatch' or properties is None or properties.get('deviceProductID') != 'cz.protocodus.Press78':
        raise ValueError(f'Incorrect patch identity: {path}')
    obj = properties.find("Object[@name='custom_properties']")
    values = list(obj) if obj is not None else []
    if len(values) != len(controls) or len(controls) != 67:
        raise ValueError(f'Expected all 67 stored values: {path}')
    found = {}
    for item in values:
        name = item.get('property')
        if item.tag != 'Value' or item.get('type') != 'number' or name not in controls or name in found:
            raise ValueError(f'Unknown, duplicate or mistyped property in {path}')
        value = float(item.text)
        row = controls[name]
        expected = voice['parameters'][name] - row['min'] if row['integer'] else (voice['parameters'][name]-row['min'])/(row['max']-row['min'])
        if not math.isfinite(value) or not math.isclose(value, expected, abs_tol=1e-14, rel_tol=1e-13):
            raise ValueError(f'Canonical physical/stored mapping mismatch: {path}:{name}')
        found[name] = value
    if set(found) != set(controls):
        raise ValueError(f'Missing properties: {path}')
    return properties.get('deviceVersion')


def analyze_wave(path, native, profile):
    rate, data = wavfile.read(path)
    if rate != 48000 or data.dtype != np.float32 or data.ndim != 2 or data.shape[1] != 2:
        raise ValueError(f'Not stereo float32/48k: {path}')
    finite = bool(np.isfinite(data).all())
    if not finite:
        return {'finite': False, 'file': str(path)}, data
    a = data.astype(np.float64)
    m = a.mean(axis=1)
    body = a[4800:52800] if profile == 'probe' else a
    end = a[-9600:]
    peak = float(np.max(np.abs(a)))
    note_offs = [e['frame'] for e in native['events'] if e['kind'] == 'note' and e['value'] == 0]
    result = dict(finite=True, frames=len(a), peak=peak, rms=rms(a), body_rms=rms(body),
                  peak_dbfs=ratio_db(peak), body_rms_dbfs=ratio_db(rms(body)),
                  final_200ms_rms=rms(end), final_200ms_relative_db=ratio_db(rms(end), rms(body)),
                  midpoint_retention_db=ratio_db(rms(m), rms(a)),
                  rail_samples=int(np.count_nonzero(np.abs(a) >= 1)),
                  exactly_zero_samples=int(np.count_nonzero(a == 0)),
                  last_noteoff_frame=max(note_offs) if note_offs else None,
                  active_voices_end=native['active_voices_end'], native=native, wav_sha256=sha(path))
    return result, data


def spectrum_feature(data):
    mid=np.asarray(data,dtype=np.float64).mean(axis=1)[4800:52800]
    _, power=welch(mid,fs=48000,nperseg=4096,noverlap=2048)
    frequencies=np.fft.rfftfreq(4096,1/48000)
    edges=np.geomspace(35,18000,65)
    bands=np.array([power[(frequencies>=a)&(frequencies<b)].sum() for a,b in zip(edges[:-1],edges[1:])])
    bands/=max(float(bands.sum()),1e-30)
    return 10*np.log10(np.maximum(bands,1e-10))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device',type=Path,default=DEFAULT_DEVICE)
    parser.add_argument('--sdk',type=Path,default=ROOT.parent/'reason-rack-extension/SDK')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--compiler',default='clang++')
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--ids',nargs='+',help='Explicit subset; report retains subset scope')
    parser.add_argument('--compile-only',action='store_true')
    args=parser.parse_args()
    if not 1<=args.workers<=8: parser.error('--workers must be 1..8')
    device=args.device.resolve(); sdk=args.sdk.resolve()
    sdk_version=(sdk/'version.txt').read_text()
    if 'JukeboxSDK_500_' not in sdk_version or 'TargetVersion=5.0' not in sdk_version:
        raise RuntimeError('Requires verified Jukebox SDK5')
    dsp=device/'Instrument/Source/DSP'
    if not (dsp/'Press78Engine.cpp').is_file():
        dsp=device/'DSP'  # Retained pre-submodule development trees.
    if not (dsp/'Press78Engine.cpp').is_file():
        raise ValueError('Initialize the canonical Instrument submodule before rendering')
    helper=load_helper(); all_voices=helper.load_modern()
    voices=[v for v in all_voices if args.ids is None or v['id'] in args.ids]
    if not voices or (args.ids and set(args.ids)!={v['id'] for v in voices}):
        raise ValueError('Empty or unknown preset selection')
    controls={r['id']:r for r in json.loads((ROOT/'Assets/controls.json').read_text())['controls']}
    patch_paths={v['id']:device/'Resources/Public'/helper.preset_relative_path(v) for v in voices}
    versions={v['id']:validate_patch(patch_paths[v['id']],v,controls) for v in voices}
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    dest=(args.output or ROOT/'build'/f'modern-preset-audition-{stamp}').resolve()
    dest.mkdir(parents=True,exist_ok=False)
    source_files=[Path(__file__).resolve(), ROOT/'Tools/modern_bank.py',ROOT/'Assets/controls.json',
                  device/'Tests/FactoryPresetAudition.cpp',device/'Tests/WrapperHostContract.cpp',device/'Press78.cpp',device/'Press78.h',
                  device/'Parameters.h',device/'ApplyParameters.inc',dsp/'Press78Engine.cpp',
                  *sorted(dsp.glob('*.h')), *sorted((ROOT/'Assets/FactoryBank').glob('modern-*.json')),
                  sdk/'version.txt',sdk/'API/Jukebox.h',sdk/'API/JukeboxTypes.h',*patch_paths.values()]
    source_hashes={str(p):sha(p) for p in source_files}
    protocol=dict(schema='press78.modern-preset-audition.v1',created_utc=datetime.now(timezone.utc).isoformat(),
        scope='Actual generated .repatch loading through native CPress78 and typed SDK5 MOM. No Reason host, subjective listening or hardware accuracy claim.',
        selected_ids=[v['id'] for v in voices],available_modern_count=len(all_voices),rate=48000,
        patch_versions=versions,source_sha256=source_hashes,sdk_version=sdk_version.strip(),
        fixture=dict(probe_seconds=2.5,noteon_seconds=.1,gate_seconds=1.0,phrase_seconds=8.0,idle_seconds=.5,
                     probe_velocity=112,soft_velocity=48,probe_wheel=0,wheel_comparison=1,common_comparison_note=48,
                     note_range='Authored recommended low, integer-floor midpoint and high. Phrase starts at min(midpoint, high-12), clamped to low.'),
        hard_gates=dict(all_properties_loaded=67,finite=True,idle_exact_zero=True,nonzero_recommended_probe_peak=1e-7,
                        maximum_absolute_peak=1.000001,rail_samples_at_or_above_one=0,render_allocations=0,mono_fold_max_error=1e-7),
        warnings=dict(quiet_probe_peak_dbfs=-50,quiet_probe_body_rms_dbfs=-65,velocity_rms_ratio_min=1.05,
                      wheel_relative_rms_min=.002,midpoint_retention_db_min=-12,
                      duplicate_waveform_distance_max=.03,duplicate_spectral_rms_db_max=.5),
        tail_policy='Report final200ms and relative decay without a universal pass/fail; pads and FX may legitimately sustain beyond the probe.',
        output_policy='Raw float32 WAV, original patch gain, no normalization. Each run is a new directory; failed metrics retained before any tuning.')
    write_json(dest/'protocol-frozen.json',protocol)
    binary=dest/'FactoryPresetAudition'
    command=[args.compiler,'-std=c++17','-O2','-Wall','-Wextra','-Werror','-pedantic','-I'+str(sdk/'API'),'-I'+str(device),'-I'+str(dsp.parent),
             str(device/'Tests/FactoryPresetAudition.cpp'),str(device/'Press78.cpp'),str(dsp/'Press78Engine.cpp'),'-o',str(binary)]
    compile_result=subprocess.run(command,text=True,capture_output=True)
    (dest/'compile.log').write_text(compile_result.stdout+compile_result.stderr)
    write_json(dest/'compile.json',dict(command=command,returncode=compile_result.returncode,protocol_sha256=sha(dest/'protocol-frozen.json')))
    if compile_result.returncode: raise RuntimeError(f'Compilation failed; preserved at {dest}')
    def verify_binding():
        changed=[p for p,h in source_hashes.items() if sha(p)!=h]
        if changed: raise RuntimeError('Sources changed during bound run: '+repr(changed))
    verify_binding()
    if args.compile_only:
        print(json.dumps({'compiled':True,'output':str(dest),'binary_sha256':sha(binary)}));return 0
    def render_voice(voice):
        folder=dest/voice['id'];folder.mkdir()
        low,high=voice['recommended_notes'];mid=(low+high)//2
        jobs=[('phrase','phrase',max(low,min(mid,high-12)),112,0,False),
              ('low','probe',low,112,0,False),('mid','probe',mid,112,0,False),('high','probe',high,112,0,False),
              ('soft','probe',mid,48,0,False),('wheel','probe',mid,112,1,False),('mono','probe',mid,112,0,True),
              ('common48','probe',48,112,0,False),('idle','idle',mid,112,0,False)]
        records={};audio={}
        for name,profile,note_number,vel,wheel,mono in jobs:
            path=folder/(name+'.wav')
            cmd=[str(binary),'--patch',str(patch_paths[voice['id']]),'--output',str(path),'--profile',profile,
                 '--category',voice['category'],'--note',str(note_number),'--velocity',str(vel),'--wheel',str(wheel)]
            if mono:cmd.append('--mono')
            proc=subprocess.run(cmd,text=True,capture_output=True)
            (folder/(name+'.log')).write_text(proc.stdout+proc.stderr)
            if proc.returncode: raise RuntimeError(f'{voice["id"]}/{name}: {proc.stderr}')
            native=json.loads(proc.stdout);result,data=analyze_wave(path,native,profile)
            result['command']=cmd;result['relative_path']=str(path.relative_to(dest));records[name]=result;audio[name]=data
        failures=[];warnings=[]
        for name,r in records.items():
            if not r['finite']:failures.append(name+': nonfinite output');continue
            if r['native']['property_count']!=67:failures.append(name+': incomplete patch load')
            if r['peak']>1.000001 or r['rail_samples']!=0:failures.append(name+': output reaches clipping rail')
            if r['native']['render_allocations']!=0:failures.append(name+': render allocation')
            if name in ('low','mid','high'):
                if r['peak']<=1e-7:failures.append(name+': silent recommended note')
                if r['peak_dbfs'] < -50 or r['body_rms_dbfs'] < -65:warnings.append(name+': quiet recommended note')
            if name!='idle' and r['midpoint_retention_db'] < -12:warnings.append(name+': low mono retention')
        if records['idle']['peak']!=0:failures.append('idle: nonzero idle signal')
        high_audio=audio['mid'].astype(np.float64);soft=audio['soft'].astype(np.float64);wheel=audio['wheel'].astype(np.float64)
        velocity_ratio=records['mid']['body_rms']/max(records['soft']['body_rms'],1e-30)
        wheel_difference=rms(wheel-high_audio)/max(rms(high_audio),1e-30)
        mono_expected=(audio['mid'][:,0]+audio['mid'][:,1])*.5
        mono_error=float(np.max(np.abs(audio['mono']-mono_expected[:,None])))
        if mono_error>1e-7:failures.append('mono: wrapper fold mismatch')
        if velocity_ratio<1.05:warnings.append('velocity: RMS response is weak or nonmonotonic; inspect FM timbre')
        if wheel_difference<.002:warnings.append('wheel: small audible-signal difference in this fixed probe')
        result=dict(id=voice['id'],name=voice['name'],category=voice['category'],description=voice['description'],
                    recommended_notes=voice['recommended_notes'],performance=voice['performance'],passed=not failures,
                    failures=failures,warnings=warnings,velocity_rms_ratio=velocity_ratio,velocity_rms_change_db=ratio_db(velocity_ratio),
                    velocity_relative_difference=rms(high_audio-soft)/max(rms(high_audio),1e-30),
                    wheel_relative_difference=wheel_difference,mono_fold_max_error=mono_error,renders=records)
        write_json(folder/'result.json',result)
        return result,audio['common48']
    results=[];common={};run_errors=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending={pool.submit(render_voice,v):v['id'] for v in voices}
        for task in as_completed(pending):
            name=pending[task]
            try:
                result,wave=task.result();results.append(result);common[name]=wave
                print(f'{name}: {"PASS" if result["passed"] else "FAIL"}, {len(result["warnings"])} review warnings',flush=True)
            except Exception as exc:
                run_errors.append(dict(id=name,error=str(exc)));print(f'{name}: ERROR {exc}',flush=True)
    verify_binding()
    order={v['id']:i for i,v in enumerate(voices)};results.sort(key=lambda v:order[v['id']])
    pairs=[];keys=sorted(common);features={k:spectrum_feature(common[k]) for k in keys}
    unit={k:common[k].astype(np.float64).ravel()/max(np.linalg.norm(common[k].astype(np.float64)),1e-30) for k in keys}
    for i,a in enumerate(keys):
        for b in keys[i+1:]:
            distance=float(min(np.linalg.norm(unit[a]-unit[b]),np.linalg.norm(unit[a]+unit[b])))
            band_rms=float(np.sqrt(np.mean((features[a]-features[b])**2)))
            pairs.append(dict(a=a,b=b,waveform_distance=distance,spectral_rms_db=band_rms,
                              possible_duplicate=distance<.03 and band_rms<.5))
    pairs.sort(key=lambda x:x['waveform_distance'])
    report=dict(schema='press78.modern-preset-audition-results.v1',passed=not run_errors and all(v['passed'] for v in results),
                scope=protocol['scope'],protocol_sha256=sha(dest/'protocol-frozen.json'),binary_sha256=sha(binary),
                source_sha256=source_hashes,preset_count=len(results),render_count=sum(len(v['renders']) for v in results),
                errors=run_errors,warning_count=sum(len(v['warnings']) for v in results),
                possible_duplicate_count=sum(p['possible_duplicate'] for p in pairs),presets=results,pairwise_comparisons=pairs,
                tail_and_listening_review_complete=False)
    write_json(dest/'results.json',report)
    esc=html.escape
    cards=[]
    for v in results:
        warnings='; '.join(v['failures']+v['warnings']) or 'Numerical checks passed; listening review remains separate.'
        cards.append('<article><h2>'+esc(v['name'])+'</h2><p>'+esc(v['description'])+'</p><audio controls preload="none" src="'+esc(v['renders']['phrase']['relative_path'])+'"></audio><p>'+esc(warnings)+'</p><p>Mid peak '+f'{v["renders"]["mid"]["peak_dbfs"]:.1f}'+' dBFS; velocity change '+f'{v["velocity_rms_change_db"]:.1f}'+' dB; mono retention '+f'{v["renders"]["mid"]["midpoint_retention_db"]:.1f}'+' dB.</p><details><summary>Fixed-note comparisons</summary>'+''.join('<p>'+label+'</p><audio controls preload="none" src="'+esc(v['renders'][key]['relative_path'])+'"></audio>' for key,label in [('mid','Velocity112, wheel0'),('soft','Velocity48, wheel0'),('wheel','Velocity112, wheel1'),('low','Recommended low note'),('high','Recommended high note')])+'</details></article>')
    page='<!doctype html><meta charset="utf-8"><title>Press78 modern preset audition</title><style>body{font:16px system-ui;background:#101319;color:#e8ebf1;max-width:1100px;margin:32px auto;padding:0 20px}article{background:#1b222c;padding:22px;margin:18px 0;border-radius:10px}audio{width:min(100%,620px)}summary{cursor:pointer}p{line-height:1.5}</style><h1>Press78 modern preset audition</h1><p>Actual generated .repatch files through the native wrapper and typed SDK5 MOM. Original patch gains; no normalization, additive noise, or hardware fit. Numerical checks do not establish subjective quality or actual Reason-host playback.</p><p>'+str(len(results))+' presets; '+str(report['render_count'])+' WAVs. '+str(report['warning_count'])+' review warnings.</p>'+''.join(cards)
    (dest/'index.html').write_text(page)
    print(json.dumps(dict(output=str(dest),passed=report['passed'],presets=len(results),renders=report['render_count'],warnings=report['warning_count'],results_sha256=sha(dest/'results.json'))))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
