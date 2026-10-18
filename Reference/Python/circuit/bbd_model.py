"""Manufacturer-conditioned MN3206 experiment, not a recovered PSS-780 circuit.

Input: AC volts directly at MN3206 input, nominal DC bias 2.5 V on 5 V supply.
Output: wet-only stereo volts at documented PSS-270 volume-pot tops. No input
pre-filter or dry path is asserted. Cubic distortion is a single-point scenario;
noise is a 100 kHz manufacturer MAXIMUM scenario with assumed flat 20Hz–20kHz
source PSD. These cannot identify the real keyboard's levels or spectrum.
"""
import math
import numpy as np
from scipy import signal
from .pss270_chorus import process_post_bbd

THD_ANCHOR_RMS_V=.25
THD_ANCHOR_RATIO=.003
NOISE_AWEIGHTED_MAX_V=100e-6
CUBIC_COEFFICIENT=4*THD_ANCHOR_RATIO/(2*THD_ANCHOR_RMS_V**2*(1+3*THD_ANCHOR_RATIO))


def a_weighting_power(f):
    """Analog A-weighting power, normalized to 0dB at 1kHz (not a PSD claim)."""
    f=np.asarray(f,dtype=float);f2=f*f
    def amp(v2):
        return 12194.217**2*v2*v2/((v2+20.598997**2)*np.sqrt((v2+107.65265**2)*(v2+737.86223**2))*(v2+12194.217**2))
    return (amp(f2)/amp(1000.**2))**2


def a_weighted_rms(audio,fs):
    """Finite-record spectral A-weighted RMS, with DC removed."""
    x=np.asarray(audio,dtype=float)
    if not len(x):return 0.
    z=np.fft.rfft(x);f=np.fft.rfftfreq(len(x),1/fs)
    weight=np.full(len(z),2.);weight[0]=1
    if len(x)%2==0:weight[-1]=1
    return float(np.sqrt(np.sum(abs(z)**2*a_weighting_power(f)*weight)/len(x)**2))


def nonlinear_transfer(audio_volts):
    """Compressive cubic calibrated to THD=.3% for a .25Vrms sine.

    Harmonic distribution/sign are a chosen scenario, not measured. Beyond
    +/-1V AC use a monotone tangent continuation to prevent cubic fold-back;
    the continuation is numerical extrapolation and is flagged in diagnostics.
    No saturation threshold is claimed for MN3206.
    """
    x=np.asarray(audio_volts,dtype=float);a=CUBIC_COEFFICIENT
    limited=np.clip(x,-1.,1.)
    return limited-a*limited**3+(x-limited)*(1-3*a)


def noise_source(n,fs,seed=780,target_aweighted_v=NOISE_AWEIGHTED_MAX_V):
    """Band-limited Gaussian scenario, exactly normalized to stated A-RMS.

    Flat 20Hz–20kHz unweighted PSD is an explicit shape assumption. This
    normalizes a noise fixture, never normalizes the musical input. Seed fixes
    a whole offline block; overlapping separately generated blocks do not
    represent a single continuous stochastic realization.
    """
    if n==0:return np.zeros(0)
    white=np.random.default_rng(seed).standard_normal(n)
    z=np.fft.rfft(white);f=np.fft.rfftfreq(n,1/fs)
    z[(f<20)|(f>min(20000,fs*.499))]=0
    y=np.fft.irfft(z,n=n)
    rms=a_weighted_rms(y,fs)
    return y*(target_aweighted_v/rms) if rms else np.zeros(n)


def held_bbd(audio_volts,fs,clock_hz=40000.,start_seconds=0.):
    """128 physical stages = 64 complete CP periods, asynchronous sample/hold.

    Source history preceding this offline block is zero. Use pre-roll for
    slices. CP phase is tied to absolute time and is not reset at each note.
    """
    x=np.asarray(audio_volts,dtype=float);n=len(x)
    if not n:return x.copy()
    phase0=start_seconds*clock_hz
    phase=phase0+np.arange(n)*(clock_hz/fs)
    if not np.isfinite(phase).all() or np.max(abs(phase))>2**48:
        raise ValueError('Clock phase exceeds numerical domain')
    # Snap only machine-roundoff neighborhoods of exact CP boundaries. Absolute
    # edge-time comparisons can choose opposite sides of a boundary in crops.
    tolerance=32*np.finfo(float).eps*max(1.,float(np.max(abs(phase))))
    cycle0=int(np.ceil(phase0-tolerance));cycle1=int(np.floor(phase[-1]+tolerance))
    if cycle1<cycle0:return np.zeros(n)
    cycles=np.arange(cycle0,cycle1+1,dtype=np.int64)
    positions=(cycles-phase0)*(fs/clock_hz)
    near=np.rint(positions)
    positions=np.where(abs(positions-near)<=tolerance*(fs/clock_hz),near,positions)
    captured=np.interp(positions,np.arange(n),x)
    delayed=np.zeros_like(captured)
    if len(captured)>64:delayed[64:]=captured[:-64]
    idx=np.floor(phase+tolerance).astype(np.int64)-cycle0
    out=np.zeros(n);valid=idx>=0;out[valid]=delayed[idx[valid]]
    return out


def process_sibling_bbd(mono_volts,sample_rate,*,start_seconds=0.,nonlinear=False,
                        noise=False,seed=780,clock_hz=40000.,clock_mode='fixed',
                        return_sources=False):
    """Return (wet_stereo_volts, JSON-safe diagnostics), no peak normalization.

    Integer-Hz fixed clocks 10–200kHz and positive integer-Hz host rates.
    Internal rate is an integer multiple of CP, >=8*CP and >=192kHz. Rational
    resampling aligns its grid across crops by padding to a common host phase.
    The .3% distortion anchor applies only to 40kHz CP; the 100uVrms-A noise
    maximum applies only to 100kHz CP. Other enabled combinations raise errors
    instead of silently transferring calibration between operating conditions.
    return_sources additionally includes internal-rate arrays for test fixtures.
    """
    x=np.asarray(mono_volts,dtype=float)
    if x.ndim!=1 or not np.isfinite(x).all():raise ValueError('Finite mono AC voltage samples required')
    if not np.isfinite(sample_rate) or sample_rate<=0:raise ValueError('Positive finite sample_rate required')
    if sample_rate!=int(sample_rate):raise ValueError('Integer-Hz host sample_rate required')
    if not np.isfinite(start_seconds):raise ValueError('Finite start_seconds required')
    if clock_mode!='fixed':raise ValueError('Only fixed manufacturer-condition clocks are implemented')
    if not np.isfinite(clock_hz) or not 10000<=clock_hz<=200000:raise ValueError('MN3206 CP operating range is 10–200kHz')
    if clock_hz!=int(clock_hz):raise ValueError('Integer-Hz fixed clock required')
    if nonlinear and clock_hz!=40000:raise ValueError('THD scenario is anchored only at40kHz CP')
    if noise and clock_hz!=100000:raise ValueError('A-weighted maximum noise scenario applies only at100kHz CP')
    fs=int(clock_hz)*max(8,int(np.ceil(192000/clock_hz)))
    divisor=math.gcd(fs,int(sample_rate));up=fs//divisor;down=int(sample_rate)//divisor
    peak=float(np.max(abs(x))) if len(x) else 0.
    if peak>np.finfo(float).max**.25:raise ValueError('Input voltage exceeds numerical domain')
    host_position=start_seconds*sample_rate
    if not np.isfinite(host_position) or abs(host_position)>2**48:raise ValueError('Start time exceeds numerical domain')
    host_tolerance=32*np.finfo(float).eps*max(1.,abs(host_position))
    prefix=int(np.floor(host_position+host_tolerance))%down
    aligned_start=start_seconds-prefix/sample_rate
    diag={'model':'MN3206 manufacturer-conditioned scenario plus documented related PSS-270 postnetwork',
          'input_point':'AC volts at MN3206 input; pre-BBD filter excluded',
          'output_point':'Wet-only PSS-270 stereo volume-pot tops; not PSS-780 identified output',
          'clock_hz':float(clock_hz),'clock_mode':'fixed','physical_stages':128,'complete_cp_delay_cycles':64,
          'ideal_delay_seconds':64/float(clock_hz),'internal_sample_rate':float(fs),
          'oversample_ratio':fs/sample_rate,'resample_up':up,'resample_down':down,
          'samples_per_cp':fs/clock_hz,'grid_alignment_prefix_host_samples':prefix,
          'input_peak_v':peak,'input_rms_v':float(np.sqrt(np.mean(x*x))) if len(x) else 0.,
          'nonlinear':bool(nonlinear),'noise':bool(noise),'seed':int(seed),
          'thd_anchor':{'rms_v':.25,'frequency_hz':1000.,'clock_hz':40000.,'static_transfer_ratio':.003,'supply_v':5.},
          'assumed_nominal_dc_bias_v':2.5,
          'noise_anchor':{'maximum_aweighted_rms_v':1e-4,'clock_hz':100000.,'supply_v':5.,'spectrum':'Assumed flat20Hz–20kHz, NOT manufacturer-specified PSD'},
          'warnings':[]}
    if peak>1.:
        diag['warnings'].append('Input exceeds +/-1V AC polynomial range; tangent continuation is unvalidated and is not hardware clipping.')
    if peak>np.sqrt(2)*.6:
        diag['warnings'].append('Peak exceeds amplitude of the datasheet0.6Vrms sinusoidal signal-swing condition; actual waveform headroom is unverified.')
    if noise:diag['warnings'].append('Noise is a manufacturer MAXIMUM-bound scenario, not typical PSS-780 noise; spectrum and supply conditions are assumed.')
    if not len(x):return np.zeros((0,2)),diag
    padded=np.pad(x,(prefix,0))
    # Suppress interpolation images before CP sampling: the default FIR leaves
    # images which fold into the audio band at 40kHz. This is numerical signal
    # reconstruction, not a newly asserted hardware anti-alias filter.
    high=signal.resample_poly(padded,up,down,window=('kaiser',8.6))
    transformed=nonlinear_transfer(high) if nonlinear else high
    held=held_bbd(transformed,fs,clock_hz,aligned_start)
    source_noise=noise_source(len(high),fs,seed) if noise else np.zeros(len(high))
    post=process_post_bbd(held+source_noise,fs)
    result=signal.resample_poly(post,down,up,axis=0,window=('kaiser',8.6))[prefix:prefix+len(x)]
    diag['source_noise_aweighted_rms_v']=a_weighted_rms(source_noise,fs) if noise else 0.
    diag['output_rms_v']=np.sqrt(np.mean(result*result,axis=0)).tolist()
    if return_sources:diag['sources']={'internal_input_v':high,'held_signal_v':held,'source_noise_v':source_noise,'internal_sample_rate':fs}
    return result,diag
