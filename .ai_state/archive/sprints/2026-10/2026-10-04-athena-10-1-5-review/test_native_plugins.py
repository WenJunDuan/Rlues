import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import tempfile
import unittest

DIST = Path.cwd() / 'vibeCoding/dist'

class NativePlugins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(['node', 'vibeCoding/athena/build.mjs', '--check'], check=True, capture_output=True, text=True)

    def test_cc_validate_and_discover(self):
        root = DIST / 'claude-plugin/10.1'
        run = subprocess.run(['claude', 'plugin', 'validate', str(root), '--json'], capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(json.loads(run.stdout)['success'])
        run = subprocess.run(['claude', '--plugin-dir', str(root), 'plugin', 'details', 'athena'], capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        for expected in ['athena 10.1.5', 'Skills (22)', 'Agents (4)', 'Hooks (9)']:
            self.assertIn(expected, run.stdout)

    def test_cx_install_and_discover_original_layout(self):
        with tempfile.TemporaryDirectory(prefix='athena-native-') as tmp:
            root = Path(tmp).resolve()
            market = root / 'market'
            (market / '.agents/plugins').mkdir(parents=True)
            shutil.copytree(DIST / 'codex-plugin/10.1', market / 'athena')
            (market / '.agents/plugins/marketplace.json').write_text(json.dumps({
                'name': 'athena-probe', 'interface': {'displayName': 'Athena probe'},
                'plugins': [{'name': 'athena', 'source': {'source': 'local', 'path': './athena'},
                             'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'}, 'category': 'Productivity'}]}))
            probe_home = root / 'home'
            (probe_home / '.codex').mkdir(parents=True)
            env = {**os.environ, 'HOME': str(probe_home), 'CODEX_HOME': str(probe_home / '.codex')}
            for args in [['marketplace', 'add', str(market), '--json'], ['add', 'athena@athena-probe', '--json']]:
                run = subprocess.run(['codex', 'plugin', *args], cwd=root, env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, 0, run.stderr)
            proc = subprocess.Popen(['codex', 'app-server', '--stdio'], cwd=root, env=env,
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
            selector = selectors.DefaultSelector()
            selector.register(proc.stdout, selectors.EVENT_READ)
            def request(seq, method, params):
                proc.stdin.write(json.dumps({'id': seq, 'method': method, 'params': params}) + '\n')
                proc.stdin.flush()
                while selector.select(15):
                    response = json.loads(proc.stdout.readline())
                    if response.get('id') == seq:
                        self.assertNotIn('error', response)
                        return response['result']
                self.fail('app-server timeout: ' + method)
            try:
                request(1, 'initialize', {'clientInfo': {'name': 'athena_probe', 'version': '1'}, 'capabilities': {'experimentalApi': True}})
                proc.stdin.write('{"method":"initialized"}\n'); proc.stdin.flush()
                info = request(2, 'plugin/read', {'pluginName': 'athena', 'marketplacePath': str(market / '.agents/plugins/marketplace.json')})['plugin']
                self.assertEqual(len(info['skills']), 22)
                self.assertEqual(len(info['hooks']), 8)
                skills = request(3, 'skills/list', {'cwds': [str(root)], 'forceReload': True})['data'][0]
                self.assertEqual(len([s for s in skills['skills'] if s.get('pluginId') == 'athena@athena-probe']), 22)
                # This verifies installed discovery only. Hook trust/tool invocation and U-001 remain open.
            finally:
                proc.terminate(); proc.wait(timeout=5)
                selector.close(); proc.stdin.close(); proc.stdout.close()

if __name__ == '__main__':
    unittest.main()
