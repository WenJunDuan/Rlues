"""Tracker dispatch contract: fake gh/glab and a local Gitee REST server."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest

from gate_harness import ENV, athena, git, tmpdir
from test_state_cli import v2project, ok, ship_ready, fm


FAKE = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
method = args[args.index('--method') + 1]
endpoint = args[args.index('--method') + 2]
data = json.load(sys.stdin) if '--input' in args else None
with open(os.environ['TRACKER_LOG'], 'a') as out:
    out.write(json.dumps([sys.argv[0], args, method, endpoint, data]) + '\\n')
if os.environ.get('FAIL_CLOSE') and data and (data.get('state') == 'closed' or data.get('state_event') == 'close'):
    sys.exit(1)
result = json.loads(Path(os.environ['TRACKER_DATA']).read_text())['user' if endpoint == 'user' else 'emails' if endpoint in ('emails', 'user/emails') else 'rows' if '?' in endpoint else 'issue']
if data and ('assignees' in data or 'assignee_ids' in data) and not os.environ.get('FAIL_CLAIM'):
    result.update(assignees=[{'login': 'dri', 'username': 'dri'}], labels=['agent-ok', 'in-progress'])
print(json.dumps(result))
'''


class Dispatch(unittest.TestCase):
    def setup_provider(self, provider):
        self.tmp = tmpdir(self)
        self.root = v2project(self.tmp)
        git(self.root, "config", "user.email", "fixture@example.invalid")
        self.provider = provider
        self.number = 'I123' if provider == 'gitee' else '23'
        git(self.root, 'remote', 'add', 'origin', f'git@{provider}.com:team/repo.git')
        self.bin = self.tmp / 'bin'
        self.bin.mkdir()
        for name in ('gh', 'glab'):
            cli = self.bin / name
            cli.write_text(FAKE)
            cli.chmod(0o755)
        self.log = self.tmp / 'calls.jsonl'
        self.data = self.tmp / 'data.json'
        self.issue = dict(number=self.number, iid=self.number, title='Repair dispatcher', body='---\nwrite_set: [src/app.js]\n---',
                          html_url=f'https://{provider}.com/team/repo/issues/{self.number}', labels=[{'name': 'agent-ok'}],
                          assignees=[], state='open')
        if provider == 'gitlab':
            self.issue.update(state='opened', labels=['agent-ok'])
        self.save()
        self.env = {'PATH': f'{self.bin}{os.pathsep}{ENV["PATH"]}', 'TRACKER_LOG': str(self.log), 'TRACKER_DATA': str(self.data),
                    'GITEE_TOKEN': 'secret-fixture-token'}
        if provider == 'gitee':
            owner = self
            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *_):
                    pass

                def do_GET(self):
                    self.respond('GET')

                def do_POST(self):
                    self.respond('POST')

                def do_PATCH(self):
                    self.respond('PATCH')

                def respond(self, method):
                    body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                    data = json.loads(body) if body else None
                    endpoint = self.path.removeprefix('/api/v5/')
                    with owner.log.open('a') as out:
                        out.write(json.dumps(['http', [], method, endpoint, data]) + '\n')
                    owner.assertEqual(self.headers['Authorization'], 'Bearer secret-fixture-token')
                    self.send_response(500 if owner.env.get('FAIL_CLOSE') and data and data.get('state') == 'closed' else 200)
                    self.end_headers()
                    values = json.loads(owner.data.read_text())
                    result = values['user' if endpoint == 'user' else 'emails' if endpoint in ('emails', 'user/emails') else 'rows' if '?' in endpoint else 'issue']
                    if data and 'assignee' in data:
                        result.update(assignee={'login': 'dri'}, assignees=[{'login': 'dri'}], labels=['agent-ok', 'in-progress'])
                    self.wfile.write(json.dumps(result).encode())
            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            self.env['ATHENA_GITEE_API_URL'] = f'http://127.0.0.1:{server.server_port}/api/v5'

    def save(self, rows=None):
        self.data.write_text(json.dumps({'user': {'login': 'dri', 'username': 'dri', 'id': 7, 'email': 'fixture@example.invalid'},
                                         'emails': [{'email': 'fixture@example.invalid'}], 'issue': self.issue, 'rows': rows if rows is not None else [self.issue]}))

    def run_cli(self, *args):
        return athena(*args, cwd=self.root, env=self.env)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_three_provider_lifecycle(self):
        for provider in ('github', 'gitlab', 'gitee'):
            with self.subTest(provider=provider):
                self.setup_provider(provider)
                other = {**self.issue, 'number': '99', 'iid': '99', 'title': 'hidden', 'assignees': [{'login': 'other', 'username': 'other'}]}
                mine = {**other, 'number': '98', 'iid': '98', 'title': 'mine', 'labels': [], 'assignees': [{'login': 'dri', 'username': 'dri'}]}
                self.save([self.issue, other, mine])
                before = git(self.root, 'status', '--porcelain').stdout
                pull = ok(self, self.run_cli('issue', 'pull'))
                self.assertIn('Repair dispatcher', pull.stdout)
                self.assertIn('mine', pull.stdout)
                self.assertNotIn('hidden', pull.stdout)
                self.assertEqual(before, git(self.root, 'status', '--porcelain').stdout)
                self.assertTrue(all(c[2] == 'GET' for c in self.calls()))
                hot = self.root / '.ai_state/sprints/hot'
                hot.mkdir(parents=True)
                (hot / 'design.md').write_text('## 允许写集\n- `src/`\n')
                start = ok(self, self.run_cli('sprint', 'start', '--issue', self.number, '--slug', 'dispatch', '--path', 'Feature'))
                self.assertIn('conflict with hot sprint hot', start.stderr)
                self.assertEqual(git(self.root, 'branch', '--show-current').stdout.strip(), f'feat/{self.number}-dispatch')
                design = self.root / '.ai_state/sprints/dispatch/design.md'
                self.assertEqual(fm(design)['issue'], f'{provider}#{self.number}')
                self.assertIn(self.issue['html_url'], design.read_text())
                changes = [c[4] for c in self.calls() if c[2] in ('PATCH', 'PUT')]
                claim = changes[-1]
                if provider == 'github':
                    self.assertEqual(claim['assignees'], ['dri'])
                    self.assertEqual(claim['labels'], ['agent-ok', 'in-progress'])
                elif provider == 'gitlab':
                    self.assertEqual(claim, {'assignee_ids': [7], 'add_labels': 'in-progress'})
                else:
                    self.assertEqual(claim, {'repo': 'repo', 'assignee': 'dri', 'labels': 'agent-ok,in-progress'})
                ship_ready(self, self.root, 'dispatch')
                ok(self, self.run_cli('ship', '--dry-run'))
                self.assertFalse(any(c[2] == 'POST' for c in self.calls()))
                ok(self, self.run_cli('ship'))
                posts = [c for c in self.calls() if c[2] == 'POST']
                self.assertEqual(len(posts), 1)
                self.assertIn('sprint dispatch; AC 1; evidence ', posts[0][4]['body'])
                self.assertIn(git(self.root, 'rev-parse', '--short', 'HEAD').stdout.strip(), posts[0][4]['body'])
                self.assertIn('comments' if provider != 'gitlab' else 'notes', posts[0][3])
                self.assertEqual(self.calls()[-1][4].get('state_event', self.calls()[-1][4].get('state')), 'close' if provider == 'gitlab' else 'closed')
                ok(self, self.run_cli('issue', 'add', '--type', 'bug', '--text', 'same text', '--push'))
                self.assertIn(f'{provider}#{self.number}', (self.root / '.ai_state/issues.md').read_text())
                created = self.calls()[-1][4]
                self.assertEqual(created['title'], 'same text')
                self.assertEqual(created.get('description', created.get('body')), 'same text')
                self.assertNotIn('secret-fixture-token', self.log.read_text())

    def test_other_claimant_refused_before_mutation(self):
        for provider in ('github', 'gitlab', 'gitee'):
            with self.subTest(provider=provider):
                self.setup_provider(provider)
                self.issue.update(labels=['in-progress'], assignees=[{'login': 'other', 'username': 'other'}])
                self.save()
                before = git(self.root, 'status', '--porcelain').stdout
                run = self.run_cli('sprint', 'start', '--issue', self.number)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn('claimed by other', run.stderr)
                self.assertEqual(before, git(self.root, 'status', '--porcelain').stdout)
                self.assertTrue(all(c[2] == 'GET' for c in self.calls()))

    def test_silently_ignored_claim_does_not_start(self):
        self.setup_provider('github')
        self.env['FAIL_CLAIM'] = '1'
        before = git(self.root, 'branch', '--show-current').stdout
        run = self.run_cli('sprint', 'start', '--issue', '23')
        self.assertIn('claim was not applied', run.stderr)
        self.assertEqual(git(self.root, 'branch', '--show-current').stdout, before)
        self.assertFalse((self.root / '.ai_state/sprints').exists())

    def test_close_failure_is_best_effort(self):
        self.setup_provider('github')
        ok(self, self.run_cli('sprint', 'start', '--issue', self.number, '--slug', 'dispatch'))
        ship_ready(self, self.root, 'dispatch')
        self.env['FAIL_CLOSE'] = '1'
        run = ok(self, self.run_cli('ship'))
        self.assertIn('manual: gh issue comment', run.stderr)
        self.assertIn('gh issue close 23', run.stderr)

    def test_detect_rejects_unknown_and_accepts_configured_gitlab(self):
        self.setup_provider('gitlab')
        git(self.root, 'remote', 'set-url', 'origin', 'https://code.example/team/sub/repo.git')
        self.assertIn('unsupported tracker host code.example', self.run_cli('issue', 'pull').stderr)
        self.env['ATHENA_GITLAB_HOSTS'] = 'code.example'
        ok(self, self.run_cli('issue', 'pull'))
        self.assertIn('projects/team%2Fsub%2Frepo/issues?', self.calls()[-1][3])

    def test_bugfix_branch_and_email_mismatch(self):
        self.setup_provider('github')
        git(self.root, 'config', 'user.email', 'wrong@example.invalid')
        self.assertIn('does not match git user.email', self.run_cli('sprint', 'start', '--issue', '23').stderr)
        git(self.root, 'config', 'user.email', 'fixture@example.invalid')
        ok(self, self.run_cli('sprint', 'start', '--issue', '23', '--slug', 'a' * 60, '--path', 'Bugfix'))
        branch = git(self.root, 'branch', '--show-current').stdout.strip()
        self.assertTrue(branch.startswith('fix/23-'))
        self.assertLessEqual(len(branch), 40)


if __name__ == '__main__':
    unittest.main()
