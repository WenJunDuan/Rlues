import unittest
from gate_harness import call, project, tmpdir, PLATFORMS

class ParsedPush(unittest.TestCase):
    def test_data_words_and_compound_quoted_heredoc_are_not_push(self):
        root = project(tmpdir(self))
        commands = ("git commit -m 'git push origin main'", "echo done # git push origin main",
                    "echo done; cat > notes.md <<'EOF'\n`unmatched and git push origin main\nEOF\necho done")
        for platform in PLATFORMS:
            for command in commands:
                with self.subTest(platform=platform, command=command):
                    self.assertFalse(call(platform, 'bash', root, command=command).blocked)

    def test_every_push_is_judged_by_its_own_repository(self):
        tmp = tmpdir(self)
        root = project(tmp, 'active'); idle = project(tmp, 'idle', path='', stage='')
        for platform in PLATFORMS:
            command = f'git -C {idle} push; git -C {root} push'
            verdict = call(platform, 'bash', root, command=command)
            self.assertTrue(verdict.blocked, command)
            self.assertIn('entire command was not executed', verdict.reason)
            self.assertFalse(call(platform, 'bash', root, command=f'git commit -m x && git -C {idle} push').blocked)
            self.assertTrue(call(platform, 'bash', idle, command=f'git -C {root} push').blocked)

    def test_allowed_push_does_not_hide_later_danger(self):
        root = project(tmpdir(self))
        for command in ('ATHENA_ALLOW_PUSH=1 git push; git push', 'ATHENA_ALLOW_PUSH=1 git push; rm -rf /',
                        "cat <<EOF\n`git push`\nEOF"):
            self.assertTrue(call('cc', 'bash', root, command=command).blocked, command)

    def test_later_cd_and_nested_push_cannot_escape_idle_stage(self):
        tmp = tmpdir(self)
        root = project(tmp, 'active'); idle = project(tmp, 'idle', path='', stage='')
        for command in (f'echo done; cd {root}; git push', f'echo done && cd {root} && git push',
                        f"bash -c 'git -C {root} push'", f'echo "$(git -C {root} push)"',
                        f"cd {root} && bash -c 'git push'", f'cd {root} && echo "$(git push)"',
                        f"cd {root}; cat <<EOF\n'$(git push)'\nEOF"):
            self.assertTrue(call('cc', 'bash', idle, command=command).blocked, command)
        self.assertFalse(call('cc', 'bash', root, command=f'echo done && cd {idle} && git push').blocked)

    def test_single_quotes_in_unquoted_heredoc_do_not_hide_substitutions(self):
        root = project(tmpdir(self))
        for command in ("cat <<EOF\n'$(git push)'\nEOF", "cat <<EOF\n'`git push`'\nEOF"):
            self.assertTrue(call('cc', 'bash', root, command=command).blocked, command)

    def test_background_push_and_cd_are_not_stage_escapes(self):
        tmp = tmpdir(self)
        root = project(tmp, 'active'); idle = project(tmp, 'idle', path='', stage='')
        for command in ('git push &', 'git push&', f'cd {idle} & wait; git push'):
            self.assertTrue(call('cc', 'bash', root, command=command).blocked, command)

    def test_heredoc_data_cd_and_previous_push_do_not_hide_target(self):
        tmp = tmpdir(self)
        root = project(tmp, 'active'); idle = project(tmp, 'idle', path='', stage='')
        cases = ((root, f'cat <<EOF\ncd {idle};\n$(git push)\nEOF'),
                 (idle, f'git -C {idle} push; cd {root}; bash -c "git push"'),
                 (root, f"cat <<'FIRST'\ncd {idle}\nFIRST\ncat <<EOF\n$(git push)\nEOF"))
        for cwd, command in cases:
            with self.subTest(command=command):
                self.assertTrue(call('cc', 'bash', cwd, command=command).blocked, command)

    def test_heredoc_delimiter_is_not_an_executed_cd(self):
        root = project(tmpdir(self))
        self.assertTrue(call('cc', 'bash', root, command="cat <<'cd'\ntext\ncd\ngit push").blocked)

    def test_nested_shell_inherits_repository_redirect_rejection(self):
        tmp = tmpdir(self)
        root = project(tmp, 'active'); idle = project(tmp, 'idle', path='', stage='')
        for command in (f'GIT_DIR={root}/.git bash -c "git push"', f'env GIT_DIR={root}/.git bash -c "git push"'):
            with self.subTest(command=command):
                self.assertTrue(call('cc', 'bash', idle, command=command).blocked, command)
