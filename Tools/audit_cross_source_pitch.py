#!/usr/bin/env python3
"""Reproduce a frozen cross-source tail pitch prediction into a new directory.

Verifies captured/producer/control hashes and retains every failed gate. Requires
NumPy/SciPy; acquires no media, renders no DSP and changes no model/alignment.
The frozen protocol and adjacent design-frozen.json are copied byte-for-byte.
"""
from pathlib import Path
import hashlib,json,math,time
import numpy as np
from scipy import optimize,signal
from scipy.io import wavfile

import argparse
parser=argparse.ArgumentParser(description="Evaluate frozen cross-source tail pitch predictions without rendering or model fitting.")
parser.add_argument("--protocol",type=Path,required=True,help="Frozen protocol; adjacent design-frozen.json is required")
parser.add_argument("--out",type=Path,required=True,help="New or empty output directory")
args=parser.parse_args()
protocol_bytes=args.protocol.read_bytes()
design_bytes=(args.protocol.parent/"design-frozen.json").read_bytes()
P=args.out.resolve();P.mkdir(parents=True,exist_ok=True)
if any(P.iterdir()):raise ValueError("Refusing a nonempty output directory")
(P/"protocol-frozen.json").write_bytes(protocol_bytes)
(P/"design-frozen.json").write_bytes(design_bytes)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pr=json.loads(protocol_bytes)
d=pr['design'];fs=d['sample_rate'];start=d['start_seconds'];end=d['end_seconds'];duration=d['duration_seconds']
assert not(P/'result.json').exists()
assert pr['design_sha256']==sha(P/'design-frozen.json')
for k,v in pr['source_files'].items():assert sha(v['path'])==v['sha256'],k
began=time.perf_counter()

def filtered(x,origin,midi,cutoff,aa,bb):
    ca=math.floor((aa-.5-origin)*fs);cb=math.ceil((bb+.5-origin)*fs)
    if ca<0 or cb>len(x):raise ValueError('Insufficient fixed context')
    tt=origin+np.arange(ca,cb)/fs;nominal=440*2**((midi-69)/12)
    z=signal.sosfiltfilt(signal.butter(4,cutoff,fs=fs,output='sos'),
                        2*x[ca:cb]*np.exp(-2j*np.pi*nominal*tt))
    return tt,z

def endpoint(x,origin,midi,cutoff,captured):
    tt,z=filtered(x,origin,midi,cutoff,start,end);nominal=440*2**((midi-69)/12)
    phase=np.unwrap(np.angle(z));a,b=np.interp([start,end],tt,phase)
    frequency=nominal+(b-a)/(2*np.pi*duration);amp=np.abs(z);inside=(tt>=start)&(tt<=end)
    minimum=float(np.min(amp[inside]));median=float(np.median(amp[inside]));endamp=np.interp([start,end],tt,amp)
    quality={'minimum_amplitude':minimum,'median_amplitude':median,
             'minimum_amplitude_dbfs':float(20*np.log10(max(minimum,1e-30))),
             'median_amplitude_dbfs':float(20*np.log10(max(median,1e-30))),
             'minimum_relative_median_db':float(20*np.log10(max(minimum,1e-30)/max(median,1e-30))),
             'endpoint_amplitudes':[float(v)for v in endamp],
             'fraction_below_point2_median':float(np.mean(amp[inside]<.2*median))}
    if captured:
        fa,fb=[d['off_seconds_continuous']+v for v in d['captured_floor_window_after_old_off_seconds']]
        ft,fz=filtered(x,origin,midi,cutoff,fa,fb);floor=float(np.median(abs(fz[(ft>=fa)&(ft<=fb)])))
        quality.update(empirical_floor_median_amplitude=floor,
                       minimum_above_floor_db=float(20*np.log10(max(minimum,1e-30)/max(floor,1e-30))))
        quality['quiet_gate']=bool(minimum>=.2*median and minimum>=10*floor and minimum>0)
    else:quality['quiet_gate']=None
    return {'hz':float(frequency),'valid':bool(np.isfinite(frequency)and frequency>0),
            'phase_start_radians':float(a),'phase_end_radians':float(b),'quality':quality}

def spectral(x,origin,midi,taper):
    aa,bb=round((start-origin)*fs),round((end-origin)*fs);v=x[aa:bb].astype(float)
    if len(v)<32 or max(abs(v))==0:raise ValueError('Too short or silent')
    v/=np.max(abs(v));nominal=440*2**((midi-69)/12)
    w=(signal.windows.hann if taper=='hann'else signal.windows.blackman)(len(v),sym=False)
    nfft=2**math.ceil(math.log2(16*len(v)));ff=np.fft.rfftfreq(nfft,1/fs);power=abs(np.fft.rfft(v*w,n=nfft))**2
    low,high=nominal*2**(-75/1200),nominal*2**(75/1200);ids=np.flatnonzero((ff>=low)&(ff<=high))
    k=int(ids[np.argmax(power[ids])]);step=fs/nfft;yy=v*w;yy/=np.linalg.norm(yy);tt=np.arange(len(v))/fs
    op=optimize.minimize_scalar(lambda frequency:-abs(np.dot(yy,np.exp(-2j*np.pi*frequency*tt)))**2,
        bounds=(max(low,ff[k]-2*step),min(high,ff[k]+2*step)),method='bounded',options={'xatol':1e-9})
    return {'hz':float(op.x),'valid':bool(op.success and k!=ids[0]and k!=ids[-1]),
            'boundary_peak':bool(k==ids[0]or k==ids[-1]),'sample_window_seconds':len(v)/fs}

def measure(source,ch,x,origin,captured):
    rows=[]
    for midi in [39,75,79,87]:
        out={}
        for cutoff in [6,12]:
            try:out[f'phase{cutoff}']=endpoint(x,origin,midi,cutoff,captured)
            except ValueError as e:out[f'phase{cutoff}']={'valid':False,'reason':str(e)}
        for taper in ['hann','blackman']:
            try:
                out[taper]=spectral(x,origin,midi,taper)
                if captured:out[taper]['quality']=out.get('phase12',{}).get('quality',{'quiet_gate':False})
            except ValueError as e:out[taper]={'valid':False,'reason':str(e)}
        nominal=440*2**((midi-69)/12)
        for est in out.values():
            if'hz'in est and est['hz']>0:est['cents_from_nominal']=float(1200*np.log2(est['hz']/nominal))
        rows.append({'source':source,'channel':ch,'midi':midi,'nominal_hz':nominal,'estimates':out})
    return rows

rows=[]
for source in ['pcm16','opus_float','aac_float','research_rr3_carrier']:
    sr,x=wavfile.read(pr['source_files'][source]['path']);assert sr==fs
    x=x.astype(float)/32768 if x.dtype==np.int16 else x.astype(float)
    x=x[d['source_trims_frames'][source]:]
    for ch,a in {'mid':x.mean(axis=1),'left':x[:,0],'right':x[:,1]}.items():
        rows.extend(measure(source,ch,a,0.,source!='research_rr3_carrier'))
    print('Measured',source,len(rows),'seconds',round(time.perf_counter()-began,2),flush=True)
controls=[]
ca=math.floor((start-.5)*fs);cb=math.ceil((end+.5)*fs);tt=np.arange(ca,cb)/fs;origin=ca/fs
for shape in d['analytic_controls']['waveforms']:
    for common in d['analytic_controls']['common_cents']:
        for phase_rule in d['analytic_controls']['initial_phase_rules']:
            source=f'{shape}_{common:g}c_'+('zero'if phase_rule=='all_zero'else'golden')
            x=np.zeros(len(tt))
            for midi in d['all_control_midi']:
                frequency=440*2**((midi-69)/12)*2**(common/1200)
                phase=0. if phase_rule=='all_zero'else 2*np.pi*((midi*.6180339887498949)%1)
                amplitude=d['analytic_controls']['amplitude_at_old_off']
                if shape=='exponential':amplitude=amplitude*10**(d['analytic_controls']['exponential_slopes_db_per_second'][str(midi)]*(tt-d['off_seconds_continuous'])/20)
                x+=amplitude*np.sin(2*np.pi*frequency*(tt-d['off_seconds_continuous'])+phase)
            rows.extend(measure(source,'mono',x,origin,False));controls.append(source)
print('Analytic controls',len(rows),'seconds',round(time.perf_counter()-began,2),flush=True)
index={(r['source'],r['channel'],r['midi']):r for r in rows};pairs=[]
for source in ['pcm16','opus_float','aac_float','research_rr3_carrier']+controls:
    for channel in (['mono']if source in controls else['mid','left','right']):
        for lo,hi in d['pair_midi']:
            for est in d['estimators']:
                low,high=[index[(source,channel,m)]['estimates'][est]for m in [lo,hi]]
                p={'source':source,'channel':channel,'midi':[lo,hi],'estimator':est,
                   'valid':bool(low['valid']and high['valid'])}
                if all('cents_from_nominal'in x for x in [low,high]):
                    p['interval_error_cents']=high['cents_from_nominal']-low['cents_from_nominal']
                    p['common_offset_cents']=(high['cents_from_nominal']+low['cents_from_nominal'])/2
                if source in ['pcm16','opus_float','aac_float']:
                    p['quiet_gate']=all(x.get('quality',{}).get('quiet_gate',False)for x in [low,high])
                pairs.append(p)
pi={(p['source'],p['channel'],tuple(p['midi']),p['estimator']):p for p in pairs}
checks=[]
for midi in d['pair_midi']:
    prediction=next(p for p in pr['predictions']if p['midi']==midi)
    for est in d['estimators']:
        cc=[pi[(source,'mono',tuple(midi),est)]for source in controls]+[pi[('research_rr3_carrier','mid',tuple(midi),est)]]
        eligible=all(p['valid']and abs(p.get('interval_error_cents',float('inf')))<=.05 for p in cc)
        oo,aa=[pi[(source,'mid',tuple(midi),est)]for source in ['opus_float','aac_float']]
        difference=aa['interval_error_cents']-oo['interval_error_cents']if all('interval_error_cents'in p for p in [aa,oo])else None
        quiet=all(p['valid']and p['quiet_gate']for p in [oo,aa])
        agreement=difference is not None and abs(difference)<=.05
        qualifies=eligible and quiet and agreement
        prediction_pass=all(prediction['acceptance_range_cents'][0]<=p.get('interval_error_cents',float('inf'))<=prediction['acceptance_range_cents'][1]for p in [oo,aa])
        checks.append({'midi':midi,'estimator':est,'control_eligible':eligible,'control_rows':cc,
                       'captured_quiet_valid_gate':quiet,'aac_minus_opus_interval_cents':difference,
                       'codec_agreement':bool(agreement),'qualified':bool(qualifies),
                       'prediction_acceptance_range_cents':prediction['acceptance_range_cents'],
                       'both_encodes_inside_prediction':bool(prediction_pass)})
support=[]
for midi in d['pair_midi']:
    cc=[c for c in checks if c['midi']==midi and c['qualified']];methods=[c['estimator']for c in cc]
    families=any(e in methods for e in ['phase6','phase12'])and any(e in methods for e in ['hann','blackman'])
    support.append({'midi':midi,'qualified_estimators':methods,'phase_and_spectral_families':families,
                    'all_qualified_predictions_pass':all(c['both_encodes_inside_prediction']for c in cc)if cc else None,
                    'supported':bool(families and all(c['both_encodes_inside_prediction']for c in cc)),
                    'endpoint_only_conditional_agreement':bool(any(c['estimator']in['phase6','phase12']and c['both_encodes_inside_prediction']for c in cc)and not families)})
out={'protocol_sha256':sha(P/'protocol-frozen.json'),'analysis_script_sha256':sha(__file__),
     'rows':rows,'pair_rows':pairs,'control_codec_prediction_checks':checks,'support':support,
     'all_sources_unchanged':all(sha(v['path'])==v['sha256']for v in pr['source_files'].values()),
     'elapsed_seconds':time.perf_counter()-began}
(P/'result.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
print(json.dumps({'support':support,'qualified_checks':[{k:v for k,v in c.items()if k!='control_rows'}for c in checks if c['qualified']]},indent=2))
