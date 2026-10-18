#!/usr/bin/env python3
"""Small scientific plot of declared circuit noise and discretization limits."""
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'Reference/Python'))
from circuit.output_stage import noise_spectrum
f=np.geomspace(20,20000,600)
fig,(top,bottom)=plt.subplots(2,1,figsize=(10,7),sharex=True,gridspec_kw={'height_ratios':[2,1]})
for label,rate,color,style in [('Continuous circuit',None,'#292f32','-'),('Native 48 kHz',48000,'#157e78','--'),('Native 96 kHz',96000,'#b47724',':')]:
 fa=f if rate is None else rate/np.pi*np.tan(np.pi*f/rate)
 cov,_=noise_spectrum(fa)
 asd=np.sqrt(cov[:,0,0].real)*1e6
 correlation=cov[:,0,1].real/np.sqrt(cov[:,0,0].real*cov[:,1,1].real)
 top.loglog(f,asd,label=label,color=color,ls=style,lw=2)
 bottom.semilogx(f,correlation,color=color,ls=style,lw=2)
top.set(ylabel='Left output amplitude spectral density (µV/√Hz)',title='Related PSS-480 output circuit: calculated resistor + opamp noise')
top.legend(loc='lower left',framealpha=.95)
bottom.set(xlabel='Frequency (Hz)',ylabel='L/R spectral correlation')
for ax in (top,bottom):ax.grid(which='both',alpha=.2)
bottom.set_xlim(20,20000)
fig.text(.11,.025,'Physical voltage units, not dBFS. 300 K resistors; 10 nV/√Hz opamp voltage noise.\nBilinear frequency warping is shown without gain compensation. Exact PSS-780 board/gain is unverified.',fontsize=9,color='#40464a')
fig.tight_layout(rect=(0,.075,1,1))
out=ROOT/'build/noise-demos/circuit-noise-spectrum.png';out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=150);print(out)
