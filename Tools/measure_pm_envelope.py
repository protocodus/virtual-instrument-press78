#!/usr/bin/env python3
"""Profile conditional 1:1 zero-feedback PM envelopes without fitting a DSP law.

Run a frozen protocol into a fresh ignored build directory. Controls run first;
failed recovery gates stop real-source inference. All nuisance branches in the
specified finite search domain are retained. Local reference PCM is needed only
if every frozen control gate passes and source analysis was requested.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
from dataclasses import dataclass
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
from scipy.spatial import cKDTree
from scipy.special import jv
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
threadpool_limits(1)
RATE = 44100

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def clean(value):
    if isinstance(value, dict): return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [clean(v) for v in value]
    if isinstance(value, np.ndarray): return clean(value.tolist())
    if isinstance(value, np.generic): return clean(value.item())
    if isinstance(value, complex): return [float(value.real), float(value.imag)]
    if isinstance(value, float) and not math.isfinite(value): return None
    return value

def write(path, obj):
    path = Path(path)
    if path.exists(): raise FileExistsError(path)
    path.write_text(json.dumps(clean(obj), indent=2, allow_nan=False) + '\n')

def artifact(path):
    p = Path(path)
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}

@dataclass
class Projector:
    matrix: np.ndarray
    design: np.ndarray
    weight: np.ndarray
    quant: np.ndarray

    def measure(self, signal):
        c = self.matrix @ signal
        # Coefficient order: DC/trend, then cos/sin and local-affine cos/sin.
        z = np.array([(c[2+4*h] - 1j*c[3+4*h]) / 2 for h in range(10)])
        amplitude = 2*np.abs(z)
        residual = signal - self.design @ c
        mean = np.sum(self.weight*signal)/np.sum(self.weight)
        denominator = np.sum(self.weight*(signal-mean)**2)
        return {'complex_harmonics': z, 'amplitudes': amplitude,
                'quantization_floor': self.quant,
                'residual_fraction': float(np.sum(self.weight*residual**2)/max(denominator, 1e-100)),
                'H1_fraction': float(amplitude[0]**2/max(np.sum(amplitude**2), 1e-100))}

PROJECTORS = {}
def projector(n, frequency):
    key = (n, float(frequency))
    if key not in PROJECTORS:
        t = (np.arange(n)-(n-1)/2)/RATE
        affine = t/(n/RATE)
        columns = [np.ones(n), affine]
        for h in range(1, 11):
            angle = 2*np.pi*h*frequency*t
            cs, sn = np.cos(angle), np.sin(angle)
            columns.extend([cs, sn, affine*cs, affine*sn])
        x = np.array(columns).T
        w = np.hanning(n)
        matrix = np.linalg.solve(x.T@(w[:, None]*x), x.T*w)
        # Deterministic PCM16 error scale, not proof of independent white noise.
        q = np.array([np.sqrt(np.sum(matrix[2+4*h]**2+matrix[3+4*h]**2)/12)/32768
                      for h in range(10)])
        PROJECTORS[key] = Projector(matrix, x, w, q)
    return PROJECTORS[key]

CENTERS = np.r_[np.linspace(.15, .55, 17), np.linspace(.65, 1.05, 17)]
def extract(signal, frequency, entry, eligible=(True, True)):
    q_start, q_end = round((entry-.15)*RATE), round((entry-.05)*RATE)
    if q_start < 0 or q_end > len(signal):
        return {'anchor_valid': False, 'reason': 'fixed quiet reference unavailable', 'cells': []}
    quiet = projector(q_end-q_start, frequency).measure(signal[q_start:q_end])
    cells = []
    for i, local in enumerate(CENTERS):
        if not eligible[i//17]:
            cells.append({'valid': False, 'reason': 'metadata-ineligible fixed interval', 'local': local})
            continue
        center = round((entry+local)*RATE)
        n = round(.05*RATE)
        start = center-n//2
        end = start+n
        if start < 0 or end > len(signal):
            cells.append({'valid': False, 'reason': 'fixed support unavailable', 'local': local})
            continue
        x = signal[start:end]
        m = projector(n, frequency).measure(x)
        floor = np.maximum(quiet['amplitudes'], m['quantization_floor'])
        visible = m['amplitudes'] >= floor*10
        phase_visible = m['amplitudes'] >= floor*10**1.5
        valid = (visible[0] and m['H1_fraction'] >= .005 and
                 m['residual_fraction'] <= .1 and np.max(np.abs(x)) < .98 and
                 np.all(np.isfinite(x)))
        cells.append({**m, 'local': local, 'source_frames': [start, end], 'floor': floor,
                      'visible': visible, 'phase_visible': phase_visible,
                      'valid': bool(valid), 'peak': float(np.max(np.abs(x)))})
    anchor = cells[0]
    anchor_ok = bool(anchor.get('valid') and np.any(anchor['visible'][1:6]))
    return {'anchor_valid': anchor_ok, 'cells': cells,
            'quiet_frames': [q_start, q_end], 'quiet_amplitudes': quiet['amplitudes'],
            'reason': None if anchor_ok else 'fixed anchor lacks H1/scored-harmonic information'}

CURVES = {}
def curves(denser=False):
    if denser not in CURVES:
        beta = np.geomspace(.001, 8, 4801 if denser else 2401)
        deltas = np.linspace(0, np.pi/2, 65 if denser else 33)
        hh = np.arange(1, 7)
        jm, jp = jv(hh[None, :]-1, beta[:, None]), jv(hh[None, :]+1, beta[:, None])
        vals = []
        for delta in deltas:
            z = (np.exp(1j*delta)*jm - (-1.)**(hh+1)*np.exp(-1j*delta)*jp)/(2j)
            a = np.abs(z)
            q = 20*np.log10(np.maximum(a[:, 1:], 1e-100)/np.maximum(a[:, :1], 1e-100))
            phase = np.angle(z[:, 1:]) - hh[None, 1:]*np.angle(z[:, :1])
            vals.append((q, phase, 20*np.log10(np.maximum(a[:, 0], 1e-100))))
        CURVES[denser] = (beta, deltas, vals)
    return CURVES[denser]

def interval_bounds(low, high, indices):
    t = CENTERS[indices]
    weight = (t-t.mean())/np.sum((t-t.mean())**2)
    lower = np.sum(np.where(weight >= 0, low[:, indices], high[:, indices])*weight, axis=1)
    upper = np.sum(np.where(weight >= 0, high[:, indices], low[:, indices])*weight, axis=1)
    return -upper, -lower  # Positive attenuation rates.

# Fixed permutation prunes impossible nuisance profiles sooner; no epoch is omitted.
ORDER = [0,16,17,33,8,24,4,12,20,28] + [i for i in range(34) if i not in [0,16,17,33,8,24,4,12,20,28]]

def profile(measured, out, name, denser=False):
    cells = measured['cells']
    if not measured['anchor_valid']:
        return {'anchor_valid': False, 'accepted_profiles': 0, 'reason': measured['reason'],
                'body': None, 'late': None, 'endpoint_hit': False}
    beta, deltas, models = curves(denser)
    anchor = cells[0]
    obs = []
    for cell in cells:
        if not cell.get('valid'):
            obs.append(None)
            continue
        visible = cell['visible'][1:6] & anchor['visible'][1:6]
        if not np.any(visible):
            obs.append(None)
            continue
        amp, a0 = cell['amplitudes'], anchor['amplitudes']
        double_db = 20*np.log10((amp[1:6]/amp[0])/(a0[1:6]/a0[0]))
        z, z0 = cell['complex_harmonics'], anchor['complex_harmonics']
        phi = np.angle(z[1:6]/z0[1:6])-np.arange(2,7)*np.angle(z[0]/z0[0])
        phase_use = cell['phase_visible'][1:6] & anchor['phase_visible'][1:6]
        phase_use &= cell['phase_visible'][0] & anchor['phase_visible'][0]
        obs.append((visible, double_db, phi, phase_use, 20*np.log10(amp[0]/a0[0])))
    observable = np.array([o is not None for o in obs])
    global_low_beta = np.full(34, np.inf); global_high_beta = np.full(34, -np.inf)
    global_low_a = np.full(34, np.inf); global_high_a = np.full(34, -np.inf)
    records = []
    trees = {}
    for di, delta in enumerate(deltas):
        q, ph, b1 = models[di]
        for sign in [1, -1]:
            alive = np.abs(b1) < 160  # Excludes numerically zero H1 models only.
            errsum = np.zeros(len(beta))
            lo_b = np.full((len(beta),34), np.nan); hi_b = lo_b.copy()
            lo_a = lo_b.copy(); hi_a = lo_b.copy()
            hit = np.zeros(len(beta), dtype=bool)
            lo_b[:,0] = hi_b[:,0] = 20*np.log10(beta)
            lo_a[:,0] = hi_a[:,0] = 0
            hit[0] = hit[-1] = True
            for ti in ORDER[1:]:
                if obs[ti] is None: continue
                mask, observed, phase_observed, phase_mask, a_observed = obs[ti]
                active = np.flatnonzero(alive)
                if not len(active): break
                key = (di, tuple(mask))
                if key not in trees: trees[key] = cKDTree(q[:,mask])
                target = q[active][:,mask] + observed[mask]
                matches = trees[key].query_ball_point(target, .1*np.sqrt(mask.sum()))
                for target_row, (pi, candidate) in enumerate(zip(active, matches)):
                    if not candidate:
                        alive[pi] = False
                        continue
                    ids = np.asarray(candidate, dtype=int)
                    if np.any(phase_mask):
                        predicted = sign*(ph[ids][:,phase_mask]-ph[pi,phase_mask])
                        difference = np.angle(np.exp(1j*(predicted-phase_observed[phase_mask])))
                        ids = ids[np.sqrt(np.mean(difference**2,axis=1)) <= .2]
                    if not len(ids):
                        alive[pi] = False
                        continue
                    difference = q[ids][:,mask]-target[target_row]
                    errsum[pi] += float(np.min(np.mean(difference*difference,axis=1)))
                    betadb = 20*np.log10(beta[ids])
                    adb = a_observed+b1[pi]-b1[ids]
                    lo_b[pi,ti], hi_b[pi,ti] = np.min(betadb), np.max(betadb)
                    lo_a[pi,ti], hi_a[pi,ti] = np.min(adb), np.max(adb)
                    if np.any((ids==0)|(ids==len(beta)-1)): hit[pi] = True
            alive &= np.sqrt(errsum/max(int(observable.sum()),1)) <= .075
            indices = np.flatnonzero(alive)
            if not len(indices): continue
            for l,g in [(lo_b,global_low_beta),(lo_a,global_low_a)]:
                g[observable] = np.minimum(g[observable],np.min(l[indices][:,observable],axis=0))
            for h,g in [(hi_b,global_high_beta),(hi_a,global_high_a)]:
                g[observable] = np.maximum(g[observable],np.max(h[indices][:,observable],axis=0))
            bounds = []
            for ii in [np.arange(17),np.arange(17,34)]:
                if np.all(observable[ii]):
                    al,ah = interval_bounds(lo_a[indices],hi_a[indices],ii)
                    bl,bh = interval_bounds(lo_b[indices],hi_b[indices],ii)
                    bounds.extend([al,ah,bl,bh])
                else: bounds.extend([np.full(len(indices),np.nan) for _ in range(4)])
            records.append(np.column_stack([np.full(len(indices),delta),np.full(len(indices),sign),
                          beta[indices],np.sqrt(errsum[indices]/max(int(observable.sum()),1)),
                          *bounds,hit[indices].astype(float)]))
    all_records = np.vstack(records) if records else np.empty((0,13))
    path = out/f'{name}-profiles.npz'
    if path.exists(): raise FileExistsError(path)
    np.savez_compressed(path, profiles=all_records,
                        columns=np.array(['delta','sign','beta_anchor','rms_db','body_A_low','body_A_high',
                        'body_beta_low','body_beta_high','late_A_low','late_A_high','late_beta_low','late_beta_high','endpoint_hit']))
    result = {'anchor_valid':True,'accepted_profiles':len(all_records),'profile_artifact':artifact(path),
              'observable_cells':observable,'endpoint_hit':bool(len(all_records) and np.any(all_records[:,-1])),
              'beta_anchor_range':[float(np.min(all_records[:,2])),float(np.max(all_records[:,2]))] if len(all_records) else None,
              'relative_beta_db_bounds':np.column_stack([global_low_beta,global_high_beta]),
              'relative_A_db_bounds':np.column_stack([global_low_a,global_high_a])}
    for kind,j in [('body',4),('late',8)]:
        if len(all_records) and np.all(np.isfinite(all_records[:,j:j+4])):
            result[kind]={'A_decay':[float(np.min(all_records[:,j])),float(np.max(all_records[:,j+1]))],
                          'beta_decay':[float(np.min(all_records[:,j+2])),float(np.max(all_records[:,j+3]))]}
        else: result[kind]=None
    return clean(result)

# Runtime orchestration is below; source reading is gated behind all controls.

def analytic_signal(case):
    t = np.arange(2*RATE)/RATE-.3
    internal_t = np.maximum(t,0)*(1+case['clock_ppm']*1e-6)
    theta = 2*np.pi*(case['frequency_hz']*internal_t+case['initial_modulator_phase_cycles'])
    a = case['initial_carrier_peak']*10**(-case['carrier_db_per_second']*internal_t/20)
    beta = case['initial_beta']*10**(-case['beta_db_per_second']*internal_t/20)
    y = a*np.sin(theta+case['relative_phase']+beta*np.sin(theta))
    y[t<0] = 0
    kind = case['id']
    if kind == 'lowpass': y = sosfilt(butter(4,3000,fs=RATE,output='sos'),y)
    elif kind == 'highpass': y = sosfilt(butter(2,30,fs=RATE,output='sos',btype='highpass'),y)
    elif kind == 'fractionaldelay':
        y = np.interp(np.arange(len(y))-.3,np.arange(len(y)),y,left=0,right=0)
    elif kind == 'delayedcopy':
        delay = round(.08*RATE)
        y = y+np.r_[np.zeros(delay),.6*y[:-delay]]
    elif kind == 'compressor':
        envelope = 0.
        for i in range(len(y)):
            factor = math.exp(-1/(RATE*(.01 if abs(y[i])>envelope else .2)))
            envelope = factor*envelope+(1-factor)*abs(y[i])
            y[i] *= max(envelope/.25,1.)**(-2/3)
    elif kind == 'two-tone':
        y += np.where(t>=0,.15*a*np.sin(1.013*theta),0)
    elif kind == 'dynamic-gain-nonidentifiability': y *= 10**(12*np.maximum(t,0)/20)
    factor = 1+case['clock_ppm']*1e-6
    truth_a = case['carrier_db_per_second']*factor
    if kind == 'dynamic-gain-nonidentifiability': truth_a -= 12
    return y,case['frequency_hz']*factor,truth_a,case['beta_db_per_second']*factor

def control_qualification(summary,truth_a,truth_b):
    result = {}
    for key in ['body','late']:
        interval = summary.get(key)
        row = {}
        for label,truth,width,error in [('A',truth_a,1.,.5),('beta',truth_b,2.,1.)]:
            bounds = interval.get(label+'_decay') if interval else None
            row[label] = {'truth_decay_db_per_second':truth,'bounds':bounds,
                          'unexpanded_truth_coverage':bool(bounds and bounds[0]<=truth<=bounds[1]),
                          'expanded_truth_coverage':bool(bounds and bounds[0]-error<=truth<=bounds[1]+error),
                          'width':bounds[1]-bounds[0] if bounds else None,
                          'qualified':bool(bounds and not summary.get('endpoint_hit') and
                                           bounds[0]-error<=truth<=bounds[1]+error and bounds[1]-bounds[0]<=width)}
        result[key] = row
    return result

def grid_comparison(coarse,dense):
    checks = []
    for kind in ['body','late']:
        for quantity,tolerance in [('A_decay',.25),('beta_decay',.5)]:
            a = coarse.get(kind)
            b = dense.get(kind)
            if a is None or b is None:
                checks.append({'interval':kind,'quantity':quantity,'passed':False,'reason':'missing conditional range'})
            else:
                change = max(abs(a[quantity][j]-b[quantity][j]) for j in range(2))
                checks.append({'interval':kind,'quantity':quantity,'max_endpoint_change':change,
                               'tolerance':tolerance,'passed':change<=tolerance})
    return {'checks':checks,'passed':all(x['passed'] for x in checks) and coarse.get('endpoint_hit')==dense.get('endpoint_hit')}

def source_measurements(protocol,out):
    # Reached only if all predeclared controls qualify. No new source fit choices.
    corpus = ROOT/'build/isolated-source-search-20261019/synth_bass_1.wav'
    rate,pcm = wavfile.read(corpus)
    if rate != RATE or pcm.dtype != np.int16 or pcm.ndim != 1: raise ValueError('Source PCM identity/format')
    source = pcm.astype(float)/32768
    result = []
    for note in protocol['prior_note_frequencies']:
        index = note['segment_index']
        windows = [w for w in protocol['windows'] if w['segment_index']==index]
        by_kind = {w['kind']:w for w in windows}
        entry = windows[0]['audio_active_entry_seconds']
        eligible = (by_kind['body']['metadata_eligible'],by_kind['late']['metadata_eligible'])
        m = extract(source,note['phase_frequency_hz'],entry,eligible)
        write(out/f'source-{index:02d}-measurements.json',m)
        p = profile(m,out,f'source-{index:02d}')
        result.append({'segment_index':index,'inferred_musical_midi':note['expected_musical_midi_under_authored_sequence'],
                       'frequency_hz_fixed':note['phase_frequency_hz'],'summary':p})
        print('SOURCE',index,'profiles',p['accepted_profiles'],flush=True)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--native-source',type=Path,default=ROOT/'Source/DSP')
    parser.add_argument('--controls-only',action='store_true')
    args = parser.parse_args()
    protocol_path = args.protocol.resolve()
    protocol = json.loads(protocol_path.read_text())
    if protocol.get('schema') != 'press78.pm-envelope-separation-design.v1':
        raise ValueError('An exact final frozen protocol is required')
    out = args.out.resolve()
    out.relative_to((ROOT/'build').resolve())
    if out == (ROOT/'build').resolve() or out.exists(): raise FileExistsError('Fresh ignored output directory required')
    for path,w in protocol['implementation'].items():
        if sha(ROOT/path)!=w['sha256']: raise ValueError('Implementation binding: '+path)
    native_source = args.native_source.resolve()
    for name,w in protocol['native_source_hashes'].items():
        if sha(native_source/name)!=w['sha256']: raise ValueError('Native source binding: '+name)
    out.mkdir(parents=True)
    start = time.monotonic()
    write(out/'run-started.json',{'protocol':artifact(protocol_path),'tool':artifact(Path(__file__)),
                                'native_source':str(native_source),'controls_only':args.controls_only})
    executable = out/'pm_envelope_control'
    command = ['clang++','-O2','-std=c++17','-I',str(native_source),
               str(ROOT/'Tools/PMEnvelopeControl.cpp'),str(native_source/'Press78Engine.cpp'),'-o',str(executable)]
    compile_result = subprocess.run(command,capture_output=True,text=True)
    write(out/'compile.json',{'command':command,'returncode':compile_result.returncode,
                             'stdout':compile_result.stdout,'stderr':compile_result.stderr})
    compile_result.check_returncode()
    results = []
    measurements = {}
    for case in protocol['controls']['cases']:
        name = case['id']
        native_metadata = None
        if case['kind']=='analytic':
            signal,frequency,truth_a,truth_b = analytic_signal(case)
        else:
            path = out/(name+'.wav')
            command = [str(executable),str(path),str(case['note']),str(case['mod_TL']),str(case['carrier_TL']),
                       str(case['mod_D2R']),str(case['carrier_D2R']),str(case['clock_ppm']),
                       'real' if case['profile']=='Real' else 'dry']
            run = subprocess.run(command,capture_output=True,text=True)
            write(out/(name+'-render.json'),{'command':command,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
            run.check_returncode()
            native_metadata = json.loads(run.stdout)
            sr,raw = wavfile.read(path)
            if sr != RATE or raw.shape!=(2*RATE,2) or not np.all(np.isfinite(raw)): raise ValueError('Native format')
            signal = raw[:,0].astype(float) if case.get('channel')=='left' else raw.astype(float).mean(axis=1)
            frequency = native_metadata['frequency_nominal_hz']
            factor = (1+case['clock_ppm']*1e-6) if case['profile']=='transparent' else 1.
            if case['profile']=='transparent': frequency *= factor
            truth_a = 2*2**(case['carrier_D2R']/4)*factor
            truth_b = 2*2**(case['mod_D2R']/4)*factor
        prepeak = float(np.max(np.abs(signal)))
        clipped = int(np.count_nonzero((signal < -1)|(signal>32767/32768)))
        quantized = np.clip(np.rint(signal*32768),-32768,32767)/32768
        waveform_hash = hashlib.sha256(np.asarray(quantized,dtype='<f8').tobytes()).hexdigest()
        measured = extract(quantized,frequency,.3)
        write(out/(name+'-measurements.json'),measured)
        measurements[name] = measured
        summary = profile(measured,out,name)
        qualification = control_qualification(summary,truth_a,truth_b)
        row = {'case':case,'fixed_frequency_hz':frequency,'pre_PCM16_peak':prepeak,'PCM16_saturation_count':clipped,
               'quantized_waveform_float64_sha256':waveform_hash,'native_metadata':native_metadata,
               'profile':summary,'qualification':qualification}
        write(out/(name+'-result.json'),row)
        results.append(row)
        print('CONTROL',name,'profiles',summary['accepted_profiles'],
              'A',[qualification[k]['A']['qualified'] for k in ['body','late']],
              'beta',[qualification[k]['beta']['qualified'] for k in ['body','late']],flush=True)
    grid_checks = []
    for name in protocol['finite_grid_check']['case_ids']:
        dense = profile(measurements[name],out,name+'-denser',True)
        coarse = next(x['profile'] for x in results if x['case']['id']==name)
        if name=='constant-beta':
            a,b = coarse.get('beta_anchor_range'),dense.get('beta_anchor_range')
            check = {'passed':bool(a and b and a[1]/a[0]>=4 and b[1]/b[0]>=4),
                     'coarse_beta_anchor_range':a,'denser_beta_anchor_range':b,
                     'criterion':'No unique absolutebeta manufactured by either grid'}
        else: check = grid_comparison(coarse,dense)
        grid_checks.append({'id':name,'dense_summary':dense,'check':check})
        print('GRID',name,check['passed'],flush=True)
    positive = [x for x in results if x['case']['classification']=='recovery']
    a_pass = all(x['qualification'][interval]['A']['qualified'] for x in positive for interval in ['body','late'])
    b_pass = all(x['qualification'][interval]['beta']['qualified'] for x in positive for interval in ['body','late'])
    constant = next(x['profile'] for x in results if x['case']['id']=='constant-beta')
    nulls = [next(x['profile'] for x in results if x['case']['id']==n) for n in ['sine-no-beta','H1-null']]
    null_pass = bool(constant.get('beta_anchor_range') and constant['beta_anchor_range'][1]/constant['beta_anchor_range'][0]>=4
                     and all(x['accepted_profiles']==0 for x in nulls))
    grid_pass = all(x['check']['passed'] for x in grid_checks)
    all_pass = a_pass and b_pass and null_pass and grid_pass
    source = None
    if all_pass and not args.controls_only:
        for name,w in protocol['sources'].items():
            p = ROOT/name
            if p.stat().st_size!=w['bytes'] or sha(p)!=w['sha256']: raise ValueError('Source binding: '+name)
        source = source_measurements(protocol,out)
    elif not all_pass:
        print('STOP: frozen control gates failed; no Bass source decoded for inference',flush=True)
    result = {'schema':'press78.pm-envelope-separation-result.v1','protocol':artifact(protocol_path),
              'implementation':protocol['implementation'],'native_source_hashes':protocol['native_source_hashes'],
              'controls':results,'finite_grid_checks':grid_checks,
              'gates':{'recovery_case_count':len(positive),'carrier_all_recovery_intervals':a_pass,
                       'beta_all_recovery_intervals':b_pass,'null_information':null_pass,'finite_grid_stability':grid_pass,
                       'all':all_pass},
              'source_inference_attempted':source is not None,'source_results':source,
              'stop_reason':None if all_pass else 'Failed frozen method-control gates; no real-source inference',
              'elapsed_seconds':time.monotonic()-start,
              'no_production_changes':True,'no_noise_path_added':True}
    write(out/'result.json',result)
    print(json.dumps(result['gates']),flush=True)

if __name__=='__main__': main()
