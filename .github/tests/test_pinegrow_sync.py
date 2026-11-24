import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('sync', Path(__file__).parents[1] / 'scripts/pinegrow_sync.py')
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


def run(*args, cwd=None):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = os.getcwd()
        self.root = Path(self.temp.name)
        self.remote = self.root / 'remote.git'
        self.work = self.root / 'work'
        run('init', '--bare', str(self.remote))
        run('clone', str(self.remote), str(self.work))
        os.chdir(self.work)
        run('config', 'user.name', 'Test')
        run('config', 'user.email', 'test@example.com')
        run('checkout', '-b', 'main')
        self.commit('shared.txt', 'base')
        run('push', 'origin', 'main')
        run('branch', 'pinegrow/mx')
        run('push', 'origin', 'pinegrow/mx')

    def tearDown(self):
        os.chdir(self.old)
        self.temp.cleanup()

    def commit(self, name, text):
        Path(name).write_text(text)
        run('add', name)
        run('commit', '-m', text)

    def test_current(self):
        self.assertEqual(sync.sync_branch('pinegrow/mx')['state'], 'current')

    def test_behind_fast_forwards(self):
        self.commit('main.txt', 'new main')
        run('push', 'origin', 'main')
        result = sync.sync_branch('pinegrow/mx')
        self.assertEqual(result['state'], 'current')
        self.assertEqual(result['head'], result['main'])

    def test_ahead_preserves_branch(self):
        run('checkout', 'pinegrow/mx')
        self.commit('mine.txt', 'my edit')
        run('push', 'origin', 'pinegrow/mx')
        result = sync.sync_branch('pinegrow/mx')
        self.assertEqual((result['state'], result['ahead'], result['behind']), ('ahead', 1, 0))

    def test_clean_divergence_preserves_both_edits(self):
        self.commit('main.txt', 'main edit')
        run('push', 'origin', 'main')
        run('checkout', 'pinegrow/mx')
        self.commit('mine.txt', 'my edit')
        original = run('rev-parse', 'HEAD')
        run('push', 'origin', 'pinegrow/mx')
        result = sync.sync_branch('pinegrow/mx')
        self.assertEqual((result['state'], result['behind']), ('ahead', 0))
        self.assertEqual(Path('main.txt').read_text(), 'main edit')
        self.assertEqual(Path('mine.txt').read_text(), 'my edit')
        run('merge-base', '--is-ancestor', original, result['head'])
        run('merge-base', '--is-ancestor', result['main'], result['head'])

    def test_conflict_leaves_remote_unchanged(self):
        self.commit('shared.txt', 'main change')
        run('push', 'origin', 'main')
        run('checkout', 'pinegrow/mx')
        self.commit('shared.txt', 'personal change')
        original = run('rev-parse', 'HEAD')
        run('push', 'origin', 'pinegrow/mx')
        result = sync.sync_branch('pinegrow/mx')
        self.assertEqual(result['state'], 'conflict')
        self.assertEqual(result['files'], ['shared.txt'])
        self.assertEqual(run('rev-parse', 'refs/heads/pinegrow/mx', cwd=self.remote), original)
        self.assertFalse(Path('.git/MERGE_HEAD').exists())

    def test_rejected_push_does_not_rewrite_remote(self):
        self.commit('main.txt', 'main change')
        run('push', 'origin', 'main')
        original = run('rev-parse', 'refs/heads/pinegrow/mx', cwd=self.remote)
        real_git = sync.git
        def reject(*args, **kwargs):
            if args[0] == 'push':
                return subprocess.CompletedProcess(args, 1, '', 'rejected')
            return real_git(*args, **kwargs)
        with patch.object(sync, 'git', side_effect=reject):
            with self.assertRaises(RuntimeError):
                sync.sync_branch('pinegrow/mx')
        self.assertEqual(run('rev-parse', 'refs/heads/pinegrow/mx', cwd=self.remote), original)


if __name__ == '__main__':
    unittest.main()
