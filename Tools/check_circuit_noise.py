#!/usr/bin/env python3
"""Native sample parity and independent MNA PSD/covariance checks."""
from pathlib import Path
import sys,json,subprocess,tempfile,hashlib
import numpy as np
from scipy import signal
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'Tools/reference'));sys.path.insert(0,str(ROOT/'Tools'))
from generate_circuit_noise import matrices
from circuit.output_stage import noise_spectrum
A,B,C,D,_=matrices()
REPORT={'kind':'Native causal PSS480 circuit-noise validation','passed':False,'source_sha256':hashlib.sha256((ROOT/'Source/DSP/CircuitNoise.h').read_bytes()).hexdigest(),'deterministic_parity':{},'stochastic':{}}
with tempfile.TemporaryDirectory(prefix='press78-circuit-noise-') as td:
 td=Path(td);exe=td/'probe'
 subprocess.run(['clang++','-std=c++17','-O3','-Wall','-Wextra',str(ROOT/'Tools/CircuitNoiseProbe.cpp'),'-o',str(exe)],check=True)
 for fs in (8000,44100,48000,96000,192000):
  n=8192;file=td/'probe.f64';meta=json.loads(subprocess.check_output([str(exe),'probe',str(fs),str(n),str(file)]));native=np.fromfile(file,dtype=np.float64).reshape(-1,2)
  ad,bd,cd,dd,_=signal.cont2discrete((A,B,C,D),1/fs,method='bilinear')
  white=((np.arange(n)[:,None]*17+np.arange(14)[None,:]*31)%101-50)/50.
  _,expected,_=signal.dlsim((ad,bd*np.sqrt(fs/2),cd,dd*np.sqrt(fs/2),1/fs),white)
  error=float(np.max(abs(native-expected)));relative=error/max(abs(expected).max(),1e-30)
  assert relative<1e-8,(fs,error,relative)
  assert meta['bytes']<4096
  REPORT['deterministic_parity'][str(fs)]={'maximum_error_v':error,'relative_peak_error':relative,**meta}
 # Sufficient stationary fixture for RMS/correlation; no per-fixture normalization.
 for fs in (44100,48000,96000):
  file=td/'noise.f64';n=fs*21;meta=json.loads(subprocess.check_output([str(exe),'noise',str(fs),str(n),str(file)]));x=np.fromfile(file,dtype=np.float64).reshape(-1,2)[fs:]
  f,power=signal.welch(x,fs,nperseg=8192,noverlap=4096,axis=0)
  _,cross=signal.csd(x[:,0],x[:,1],fs,nperseg=8192,noverlap=4096)
  keep=(f>=20)&(f<=20000);fq=f[keep];fa=fs/np.pi*np.tan(np.pi*fq/fs);pred,_=noise_spectrum(fa)
  measured=np.sqrt(np.trapz(power[keep],fq,axis=0));expected=np.sqrt(np.trapz(pred[:,[0,1],[0,1]].real,fq,axis=0))
  corr=float(np.trapz(cross[keep].real,fq)/(measured[0]*measured[1]));corr_expected=float(np.trapz(pred[:,0,1].real,fq)/(expected[0]*expected[1]))
  assert np.all(abs(measured/expected-1)<.02),(fs,measured,expected)
  assert abs(corr-corr_expected)<.015,(fs,corr,corr_expected)
  bands=[]
  for lo,hi in [(30,100),(100,1000),(1000,5000),(5000,10000),(10000,20000)]:
   b=(fq>=lo)&(fq<=hi);actual=np.trapz(power[keep][b],fq[b],axis=0);desired=np.trapz(pred[b][:,[0,1],[0,1]].real,fq[b],axis=0)
   err=10*np.log10(actual/desired);assert np.max(abs(err))<.9,(fs,lo,hi,err)
   bands.append({'band_hz':[lo,hi],'power_error_db':err.tolist()})
  REPORT['stochastic'][str(fs)]={'predicted_rms_v':expected.tolist(),'native_rms_v':measured.tolist(),'expected_correlation':corr_expected,'native_correlation':corr,'bands':bands,'generation':meta,'normalization':'none; fixed physical input noise PSD'}
 # Repeated seed is exact and invalid-rate preparation is finite/falls back.
 first=td/'first';second=td/'second'
 subprocess.run([str(exe),'noise','48000','512',str(first)],check=True,capture_output=True)
 subprocess.run([str(exe),'noise','48000','512',str(second)],check=True,capture_output=True)
 assert first.read_bytes()==second.read_bytes();REPORT['seed_repeat_bit_exact']=True
 for fs in ('nan','-1','1e9'):
  subprocess.run([str(exe),'noise',fs,'512',str(first)],check=True,capture_output=True)
  assert np.isfinite(np.fromfile(first,dtype=np.float64)).all()
 REPORT['invalid_rate_sanitization_finite']=True
REPORT['passed']=True
out=ROOT/'Tests/results/circuit-noise-runtime.json';out.write_text(json.dumps(REPORT,indent=2)+'\n')
print(json.dumps({'passed':True,'instance_bytes':meta['bytes'],'native_parity_rates':list(REPORT['deterministic_parity']),'native_stochastic_rates':list(REPORT['stochastic']),'result':str(out)},indent=2))
