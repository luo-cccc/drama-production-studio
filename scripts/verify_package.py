"""Reproducible local review checks; no media/network calls or production state changes."""
from pathlib import Path
import argparse
from datetime import datetime,timezone
import hashlib
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def hashes():
    paths=[ROOT/name for name in ('SKILL.md','README.md','CHANGELOG.md','LICENSE','package-manifest.json','.gitignore')]
    for name in ('references','templates','scripts','tests','examples','docs'):
        paths.extend(p for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix in ('.md','.py','.json') and '__pycache__' not in p.parts and p.name not in ('verification-results.json',))
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def main():
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='New JSON evidence path; never overwrite')
    args=parser.parse_args()
    if args.output and args.output.exists():
        parser.error('Evidence already exists; use a new output path')
    before=hashes()
    commands=[
        ['-m','unittest','discover','-s','tests','-v'],
        ['scripts/check_episode.py','--self-test'],
        ['scripts/check_series.py','--self-test'],
        ['scripts/check_episode.py','examples/screenplay-standard.md','--format','standard'],
        ['scripts/check_episode.py','examples/screenplay-extended.md','--format','long'],
        ['scripts/check_episode.py','examples/storyboard-scene.md','--scope','visual','--source','examples/storyboard-source.md'],
        ['scripts/check_episode.py','examples/storyboard-content-segmented.md','--scope','visual','--source','examples/storyboard-source.md'],
        ['scripts/check_episode.py','examples/faithful-fight-scene.md','--scope','visual','--require-visual','--source','examples/faithful-fight-source.md'],
    ]
    for fixture in sorted((ROOT/'examples/fight').glob('*.json')):
        commands.append(['scripts/check_episode.py','--combat-json',str(fixture.relative_to(ROOT))])
    results=[]
    for cmd in commands:
        command=[sys.executable,'-B','-X','utf8',*cmd]
        try:
            p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=55)
            results.append({'command':['python','-B','-X','utf8',*cmd],'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        except subprocess.TimeoutExpired:
            results.append({'command':cmd,'exit_code':None,'stderr':'Timed out after 55s','stdout':''})
    after=hashes()
    tests=results[0]['stdout']+results[0]['stderr']
    count=re.search(r'Ran (\d+) tests?',tests)
    success=all(r['exit_code']==0 for r in results) and before==after and count is not None
    skipped=re.search(r'OK \(skipped=(\d+)\)',tests)
    evidence={'status':'PASS' if success else 'FAIL','recorded_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'Local package/unit/CLI/JSON examples. Model behavior is separate; platform/media not run.','test_count':int(count.group(1)) if count else 0,'skipped_tests':int(skipped.group(1)) if skipped else 0,'python_version':sys.version.split()[0],'inputs_unchanged':before==after,'input_sha256':before,'commands':results}
    encoded=json.dumps(evidence,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x',encoding='utf-8') as out:
            out.write(encoded)
        print(json.dumps({k:evidence[k] for k in ('status','test_count','inputs_unchanged')},ensure_ascii=False))
        print(args.output)
    else:
        print(encoded,end='')
    return 0 if success else 1


if __name__=='__main__':
    sys.exit(main())
