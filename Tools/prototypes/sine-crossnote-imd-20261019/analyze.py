#!/usr/bin/env python3
"""Fixed mixed-note sideband qualification. Source PCM is gated on all controls.

No source downloads or codec decodes. A failed qualification is a completed
result and cannot be rescued by changing this experiment's basis or supports.
"""
from pathlib import Path
import hashlib,json,subprocess,shutil,math,time,platform
import numpy as np
from scipy import signal,linalg
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
OUT=ROOT/'build/sine-crossnote-imd-20261019';SR=48000

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def circular(x):return float(np.angle(np.exp(1j*x)))
def frequency(n):return 440*2**((n-69)/12)

class Estimator:
 def __init__(self,lo,hi,protocol):
  self.lo,self.hi=lo,hi;self.a,self.z=round(lo*SR),round(hi*SR);self.t=np.arange(self.a,self.z)/SR;self.center=(self.t[0]+self.t[-1])/2
  u=(self.t-self.center)/((hi-lo)/2);self.frequencies=[x['hz']for x in protocol['nuisance_lines']]+list(protocol['witness_frequencies'].values());self.cols=[u**k for k in range(3)];self.locations={}
  for f in self.frequencies:
   self.locations[f]=len(self.cols)
   for k in range(3):self.cols.extend([u**k*np.cos(2*np.pi*f*(self.t-self.center)),u**k*np.sin(2*np.pi*f*(self.t-self.center))])
  self.B=np.column_stack(self.cols);w=signal.windows.hann(len(self.t));self.w=w
  self.Bw=self.B*w[:,None];U,s,Vh=linalg.svd(self.Bw,full_matrices=False,lapack_driver='gesdd');self.singular=s;self.condition=float(s[0]/s[-1]);mask=s>s[0]*1e-12;self.rank=int(mask.sum());self.pinv=(Vh[mask].T/s[mask])@U[:,mask].T
 def fit(self,y):
  yy=np.asarray(y[self.a:self.z],dtype=float);yy=yy[:,None]if yy.ndim==1 else yy;coef=self.pinv@(yy*self.w[:,None]);pred=self.B@coef;result={}
  for f,idx in self.locations.items():
   # Real y=cosCoeff*cos+sinCoeff*sin; use onset-referenced complex amplitude.
   result[f]=(coef[idx]-1j*coef[idx+1])*np.exp(-2j*np.pi*f*self.center)
  residual=float(np.sqrt(np.mean((pred-yy)**2))/max(np.sqrt(np.mean(yy**2)),1e-30));return result,residual

def independent_signal(t,phases,detune=None,drift=False,harmonics=False):
 parts=[];notes=[39,75,79,87];detune=detune or[0,0,0,0]
 for n,p,c in zip(notes,phases,detune):
  f=frequency(n)*2**(c/1200);phase=2*np.pi*f*t+p
  if drift:phase+=2*np.pi*f*.0005*(1-np.cos(2*np.pi*.7*t))/(2*np.pi*.7)
  x=.1*np.cos(phase)
  if harmonics:
   for h in range(2,21):x+=.1*(.03 if h==2 else .01 if h==3 else .003*4/h)*np.cos(h*phase+.17*h)
  parts.append(x)
 return parts

def delay_components(parts,t):
 stereo=[];component_stereo=[]
 for sign in[-1,1]:
  delay=.004+sign*.0005*np.sin(2*np.pi*.954647*t+.3);components=[np.interp(t-delay,t,x,left=0,right=0)for x in parts];component_stereo.append(components);stereo.append(sum(components))
 return np.column_stack(stereo),component_stereo

def evaluate(key,y,estimators,protocol,expected=None):
 rows=[];gate=protocol['qualification'];qualified=True
 for e in estimators:
  z,residual=e.fit(y);primary=max(float(np.max(abs(z[frequency(n)])))for n in[39,75,79,87]);witness={}
  for name,f in protocol['witness_frequencies'].items():
   values=z[f];ratio=float(np.max(abs(values))/max(primary,1e-30));db=20*math.log10(max(ratio,1e-300));witness[name]={'max_amplitude_relative_to_primary':ratio,'max_db_relative_to_primary':db,'complex_coefficients':[[float(v.real),float(v.imag)]for v in values]}
   if expected is None:
    passed=db<=gate['negative_witness_relative_to_largest_primary_max_db']
   else:
    true=np.asarray(expected(e,name),dtype=complex);true=np.broadcast_to(true,values.shape);relative=abs(values-true)/np.maximum(abs(true),1e-30);phase=np.angle(values/true);witness[name].update(expected_complex=[[float(v.real),float(v.imag)]for v in true],max_relative_complex_error=float(np.max(relative)),max_phase_error_rad=float(np.max(abs(phase))));passed=float(np.max(relative))<=gate['positive_relative_amplitude_error_max']and float(np.max(abs(phase)))<=gate['positive_phase_error_rad_max']
   witness[name]['passed']=bool(passed);qualified=qualified and passed
  rows.append({'support':[e.lo,e.hi],'weighted_design_condition':e.condition,'rank':e.rank,'columns':e.B.shape[1],'unweighted_relative_residual':residual,'witnesses':witness})
 return {'case':key,'positive':expected is not None,'passed':bool(qualified),'rows':rows}

def main():
 if(OUT/'result.json').exists():raise RuntimeError('Completed result exists; never overwrite')
 protocol=json.loads((HERE/'design-frozen.json').read_text());OUT.mkdir(parents=True,exist_ok=True)
 save(OUT/'execution-start.json',{'design_sha256':sha(HERE/'design-frozen.json'),'analysis_sha256':sha(Path(__file__)),'native_probe_source_sha256':sha(HERE/'NativeProbe.cpp'),'source_pcm_opened':False})
 estimators=[Estimator(a,b,protocol)for a,b in protocol['supports_relative_to_on_seconds']]
 matrices=[{'support':[e.lo,e.hi],'condition':e.condition,'rank':e.rank,'columns':e.B.shape[1]}for e in estimators];print('Matrices',matrices,flush=True)
 # Generate only synthetic/native audio before the all-controls gate.
 t=np.arange(SR)/SR;phases=[.2,1.1,-.7,2.0];alpha=protocol['qualification']['positive_injected_alpha'];parts=independent_signal(t,phases);harmonic=independent_signal(t,phases,harmonics=True)
 chorus,_=delay_components(harmonic,t);clean_chorus,clean_components=delay_components(parts,t)
 cases=[('clean_linear',sum(parts),None),('independent_harmonic',sum(harmonic),None),('detuned_harmonic',sum(independent_signal(t,phases,[-2,1,.5,-1],True,True)),None),('linear_chorus',chorus,None),('independent_nonlinearity',sum(x+alpha*x*x+.03*x*x*x for x in parts),None)]
 # y=A*cos(wt+phi), so both sum and difference quadraticcoefficients have alpha*A*B.
 def expected_clean(e,name):return alpha*.1*.1*np.exp(1j*(phases[2]+(phases[0]if name=='sum'else-phases[0])))
 cases.append(('quadratic_positive',sum(parts)+alpha*sum(parts)**2,expected_clean))
 def expected_chorus(e,name):
  phase_values=[]
  for sign in[-1,1]:
   delay=.004+sign*.0005*math.sin(2*math.pi*.954647*e.center+.3)
   za=.1*np.exp(1j*(phases[2]-2*math.pi*frequency(79)*delay));zb=.1*np.exp(1j*(phases[0]-2*math.pi*frequency(39)*delay));phase_values.append(alpha*za*(zb if name=='sum'else np.conj(zb)))
  return np.array(phase_values)
 cases.append(('quadratic_after_chorus_positive',clean_chorus+alpha*clean_chorus**2,expected_chorus))
 rows=[evaluate(k,y,estimators,protocol,ex)for k,y,ex in cases]
 source=OUT/'native-source';source.mkdir(exist_ok=True)
 for p in(ROOT/'Source/DSP').iterdir():
  if p.is_file():shutil.copy2(p,source/p.name)
 native=OUT/'native_probe';command=['c++','-std=c++17','-O2','-I',str(source),str(HERE/'NativeProbe.cpp'),str(source/'Press78Engine.cpp'),'-o',str(native)];subprocess.run(command,check=True,capture_output=True,text=True)
 native_details=[]
 for mode in['dry','circuit','chorus','both']:
  path=OUT/f'native-{mode}.f32';run=[str(native),mode,str(path)];p=subprocess.run(run,check=True,capture_output=True,text=True);data=np.fromfile(path,dtype='<f4').reshape(-1,2);assert np.isfinite(data).all();row=evaluate('native_'+mode,data,estimators,protocol);rows.append(row);native_details.append({'mode':mode,'run_command':run,'render':json.loads(p.stdout),'audio_sha256':sha(path)})
 matrix_gate=all(m['condition']<=protocol['qualification']['condition_number_max']and m['rank']==m['columns']for m in matrices);qualified=matrix_gate and all(r['passed']for r in rows)
 report={'schema':'press78.sine-crossnote-imd.result.v1','design':protocol,'design_sha256':sha(HERE/'design-frozen.json'),'analysis_sha256':sha(Path(__file__)),'native_probe_source_sha256':sha(HERE/'NativeProbe.cpp'),'source_pcm_opened':False,'source_downloaded_or_decoded':False,'matrix_diagnostics':matrices,'matrix_gate_passed':matrix_gate,'qualification_cases':rows,'all_qualification_passed':bool(qualified),'native':{'source_sha256':{p.name:sha(p)for p in sorted(source.iterdir())if p.is_file()},'compile_command':command,'executable_sha256':sha(native),'renders':native_details},'production_changed':False}
 save(OUT/'qualification.json',report)
 if not qualified:
  report['status']='Qualification failed; source PCM analysis deliberately not performed';report['source_result']=None;report['consequence']='This fixed estimator cannot support a source cross-note IMD claim. Failure is not evidence that the hardware is linear or nonlinear. Preserve it; do not revise this run to rescue source analysis.';save(OUT/'result.json',report);print(report['status'],flush=True);return
 # This branch is allowed only after every prospective synthetic/native case passed.
 raise RuntimeError('Qualification passed. Stop for explicit review before source slicing; no source has been opened yet.')

if __name__=='__main__':main()
