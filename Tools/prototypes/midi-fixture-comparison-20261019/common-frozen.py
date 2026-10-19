#!/usr/bin/env python3
"""Research-only fixed b12 pitch-law comparison. Requires existing local evidence.

freeze records the design before candidate measurements; bind snapshots the final
candidate and runner separately; run never fits or changes events or parameters.
Original recordings and firmware are never downloaded or distributed here.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import time

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
MAPS = ('unchanged', 'old_scale_median_offset', 'nominal_scale_median_intercept', 'equal_patch_robust_affine')
METRICS = ('joint_lr_band_rmse_db', 'mid_band_rmse_db', 'stereo_stft_convergence', 'stereo_stft_log_error_db')
FOCUS = (65, 93, 97)
WHOLE_FNUM = (2394,2537,2688,2847,3017,3196,3386,3588,3801,4027,4266,4520)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()


def read(path): return json.loads(Path(path).read_text())
def write(path, data): Path(path).write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
def record(path): return {'path': str(Path(path).resolve()), 'sha256': sha(path)}
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def verify(item):
    assert sha(item['path']) == item['sha256'], item['path']


def freeze(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    target = out/'design-frozen.json'
    if target.exists(): raise RuntimeError('Preserve existing design; choose a new benchmark subdirectory')
    prior = args.prior.resolve()
    p, result = read(prior/'protocol-frozen.json'), read(prior/'result.json')
    assert tuple(m['id'] for m in p['maps']) == MAPS
    snapshots = out/'snapshots'; snapshots.mkdir()
    for name in ('stereo_metrics.py', 'v4-protocol.json', 'HardwareSequencePressure.cpp'):
        src = prior/'snapshots'/name
        assert sha(src) == p['snapshots'][name]
        shutil.copy2(src, snapshots/name)
    windows = read(snapshots/'v4-protocol.json')['windows']
    assert len(windows)==100 and sorted(w['patch'] for w in windows)==list(range(100))
    inputs = {k:p['inputs'][k] for k in ('recording','notes','timeline','bank')}
    inputs.update({
        'prior_mode00_protocol':record(prior/'protocol-frozen.json'),
        'prior_mode00_result':record(prior/'result.json'),
        'pitch_frequency_report':record(ROOT/'Reference/Research/opu-frequency-hypothesis-20261019.json'),
        'pitch_command_report':record(ROOT/'Reference/Research/opu-pitch-command-path-20261019.json'),
        'baseline_source_manifest':record(args.baseline/'source-frozen.json')})
    for item in inputs.values(): verify(item)
    maps=[]
    for m in p['maps']:
        verify(m['filtered_events'])
        lines=Path(m['filtered_events']['path']).read_text().splitlines()
        assert len(lines)==3622 and sum(' on ' in x for x in lines)==1761 and sum(' patch ' in x for x in lines)==100
        oldaudio=result['models_and_renders'][m['id']+'/baseline']['branches']['mode00']['audio']
        verify(oldaudio)
        maps.append({'id':m['id'],'offset_seconds':m['offset_seconds'],'scale':m['scale'],
                     'events':m['filtered_events'],'expected_equal_audio':oldaudio})
    design={
        'schema':'press78.b12-pitch-law-fixed-comparison.v1','frozen_at_utc':now(),
        'status':'Design frozen before candidate compilation, rendering or scoring',
        'inputs':inputs,'maps':maps,'windows':windows,
        'snapshots':{x.name:sha(x) for x in snapshots.iterdir()},
        'render':p['render'],'events':{'accepted_notes':1761,'events':3622,'programs':100,'excluded_notes':18},
        'timing_and_metric':p['timing_and_metric'],
        'laws':{'Equal':0,'Original':1},
        'unchanged_controls':'Raw33 factory bank, operator DT/ratios/envelopes, internal continuous LFO, Recorded chorus, analog circuit,12 voices,32-frame delay and epoch correction. No bend/fine tune, added noise, envelope/Reverb hypothesis or control fitting.',
        'candidate_frequency':'Audited whole FNUM commands; floor(FNUM*2^(block-3))*5500000/(6*2^24). Downstream floor/timebase remain behavioral hypotheses. No fitted per-unit clock is shipped.',
        'producer_check':{'source_rows':'all63 retained; same62 accepted by prior source eligibility',
                          'nuisance':'Reuse exact prior per-pack candidate cents offsets for both estimators; never refit',
                          'whole_fnum_C_to_B':list(WHOLE_FNUM),'rms_cents_max':0.011,
                          'scope':'Posthoc reused four pitch classes, not a fresh holdout or independent unit count'},
        'gates':{'equal_full_wav_mismatches_allowed':0,'all100_joint_band_mean_delta_max_db':0.03,
                 'each_focus_each_map_joint_band_delta_max_db':0.1,
                 'producer_both_estimators_fixed_nuisance_rms_max_cents':0.011,
                 'audited_command_helper_match_required':True,
                 'external_gates':'CPU, wrapper, packaging, native API and exhaustive command helper validation are separately audited and must not be inferred from audio.'},
        'analysis':'Keep all100 per-preset scores and signed deltas for all4 maps, all four mixed metrics, regressions and focus65/93/97. No selection of map, window, estimator or parameter from results.',
        'audition':'For each focus/window/map: hardware then Equal then Original, 250ms gaps, one RMS scalar per stereo model pair, common safety scalar per focus across all maps/models. No independent channel gain, EQ, timing or pitch fit. Keep local media only.',
        'storage':'Delete only newly rendered Equal temporary WAV after complete historical hash equality. Retain4 Original WAVs and local clips; new WAV bytes <500000000; never delete historical files.',
        'limitations':['The4 maps and all100 windows were already observed;3 alternative maps previously failed timing adoption and remain scenarios.',
                       'Source MIDI identity, observed c.00 continuity and inferred program times remain conditional.',
                       'No new fit, note remap, gate retiming, per-patch correction or artificial noise. Audio scores cannot establish native phase width, divider or envelope law.']}
    write(target,design)
    print(json.dumps({'design':str(target),'sha256':sha(target),'maps':4,'laws':2,'windows':100},indent=2))


def bind(args):
    out=args.output.resolve(); design=read(out/'design-frozen.json')
    if (out/'candidate-bound.json').exists(): raise RuntimeError('Candidate already bound')
    for item in design['inputs'].values(): verify(item)
    source=out/'candidate-source'; shutil.copytree(args.source.resolve(),source)
    # Minimal fixture change: a fixed command-line law, no changes to event parsing,
    # output controls, factory decode, event order, pressure logging or WAV format.
    original=(out/'snapshots/HardwareSequencePressure.cpp').read_text()
    assert original.count('if(argc!=7)')==1
    fixture=original.replace('if(argc!=7)','if(argc!=8)')
    needle='press78::Controls c;c.masterGain=1.;'
    assert fixture.count(needle)==1
    fixture=fixture.replace(needle,'press78::Controls c;c.pitchModel=std::stoi(argv[7]);c.midiPitchBend=-1;c.masterGain=1.;')
    (out/'PitchSequence.cpp').write_text(fixture)
    shutil.copy2(Path(__file__),out/'snapshots/runner-bound.py')
    command_report=read(args.command_validation)
    assert command_report['passed'] and command_report['converter_cases']==49152
    for name, item in command_report['bindings'].items():
        assert sha(ROOT/name)==item['sha256'],name
    assert sha(source/'FirmwarePitch.h')==command_report['bindings']['Source/DSP/FirmwarePitch.h']['sha256']
    bound={'bound_at_utc':now(),'design_sha256':sha(out/'design-frozen.json'),
           'source':{p.name:sha(p) for p in source.iterdir() if p.is_file()},
           'source_directory':str(source),'fixture':record(out/'PitchSequence.cpp'),
           'runner':record(out/'snapshots/runner-bound.py'),
           'command_helper_validation':record(args.command_validation),
           'command_helper_case_count':command_report['converter_cases'],
           'status':'Candidate hash binding before compile/render; no measurement yet'}
    write(out/'candidate-bound.json',bound)
    print(json.dumps(bound,indent=2))


def producer_check(design):
    old=read(design['inputs']['pitch_frequency_report']['path'])
    rows=[]
    for row in old['producer_rows']:
        note=row['expected_musical_midi_under_authored_sequence']
        hz=math.floor(WHOLE_FNUM[note%12]*2.**(note//12-4))*5500000/(6*2**24)
        offset=old['producer_offsets'][row['file']]['candidate']['cents']
        errors={k:1200*math.log2(row[k+'_frequency_hz']/hz)-offset for k in ('fft','phase')}
        rows.append({**row,'original_hz':hz,'reused_nuisance_cents':offset,'original_residuals_cents':errors})
    accepted=[r for r in rows if r['interval_fixture_accepted']]
    assert len(rows)==63 and len(accepted)==62
    summary={k:{'count':len(accepted),'rms_cents':float(np.sqrt(np.mean([r['original_residuals_cents'][k]**2 for r in accepted]))),
                'max_abs_cents':max(abs(r['original_residuals_cents'][k]) for r in accepted)} for k in ('fft','phase')}
    return {'rows':rows,'summary':summary,'passed':all(s['rms_cents']<=0.011 for s in summary.values()),'new_fit':False}


def run(args):
    out=args.output.resolve(); design=read(out/'design-frozen.json'); bound=read(out/'candidate-bound.json')
    if (out/'run-started.json').exists(): raise RuntimeError('Preserve completed or partial run; do not overwrite')
    assert sha(out/'design-frozen.json')==bound['design_sha256']
    assert sha(Path(__file__))==bound['runner']['sha256'],'Runner changed after binding'
    for item in design['inputs'].values(): verify(item)
    for name,h in design['snapshots'].items(): assert sha(out/'snapshots'/name)==h
    source=Path(bound['source_directory'])
    assert {p.name:sha(p) for p in source.iterdir() if p.is_file()}==bound['source']
    verify(bound['fixture']);verify(bound['command_helper_validation'])
    write(out/'run-started.json',{'utc':now(),'candidate_binding_sha256':sha(out/'candidate-bound.json')})
    exe=out/'pitch_sequence'
    cmd=['c++','-std=c++17','-O2','-I',str(source),str(out/'PitchSequence.cpp'),str(source/'Press78Engine.cpp'),'-o',str(exe)]
    subprocess.run(cmd,check=True,capture_output=True,text=True)
    rate,reference=wavfile.read(design['inputs']['recording']['path'],mmap=True)
    assert rate==SR and reference.dtype==np.int16 and reference.shape[1]==2
    model_data={};renders={};max_bytes=0
    for m in design['maps']:
        verify(m['events']); verify(m['expected_equal_audio'])
        folder=out/'maps'/m['id'];folder.mkdir(parents=True)
        model_data[m['id']]={}
        for name,law in design['laws'].items():
            audio=folder/(name+'.wav'); pressure=folder/(name+'-pressure.csv')
            command=[str(exe),m['events']['path'],str(audio),str(design['render']['frames']),str(SR),'recorded',str(pressure),str(law)]
            start=time.perf_counter(); proc=subprocess.run(command,check=True,capture_output=True,text=True)
            detail=json.loads(proc.stdout);detail['wall_seconds']=time.perf_counter()-start
            sr,data=wavfile.read(audio,mmap=True)
            assert sr==SR and data.shape==(design['render']['frames'],2) and np.isfinite(data).all()
            assert detail['events']==3622 and detail['latency_samples']==32
            artifact=record(audio); artifact['frames']=len(data); artifact['peak']=float(np.max(np.abs(data)))
            size=sum(p.stat().st_size for p in out.rglob('*.wav')); max_bytes=max(max_bytes,size);assert size<500000000
            render={'command':command,'render':detail,'audio':artifact,'pressure':record(pressure)}
            if name=='Equal':
                assert artifact['sha256']==m['expected_equal_audio']['sha256'],'Legacy full-WAV identity failed; preserve temporary WAV for diagnosis'
                del data; audio.unlink();render['deleted_only_after_exact_historical_hash_match']=True
                _,data=wavfile.read(m['expected_equal_audio']['path'],mmap=True)
            model_data[m['id']][name]=data[32:32+len(reference)]
            assert model_data[m['id']][name].shape==reference.shape
            renders[m['id']+'/'+name]=render
            write(out/'render-progress.json',renders)
            print('Rendered',m['id'],name,'hash checked' if name=='Equal' else '',flush=True)
    spec=importlib.util.spec_from_file_location('frozen_pitch_metrics',out/'snapshots/stereo_metrics.py')
    metric=importlib.util.module_from_spec(spec);spec.loader.exec_module(metric)
    rows=[]
    for window in design['windows']:
        a,z=round(window['start_seconds']*SR),round(window['end_seconds']*SR)
        observed=reference[a:z].astype(float)/32768
        scores={m['id']:{name:metric.stereo_compare(observed,model_data[m['id']][name][a:z],SR) for name in ('Equal','Original')} for m in design['maps']}
        delta={mid:{key:scores[mid]['Original'][key]-scores[mid]['Equal'][key] for key in METRICS} for mid in MAPS}
        rows.append({**window,'scores':scores,'original_minus_equal':delta})
        if len(rows)%10==0: print('Scored',len(rows),'windows',flush=True)
    groups={'all100':list(range(100)),'focus':list(FOCUS),'neighbors':[64,66,92,94,96,98]}
    aggregate={g:{mid:{name:{key:float(np.mean([r['scores'][mid][name][key] for r in rows if r['patch'] in patches])) for key in METRICS} for name in ('Equal','Original')} for mid in MAPS} for g,patches in groups.items()}
    regressions={mid:{key:[{'patch':r['patch'],'delta':r['original_minus_equal'][mid][key]} for r in rows if r['original_minus_equal'][mid][key]>0] for key in METRICS} for mid in MAPS}
    producer=producer_check(design)
    gates={'legacy_whole_wav_identity_all4':True,'producer_fixed_nuisance':producer['passed'],
           'all100_each_map_no_more_than_0_03_db':all(aggregate['all100'][mid]['Original']['joint_lr_band_rmse_db']-aggregate['all100'][mid]['Equal']['joint_lr_band_rmse_db']<=.03 for mid in MAPS),
           'every_focus_each_map_no_more_than_0_1_db':all(r['original_minus_equal'][mid]['joint_lr_band_rmse_db']<=.1 for r in rows if r['patch'] in FOCUS for mid in MAPS)}
    auditions=make_auditions(out,design,reference,model_data)
    total=sum(p.stat().st_size for p in out.rglob('*.wav'));max_bytes=max(max_bytes,total);assert total<500000000
    result={'schema':design['schema'],'design':record(out/'design-frozen.json'),'candidate_binding':record(out/'candidate-bound.json'),
            'protocol':design,'candidate_source_sha256':bound['source'],'compile_command':cmd,'executable':record(exe),
            'renders':renders,'rows':rows,'aggregate':aggregate,'regressions':regressions,'producer':producer,'audio_gates':gates,
            'audio_gates_passed':all(gates.values()),
            'command_helper_gate':{'passed':True,'evidence':bound['command_helper_validation'],'converter_cases':bound['command_helper_case_count'],'scope':'Separate compiled helper versus the previously ROM-verified functional command model; no new firmware execution in this benchmark'},
            'external_cpu_wrapper_packaging_gates':'Pending separate independent validation; no automatic adoption here',
            'auditions':auditions,'maximum_new_wav_bytes':max_bytes,'no_new_fit':True,'no_artificial_noise':True}
    write(out/'result.json',result)
    print(json.dumps({'result':str(out/'result.json'),'audio_gates':gates,'audio_gates_passed':all(gates.values())},indent=2))


def make_auditions(out,design,reference,model_data):
    dest=out/'auditions';dest.mkdir();records=[];html=['<!doctype html><meta charset="utf-8"><title>Fixed pitch-law comparison</title><h1>Hardware → Equal → Original</h1><p>Same fixed window and timing map. Pair RMS matching only; no EQ, timing or pitch fit.</p>']
    for patch in FOCUS:
        w=next(w for w in design['windows'] if w['patch']==patch)
        a,z=round(w['start_seconds']*SR),round(w['end_seconds']*SR)
        hardware=reference[a:z].astype(float)/32768
        target=float(np.sqrt(np.mean(hardware**2))); normalized={};gains={}
        for mid in MAPS:
            normalized[mid]={};gains[mid]={}
            for name in ('Equal','Original'):
                x=model_data[mid][name][a:z].astype(float);rms=float(np.sqrt(np.mean(x*x)))
                assert rms>0
                gain=target/rms; normalized[mid][name]=x*gain;gains[mid][name]=gain
        peak=max(float(np.max(np.abs(hardware))),*(float(np.max(np.abs(x))) for v in normalized.values() for x in v.values()))
        safety=min(1.,.9/max(peak,1e-12))
        for mid in MAPS:
            gap=np.zeros((SR//4,2));audio=np.concatenate((hardware,gap,normalized[mid]['Equal'],gap,normalized[mid]['Original']))*safety
            assert np.isfinite(audio).all() and np.max(np.abs(audio))<=.900001
            path=dest/f'{patch:02d}-{mid}-hardware-equal-original.wav';wavfile.write(path,SR,np.asarray(audio,dtype=np.float32))
            records.append({'patch':patch,'map':mid,'audio':record(path),'pair_gains':gains[mid],'common_focus_safety_gain':safety,'peak':float(np.max(np.abs(audio)))})
            html.append(f'<h2>{patch} {mid}</h2><audio controls src="auditions/{path.name}"></audio>')
    (out/'audition.html').write_text('\n'.join(html))
    return records


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('freeze','bind','run'))
    parser.add_argument('--output',type=Path,default=ROOT/'build/pitch-model-b12-20261019/benchmark')
    parser.add_argument('--prior',type=Path,default=ROOT/'build/mode00-benchmark-20261019')
    parser.add_argument('--baseline',type=Path,default=ROOT/'build/pitch-model-b12-20261019/baseline')
    parser.add_argument('--source',type=Path,default=ROOT/'Source/DSP')
    parser.add_argument('--command-validation',type=Path,default=ROOT/'build/pitch-model-b12-20261019/command-helper-validation.json')
    args=parser.parse_args();globals()[args.action](args)


if __name__=='__main__':main()
