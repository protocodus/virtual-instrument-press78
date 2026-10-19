#!/usr/bin/env python3
"""Measure a previously frozen pitch-pattern protocol into a new directory.

Uses NumPy/SciPy only. Verifies all frozen source hashes, retains failures, and
never renders DSP, alters alignments, acquires media or replaces old results.

Example:
  python3 Tools/audit_pitch_pattern.py --protocol build/pitch-pattern-audit-20261019/protocol-frozen.json --out build/pitch-pattern-reproduction
"""
from pathlib import Path
import hashlib,json,math,time
import numpy as np
from scipy import signal,optimize
from scipy.io import wavfile

import argparse
parser=argparse.ArgumentParser(description="Reproduce a frozen metadata-selected pitch-pattern experiment without DSP or alignment changes.")
parser.add_argument("--protocol",type=Path,required=True,help="Frozen pitch-pattern protocol JSON with bound source hashes")
parser.add_argument("--out",type=Path,required=True,help="New or empty output directory; existing results are never replaced")
args=parser.parse_args()
protocol_bytes=args.protocol.read_bytes()
P=args.out.resolve()
P.mkdir(parents=True,exist_ok=True)
if any(P.iterdir()):raise ValueError("Refusing a nonempty output directory")
(P/"protocol-frozen.json").write_bytes(protocol_bytes)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pr=json.loads(protocol_bytes)
assert not(P/'result.json').exists()
for k,v in pr['source_files'].items():assert sha(v['path'])==v['sha256'],k
fs=pr['sample_rate'];midis=pr['joint_basis_midi'];K=len(midis);elapsed=time.perf_counter()
N=round(.120*fs);tau=(np.arange(N)-N//2)/fs
B=np.column_stack([*[np.cos(2*np.pi*440*2**((m-69)/12)*tau)for m in midis],
                   *[np.sin(2*np.pi*440*2**((m-69)/12)*tau)for m in midis],np.ones(N)])
ww=signal.windows.hann(N,sym=False)
singular=np.linalg.svd(B*ww[:,None],compute_uv=False)
dual=np.linalg.pinv(B*ww[:,None])*ww[None,:]

def phase_fit(z,tt,center):
    amp=np.abs(z);keep=amp>=.2*np.median(amp)
    if np.count_nonzero(keep)<16:raise ValueError('Fewer than16 retained phase samples')
    ph=np.unwrap(np.angle(z));wt=(amp[keep]/max(amp[keep]))**2
    dt=tt[keep]-np.average(tt[keep],weights=wt)
    slope=np.sum(wt*dt*(ph[keep]-np.average(ph[keep],weights=wt)))/np.sum(wt*dt*dt)
    hz=float(center+slope/(2*np.pi))
    if not np.isfinite(hz)or hz<=0:raise ValueError('Invalid phase frequency')
    return {'hz':hz,'valid':True,'retained_phase_fraction':float(np.mean(keep)),
            'minimum_amplitude_relative_median_db':float(20*np.log10(max(np.min(amp),1e-30)/max(np.median(amp),1e-30)))}

def hann(x,nominal):
    if len(x)<32 or np.max(np.abs(x))==0:raise ValueError('Too short or silent')
    x=np.asarray(x,dtype=float);x=x/np.max(np.abs(x));w=signal.windows.hann(len(x),sym=False)
    nfft=2**math.ceil(math.log2(16*len(x)));ff=np.fft.rfftfreq(nfft,1/fs)
    power=np.abs(np.fft.rfft(x*w,n=nfft))**2;lo,hi=nominal*2**(-75/1200),nominal*2**(75/1200)
    ii=np.flatnonzero((ff>=lo)&(ff<=hi));k=int(ii[np.argmax(power[ii])]);step=fs/nfft
    tt=np.arange(len(x))/fs;v=x*w;v/=np.linalg.norm(v)
    opt=optimize.minimize_scalar(lambda f:-abs(np.dot(v,np.exp(-2j*np.pi*f*tt)))**2,
                                bounds=(max(lo,ff[k]-2*step),min(hi,ff[k]+2*step)),
                                method='bounded',options={'xatol':1e-9})
    return {'hz':float(opt.x),'valid':bool(opt.success and k!=ii[0]and k!=ii[-1]),
            'boundary_peak':bool(k==ii[0]or k==ii[-1]),'physical_window_seconds':len(x)/fs}

def joint_window(x,start,end,targets):
    a,b=round(start*fs),round(end*fs);centers=np.arange(a,b+1,96,dtype=int)
    if centers[0]-N//2<0 or centers[-1]+N//2>len(x):raise ValueError('Insufficient joint context')
    segments=x[centers[:,None]+np.arange(N)[None,:]-N//2].T
    ids=[midis.index(m)for m in targets];coeff=dual[ids+[i+K for i in ids]]@segments
    result={};tt=centers/fs
    for j,m in enumerate(targets):
        nominal=440*2**((m-69)/12);z=(coeff[j]-1j*coeff[j+len(ids)])*np.exp(-2j*np.pi*nominal*tt)
        try:result[m]=phase_fit(z,tt,nominal)
        except ValueError as e:result[m]={'valid':False,'reason':str(e)}
    return result

def measure(x,start,end,nominal,joint):
    out={'joint120':dict(joint)}
    try:out['hann']=hann(x[round(start*fs):round(end*fs)],nominal)
    except ValueError as e:out['hann']={'valid':False,'reason':str(e)}
    for cutoff in [6,12]:
        try:
            if not out['hann']['valid']:raise ValueError('Invalid Hann center')
            a,b=round(start*fs),round(end*fs);ca,cb=a-24000,b+24000
            if ca<0 or cb>len(x):raise ValueError('Insufficient phase context')
            tt=np.arange(ca,cb)/fs;v=x[ca:cb];scale=np.max(abs(v))
            if scale==0:raise ValueError('Silent phase context')
            center=out['hann']['hz'];z=signal.sosfiltfilt(signal.butter(4,cutoff,fs=fs,output='sos'),
                                                        2*(v/scale)*np.exp(-2j*np.pi*center*tt))
            ids=np.arange(a-ca,b-ca,48);out[f'phase{cutoff}']=phase_fit(z[ids],tt[ids],center)
        except ValueError as e:out[f'phase{cutoff}']={'valid':False,'reason':str(e)}
    for v in out.values():
        if 'hz'in v:v['cents_from_nominal']=float(1200*np.log2(v['hz']/nominal))
    return out

rows=[]
obsby={w['window_id']:[o for o in pr['observations']if o['window_id']==w['window_id']]for w in pr['windows']}
for source in ['pcm16','opus_float','aac_float','native_b11']:
    sr,a=wavfile.read(pr['source_files'][source]['path']);assert sr==fs
    a=a.astype(float)/32768 if a.dtype==np.int16 else a.astype(float)
    a=a[pr['source_trim_frames'][source]:]
    for channel,x in {'mid':a.mean(axis=1),'left':a[:,0],'right':a[:,1]}.items():
        for w in pr['windows']:
            obs=obsby[w['window_id']];targets=[o['event']['midi']for o in obs]
            jj=joint_window(x,w['start_seconds'],w['end_seconds'],targets)
            for o in obs:
                m=o['event']['midi'];rows.append({'source':source,'channel':channel,'observation_id':o['observation_id'],
                    'estimates':measure(x,w['start_seconds'],w['end_seconds'],o['event']['expected_hz'],jj[m])})
    print(source,'rows',len(rows),'seconds',round(time.perf_counter()-elapsed,2),flush=True)
    del a

for control in pr['controls']:
    for w in pr['windows']:
        start,end=w['start_seconds'],w['end_seconds'];ca,cb=round((start-.6)*fs),round((end+.6)*fs)
        tt=np.arange(ca,cb)/fs;localstart=start-ca/fs;localend=end-ca/fs
        obs=obsby[w['window_id']];targets=[o['event']['midi']for o in obs]
        if control['kind']=='isolated':
            for o in obs:
                m=o['event']['midi'];f=o['event']['expected_hz'];phase=2*np.pi*((m*.6180339887498949)%1)
                x=control['amplitude']*np.sin(2*np.pi*f*tt+phase)
                jj=joint_window(x,localstart,localend,[m])
                rows.append({'source':control['id'],'channel':'mono','observation_id':o['observation_id'],
                    'estimates':measure(x,localstart,localend,f,jj[m])})
        else:
            x=np.zeros(len(tt))
            if control['kind']=='stationary_ensemble':
                for m in midis:
                    f=440*2**((m-69)/12)*2**(control['common_cents']/1200);phase=2*np.pi*((m*.6180339887498949)%1)
                    x+=control['amplitude_per_tone']*np.sin(2*np.pi*f*tt+phase)
            else:
                for n in pr['all_program99_events']:
                    on,off=n['onset_seconds'],n['off_seconds'];inside=(tt>=on)&(tt<off)
                    phase=2*np.pi*((n['event_index']*.6180339887498949)%1)
                    x[inside]+=control['amplitude_per_note']*np.sin(2*np.pi*n['expected_hz']*(tt[inside]-on)+phase)
            jj=joint_window(x,localstart,localend,targets)
            for o in obs:
                m=o['event']['midi'];rows.append({'source':control['id'],'channel':'mono','observation_id':o['observation_id'],
                    'estimates':measure(x,localstart,localend,o['event']['expected_hz'],jj[m])})
    print(control['id'],'rows',len(rows),'seconds',round(time.perf_counter()-elapsed,2),flush=True)

indexed={(r['source'],r['channel'],r['observation_id']):r for r in rows}
pair_rows=[];eligibility=[]
sources=['pcm16','opus_float','aac_float','native_b11']+[c['id']for c in pr['controls']]
for pair in pr['pairs']:
    wid=pair['window_id'];events=pair['events'];mn=pair['midi']
    for est in pr['estimators']:
        calc={}
        for source in sources:
            for ch in (['mono']if source not in ['pcm16','opus_float','aac_float','native_b11']else pr['channels']):
                l,h=[indexed[(source,ch,f'{wid}_{event}')]['estimates'][est]for event in events]
                rr={'pair_id':pair['pair_id'],'source':source,'channel':ch,'estimator':est,
                    'valid':bool(l['valid']and h['valid'])}
                if 'cents_from_nominal'in l and 'cents_from_nominal'in h:
                    low,high=l['cents_from_nominal'],h['cents_from_nominal'];rr.update(
                        interval_error_cents=high-low,common_offset_cents=(low+high)/2,
                        G_minus_Dsharp_cents=((high-low)if mn[1]%12==7 else(low-high))if pair['calibrated_G_Dsharp_classes']else None)
                calc[(source,ch)]=rr;pair_rows.append(rr)
        controlrows=[calc[(c['id'],'mono')]for c in pr['controls']]+[calc[('native_b11','mid')]]
        ctrlpass=all(r['valid']and abs(r.get('interval_error_cents',float('inf')))<=.10 for r in controlrows)
        aa,oo=calc[('aac_float','mid')],calc[('opus_float','mid')]
        difference=(aa['interval_error_cents']-oo['interval_error_cents'])if'interval_error_cents'in aa and'interval_error_cents'in oo else None
        codecpass=aa['valid']and oo['valid']and difference is not None and abs(difference)<=.05
        eligibility.append({'pair_id':pair['pair_id'],'estimator':est,'control_eligible':ctrlpass,
                            'control_biases':[{k:r[k]for k in ['source','valid','interval_error_cents']if k in r}for r in controlrows],
                            'aac_minus_opus_interval_cents':difference,'codec_agreement':bool(codecpass),
                            'qualified':bool(ctrlpass and codecpass)})

pairindex={(r['pair_id'],r['source'],r['channel'],r['estimator']):r for r in pair_rows}
eligindex={(r['pair_id'],r['estimator']):r for r in eligibility}
obsindex={o['observation_id']:o for o in pr['observations']}
def support(kind):
    checks=[]
    for pair in pr['pairs']:
        if not pair['primary_G_Dsharp_extension'if kind=='G_Dsharp'else'primary_octave_extension']:continue
        q=[est for est in pr['estimators']if eligindex[(pair['pair_id'],est)]['qualified']]
        enough='hann'in q and any(est in q for est in ['phase6','phase12','joint120'])
        values=[]
        for est in q:
            for source in ['opus_float','aac_float']:
                rr=pairindex[(pair['pair_id'],source,'mid',est)]
                value=rr['G_minus_Dsharp_cents']if kind=='G_Dsharp'else rr['interval_error_cents']
                passes=value>.20 and abs(value-pr['calibration']['fixed_G_minus_Dsharp_cents'])<=.15 if kind=='G_Dsharp'else abs(value)<=.15
                values.append({'source':source,'estimator':est,'value_cents':value,'passes_fixed_prediction':bool(passes)})
        oo=[obsindex[f'{pair["window_id"]}_{e}']for e in pair['events']]
        checks.append({'pair_id':pair['pair_id'],'window_id':pair['window_id'],'midi':pair['midi'],
                       'qualified_estimators':q,'enough_qualified_families':enough,
                       'all_qualified_predictions_pass':all(v['passes_fixed_prediction']for v in values)if values else None,
                       'evaluable':bool(enough),'support':bool(enough and all(v['passes_fixed_prediction']for v in values)),
                       'both_components_release_clear_2s':all(o['release_clear_2s']for o in oo),
                       'harmonic_ambiguity':any(o['possible_lower_harmonics_with_2s_release_lookback']for o in oo),
                       'values':values})
    windows=[]
    for wid in sorted({r['window_id']for r in checks}):
        cc=[r for r in checks if r['window_id']==wid and r['evaluable']]
        windows.append({'window_id':wid,'evaluable_pairs':len(cc),'evaluable':bool(cc),
                        'support':bool(cc)and all(r['support']for r in cc)})
    evaluated=[w for w in windows if w['evaluable']]
    pitches={m for c in checks if c['evaluable']for m in c['midi']if any(o['event']['midi']==m and o['new_frequency_event']for o in pr['observations'])}
    classes={c['midi'][0]%12 for c in checks if c['evaluable']}
    # These fixed anchorwindows are nonoverlapping except exact coincident creator groups, already deduplicated.
    ordered=sorted([next(w for w in pr['windows']if w['window_id']==q['window_id'])for q in evaluated],key=lambda w:w['start_seconds'])
    nonoverlap=sum(1 for i,w in enumerate(ordered)if i==0 or w['start_seconds']>=ordered[i-1]['end_seconds']-1e-8)
    overall=len(evaluated)>=3 and nonoverlap>=3 and all(w['support']for w in evaluated)
    overall&=len(pitches)>=2 if kind=='G_Dsharp'else len(classes)>=3
    return {'pair_checks':checks,'window_checks':windows,'evaluable_window_count':len(evaluated),
            'nonoverlapping_evaluable_window_count':nonoverlap,'new_midi_pitches':sorted(pitches),
            'octave_pitchclasses':sorted(classes)if kind!='G_Dsharp'else None,
            'frozen_overall_support':bool(overall)}

repeated=[]
for midi in sorted({tuple(p['midi'])for p in pr['pairs']if p['anchor_window']and p['at_least_one_new_frequency_event']}):
    pp=[p for p in pr['pairs']if tuple(p['midi'])==midi and p['anchor_window']and p['at_least_one_new_frequency_event']]
    for est in pr['estimators']:
        eligible=[p for p in pp if eligindex[(p['pair_id'],est)]['qualified']]
        if len(eligible)<2:continue
        for source in ['opus_float','aac_float']:
            rr=[pairindex[(p['pair_id'],source,'mid',est)]for p in eligible];vv=[r['interval_error_cents']for r in rr]
            repeated.append({'midi':list(midi),'estimator':est,'source':source,'pair_ids':[p['pair_id']for p in eligible],
                             'values_cents':vv,'range_cents':max(vv)-min(vv),'within_fixed_point2c':max(vv)-min(vv)<=.20})
result={'protocol_sha256':sha(P/'protocol-frozen.json'),'analysis_script_sha256':sha(__file__),
        'rows':rows,'pair_rows':pair_rows,'eligibility':eligibility,
        'G_Dsharp_fixed_prediction':support('G_Dsharp'),'apparent_octave_replication':support('octave'),
        'repeated_interval_diagnostics':repeated,
        'joint_basis_condition_number':float(singular[0]/singular[-1]),
        'elapsed_seconds':time.perf_counter()-elapsed,
        'source_hashes_unchanged':all(sha(v['path'])==v['sha256']for v in pr['source_files'].values())}
(P/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'rows':len(rows),'pair_rows':len(pair_rows),'eligibility_rows':len(eligibility),
                  'G_Dsharp':{k:v for k,v in result['G_Dsharp_fixed_prediction'].items()if k not in ['pair_checks','window_checks']},
                  'octave':{k:v for k,v in result['apparent_octave_replication'].items()if k not in ['pair_checks','window_checks']},
                  'invalid_estimates':sum(not e['valid']for r in rows for e in r['estimates'].values()),
                  'joint_condition':result['joint_basis_condition_number']},indent=2))
