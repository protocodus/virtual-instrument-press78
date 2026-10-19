#!/usr/bin/env python3
"""Independent analytic Kaiser coefficients audit of native phase L1 bounds."""
from pathlib import Path
import json,math,numpy as np
P=Path(__file__).resolve().parent;OUT=P.parents[2]/'build/fixed-output-bus-20261019'
rows=[];native=json.loads((OUT/'response.json').read_text())['rows']
for row in native:
 rate=row['rate'];r=min(1,rate/48000);half=math.ceil(96/r);phases=rate//math.gcd(rate,48000);rel=np.arange(-half,half+1);best=0;lo=2;hi=0
 for start in range(0,phases,512):
  n=np.arange(start,min(start+512,phases));frac=(n*48000%rate)/rate;u=r*(rel[None,:]-frac[:,None]);valid=abs(u)<=96
  c=r*.95*np.sinc(.95*u)*np.i0(10*np.sqrt(np.maximum(0,1-(u/96)**2)))/np.i0(10)*valid;total=c.sum(axis=1)
  best=max(best,float((abs(c).sum(axis=1)/abs(total)).max()));lo=min(lo,float(total.min()));hi=max(hi,float(total.max()))
 rows.append({'rate':rate,'native_L1_max':row['maximum_l1'],'independent_analytic_L1_max':best,'difference':row['maximum_l1']-best,'analytic_denominator_min':lo,'analytic_denominator_max':hi,'active_wrapper_bound':1 if rate==48000 else row['maximum_l1']})
input_stress=json.loads((OUT/'overshoot.json').read_text())['rows'];bounds={r['rate']:r['active_wrapper_bound'] for r in rows};violations=[r for r in input_stress if r['output_peak']>r['input_peak']*bounds[r['rate']]+1e-6]
result={'rows':rows,'maximum_L1_difference':max(abs(r['difference']) for r in rows),'stress_bound_violations':violations,'bound_scope':'Finiteinputnormpointwise triangleinequality, withfloatroundingmargin1e-6 inthese<=1inputfixtures; notanaudiopeaklimiter.48directbound1.'}
(OUT/'independent-bounds.json').write_text(json.dumps(result,indent=2)+'\n');print(result['maximum_L1_difference'],len(violations))
