"""Original PSS-270 post-BBD filter/mixer, NOT a PSS-780 schematic.

Source: Yamaha foldout pp10–12, G5–H5/H3–H4. FET2 is ideal ON; all bias
supplies are AC-ground. BBD output is an ideal voltage source; unknown chip
output impedance, FET resistance and nonlinearities are deliberately excluded.
"""
from pathlib import Path
import numpy as np
from scipy import linalg,signal
import warnings
from .model import MNA,CircuitParameters
SOURCE='Original Yamaha PSS-270 schematic pp10-12 G5-H5/H3-H4; transfer to PSS-780 unverified'
HERE=Path(__file__).resolve().parent

def build_post_bbd(params=None):
    p=params or CircuitParameters()
    c=MNA(['bbd_out','wet_ac','sk_a','sk_b','wet_pos','inv_minus','wet_neg','pos_ac','neg_ac','mix_l','mix_r','dry_ac'])
    c.voltage_input('bbd_out')
    def r(name,a,b,v):c.resistor('P270_'+name,a,b,v,SOURCE)
    def cap(name,a,b,v):c.capacitor('P270_'+name,a,b,v,SOURCE)
    r('BBD_LOAD','bbd_out','0',100e3);cap('BBD_SHUNT','bbd_out','0',2200e-12)
    cap('BBD_COUPLE','bbd_out','wet_ac',.1e-6)
    # Two 100k bias resistors straddle FET2. Ideal ON joins their nodes.
    r('FET_BIAS_PRE','wet_ac','0',100e3);r('FET_BIAS_POST','wet_ac','0',100e3)
    r('SK_R1','wet_ac','sk_a',22e3);r('SK_R2','sk_a','sk_b',22e3)
    cap('SK_FEEDBACK','sk_a','wet_pos',.012e-6);cap('SK_GROUND','sk_b','0',680e-12)
    c.opamp('P270_IC8A','sk_b','wet_pos','wet_pos',p)
    r('INVERTER_IN','wet_pos','inv_minus',47e3);r('INVERTER_FB','inv_minus','wet_neg',47e3)
    cap('INVERTER_FB','inv_minus','wet_neg',220e-12)
    c.opamp('P270_IC8B','0','inv_minus','wet_neg',p)
    cap('POS_COUPLE','wet_pos','pos_ac',.1e-6);cap('NEG_COUPLE','wet_neg','neg_ac',.1e-6)
    r('POS_MIX','pos_ac','mix_l',6.8e3);r('NEG_MIX','neg_ac','mix_r',6.8e3)
    # Suppress dry source for wet transfer, retaining loading and cross-coupling.
    cap('DRY_COUPLE','0','dry_ac',4.7e-6)
    for side in ['l','r']:
        r('DRY_MIX_'+side,'dry_ac','mix_'+side,8.2e3)
        r('MIX_SHUNT_'+side,'mix_'+side,'0',2.2e3)
        r('POT_'+side,'mix_'+side,'0',100e3)
    return c,{'positive':'wet_pos','negative':'wet_neg','left':'mix_l','right':'mix_r'}

def voltage_driven_state_space(c,output):
    """Eliminate prescribed input voltage before descriptor reduction.

    Capacitors at an ideal source introduce input-derivative terms. The change
    x=z+k*u, C*k=-C_source, removes those terms exactly; no fabricated source
    resistance or deleted capacitor is needed.
    """
    vi=c.index('bbd_out');ii=c.names.index('I_dac_source')
    keep=[i for i in range(len(c.G)) if i not in (vi,ii)]
    names=[c.names[i] for i in keep]
    cr=c.C[np.ix_(keep,keep)];gr=c.G[np.ix_(keep,keep)]
    cu=c.C[keep,vi:vi+1];gu=c.G[keep,vi:vi+1]
    k=linalg.lstsq(cr,-cu,cond=1e-13)[0]
    assert np.linalg.norm(cr@k+cu)<1e-15
    reduced=MNA(names);reduced.C=cr;reduced.G=gr;reduced.B=-(gr@k+gu)
    ss=reduced.state_space(output)
    return signal.StateSpace(ss.A,ss.B,ss.C,ss.D+k[names.index(output),0])

def discrete_sos(c,sample_rate,output):
    ss=voltage_driven_state_space(c,output)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore',category=signal.BadCoefficients)
        z,p,k=signal.ss2zpk(ss.A,ss.B,ss.C,ss.D)
    zd,pd,kd=signal.bilinear_zpk(z,p,k,sample_rate)
    return signal.zpk2sos(zd,pd,kd)

def process_post_bbd(audio,sample_rate,params=None):
    """Wet-only stereo at volume-pot tops for related PSS-270."""
    c,n=build_post_bbd(params)
    return np.column_stack([signal.sosfilt(discrete_sos(c,sample_rate,n[side]),audio) for side in ['left','right']])

def export_netlist(path=None,params=None):
    p=params or CircuitParameters();c,n=build_post_bbd(p)
    lines=['* Documented PSS-270 post-BBD/mixer, NOT recovered PSS-780 circuit',
           '* FET2 ideal ON; +3/+5 biases AC-grounded; BBD output ideal source.',
           '* R/C labels below are role names, not original reference designators.',
           'Vbbd bbd_out 0 AC 1','.subckt op4558 plus minus out','Ggm 0 control plus minus 1',
           f'Rdom control 0 {p.opamp_dc_gain:.12g}',f'Cdom control 0 {1/(2*np.pi*p.opamp_gbw_hz):.12g}',
           'Ebuf out 0 control 0 1',f'Rin plus minus {p.opamp_input_ohm:.12g}','.ends op4558']
    for x in c.parts:
        if x['kind'] in ('R','C') and not x['name'].endswith('_Rin'):
            lines.append(f"{x['kind']}{x['name']} {x['a']} {x['b']} {x['value']:.12g}")
        elif x['kind']=='opamp':lines.append(f"X{x['name']} {x['plus']} {x['minus']} {x['out']} op4558")
    lines+=['.ac dec 100 1 200000','.print ac vdb(mix_l) vp(mix_l) vdb(mix_r) vp(mix_r)','.end']
    (Path(path) if path else HERE/'pss270_related_chorus.cir').write_text('\n'.join(lines)+'\n')
    return c,n
