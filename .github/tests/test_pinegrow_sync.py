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
        Path(name).parent.mkdir(parents=True, exist_ok=True)
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
        self.assertEqual(result['changed_files'], ['mine.txt'])

    def test_reverted_edits_are_current_despite_extra_history(self):
        run('checkout', 'pinegrow/mx')
        self.commit('shared.txt', 'temporary edit')
        self.commit('shared.txt', 'base')
        run('push', 'origin', 'pinegrow/mx')
        original = run('rev-parse', 'HEAD')
        result = sync.sync_branch('pinegrow/mx')
        self.assertEqual((result['state'], result['ahead']), ('current', 2))
        self.assertEqual(result['changed_files'], [])
        self.assertEqual(result['head'], original)

    def test_sync_history_with_identical_files_is_current(self):
        run('checkout', 'pinegrow/mx')
        run('commit', '--allow-empty', '-m', 'Earlier synchronization')
        run('push', 'origin', 'pinegrow/mx')
        run('checkout', 'main')
        self.commit('main.txt', 'new main')
        run('push', 'origin', 'main')
        result = sync.sync_branch('pinegrow/mx')
        self.assertEqual((result['state'], result['behind']), ('current', 0))
        self.assertGreater(result['ahead'], 0)
        self.assertEqual(result['changed_files'], [])
        self.assertEqual(run('show', '-s', '--format=%s', result['head']),
                         'Sync main into pinegrow/mx')

    def test_repeated_squash_merges_keep_main_clean_and_clear_warnings(self):
        for name, title in [('first', 'Publish first edit'), ('second', 'Publish second edit')]:
            run('checkout', 'pinegrow/mx')
            run('merge', '--ff-only', 'origin/pinegrow/mx')
            self.commit(name + '.txt', name + ' website edit')
            run('push', 'origin', 'pinegrow/mx')
            pending = sync.sync_branch('pinegrow/mx')
            self.assertEqual(pending['state'], 'ahead')
            self.assertEqual(pending['changed_files'], [name + '.txt'])
            run('checkout', 'main')
            run('merge', '--squash', 'origin/pinegrow/mx')
            run('commit', '-m', title)
            run('push', 'origin', 'main')
            result = sync.sync_branch('pinegrow/mx')
            self.assertEqual((result['state'], result['behind']), ('current', 0))
            self.assertGreater(result['ahead'], 0)
            self.assertEqual(result['changed_files'], [])
        self.assertEqual(run('log', '--format=%s', 'main').splitlines(),
                         ['Publish second edit', 'Publish first edit', 'base'])
        self.assertEqual(run('rev-list', '--merges', 'main'), '')

    def test_report_closes_issue_for_history_only_commits(self):
        run('checkout', 'pinegrow/mx')
        run('commit', '--allow-empty', '-m', 'Earlier synchronization')
        run('push', 'origin', 'pinegrow/mx')
        status = sync.sync_branch('pinegrow/mx')
        issue = {'number': 3, 'user': {'type': 'Bot'}, 'state': 'open',
                 'body': '<!-- pinegrow-sync:pinegrow/mx -->\nOld warning'}
        def api_response(method, path, payload=None):
            return [issue] if method == 'GET' and '/issues?' in path else None
        with patch.dict(os.environ, {'GH_REPO': 'example/site', 'GITHUB_RUN_ID': '1',
                                    'GITHUB_STEP_SUMMARY': ''}):
            with patch.object(sync, 'api', side_effect=api_response) as api:
                sync.report('pinegrow/mx', status)
        update = next(call.args[2] for call in api.call_args_list if call.args[0] == 'PATCH')
        self.assertEqual(update['state'], 'closed')
        self.assertEqual(update['labels'], ['pinegrow-sync'])
        self.assertIn('0 files changed', update['title'])
        self.assertIn('no pending file changes', update['body'])
        check = next(call.args[2] for call in api.call_args_list if '/check-runs' in call.args[1])
        self.assertEqual(check['conclusion'], 'success')

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

    def test_deleted_workflow_is_restored_even_when_main_is_not_ahead(self):
        workflow = '.github/workflows/pinegrow-sync.yml'
        self.commit(workflow, 'shared workflow')
        run('push', 'origin', 'main')
        run('checkout', 'pinegrow/mx')
        run('merge', '--ff-only', 'main')
        run('rm', workflow)
        run('commit', '-m', 'Pinegrow publish deleted hidden files')
        self.commit('mine.txt', 'keep my website edit')
        run('push', 'origin', 'pinegrow/mx')
        result = sync.sync_branch('pinegrow/mx')
        self.assertEqual(result['state'], 'ahead')
        self.assertEqual(result['behind'], 0)
        self.assertEqual(Path(workflow).read_text(), 'shared workflow')
        self.assertEqual(Path('mine.txt').read_text(), 'keep my website edit')
        self.assertEqual(run('show', 'refs/heads/pinegrow/mx:' + workflow, cwd=self.remote), 'shared workflow')

    def test_repair_without_website_edits_is_current(self):
        workflow = '.github/workflows/pinegrow-sync.yml'
        self.commit(workflow, 'shared workflow')
        run('push', 'origin', 'main')
        run('checkout', 'pinegrow/mx')
        run('merge', '--ff-only', 'main')
        run('rm', workflow)
        run('commit', '-m', 'Pinegrow publish deleted hidden files')
        run('push', 'origin', 'pinegrow/mx')
        result = sync.sync_branch('pinegrow/mx')
        self.assertEqual(result['state'], 'current')
        self.assertGreater(result['ahead'], 0)
        self.assertEqual(result['changed_files'], [])
        self.assertEqual(Path(workflow).read_text(), 'shared workflow')


if __name__ == '__main__':
    unittest.main()
