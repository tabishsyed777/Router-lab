import importlib.util
from pathlib import Path
import unittest
from routelab.runner import validate_report, validate_harbor_trial

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('route_verifier',ROOT/'tasks/proxy-contract/tests/grade.py')
verifier=importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class RouteVerifierUnitTests(unittest.TestCase):
    def test_unauthorized_and_wrong_prefix_are_rejected(self):
        self.assertFalse(verifier.matches_echo(200,{'path':'/api/items/7','query':'x=1','method':'GET','body':'','forwarded_for':'127.0.0.1','request_id':'r1'},'/items/7','x=1','GET','','r1'))
        self.assertFalse(verifier.matches_echo(401,{},'/items/7','x=1','GET','','r1'))

    def test_valid_echo_requires_method_query_body_and_headers(self):
        body={'path':'/items/7','query':'x=1','method':'POST','body':'hello','forwarded_for':'127.0.0.1','request_id':'r1'}
        self.assertTrue(verifier.matches_echo(200,body,'/items/7','x=1','POST','hello','r1'))
        for key in ['path','query','method','body','forwarded_for','request_id']:
            wrong=dict(body); wrong[key]='wrong'
            self.assertFalse(verifier.matches_echo(200,wrong,'/items/7','x=1','POST','hello','r1'))

    def test_runner_requires_consistent_nonempty_checks(self):
        self.assertTrue(validate_report({'passed':True,'checks':[{'name':'a','passed':True}]}))
        with self.assertRaises(ValueError):
            validate_report({'passed':True,'checks':[{'name':'a','passed':False}]})


class HarborResultUnitTests(unittest.TestCase):
    def test_harbor_requires_expected_reward_and_no_exception(self):
        trial={'reward_valid':True,'exception_info':None,'verifier_result':{'rewards':{'reward':1.0}}}
        self.assertTrue(validate_harbor_trial(trial,1.0))
        for bad in [{},dict(trial,reward_valid=False),dict(trial,exception_info={'error':'failed'}),dict(trial,verifier_result={'rewards':{'reward':0.0}})]:
            with self.assertRaises(ValueError):
                validate_harbor_trial(bad,1.0)
