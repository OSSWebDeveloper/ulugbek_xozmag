from unittest import TestCase
from unittest.mock import Mock, patch
import bizaropos_server as server


class ServerUpdateTests(TestCase):
    def setUp(self):
        self.app = server.Supervisor()
        self.app.icon = Mock()
        self.app.notify = Mock()
        self.app.start = Mock()
        self.app.stop_worker = Mock()
        self.app.check_update = Mock(return_value=('old', 'new'))

    def test_current_version_does_not_stop_server(self):
        self.app.check_update.return_value = ('same', 'same')
        self.app.update()
        self.app.stop_worker.assert_not_called()

    def test_unpublished_code_is_not_overwritten(self):
        self.app.git = Mock(return_value=' M sotuv/views.py')
        self.app.update()
        self.app.stop_worker.assert_not_called()
        self.assertIn('saqlanmagan', self.app.notify.call_args.args[0])

    def test_remote_database_change_is_blocked(self):
        self.app.git = Mock(side_effect=['', '', 'db.sqlite3\nsotuv/views.py'])
        with self.assertRaises(RuntimeError):
            self.app.update()
        self.app.stop_worker.assert_not_called()

    @patch.object(server, 'backup')
    def test_backup_precedes_fast_forward(self, backup):
        order = []
        self.app.git = Mock(side_effect=lambda *args: 'sotuv/views.py' if args[0] == 'diff' else order.append(args[0]) or '')
        backup.side_effect = lambda: order.append('backup') or 'saved'
        self.app.update()
        self.assertLess(order.index('backup'), order.index('merge'))
        self.app.start.assert_called_once()

    @patch.object(server, 'backup', side_effect=OSError('disk full'))
    def test_backup_failure_never_merges(self, backup):
        self.app.git = Mock(side_effect=['', '', 'sotuv/views.py'])
        with self.assertRaises(OSError):
            self.app.update()
        self.assertEqual(self.app.git.call_count, 3)
        self.app.start.assert_called_once()
