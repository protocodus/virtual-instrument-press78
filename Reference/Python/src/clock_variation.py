"""Optional common-clock timebase experiment around the frozen FM renderer.

No clock-error values are inferred from the instrument. The nominal engine
cadence remains its existing simulation hypothesis. This adapter changes the
timebase of the whole digital core while leaving external MIDI timestamps and
the later analog circuitry in real seconds. It is not a DAC jitter emulator.
"""
from dataclasses import dataclass, asdict
import math
import numpy as np
from pss780 import render_program_sequence, njit


@dataclass(frozen=True)
class ClockProfile:
    offset_ppm: float = 0.
    drift_peak_ppm: float = 0.
    drift_hz: float = .1
    periodic_jitter_rms_seconds: float = 0.
    periodic_jitter_hz: float = 100.

    def __post_init__(self):
        if not all(np.isfinite(v) for v in asdict(self).values()):
            raise ValueError('Clock profile must be finite')
        if self.drift_hz <= 0 or self.periodic_jitter_hz <= 0:
            raise ValueError('Positive modulation frequencies required')
        if self.periodic_jitter_rms_seconds < 0:
            raise ValueError('Jitter RMS must be nonnegative')
        if self.maximum_rate_deviation >= .5:
            raise ValueError('Clock excursion exceeds the bounded experiment domain')

    @property
    def maximum_rate_deviation(self):
        return (abs(self.offset_ppm)*1e-6+abs(self.drift_peak_ppm)*1e-6
                +2*np.pi*self.periodic_jitter_hz*np.sqrt(2)*self.periodic_jitter_rms_seconds)

    @property
    def is_ideal(self):
        return self.maximum_rate_deviation == 0

    def nominal_time(self, real_seconds):
        """Integral of the positive common clock rate, with tau(0)=0.

        Jitter here is one deterministic phase-modulation tone. It is neither
        random phase noise nor a measured resonator spectrum.
        """
        t=np.asarray(real_seconds,dtype=float)
        return ((1+self.offset_ppm*1e-6)*t
                +self.drift_peak_ppm*1e-6*np.sin(2*np.pi*self.drift_hz*t)/(2*np.pi*self.drift_hz)
                +np.sqrt(2)*self.periodic_jitter_rms_seconds*np.sin(2*np.pi*self.periodic_jitter_hz*t))

    def rate_ratio(self, real_seconds):
        t=np.asarray(real_seconds,dtype=float)
        return (1+self.offset_ppm*1e-6
                +self.drift_peak_ppm*1e-6*np.cos(2*np.pi*self.drift_hz*t)
                +2*np.pi*self.periodic_jitter_hz*np.sqrt(2)*self.periodic_jitter_rms_seconds
                 *np.cos(2*np.pi*self.periodic_jitter_hz*t))


@njit(cache=True)
def _sinc_sample(source, positions, cutoff, radius=64):
    """Offline bandlimited timebase conversion; four-term Blackman-Harris."""
    out=np.zeros(len(positions))
    for n in range(len(positions)):
        p=positions[n];base=int(math.floor(p));value=0.;total=0.
        for k in range(base-radius+1,base+radius+1):
            d=p-k
            w=(.35875+.48829*math.cos(math.pi*d/radius)
               +.14128*math.cos(2*math.pi*d/radius)
               +.01168*math.cos(3*math.pi*d/radius))
            z=math.pi*cutoff*d
            w*=cutoff*(1. if abs(z)<1e-14 else math.sin(z)/z)
            total+=w
            if 0<=k<len(source):value+=w*source[k]
        out[n]=value/total
    return out


def map_events(notes,programs,profile):
    mapped_notes=[]
    for event in notes:
        start=float(event['start']);gate=float(event['gate'])
        if not np.isfinite(start) or start<0 or not np.isfinite(gate) or gate<0:
            raise ValueError('Nonnegative finite note times required')
        mapped_notes.append({**event,'start':float(profile.nominal_time(start)),
                             'gate':float(profile.nominal_time(start+gate)-profile.nominal_time(start))})
    mapped_programs=[]
    for event in programs:
        time=float(event['time'])
        if not np.isfinite(time) or time<0:raise ValueError('Nonnegative finite program time required')
        mapped_programs.append({**event,'time':float(profile.nominal_time(time))})
    return mapped_notes,mapped_programs


def render_clocked_performance(notes,programs,duration,sr=48000,*,profile=None,
                               model=None,initial_patch=0,max_voices=12):
    """Raw FM in real time under an explicit common-clock hypothesis.

    All note on/off and program events are first mapped into chip-clock time.
    The raw digital result is then reconstructed in real time. Apply analog
    filters/chorus afterward so their independent time constants do not drift.
    Zero variation bypasses conversion and is bit-identical to the baseline.
    This inherits baseline phase-reset, envelope and allocation assumptions.
    """
    profile=ClockProfile() if profile is None else profile
    if not isinstance(profile,ClockProfile):raise TypeError('ClockProfile required')
    if not np.isfinite(duration) or duration<0 or duration>590:
        raise ValueError('Duration must be finite in0..590seconds')
    if not isinstance(sr,(int,np.integer)) or isinstance(sr,bool) or not 8000<=sr<=384000:
        raise ValueError('Integer sample rate8..384kHz required')
    notes=list(notes);programs=list(programs)
    kwargs=dict(model=model,initial_patch=initial_patch,max_voices=max_voices)
    if profile.is_ideal:
        return render_program_sequence(notes,programs,duration,sr,**kwargs)
    if (profile.drift_peak_ppm and profile.drift_hz>sr/8
            or profile.periodic_jitter_rms_seconds and profile.periodic_jitter_hz>sr/8):
        raise ValueError('Timing modulation must be below one eighth of the host rate')
    wanted=round(duration*sr)
    if wanted==0:return np.zeros(0)
    clock_notes,clock_programs=map_events(notes,programs,profile)
    nominal_end=float(profile.nominal_time(duration))+128/sr
    if nominal_end>600:raise ValueError('Nominal endpoint exceeds frozen renderer domain')
    source=render_program_sequence(clock_notes,clock_programs,nominal_end,sr,**kwargs)
    positions=profile.nominal_time(np.arange(wanted)/sr)*sr
    cutoff=min(1.,1/(1+profile.maximum_rate_deviation))
    return _sinc_sample(source,positions,cutoff)
