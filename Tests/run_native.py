"""Build/run native contracts and emit reproducible source-hashed evidence."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sanitize',action='store_true')
    parser.add_argument('--compiler',default='clang++');args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='press78-native-') as temp:
        command=[args.compiler,'-std=c++17','-O1' if args.sanitize else '-O2','-g',
                 '-Wall','-Wextra','-Werror','-pedantic','-ISource/DSP',
                 'Tests/test_dsp.cpp','Source/DSP/Press78Engine.cpp','-o',str(Path(temp)/'tests')]
        if args.sanitize:command[1:1]=['-fsanitize=address,undefined','-fno-omit-frame-pointer']
        subprocess.run(command,cwd=ROOT,check=True)
        result=subprocess.run([str(Path(temp)/'tests')],cwd=ROOT,text=True,capture_output=True)
    output=result.stdout+result.stderr
    counts=re.search(r'(\d+) passed, (\d+) failed',output)
    size=re.search(r'engine_bytes=(\d+)',output)
    paths=[*sorted((ROOT/'Source/DSP').glob('*.h')),*sorted((ROOT/'Source/DSP').glob('*.cpp')),
           ROOT/'Tests/test_dsp.cpp',Path(__file__)]
    report={'scope':'Native behavioral-model correctness and effect parity contracts; not hardware or Reason validation.',
            'passed':result.returncode==0 and counts is not None and counts[2]=='0',
            'tests_passed':int(counts[1]) if counts else 0,'tests_failed':int(counts[2]) if counts else None,
            'address_sanitizer':args.sanitize,'undefined_behavior_sanitizer':args.sanitize,
            'engine_size_bytes':int(size[1]) if size else None,'platform':platform.platform(),
            'compiler':subprocess.run([args.compiler,'--version'],text=True,capture_output=True,check=True).stdout.splitlines()[0],
            'compile_command':command,
            'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'limitations':['Fixed48k internalclock is a modeling choice, not measured OPU timing.',
                'Reported32-tick latency is nominal and changes with clock ratio; positive clockoffset can alias nearNyquist.',
                'Recorded chorus is a causal effective capturetransfer, not identified physical BBD; Studio remainsdefault.',
                'Native tests do not establish SDK target or Reason host execution.']}
    out=ROOT/'Tests/results';out.mkdir(exist_ok=True)
    (out/('native-sanitizer.log' if args.sanitize else 'native-tests.log')).write_text(output)
    (out/'native-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(output,end='')
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
