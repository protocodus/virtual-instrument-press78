"""Preserve documented parameter data; generate product names and C++ tables."""
from pathlib import Path
import argparse
import json

ROOT=Path(__file__).resolve().parents[1]


def generate():
    bank=json.loads((ROOT/'Resources/FactoryBank/pss780-source.json').read_text())
    rows=[]
    assert len(bank['voices'])==100
    for i,voice in enumerate(bank['voices']):
        assert voice['number']==i
        data=bytes.fromhex(voice['sysex_hex'])
        assert len(data)==72 and data[:4]==bytes([240,67,118,0]) and data[-1]==247
        assert all(x<16 for x in data[4:70]) and sum(data[4:71])%128==0
        raw=[data[n]*16+data[n+1] for n in range(4,70,2)]
        name=f'PSS {i:02d} '+voice['name'].title()
        rows.append({'number':i,'name':name,'raw_data':raw,'sysex_hex':voice['sysex_hex']})
    lines=['#pragma once','#include <array>','#include <cstdint>',
           '#include "Press78Engine.h"','namespace press78 {',
           '// Factory parameter provenance and unresolved distribution rights: Resources/FactoryBank/provenance.json.',
           'struct FactoryVoice { int number; const char* name; std::array<std::uint8_t,33> bytes; };',
           'inline constexpr std::array<FactoryVoice,100> kFactoryVoices{{']
    for row in rows:
        lines.append('  {'+str(row['number'])+', '+json.dumps(row['name'])+', {{'+','.join(map(str,row['raw_data']))+'}}},')
    lines+=['}};','inline Patch factoryPatch(unsigned index) noexcept {',
            '  return decodeVoice(kFactoryVoices[index < kFactoryVoices.size() ? index : 0].bytes);','}',
            '} // namespace press78','']
    return {'Source/DSP/FactoryVoices.h':'\n'.join(lines),
            'Resources/FactoryBank/press78-factory.json':json.dumps({'voices':rows},indent=2)+'\n'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for name,content in generate().items():
        path=ROOT/name
        if args.check:
            assert path.read_text()==content, f'Stale generated file: {name}'
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    print('100 PSS-prefixed voices: names, checksums and generated data verified')


if __name__=='__main__':main()
