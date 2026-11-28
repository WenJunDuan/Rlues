"""G-042: review prepare keeps sprint work across pause/resume and writer merges."""
import unittest
from pathlib import Path

from gate_harness import athena, git, tmpdir
from test_feedback_g024 import branch_merge, commit, head
from test_feedback_g033 import changes, prepare
from test_state_cli import ok, v2project


class ReviewPauseAttribution(unittest.TestCase):
    def setUp(self) -> None:
        self.root = v2project(tmpdir(self))
        self.main = git(self.root, 'branch', '--show-current').stdout.strip()
        ok(self, athena('sprint', 'start', 'r/x', '--slug', 's-x', cwd=self.root))

    def pause(self) -> None:
        ok(self, athena('sprint', 'pause', '--resume-when', 'resume review', cwd=self.root))

    def resume(self) -> None:
        ok(self, athena('sprint', 'resume', 's-x', cwd=self.root))

    def foreign_commit(self) -> str:
        ok(self, athena('sprint', 'start', 'r/y', '--slug', 's-y', cwd=self.root))
        foreign = commit(self.root, 'foreign.js', 'feat(s-y): other sprint')
        self.pause()
        return foreign

    def source_commit(self, name: str, message: str) -> str:
        # Keep state changes local across switches between the integration branches.
        (self.root / name).write_text(f'{name}\n', encoding='utf-8')
        git(self.root, 'add', name)
        git(self.root, 'commit', '-qm', message)
        return head(self.root)

    def assert_changes(self, packet: str, *files: str) -> None:
        for name in files:
            self.assertIn(f'- A\t{name}\n', changes(packet))

    def assert_exclusions(self, packet: str, *, kept: tuple[str, ...], excluded: tuple[str, ...]) -> None:
        exclusions = packet.split('## Acceptance')[0]
        for sha in kept:
            self.assertNotIn(sha, exclusions)
        for sha in excluded:
            self.assertIn(sha, exclusions)

    def test_pre_pause_changes_survive_a_later_pause_from_an_older_head(self) -> None:
        base = head(self.root)
        own = self.source_commit('own.js', 'fix: prepare own changes')
        self.pause()
        self.resume()

        # The second pause records an older integration branch, then review resumes on main.
        git(self.root, 'switch', '-qc', 'integration', base)
        self.pause()
        git(self.root, 'switch', '-q', self.main)
        foreign = self.foreign_commit()
        self.resume()

        packet = prepare(self, self.root)
        self.assert_changes(packet, 'own.js')
        self.assertNotIn('foreign.js', changes(packet))
        self.assert_exclusions(packet, kept=(own,), excluded=(foreign,))

    def test_pre_pause_work_reintroduced_through_a_foreign_merge_stays_visible(self) -> None:
        base = head(self.root)
        own = self.source_commit('own.js', 'fix: prepare own changes')
        self.pause()

        git(self.root, 'switch', '-qc', 'integration', base)
        foreign = self.foreign_commit()
        git(self.root, 'merge', '--no-ff', '-qm', 'merge s-y integration', self.main)
        merge = head(self.root)
        self.resume()

        packet = prepare(self, self.root)
        self.assert_changes(packet, 'own.js')
        self.assertNotIn('foreign.js', changes(packet))
        self.assert_exclusions(packet, kept=(own,), excluded=(foreign, merge))

    def test_slug_in_merge_branch_keeps_unsigned_writer_commits(self) -> None:
        self.pause()
        foreign = self.foreign_commit()
        side, merge = branch_merge(self.root, 'feat/s-x-review', 'writer.js', 'add writer change')
        self.resume()

        packet = prepare(self, self.root)
        self.assert_changes(packet, 'writer.js')
        self.assertNotIn('foreign.js', changes(packet))
        self.assert_exclusions(packet, kept=(side, merge), excluded=(foreign,))

    def test_dispatched_custom_branch_keeps_unsigned_writer_commits(self) -> None:
        branch = 'writer/custom'
        ok(self, athena('writer', 'dispatch', '--tool', 'codex', '--family', 'openai', '--branch', branch, cwd=self.root))
        wt = Path(f'{self.root}-wt') / 's-x-codex'
        self.pause()
        first = commit(wt, 'writer.js', 'add writer change')
        second = commit(wt, 'writer-test.js', 'add writer tests')
        git(self.root, 'merge', '--no-ff', '-q', branch)
        merge = head(self.root)
        self.resume()

        packet = prepare(self, self.root)
        self.assert_changes(packet, 'writer.js', 'writer-test.js')
        self.assert_exclusions(packet, kept=(first, second, merge), excluded=())

    def test_dispatched_branch_matches_merge_with_a_custom_subject(self) -> None:
        branch = 'writer/custom'
        ok(self, athena('writer', 'dispatch', '--tool', 'codex', '--family', 'openai', '--branch', branch, cwd=self.root))
        wt = Path(f'{self.root}-wt') / 's-x-codex'
        self.pause()
        foreign = self.foreign_commit()
        side = commit(wt, 'writer.js', 'fix: update integration with s-y')
        git(self.root, 'merge', '--no-ff', '-qm', 'Merge implementation', branch)
        merge = head(self.root)
        self.resume()

        packet = prepare(self, self.root)
        self.assert_changes(packet, 'writer.js')
        self.assertNotIn('foreign.js', changes(packet))
        self.assert_exclusions(packet, kept=(side, merge), excluded=(foreign,))

    def test_side_message_keeps_writer_parts_after_main_is_merged_into_branch(self) -> None:
        wt = self.root.parent / 'writer'
        git(self.root, 'worktree', 'add', '-qb', 'writer/opaque', str(wt))
        self.pause()
        first = commit(wt, 'writer.js', 'feat(s-x): writer implementation')
        foreign = self.foreign_commit()
        git(wt, 'merge', '--no-ff', '-q', self.main)
        sync = head(wt)
        second = commit(wt, 'writer-test.js', 'add writer tests')
        git(self.root, 'merge', '--no-ff', '-q', 'writer/opaque')
        merge = head(self.root)
        self.resume()

        packet = prepare(self, self.root)
        self.assert_changes(packet, 'writer.js', 'writer-test.js')
        self.assertNotIn('foreign.js', changes(packet))
        self.assert_exclusions(packet, kept=(first, sync, second, merge), excluded=(foreign,))

    def test_unknown_paused_changes_are_kept_even_after_an_immediate_pause(self) -> None:
        self.pause()
        plain = commit(self.root, 'plain.js', 'add util')
        side, merge = branch_merge(self.root, 'writer/opaque', 'writer.js', 'add writer change')
        self.resume()

        packet = prepare(self, self.root)
        self.assert_changes(packet, 'plain.js', 'writer.js')
        self.assert_exclusions(packet, kept=(plain, side, merge), excluded=())

    def test_writer_created_while_paused_and_merged_after_resume(self) -> None:
        wt = self.root.parent / 'writer'
        git(self.root, 'worktree', 'add', '-qb', 'writer/opaque', str(wt))
        self.pause()
        first = commit(wt, 'writer.js', 'add writer change')
        second = commit(wt, 'writer-test.js', 'add writer tests')
        foreign = self.foreign_commit()
        self.resume()
        git(self.root, 'merge', '--no-ff', '-q', 'writer/opaque')
        merge = head(self.root)

        packet = prepare(self, self.root)
        self.assert_changes(packet, 'writer.js', 'writer-test.js')
        self.assertNotIn('foreign.js', changes(packet))
        self.assert_exclusions(packet, kept=(first, second, merge), excluded=(foreign,))

    def test_later_merge_does_not_reintroduce_an_excluded_side_commit(self) -> None:
        self.pause()
        git(self.root, 'switch', '-qc', 'integration')
        ok(self, athena('sprint', 'start', 'r/y', '--slug', 's-y', cwd=self.root))
        foreign = self.source_commit('foreign.js', 'feat(s-y): other sprint')
        self.pause()
        self.resume()

        git(self.root, 'switch', '-q', self.main)
        git(self.root, 'merge', '--no-ff', '--no-commit', '-q', 'integration')
        merge = self.source_commit('merge-only.js', 'merge integration')

        packet = prepare(self, self.root)
        self.assert_changes(packet, 'merge-only.js')
        self.assertNotIn('foreign.js', changes(packet))
        self.assert_exclusions(packet, kept=(merge,), excluded=(foreign,))


if __name__ == '__main__':
    unittest.main()
