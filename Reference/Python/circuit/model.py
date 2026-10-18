"""Hardware-informed circuit experiment. This is NOT a circuit-exact PSS-780 model.

Evidence: PSS-780 service parts list identifies YM3420BF/C, NJM4558 and
MN3102/MN3206. Investigator's YM3420BF drawing shows 47k input resistor,
unity follower, 2.2k output resistor, but does not identify its keyboard.
The PSS-480 factory foldout acquired in v2 resolves that drawing's complete
related-hardware buffer/preamp path. model='pss480' simulates that documented
path through the volume-pot input. Its application to PSS-780 is a surrogate,
not proof that the two instruments use the same analog board.
Optional reconstruction network and clock/modulation values remain hypotheses.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import warnings
import numpy as np
from scipy import signal, linalg


@dataclass(frozen=True)
class CircuitParameters:
    # Observed in d-tech YM3420BF drawing; transfer to PSS-780 remains an inference.
    buffer_input_ohm: float = 47000.0
    buffer_output_ohm: float = 2200.0
    # PSS-480 factory overall schematic, D4 and G3; related hardware, not PSS-780.
    pss480_buffer_lowpass_f: float = 10e-9
    pss480_mix_input_f: float = 1e-6
    pss480_fm_mix_ohm: float = 47000.0
    pss480_drum_mix_ohm: float = 10000.0
    pss480_feedback_ohm: float = 47000.0
    pss480_feedback_f: float = 220e-12
    pss480_output_f: float = 1e-6
    # NJM4558 manufacturer's typical values, not measurements of this instrument.
    opamp_dc_gain: float = 100000.0
    opamp_gbw_hz: float = 3000000.0
    opamp_input_ohm: float = 5000000.0
    # Load and ALL following RC/LFO/mix values are unverified hypotheses.
    line_load_ohm: float = 100000.0
    coupling_f: float = 1e-6
    bias_ohm: float = 47000.0
    lowpass_r_ohm: float = 8200.0
    lowpass_feedback_f: float = 4.7e-9
    lowpass_ground_f: float = 2.2e-9
    output_coupling_f: float = 10e-6
    # 10k dual volume potentiometer is confirmed; position/taper/loading are not.
    volume_pot_ohm: float = 10000.0
    volume_fraction: float = 0.8
    # 128 physical stages is confirmed by PSS-780 parts list and Panasonic catalog.
    bbd_stages: int = 128
    bbd_clock_hz: float = 22000.0
    bbd_clock_depth_hz: float = 8000.0
    chorus_lfo_hz: float = 0.65
    chorus_mix: float = 0.35


class MNA:
    """Linear modified nodal analysis, including finite one-pole opamps.

    C dx/dt + G x = B u. Node voltages and ideal voltage-source branch
    currents are retained. Algebraic variables are eliminated by SVD of C
    before converting the remaining dynamics to a state-space audio filter.
    """
    def __init__(self, nodes):
        self.names = list(nodes)
        self.ids = {n:i for i,n in enumerate(nodes)}
        self.n = len(nodes)
        self.G = np.zeros((self.n,self.n))
        self.C = np.zeros_like(self.G)
        self.B = np.zeros((self.n,1))
        self.parts = []

    def index(self, node):
        return None if node == '0' else self.ids[node]

    def stamp(self, matrix, a, b, value):
        a,b = self.index(a),self.index(b)
        if a is not None: matrix[a,a] += value
        if b is not None: matrix[b,b] += value
        if a is not None and b is not None:
            matrix[a,b] -= value
            matrix[b,a] -= value

    def resistor(self, name, a, b, value, provenance):
        self.stamp(self.G,a,b,1/value)
        self.parts.append(dict(name=name,kind='R',a=a,b=b,value=value,unit='ohm',provenance=provenance))

    def capacitor(self, name, a, b, value, provenance):
        self.stamp(self.C,a,b,value)
        self.parts.append(dict(name=name,kind='C',a=a,b=b,value=value,unit='F',provenance=provenance))

    def branch(self, name):
        n = len(self.G)
        self.G=np.pad(self.G,((0,1),(0,1)))
        self.C=np.pad(self.C,((0,1),(0,1)))
        self.B=np.pad(self.B,((0,1),(0,0)))
        self.names.append(name)
        return n

    def voltage_input(self, node):
        k=self.branch('I_dac_source');i=self.index(node)
        self.G[i,k]=1;self.G[k,i]=1;self.B[k,0]=1

    def opamp(self, name, plus, minus, out, params):
        k=self.branch('I_'+name);o=self.index(out);p=self.index(plus);m=self.index(minus)
        self.G[o,k]=1
        self.G[k,o]+=1
        if p is not None:self.G[k,p]-=params.opamp_dc_gain
        if m is not None:self.G[k,m]+=params.opamp_dc_gain
        self.C[k,o]=params.opamp_dc_gain/(2*np.pi*params.opamp_gbw_hz)
        self.resistor(name+'_Rin',plus,minus,params.opamp_input_ohm,'NJM4558 typical differential input resistance')
        self.parts.append(dict(name=name,kind='opamp',plus=plus,minus=minus,out=out,
            dc_gain=params.opamp_dc_gain,gbw_hz=params.opamp_gbw_hz,
            provenance='NJM4558 typical one-pole macro; not transistor-level'))

    def frequency_response(self, hz, output):
        c=np.zeros(len(self.G));c[self.index(output)]=1
        return np.asarray([(c@np.linalg.solve(self.G+2j*np.pi*f*self.C,self.B)).item() for f in np.atleast_1d(hz)])

    def state_space(self, output):
        U,s,Vh=linalg.svd(self.C)
        r=np.count_nonzero(s>max(s)*1e-13)
        V=Vh.T;Ud=U[:,:r];Ua=U[:,r:];Vd=V[:,:r];Va=V[:,r:]
        gdd=Ud.T@self.G@Vd;gda=Ud.T@self.G@Va
        gad=Ua.T@self.G@Vd;gaa=Ua.T@self.G@Va
        bd=Ud.T@self.B;ba=Ua.T@self.B
        invgad=linalg.solve(gaa,gad);invba=linalg.solve(gaa,ba)
        A=-(gdd-gda@invgad)/s[:r,None]
        B=(bd-gda@invba)/s[:r,None]
        selector=np.zeros((1,len(self.G)));selector[0,self.index(output)]=1
        C=selector@(Vd-Va@invgad)
        D=selector@Va@invba
        return signal.StateSpace(A,B,C,D)

    def discrete_sos(self, fs, output):
        """Trapezoidal state-space transfer as efficient second-order sections."""
        ss=self.state_space(output)
        # Convert to low-order SOS for efficient stable streaming. Bilinear
        # integration is exactly trapezoidal MNA for this linear descriptor.
        # SVD elimination leaves near-zero polynomial leading coefficients.
        # scipy trims these; independent MNA/SS and audio/AC tests in analyze.py
        # validate the reduction to <1e-6 absolute response error.
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=signal.BadCoefficients)
            z,p,k=signal.ss2zpk(ss.A,ss.B,ss.C,ss.D)
        zd,pd,kd=signal.bilinear_zpk(z,p,k,fs)
        return signal.zpk2sos(zd,pd,kd)

    def process(self, audio, fs, output):
        return signal.sosfilt(self.discrete_sos(fs,output),np.asarray(audio,dtype=float),axis=0)


def build_circuit(params=None, model='buffer'):
    p=params or CircuitParameters()
    if model=='pss480':return build_pss480_circuit(p)
    if model not in ('buffer','hypothesis'):
        raise ValueError("model must be 'buffer', 'pss480', or 'hypothesis'")
    nodes=['dac_tb','buffer_plus','buffer_out','buffer_series']
    if model=='hypothesis':nodes+=['ac_in','lp_a','lp_b','lp_out','pot_top','aux_out']
    c=MNA(nodes);c.voltage_input('dac_tb')
    observed='d-tech YM3420BF drawing; PSS-780 application inferred'
    unknown='Hypothesis: exact PSS-780 schematic/value unavailable'
    c.resistor('OBS_R47K','dac_tb','buffer_plus',p.buffer_input_ohm,observed)
    c.opamp('NJM4558_buffer','buffer_plus','buffer_out','buffer_out',p)
    c.resistor('OBS_R2K2','buffer_out','buffer_series',p.buffer_output_ohm,observed)
    if model=='buffer':
        c.resistor('H_Rload','buffer_series','0',p.line_load_ohm,unknown)
        return c,'buffer_series'
    c.capacitor('H_Ccouple','buffer_series','ac_in',p.coupling_f,unknown)
    c.resistor('H_Rbias','ac_in','0',p.bias_ohm,unknown)
    c.resistor('H_Rlp1','ac_in','lp_a',p.lowpass_r_ohm,unknown)
    c.resistor('H_Rlp2','lp_a','lp_b',p.lowpass_r_ohm,unknown)
    c.capacitor('H_Cfeedback','lp_a','lp_out',p.lowpass_feedback_f,unknown)
    c.capacitor('H_Cground','lp_b','0',p.lowpass_ground_f,unknown)
    c.opamp('H_NJM4558_filter','lp_b','lp_out','lp_out',p)
    c.capacitor('H_Cout','lp_out','pot_top',p.output_coupling_f,unknown)
    c.resistor('H_Rpot_top','pot_top','aux_out',max(1,p.volume_pot_ohm*(1-p.volume_fraction)),unknown)
    c.resistor('H_Rpot_bottom','aux_out','0',max(1,p.volume_pot_ohm*p.volume_fraction),unknown)
    c.resistor('H_Rload','aux_out','0',p.line_load_ohm,unknown)
    return c,'aux_out'


def build_pss480_circuit(params=None):
    """Factory PSS-480 D4/G3 path, with both stereo mixing loads retained.

    FM output through IC13 followers and 2.2k/10nF filter; common 1uF
    coupling into the two IC12 inverting preamps; 1uF outputs loaded by the
    documented A10k volume pots. Inactive rhythm outputs are AC-grounded
    ideal voltage sources through their actual 1uF/10k mixing paths.
    Output is left volume-pot TOP, not a fabricated PSS-780 AUX connector.
    The 2.5V reference is small-signal ground. No power-amp/speaker model.
    """
    p=params or CircuitParameters()
    nodes=['dac_tb','ic13_5','ic13_7','ic13_3','ic13_1','fm_ac']
    for side in ('l','r'):nodes += ['mix_'+side,'drum_ac_'+side,'preamp_'+side,'volume_top_'+side]
    c=MNA(nodes);c.voltage_input('dac_tb')
    source='Yamaha PSS-480 overall circuit diagram D4/G3/K5; PSS-780 transfer unverified'
    c.resistor('P480_R47K_TB','dac_tb','ic13_5',p.buffer_input_ohm,source)
    c.opamp('P480_IC13A','ic13_5','ic13_7','ic13_7',p)
    c.resistor('P480_R2K2_LP','ic13_7','ic13_3',p.buffer_output_ohm,source)
    c.capacitor('P480_C10N_LP','ic13_3','0',p.pss480_buffer_lowpass_f,source)
    c.opamp('P480_IC13B','ic13_3','ic13_1','ic13_1',p)
    c.capacitor('P480_C1U_FM','ic13_1','fm_ac',p.pss480_mix_input_f,source)
    for side in ('l','r'):
        mix='mix_'+side;pre='preamp_'+side;out='volume_top_'+side;drum='drum_ac_'+side
        c.resistor('P480_R47K_FM_'+side,'fm_ac',mix,p.pss480_fm_mix_ohm,source)
        c.capacitor('P480_C1U_RHYTHM_'+side,'0',drum,p.pss480_mix_input_f,source+'; inactive rhythm source AC grounded')
        c.resistor('P480_R10K_RHYTHM_'+side,drum,mix,p.pss480_drum_mix_ohm,source)
        c.resistor('P480_R47K_FB_'+side,mix,pre,p.pss480_feedback_ohm,source)
        c.capacitor('P480_C220P_FB_'+side,mix,pre,p.pss480_feedback_f,source)
        c.opamp('P480_IC12_'+side,'0',mix,pre,p)
        c.capacitor('P480_C1U_OUT_'+side,pre,out,p.pss480_output_f,source)
        c.resistor('P480_R10K_VOLUME_'+side,out,'0',p.volume_pot_ohm,source+'; volume-pot top endpoint, wiper unloaded')
    return c,'volume_top_l'


def bbd128(audio, fs, params=None, return_clock=False):
    """Ideal two-phase BBD bucket-transfer macro with asynchronous clock events.

    MN3206 has 128 physical stages, two transfers per complete CP cycle,
    therefore 64 stored samples at input acquisition frequency fCP.
    Each input clock edge is interpolated from the oversampled analog signal;
    the output holds the acquisition from 64 cycles earlier. LFO affects actual
    edge timing, avoiding the incorrect instantaneous-delay approximation.
    No fabricated MOS parameters, charge leakage, noise, or clock feedthrough.
    """
    p=params or CircuitParameters();x=np.asarray(audio,dtype=float)
    if x.ndim!=1:raise ValueError('BBD input must be mono')
    if p.bbd_stages!=128:raise ValueError('PSS-780 evidence identifies 128 stages')
    if fs<4*(p.bbd_clock_hz+abs(p.bbd_clock_depth_hz)):
        raise ValueError('Use an internal sample rate >= four times maximum clock')
    n=len(x)
    if n==0:return (x, {}) if return_clock else x
    t=np.arange(n)/fs
    f=p.bbd_clock_hz+p.bbd_clock_depth_hz*np.sin(2*np.pi*p.chorus_lfo_hz*t)
    if np.any(f<=0):raise ValueError('Clock must remain positive')
    phase=np.r_[0,np.cumsum((f[1:]+f[:-1])/(2*fs))]
    edge_cycles=np.arange(int(np.floor(phase[-1]))+1)
    edge_t=np.interp(edge_cycles,phase,t)
    captured=np.interp(edge_t,t,x)
    latency=p.bbd_stages//2
    held=np.zeros_like(captured)
    if len(held)>latency:held[latency:]=captured[:-latency]
    idx=np.maximum(0,np.searchsorted(edge_t,t,side='right')-1)
    y=held[idx]
    if return_clock:
        return y,dict(time_s=t,clock_hz=f,edge_time_s=edge_t,
            actual_delay_s=edge_t[latency:]-edge_t[:-latency])
    return y


def process_audio(audio, sample_rate, chorus=False, model='buffer', params=None):
    """Offline process numpy mono/stereo audio; chorus yields stereo from mono.

    Input/output units are volts relative to the unspecified analog bias.
    No normalization, noise addition or nonlinear saturation is applied.
    'buffer' retains the v1 minimal path. 'pss480' includes the complete
    documented related-instrument buffer and preamp; it is an explicit
    surrogate for the still unavailable PSS-780 schematic. 'hypothesis'
    retains the guessed RC reconstruction/coupling/pot network.
    """
    p=params or CircuitParameters();x=np.asarray(audio,dtype=np.float64)
    if sample_rate<=0:raise ValueError('sample_rate must be positive')
    if x.ndim not in (1,2):raise ValueError('audio must be mono or samples x channels')
    if len(x)==0:return np.zeros((0,2)) if chorus else x.copy()
    if not np.all(np.isfinite(x)):raise ValueError('audio must contain finite values')
    # Oversample analog reconstruction/clock events and anti-alias on return.
    factor=max(1,int(np.ceil(max(192000,4*(p.bbd_clock_hz+abs(p.bbd_clock_depth_hz)))/sample_rate))) if chorus else 4
    fs=sample_rate*factor
    hi=signal.resample_poly(x,factor,1,axis=0)
    circuit,out=build_circuit(p,model)
    dry=circuit.process(hi,fs,out)
    if chorus:
        mono=hi if hi.ndim==1 else hi.mean(axis=1)
        # Filtering around the sampled analog device requires assumptions.
        # Apply the hypothesis lowpass to wet path even in 'buffer' mode.
        wet_net,wet_out=build_circuit(p,'hypothesis')
        pre=wet_net.process(mono,fs,wet_out)
        wet=wet_net.process(bbd128(pre,fs,p),fs,wet_out)
        drymono=dry if dry.ndim==1 else dry.mean(axis=1)
        # Antiphase stereo wet mix is a stated topology hypothesis.
        processed=np.column_stack((drymono+p.chorus_mix*wet,drymono-p.chorus_mix*wet))
    else:processed=dry
    return signal.resample_poly(processed,1,factor,axis=0)[:len(x)]


def export_netlist(path, params=None, model='hypothesis'):
    p=params or CircuitParameters();c,out=build_circuit(p,model)
    lines=['* PSS-780 hardware-informed experiment; NOT the verified Yamaha schematic',
        '* OBS_ values from d-tech YM3420BF drawing, instrument unspecified.',
        '* P480_ values from PSS-480 factory schematic; PSS-780 transfer unverified.',
        '* H_ values/topology are hypotheses. Opamp is a typical linear macro.',
        'Vdac dac_tb 0 AC 1', '.subckt op4558 plus minus out',
        'Ggm 0 control plus minus 1',f'Rdom control 0 {p.opamp_dc_gain:.12g}',
        f'Cdom control 0 {1/(2*np.pi*p.opamp_gbw_hz):.12g}',
        'Ebuf out 0 control 0 1',f'Rin plus minus {p.opamp_input_ohm:.12g}',
        '.ends op4558']
    for part in c.parts:
        if part['kind'] in ('R','C') and not part['name'].endswith('_Rin'):
            lines+=[f"* {part['provenance']}",f"{part['kind']}{part['name']} {part['a']} {part['b']} {part['value']:.12g}"]
        elif part['kind']=='opamp':
            lines+=[f"X{part['name']} {part['plus']} {part['minus']} {part['out']} op4558"]
    lines += ['.ac dec 100 1 200000',f'.print ac vdb({out}) vp({out})','.end']
    Path(path).write_text('\n'.join(lines)+'\n')
    return c
