import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ProxyIntegrationTests(unittest.TestCase):
    def test_real_nginx_reference_passes_and_auth_bypass_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'demo'
            result=subprocess.run([sys.executable,'-m','routelab','demo','--output',str(out)],capture_output=True,text=True,timeout=240)
            details=(out/'report.json').read_text() if (out/'report.json').exists() else ''
            self.assertEqual(result.returncode,0,result.stdout+result.stderr+details)
            report=json.loads((out/'report.json').read_text())
            self.assertTrue(report['oracle']['passed'])
            self.assertFalse(report['nop']['passed'])
            self.assertFalse(report['auth_bypass']['passed'])
            self.assertGreaterEqual(len(report['oracle']['checks']),12)
            self.assertTrue((out/'report.html').is_file())
