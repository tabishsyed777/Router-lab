"""Fresh-container grading for a configuration-repair terminal task."""
import argparse
import html
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tarfile

ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT/'tasks'/'proxy-contract'
IMAGE=os.getenv('LAB_IMAGE','routelab-task:dev')
ARTIFACT='/app/nginx.conf'
CONFIG='nginx.conf'


def validate_report(report):
    if not isinstance(report,dict) or not isinstance(report.get('passed'),bool) or not isinstance(report.get('checks'),list) or not report['checks']:
        raise ValueError('Missing verdict or checks')
    for item in report['checks']:
        if not isinstance(item,dict) or not isinstance(item.get('name'),str) or not isinstance(item.get('passed'),bool):
            raise ValueError('Invalid check')
    if report['passed'] != all(item['passed'] for item in report['checks']):
        raise ValueError('Verdict contradicts checks')
    return report['passed']


def validate_harbor_trial(trial,expected):
    if not isinstance(trial,dict) or trial.get('reward_valid') is not True or trial.get('exception_info') is not None:
        raise ValueError('Harbor trial has invalid reward or an exception')
    verdict=trial.get('verifier_result')
    rewards=verdict.get('rewards') if isinstance(verdict,dict) else None
    reward=rewards.get('reward') if isinstance(rewards,dict) else None
    if isinstance(reward,bool) or not isinstance(reward,(int,float)) or reward!=expected:
        raise ValueError('Harbor reward does not match the expected outcome')
    return True


def docker(*args,timeout=180):
    result=subprocess.run(['docker',*map(str,args)],capture_output=True,text=True,timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:]+result.stdout[-2000:])
    return result.stdout


def grade(candidate):
    candidate=Path(candidate)
    if candidate.is_symlink() or not candidate.is_file() or candidate.stat().st_size>65536:
        raise ValueError('Candidate must be a regular nonsymlink file of at most 64 KiB')
    container=docker('create','--network','none','--memory','768m','--cpus','1','--pids-limit','128',
                     '--cap-drop','ALL','--cap-add','SETUID','--cap-add','SETGID',
                     '--security-opt','no-new-privileges',IMAGE).strip()
    try:
        docker('start',container)
        with tempfile.TemporaryDirectory() as staging:
            archive=Path(staging)/'verifier.tar'
            def normalize(info):
                info.uid=info.gid=0
                info.uname=info.gname='root'
                info.mode=0o755 if info.name.endswith('.sh') else 0o644
                return info
            with tarfile.open(archive,'w') as bundle:
                for name in ['grade.py','test.sh']:
                    bundle.add(TASK/'tests'/name,arcname='tests/'+name,filter=normalize)
                bundle.add(candidate,arcname=ARTIFACT.lstrip('/'),filter=normalize)
            archive.chmod(0o644)
            docker('cp',archive,f'{container}:/tmp/verifier.tar')
            docker('exec',container,'tar','--no-same-owner','-xf','/tmp/verifier.tar','-C','/')
            docker('exec',container,'rm','/tmp/verifier.tar')
        output=docker('exec',container,'bash','/tests/test.sh',timeout=120)
        report=json.loads(output.strip().splitlines()[-1])
        validate_report(report)
        return report
    finally:
        subprocess.run(['docker','rm','-f',container],capture_output=True,timeout=15)


def shortcut(reference):
    return reference.replace('if ($http_authorization != "Bearer route-lab-token") { return 401; }','')


def write_report(out,report):
    text=json.dumps(report,indent=2,allow_nan=False)
    (out/'report.json').write_text(text+'\n',encoding='utf-8')
    (out/'report.html').write_text(f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>RouteLab evidence</title><style>body{{font:16px system-ui;background:#0d1727;color:#e8efff;max-width:1050px;margin:48px auto;padding:24px}}h1,a{{color:#83ead1}}pre{{background:#19273c;white-space:pre-wrap;overflow-wrap:anywhere;padding:24px;border-radius:12px}}</style><h1>RouteLab / verifier evidence</h1><p>Real container workload · fresh verification · no model calls</p><p>Reference/NOP checks establish evaluator behavior, not agent capability or task difficulty.</p><a href="report.json">JSON report</a><pre>{html.escape(text)}</pre></html>',encoding='utf-8')


def main(argv=None):
    parser=argparse.ArgumentParser(description='RouteLab task runner')
    parser.add_argument('command',choices=['demo','grade'])
    parser.add_argument('--candidate',type=Path)
    parser.add_argument('--output',type=Path,default=Path('runs/demo'))
    parser.add_argument('--skip-build',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError('Output directory already exists; choose a new path')
        if args.command=='grade' and args.candidate is None:
            raise ValueError('grade requires --candidate')
        if not args.skip_build:
            docker('build','-q','-t',IMAGE,TASK/'environment',timeout=600)
        args.output.mkdir(parents=True,exist_ok=False)
        image_id=docker('image','inspect',IMAGE,'--format','{{.Id}}').strip()
        if args.command=='grade':
            report=grade(args.candidate)
            report['image_id']=image_id
            write_report(args.output,report)
            return 0 if report['passed'] else 1
        reference=(TASK/'solution'/CONFIG).read_text()
        with tempfile.TemporaryDirectory() as temporary:
            altered=Path(temporary)/CONFIG
            altered.write_text(shortcut(reference))
            report={'oracle':grade(TASK/'solution'/CONFIG),'nop':grade(TASK/'environment'/'nginx.conf'),
                    'auth_bypass':grade(altered),'model_calls':0,'image_id':image_id}
        report['passed']=report['oracle']['passed'] and not report['nop']['passed'] and not report['auth_bypass']['passed']
        write_report(args.output,report)
        print(json.dumps({'passed':report['passed'],'output':str(args.output),'image_id':image_id}))
        return 0 if report['passed'] else 1
    except (ValueError,RuntimeError,OSError,subprocess.TimeoutExpired,IndexError) as error:
        print(str(error))
        return 2
