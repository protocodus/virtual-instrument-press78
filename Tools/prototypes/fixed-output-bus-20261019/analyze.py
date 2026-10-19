#!/usr/bin/env python3
"""Prospectively specified coefficient / independent SRC verification. No fitting."""
import hashlib,json,math,pathlib,subprocess,sys,time
import numpy as np
from scipy.signal import resample_poly, firwin
P=pathlib.Path(__file__).resolve().parent
ROOT=P.parents[2]; OUT=ROOT/'build/fixed-output-bus-20261019'; EXE=OUT/'probe-03'
rates=[8000,11025,16000,22050,24000,32000,44100,44117,48000,88200,96000,176400,192000]
def dump(name,d): (OUT/name).write_text(json.dumps(d,indent=2,allow_nan=False,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def native(*args):return subprocess.run([str(EXE),*map(str,args)],check=True,capture_output=True,text=True).stdout

def response():
    rows=[]
    for rate in rates:
        f=OUT/f'coeff-{rate}.bin'; meta=json.loads(native('coeff',rate,f))
        header=np.fromfile(f,dtype=np.uint64,count=3); phases,taps,half=map(int,header)
        c=np.memmap(f,dtype=np.float64,mode='r',offset=24,shape=(phases,taps))
        frac=((np.arange(phases,dtype=np.int64)*48000)%rate)/rate
        relative=np.arange(taps)-half
        passfreq=np.r_[0,np.linspace(20,20000 if rate>=44100 else rate*.4,24)]
        stopfreq=np.r_[rate/2+1,np.linspace(rate/2+1,23900,32)] if rate<48000 else np.array([])
        freqs=np.r_[passfreq,stopfreq]; h=np.empty((phases,len(freqs)),complex)
        for j,freq in enumerate(freqs):
            h[:,j]=c@np.exp(2j*np.pi*freq/48000*relative)*np.exp(-2j*np.pi*freq/48000*frac)
        gain=20*np.log10(np.maximum(np.abs(h[:,:len(passfreq)]),1e-300));phase=np.angle(h[:,:len(passfreq)])*180/np.pi
        maxgain=float(np.max(abs(gain)));maxphase=float(np.max(abs(phase)))
        if rate<48000:rejection=-20*np.log10(max(float(np.max(abs(h[:,len(passfreq):]))),1e-300))
        elif phases>1:
            images=np.fft.fft(h[:,:len(passfreq)],axis=0)/phases
            rejection=-20*np.log10(max(float(np.max(abs(images[1:]/images[0]))),1e-300))
        else:rejection=None
        row={'rate':rate,'phases':phases,'taps':taps,**meta,'passband_end_hz':float(passfreq[-1]),'max_gain_error_db':maxgain,'max_phase_error_degrees':maxphase,'stop_or_image_rejection_db':rejection,'passed':maxgain<=.01 and maxphase<=.05 and (rejection is None or rejection>=80),'scope':'standaloneSRC; wrapper48000 bypasses this filter entirely' if rate==48000 else 'active non48 SRC','per_frequency_worst_gain_db':np.max(abs(gain),axis=0).tolist(),'pass_frequencies_hz':passfreq.tolist()}
        rows.append(row);dump('response-progress.json',rows);print('response',rate,row['passed'],maxgain,rejection,flush=True)
        del c;f.unlink()
    dump('response.json',{'passed':all(r['passed'] for r in rows),'rows':rows})

def exact_ref(x,rate,count=None,panic_frame=None):
    ratio=min(1,rate/48000);half=math.ceil(96/ratio);n=count if count is not None else math.floor(len(x)*rate/48000)
    out=np.empty((n,2),np.float64); relative=np.arange(-half,half+1);den=np.i0(10.)
    for start in range(0,n,1024):
        frames=np.arange(start,min(start+1024,n),dtype=np.int64);products=frames*48000;low=products//rate;frac=(products%rate)/rate
        indices=low[:,None]-half+relative
        u=ratio*(relative[None,:]-frac[:,None]);valid=abs(u)<=96
        c=ratio*.95*np.sinc(.95*u)*np.i0(10*np.sqrt(np.maximum(0,1-(u/96)**2)))/den*valid
        good=(indices>=0)&(indices<len(x))
        if panic_frame is not None:
            panic_index=(panic_frame*48000+rate-1)//rate
            good &= ~((frames[:,None]>=panic_frame)&(indices<panic_index))
        values=x[np.clip(indices,0,len(x)-1)]*good[:,:,None]
        out[start:start+len(frames)]=(c[:,:,None]*values).sum(axis=1)/c.sum(axis=1)[:,None]
    return out

def component():
    t=np.arange(96000)/48000.; signal=.09*np.sin(2*np.pi*123*t)+.1*np.sin(2*np.pi*7193*t)+.08*np.sin(2*np.pi*(200*t+6000*t*t))
    x=np.column_stack([signal,.7*signal+.02*np.cos(2*np.pi*17931*t)]).astype('f4');x[0]=[1,-1];x[100:200]=1;x[200:300]=-1
    infile=OUT/'component-input.f32';x.tofile(infile);rows=[]
    for rate in rates:
        f=OUT/f'component-{rate}.f32';native('src',infile,f,rate);y=np.fromfile(f,dtype='f4').reshape(-1,2);ref=exact_ref(x,rate)
        err=y-ref;maximum=float(abs(err).max());relative=float(np.sqrt(np.sum(err**2)/np.sum(ref**2)))
        rows.append({'rate':rate,'max_absolute_error':maximum,'relative_rms_error':relative,'passed':maximum<=2e-6 and relative<=2e-5,'output_peak':float(abs(y).max()),'input_peak':float(abs(x).max())});dump('component-progress.json',rows);print('component',rate,rows[-1]['passed'],maximum,flush=True);f.unlink()
    dump('component.json',{'passed':all(r['passed'] for r in rows),'rows':rows})

def full():
    rows=[]
    for rate in rates:
        f,raw=OUT/f'engine-{rate}.f32',OUT/f'engine-reference-{rate}.f32';native('full',rate,f,raw)
        y=np.fromfile(f,dtype='f4').reshape(-1,2);x=np.fromfile(raw,dtype='f4').reshape(-1,2)
        ref=x[:len(y)] if rate==48000 else exact_ref(x,rate,len(y),round(1.11019*rate))
        err=y-ref;maximum=float(abs(err).max());relative=float(np.sqrt(np.sum(err**2)/np.sum(ref**2)))
        rows.append({'rate':rate,'max_absolute_error':maximum,'relative_rms_error':relative,'passed':maximum<=2e-6 and relative<=2e-5,'output_peak':float(abs(y).max()),'source_peak':float(abs(x).max()),'native_source_sha256':sha(raw)});dump('engine-progress.json',rows);print('engine',rate,rows[-1]['passed'],maximum,flush=True);f.unlink();raw.unlink()
    dump('engine.json',{'passed':all(r['passed'] for r in rows),'rows':rows})

def overshoot():
    n=96000;t=np.arange(n)/48000.;waves={}
    a=np.zeros(n);a[12000]=1;waves['impulse']=a
    a=np.ones(n);a[:12000]=-1;waves['step']=a
    waves['near_nyquist']=np.sin(2*np.pi*23900*t)
    a=sum(np.sin(2*np.pi*f*t+.2*i) for i,f in enumerate([53,719,3179,8011,17003,21997]));waves['normalized_multitone']=a/max(abs(a))
    # Deliberately bounded arbitrary sample sequence approaching the L1 bound at one phase.
    # Defined deterministically, not selected from measured maxima.
    a=np.ones(n);a[12000:12096:2]=-1;waves['alternating_transition']=a
    rows=[]
    for name,a in waves.items():
        x=np.column_stack([a,-a]).astype('f4');f=OUT/'overshoot-input.f32';x.tofile(f)
        for rate in rates:
            if rate==48000:y=x
            else:
                o=OUT/'overshoot-output.f32';native('src',f,o,rate);y=np.fromfile(o,dtype='f4').reshape(-1,2);o.unlink()
            peak=float(abs(y).max());rows.append({'fixture':name,'rate':rate,'input_peak':float(abs(x).max()),'output_peak':peak,'exceeds_unity':peak>1.0000001});
        dump('overshoot-progress.json',rows)
    dump('overshoot.json',{'rows':rows,'maximum_output_peak':max(r['output_peak'] for r in rows),'old_unity_limit_preserved':not any(r['exceeds_unity'] for r in rows),'scope':'Bounded component fixtures; no hidden clamp. Non48 limit contract is not preserved if any peak exceeds1.'})

def polyphase():
    rows=[];n=96000;t=np.arange(n)/48000.
    for rate in rates:
        upper=20000 if rate>=44100 else rate*.4
        frequencies=np.array([1000.,upper]);half=math.ceil(96/min(1,rate/48000))
        x=(.25*np.sin(2*np.pi*t[:,None]*frequencies)).astype('f4')
        infile,outfile=OUT/'poly-input.f32',OUT/'poly-output.f32';x.tofile(infile);native('src',infile,outfile,rate)
        y=np.fromfile(outfile,dtype='f4').reshape(-1,2)
        divisor=math.gcd(rate,48000);up,down=rate//divisor,48000//divisor
        # Independent SciPy polyphase FIR, centercompensated; sourcephase accounts
        # for native physicaldelay. No audio alignment or fitted scalar.
        shifted=.25*np.sin(2*np.pi*(t[:,None]-half/48000)*frequencies)
        taps=firwin(64*max(up,down)+1,1/max(up,down),window=('kaiser',10)) if max(up,down)>1 else np.array([1.])
        z=resample_poly(shifted,up,down,axis=0,window=taps)[:len(y)]
        time=np.arange(len(y))/rate;keep=(time>=.1)&(time<1.9);gain=[];phase=[]
        for channel,f in enumerate(frequencies):
            basis=np.column_stack([np.sin(2*np.pi*f*time[keep]),np.cos(2*np.pi*f*time[keep])])
            a=np.linalg.lstsq(basis,y[keep,channel],rcond=None)[0];b=np.linalg.lstsq(basis,z[keep,channel],rcond=None)[0]
            gain.append(float(20*np.log10(np.linalg.norm(a)/np.linalg.norm(b))))
            phase.append(float(np.angle((a[0]+1j*a[1])/(b[0]+1j*b[1]))*180/np.pi))
        rows.append({'rate':rate,'frequencies_hz':frequencies.tolist(),'native_vs_independent_polyphase_gain_db':gain,'phase_degrees':phase,'reference_fir_taps':len(taps),'scope':'Diagnostic independentpolyphase filter has its own differenttransition; no fit. Native48000 here is standalonecomponent, wrapperbypasses.'});dump('polyphase-progress.json',rows);print('polyphase',rate,max(abs(v) for v in gain),flush=True)
        outfile.unlink()
    dump('polyphase.json',{'rows':rows})

def main():
    action=sys.argv[1]
    if action=='response':response()
    elif action=='component':component()
    elif action=='full':full()
    elif action=='overshoot':overshoot()
    elif action=='polyphase':polyphase()
    else:raise ValueError(action)
if __name__=='__main__':main()
