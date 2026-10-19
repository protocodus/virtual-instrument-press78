"""Freeze the researched PSS480 small-signal output circuit for C++ streaming."""
from pathlib import Path
import hashlib
import json
import sys
import argparse

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Tools/reference'))
import numpy as np
from scipy import signal
from circuit.model import build_circuit


def retarget(sos,rate):
    result=[]
    r=rate/48000.
    for section in sos:
        coefficients=[]
        for x in [section[:3],section[3:]]:
            p=x[0]+x[1]+x[2]
            q=2*(x[0]-x[2])*r
            s=(x[0]-x[1]+x[2])*r*r
            coefficients.extend([p+q+s,2*(p-s),p-q+s])
        coefficients=np.asarray(coefficients);result.append(coefficients/coefficients[3])
    return np.asarray(result)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    circuit,output=build_circuit(model='pss480')
    sos=circuit.discrete_sos(48000,output)
    assert sos.shape==(6,6)
    coefficients=',\n'.join('        {{'+','.join(format(v,'.17g') for v in row)+'}}' for row in sos)
    header='''#pragma once
#include <array>
#include <cmath>

namespace press78 {
// Generated from the frozen Python MNA: PSS480 buffer/preamp, volume-pot top.
// Related-hardware surrogate, not a recovered PSS780 analog board or DAC.
// Six stable SOS implement trapezoidal integration of the linear circuit.
class AnalogOutput {
public:
    void prepare(double sampleRate) noexcept {
        const double ratio=sampleRate/48000.0;
        for(unsigned n=0;n<6;++n) {
            const auto& s=reference_[n];
            std::array<double,6> t{};
            if(sampleRate==48000.0)t=s;
            else for(unsigned j=0;j<2;++j) {
                const unsigned k=j*3;
                const double p=s[k]+s[k+1]+s[k+2];
                const double q=2.0*(s[k]-s[k+2])*ratio;
                const double r=(s[k]-s[k+1]+s[k+2])*ratio*ratio;
                t[k]=p+q+r;t[k+1]=2.0*(p-r);t[k+2]=p-q+r;
            }
            for(unsigned j=0;j<6;++j)sections_[n][j]=t[j]/t[3];
        }
        reset();
    }
    void reset() noexcept {for(auto& pair:state_)pair={0.0,0.0};}
    double process(double input) noexcept {
        for(unsigned n=0;n<6;++n) {
            const auto& s=sections_[n];auto& z=state_[n];
            const double output=s[0]*input+z[0];
            z[0]=s[1]*input-s[4]*output+z[1];
            z[1]=s[2]*input-s[5]*output;
            input=output;
        }
        return input;
    }
private:
    inline static constexpr std::array<std::array<double,6>,6> reference_{{
COEFFICIENTS
    }};
    std::array<std::array<double,6>,6> sections_{};
    std::array<std::array<double,2>,6> state_{};
};
} // namespace press78
'''.replace('COEFFICIENTS',coefficients)
    target=ROOT/'Source/DSP/AnalogOutput.h'
    if args.check:assert target.read_text()==header,'Stale AnalogOutput.h'
    else:target.write_text(header)
    rows=[]
    for rate in (8000,16000,22050,24000,32000,44100,44117,48000,88200,96000,176400,192000):
        hz=np.geomspace(20,rate*.45,2000)
        native=sos if rate==48000 else retarget(sos,rate)
        _,a=signal.sosfreqz(native,worN=hz,fs=rate)
        _,b=signal.sosfreqz(circuit.discrete_sos(rate,output),worN=hz,fs=rate)
        error=float(np.max(abs(a-b)))
        assert error<1e-7,(rate,error)
        rows.append({'sample_rate':rate,'max_complex_transfer_error':error})
    result={'passed':True,'scope':'Frozen MNA transfer and analytic sample-rate conversion; circuit transfer to PSS780 remains unverified.',
            'rows':rows,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [ROOT/'Tools/reference/circuit/model.py',Path(__file__),target]}}
    out=ROOT/'Tests/results';out.mkdir(parents=True,exist_ok=True)
    (out/'analog-coefficients.json').write_text(json.dumps(result,indent=2)+'\n')
    print('12 rates: frozen analog transfer and sample-rate mapping passed')


if __name__=='__main__':main()
