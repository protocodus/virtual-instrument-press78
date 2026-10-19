#!/usr/bin/env python3
"""Posthoc synthetic-only diagnostic of a frozen PM-envelope control failure.

Compares known instantaneous PM coefficients with saved window-extracted values.
No source recording is read, no parameter is fitted, and no failed gate is
changed. Exact-coefficient replays use only the original fixed grid-check cases.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import sys
import numpy as np
from scipy.special import jv

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pm_frozen',ROOT/'Tools/measure_pm_envelope.py')
pm=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pm;spec.loader.exec_module(pm)

def load_measurement(path):
    m=json.loads(path.read_text())
    for c in m['cells']:
        if 'complex_harmonics' not in c:continue
        c['complex_harmonics']=np.array([complex(*z) for z in c['complex_harmonics']])
        for name in ['amplitudes','quantization_floor','floor']:c[name]=np.array(c[name])
        for name in ['visible','phase_visible']:c[name]=np.array(c[name],dtype=bool)
    return m

def ratios(z):
    amp=np.abs(z)
    db=20*np.log10((amp[:,1:6]/amp[:,:1])/(amp[0,1:6]/amp[0,0]))
    phase=np.angle(z[:,1:6]/z[0,1:6])-np.arange(2,7)*np.angle(z[:,:1]/z[0,0])
    return db,phase

def bessel(beta,delta,harmonics=10):
    h=np.arange(1,harmonics+1)
    return (np.exp(1j*delta)*jv(h[None,:]-1,beta[:,None])-
            (-1.)**(h+1)*np.exp(-1j*delta)*jv(h[None,:]+1,beta[:,None]))/(2j)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();out=args.out.resolve();out.relative_to((ROOT/'build').resolve())
    if out.exists() or out==(ROOT/'build').resolve():raise FileExistsError('Fresh ignored output required')
    protocol=json.loads(args.protocol.read_text());result=json.loads((args.run/'result.json').read_text())
    assert pm.sha(ROOT/'Tools/measure_pm_envelope.py')==protocol['implementation']['Tools/measure_pm_envelope.py']['sha256']
    assert not result['gates']['all'] and not result['source_inference_attempted']
    out.mkdir(parents=True)
    pm.write(out/'diagnostic-design-before-run.json',{
        'scope':'Posthoc synthetic diagnosis only; frozen failed run untouched. No source audio.',
        'original_result':pm.artifact(args.run/'result.json'),'protocol':pm.artifact(args.protocol),
        'tool':pm.artifact(Path(__file__)),'cases':'all36 unprocessed analytic controls',
        'residuals':'known continuous instantaneous truth and nearest original grid, no fitting',
        'profile_replays':['analytic-00','analytic-11','analytic-24'],
        'replay_rule':'Replace only complex coefficients/amplitudes with instantaneous known truth; retain original window/floor/visibility/gate masks. Same frozen radii and coarse/denser grids. Not a rescued experiment.'})
    beta_grid,delta_grid,_=pm.curves(False)
    rows=[];replays=[]
    for original in result['controls']:
        c=original['case']
        if c['kind']!='analytic' or c['processing']!='none' or not c['id'].startswith('analytic-'):continue
        measured=load_measurement(args.run/(c['id']+'-measurements.json'))
        observed=np.array([x['complex_harmonics'] for x in measured['cells']])
        centers=np.array([(x['source_frames'][0]+x['source_frames'][1]-1)/2 for x in measured['cells']])/pm.RATE-.3
        internal=np.maximum(centers,0)*(1+c['clock_ppm']*1e-6)
        beta=c['initial_beta']*10**(-c['beta_db_per_second']*internal/20)
        amplitude=c['initial_carrier_peak']*10**(-c['carrier_db_per_second']*internal/20)
        theta=2*np.pi*(c['frequency_hz']*internal+c['initial_modulator_phase_cycles'])
        coefficient=bessel(beta,c['relative_phase'])
        exact=amplitude[:,None]*coefficient*np.exp(1j*theta[:,None]*np.arange(1,11))
        q_ob,p_ob=ratios(observed);q_ex,p_ex=ratios(exact)
        nearest_beta=beta_grid[np.argmin(np.abs(np.log(beta_grid[:,None])-np.log(beta[None,:])),axis=0)]
        nearest_delta=float(delta_grid[np.argmin(np.abs(delta_grid-c['relative_phase']))])
        nearest=bessel(nearest_beta,nearest_delta)
        q_grid,p_grid=ratios(nearest)
        _,p_identity=ratios(coefficient)
        mask=np.array([x['visible'][1:6]&measured['cells'][0]['visible'][1:6] for x in measured['cells']])
        phase_mask=np.array([x['phase_visible'][1:6]&measured['cells'][0]['phase_visible'][1:6]&x['phase_visible'][0]&measured['cells'][0]['phase_visible'][0] for x in measured['cells']])
        def cell_rms(d,m):
            return [float(np.sqrt(np.mean(d[i,m[i]]**2))) if np.any(m[i]) else None for i in range(34)]
        window_bias=cell_rms(q_ob-q_ex,mask)
        grid_bias=cell_rms(q_grid-q_ex,mask)
        combined=cell_rms(q_ob-q_grid,mask)
        phase_bias=cell_rms(np.angle(np.exp(1j*(p_ob-p_ex))),phase_mask)
        identity=np.max(np.abs(np.angle(np.exp(1j*(p_ex-p_identity)))))
        row={'case_id':c['id'],'phase_true':c['relative_phase'],'phase_nearest_grid':nearest_delta,
             'beta_anchor_true':float(beta[0]),'beta_anchor_nearest_grid':float(nearest_beta[0]),
             'window_minus_continuous_truth_cell_rms_db':window_bias,
             'nearest_grid_minus_continuous_truth_cell_rms_db':grid_bias,
             'window_minus_nearest_grid_truth_cell_rms_db':combined,
             'window_phase_invariant_minus_truth_rms_rad':phase_bias,
             'exact_phase_invariant_formula_identity_max_rad':float(identity),
             'cells_over_frozen_point1db_against_continuous_truth':sum(x is not None and x>.1 for x in window_bias),
             'saved_measurement':pm.artifact(args.run/(c['id']+'-measurements.json'))}
        rows.append(row)
        if c['id'] in ['analytic-00','analytic-11','analytic-24']:
            for i,cell in enumerate(measured['cells']):
                cell['complex_harmonics']=exact[i]
                cell['amplitudes']=2*np.abs(exact[i])
            replay={'case_id':c['id'],'original_extracted_profile':original['profile']}
            for dense,label in [(False,'coarse'),(True,'denser')]:
                replay[label]=pm.profile(measured,out,c['id']+'-instant-'+label,dense)
                print('INSTANT',c['id'],label,replay[label]['accepted_profiles'],flush=True)
            replays.append(replay)
        print('DIAGNOSTIC',c['id'],'max_window_bias',max(x for x in window_bias if x is not None),flush=True)
    pm.write(out/'result.json',{'schema':'press78.pm-envelope-posthoc-control-diagnostic.v1',
             'scope':'Posthoc exact-control diagnosis; no source measurement, no gate/model changes and no rescued-pass claim.',
             'rows':rows,'instantaneous_replays':replays,
             'source_inference_attempted':False,'original_result':pm.artifact(args.run/'result.json'),
             'implementation':pm.artifact(Path(__file__))})

if __name__=='__main__':main()
