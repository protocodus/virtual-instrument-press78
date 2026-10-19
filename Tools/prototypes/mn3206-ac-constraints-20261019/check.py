"""Bounded stdlib verification of the frozen graph oracle; no audio execution."""
from collections import Counter
from dataclasses import asdict
from fractions import Fraction as F
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import sys
import traceback
from mn3206_ac import MN3206AC,DESIGN_SHA256

HERE=Path(__file__).resolve().parent
COUNTS=Counter()
def check(ok,group):
    COUNTS[group]+=1
    if not ok: raise AssertionError(group)
def binding(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def rejects(fn,group):
    try:fn()
    except (ValueError,TypeError,OverflowError):check(True,group)
    else:check(False,group)
def rational_close(actual,expected):
    return abs(actual-float(expected))<=max(math.ulp(float(expected))*2,1e-16)


def run():
    d=json.loads((HERE/'design-frozen.json').read_text())
    check(binding(HERE/'design-frozen.json')['sha256']==DESIGN_SHA256,'design_binding')
    for s in ('curve_page','table_page','manufacturer_pdf'):
        source=d['sources'][s]
        actual=binding(Path(source['path']))
        check(actual['sha256']==source['sha256'] and actual['bytes']==source['bytes'],'primary_source_binding')
    for b in json.loads((HERE/'implementation-bound.json').read_text())['files']:
        actual=binding(HERE/b['path'])
        check(actual['sha256']==b['sha256'] and actual['bytes']==b['bytes'],'implementation_before_execution_binding')
    model=MN3206AC()
    ports=dict(mode=model.MODE,axis_reference=model.AXIS_REFERENCE,vdd_v=5,vgg_v=F(14,3),vss_v=0,cp_hz=40000,signal_hz=1000,temperature_c=25,lpf_hz=20000,lpf_db_per_octave=-48)
    coords=list(zip(map(F,d['readings']['pixel_x']),map(F,d['readings']['pixel_y'])))
    axis=d['axis']
    xlo,xhi,yzero,ytop=map(F,[axis['x_low_px'],axis['x_high_px'],axis['y_zero_px'],axis['y_high_px']])
    lower,upper=map(F,[axis['x_low_dbm'],axis['x_high_dbm']])
    height=F(axis['y_high_thd_percent']);width=upper-lower
    def interp(x):
        for (xa,ya),(xb,yb) in zip(coords,coords[1:]):
            if xa<=x<=xb:
                return (ya*(xb-x)+yb*(x-xa))/(xb-xa)
        raise AssertionError('Independent query outside raw support')
    xs=[(xlo+i,xhi+j,3*k) for i,j,k in product((-1,1),repeat=3)]
    ys=[(yzero+i,ytop+j,3*k) for i,j,k in product((-1,1),repeat=3)]
    low=max(lower+width*(coords[0][0]-shift-a)/(b-a) for a,b,shift in xs)
    high=min(lower+width*(coords[-1][0]-shift-a)/(b-a) for a,b,shift in xs)
    check((low,high)==model.input_range_exact_axis_dbm,'independent_common_support')
    check((lower+width*(coords[0][0]-xlo)/(xhi-xlo),lower+width*(coords[-1][0]-xlo)/(xhi-xlo))==model.nominal_input_range_exact_axis_dbm,'nominal_support')
    for x,y in coords:
        level=lower+width*(x-xlo)/(xhi-xlo)
        check(xlo+(level-lower)*(xhi-xlo)/width==x,'all_knots_axis_inversion')
        if low<=level<=high:
            check(rational_close(model.thd_constraint(level,**ports).nominal_thd_percent,height*(yzero-y)/(yzero-ytop)),'supported_knots')
    levels=[low+(high-low)*F(i,100) for i in range(101)]
    for q in levels:
        result=model.thd_constraint(q,**ports)
        pixel=(xlo*(upper-q)+xhi*(q-lower))/width
        nominal=height*(yzero-interp(pixel))/(yzero-ytop)
        check(rational_close(result.nominal_thd_percent,nominal),'independent_nominal_interpolation')
        allvalues=[]
        for a,b,shift in xs:
            yp=interp((a*(upper-q)+b*(q-lower))/width+shift)
            for c,e,dy in ys:
                v=height*(c-yp-dy)/(c-e);allvalues.append(v)
                check(F(result.graph_scenario_low_percent)<=v<=F(result.graph_scenario_high_percent),'independent_corner_containment')
        check(rational_close(result.graph_scenario_low_percent,min(allvalues)),'independent_corner_min')
        check(rational_close(result.graph_scenario_high_percent,max(allvalues)),'independent_corner_max')
        check(result.graph_scenario_low_percent<=result.nominal_thd_percent<=result.graph_scenario_high_percent,'nominal_containment')
    for end in (low,high,*model.input_range_axis_dbm):
        check(math.isfinite(model.thd_constraint(end,**ports).nominal_thd_percent),'inclusive_supported_endpoints')
    for q in (low-F(1,10**30),high+F(1,10**30),math.nextafter(model.input_range_axis_dbm[0],-math.inf),math.nextafter(model.input_range_axis_dbm[1],math.inf),-20,0,4):
        rejects(lambda q=q:model.thd_constraint(q,**ports),'no_extrapolation')
    alias=float(F(14,3))
    for q in (F(14,3),alias):
        check(model.thd_constraint(-12,**dict(ports,vgg_v=q))==model.thd_constraint(-12,**ports),'exact_and_alias_vgg')
    for q in (math.nextafter(alias,-math.inf),math.nextafter(alias,math.inf),F(14,3)-F(1,10**30),F(14,3)+F(1,10**30),F(alias)-F(1,10**30),F(alias)+F(1,10**30)):
        rejects(lambda q=q:model.thd_constraint(-12,**dict(ports,vgg_v=q)),'nearby_vgg_rejection')
    for name,val in ports.items():
        p=dict(ports);p.pop(name)
        rejects(lambda p=p:model.thd_constraint(-12,**p),'mandatory_conditions')
        altered=(val+'_wrong' if isinstance(val,str) else val+1)
        rejects(lambda name=name,altered=altered:model.thd_constraint(-12,**dict(ports,**{name:altered})),'unsupported_conditions')
        if not isinstance(val,str):
            for bad in (True,None,'5',float('nan'),float('inf'),float('-inf'),10**400):
                rejects(lambda bad=bad,name=name:model.thd_constraint(-12,**dict(ports,**{name:bad})),'invalid_condition_values')
    for bad in (True,None,'-12',float('nan'),float('inf'),float('-inf'),10**400):
        rejects(lambda bad=bad:model.thd_constraint(bad,**ports),'invalid_level_values')
    first=[model.thd_constraint(q,**ports) for q in levels]
    check(first==[model.thd_constraint(q,**ports) for q in reversed(levels)][::-1],'query_order_independence')
    examples={str(q):asdict(model.thd_constraint(q,**ports)) for q in (-18,-12,-4,-2)}
    for q in (-18,-12,-4,-2):
        r=model.thd_constraint(q,**ports)
        check(model.compare_aggregate_thd(0,q,**ports)=='below_declared_reading_scenarios','comparison_below')
        check(model.compare_aggregate_thd(r.nominal_thd_percent,q,**ports)=='within_declared_reading_scenarios','comparison_within')
        check(model.compare_aggregate_thd(10,q,**ports)=='above_declared_reading_scenarios','comparison_above')
    for bad in (-1,True,None,'0.3',float('nan'),float('inf')):
        rejects(lambda bad=bad:model.compare_aggregate_thd(bad,-12,**ports),'invalid_candidate')
    shape={
        'minus18_lower_above_minus12_upper':examples['-18']['graph_scenario_low_percent']>examples['-12']['graph_scenario_high_percent'],
        'minus2_lower_above_minus12_upper':examples['-2']['graph_scenario_low_percent']>examples['-12']['graph_scenario_high_percent'],
        'meaning':'Only a shape constraint across these declared graph-reading scenarios. It identifies no harmonic content, noise cause, target operating point or voltage-reference conversion.'}
    return dict(passed=True,scope=d['scope'],checks=dict(COUNTS),total_checks=sum(COUNTS.values()),
                input_support_exact_axis_dbm=[str(low),str(high)],
                input_support_axis_dbm=model.input_range_axis_dbm,
                nominal_input_support_exact_axis_dbm=list(map(str,model.nominal_input_range_exact_axis_dbm)),
                examples=examples,shape_constraints=shape,
                files=[binding(HERE/n) for n in ('design-frozen.json','mn3206_ac.py','check.py','implementation-bound.json')],
                conditions=ports_serializable(ports),
                excluded_claims=d['oracle']['excluded'])

def ports_serializable(ports):
    return {k:str(v) if isinstance(v,F) else v for k,v in ports.items()}

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: check.py NEW_RECEIPT.json')
    out=Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True)
    # Claim the receipt before running so failures and repeated runs remain visible.
    with out.open('x') as f:
        try:r=run()
        except Exception as exc:
            r=dict(passed=False,checks=dict(COUNTS),total_checks=sum(COUNTS.values()),error=repr(exc),traceback=traceback.format_exc())
        json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps({'passed':r['passed'],'checks':r['total_checks'],'receipt':str(out)}))
    raise SystemExit(0 if r['passed'] else 1)
