"""Assert one real Harbor trial's recorded reward and exception status."""
import argparse
import json
from pathlib import Path
from .runner import validate_harbor_trial


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    parser.add_argument('--expected',type=float,required=True,choices=[0.,1.])
    args=parser.parse_args()
    try:
        trials=[]
        for file in args.directory.rglob('result.json'):
            trial=json.loads(file.read_text())
            if isinstance(trial,dict) and 'verifier_result' in trial:
                trials.append(trial)
        if len(trials)!=1:
            raise ValueError('Expected exactly one recorded trial')
        validate_harbor_trial(trials[0],args.expected)
        print(f'Verified reward {args.expected}, no exception')
        return 0
    except (ValueError,OSError) as error:
        print(str(error))
        return 1


if __name__=='__main__':
    raise SystemExit(main())
