#pylint: disable=wrong-import-position, attribute-defined-outside-init
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from unittest.mock import MagicMock, patch, call
from tests.helpers import setup_storage
from album_rsync.sync import Sync
from album_rsync.file import File
from album_rsync.folder import Folder, RootFolder

class TestSyncBase:

    def setup_method(self):
        self.print_patch = patch('album_rsync.sync.print')
        self.mock_print = self.print_patch.start()
        self.logger_patch = patch('album_rsync.csv_walker.logger', create=True)
        self.logger_patch.start()
        self.choice_patch = patch('album_rsync.sync.choice')
        self.choice_patch.start().return_value = True

        self.config = MagicMock()
        self.config.dry_run = False
        self.src_storage = MagicMock()
        self.dest_storage = MagicMock()
        self.folder_one = Folder(id=1, name='A')
        self.folder_two = Folder(id=2, name='B')
        self.folder_three = Folder(id=3, name='C')
        self.folder_four = Folder(id=4, name='D')
        self.root_folder = RootFolder()
        self.file_one = File(id=1, name='A')
        self.file_two = File(id=1, name='B')

        self.sync = Sync(self.config, self.src_storage, self.dest_storage)
        self.mock = MagicMock()
        self.src_storage.copy_file = self.mock

        self.mock_delete_folder = MagicMock()
        self.mock_delete_folder.return_value = 1
        self.dest_storage.delete_folder = self.mock_delete_folder

    def teardown_method(self):
        self.print_patch.stop()
        self.logger_patch.stop()
        self.choice_patch.stop()

class TestSync(TestSyncBase):

    def test_should_not_copy_anything_given_dry_run_enabled(self):
        self.config.dry_run = True
        setup_storage(self.src_storage, [
            {'folder': self.folder_one, 'files': [self.file_one]},
            {'folder': self.folder_two, 'files': [self.file_one, self.file_two]}
        ])
        setup_storage(self.dest_storage, [
            {'folder': self.folder_two, 'files': [self.file_one]}
        ])

        self.sync.run()

        self.mock.assert_not_called()

class TestSyncCopy(TestSyncBase):

    def test_should_copy_folder_for_each_missing_folder_in_src(self):
        setup_storage(self.src_storage, [
            {'folder': self.folder_one, 'files': [self.file_one]},
            {'folder': self.folder_two, 'files': [self.file_one]},
            {'folder': self.folder_three, 'files': [self.file_one]},
        ])
        setup_storage(self.dest_storage, [])

        self.sync.run()

        self.mock.assert_has_calls_exactly([
            call(self.file_one, self.folder_one.name, self.dest_storage),
            call(self.file_one, self.folder_two.name, self.dest_storage),
            call(self.file_one, self.folder_three.name, self.dest_storage)
        ], any_order=True)

    def test_should_copy_folder_for_each_missing_folder_given_some_exist_already(self):
        setup_storage(self.src_storage, [
            {'folder': self.folder_one, 'files': [self.file_one]},
            {'folder': self.folder_two, 'files': [self.file_one]},
            {'folder': self.folder_three, 'files': [self.file_one]},
            {'folder': self.folder_four, 'files': [self.file_one]},
        ])
        setup_storage(self.dest_storage, [
            {'folder': self.folder_four, 'files': [self.file_one]},
            {'folder': self.folder_three, 'files': [self.file_one]}
        ])

        self.sync.run()

        self.mock.assert_has_calls_exactly([
            call(self.file_one, self.folder_one.name, self.dest_storage),
            call(self.file_one, self.folder_two.name, self.dest_storage)
        ], any_order=True)

    def test_should_not_copy_folder_given_all_exist_already(self):
        setup_storage(self.src_storage, [
            {'folder': self.folder_one, 'files': [self.file_one]},
            {'folder': self.folder_two, 'files': [self.file_one]}
        ])
        setup_storage(self.dest_storage, [
            {'folder': self.folder_two, 'files': [self.file_one]},
            {'folder': self.folder_one, 'files': [self.file_one]}
        ])

        self.sync.run()

        self.mock.assert_not_called()

    def test_should_skip_copying_when_error_occurs(self):
        self.mock.side_effect = FileNotFoundError()
        setup_storage(self.src_storage, [
            {'folder': self.folder_one, 'files': [self.file_one]},
            {'folder': self.folder_two, 'files': [self.file_one, self.file_two]}
        ])
        setup_storage(self.dest_storage, [
            {'folder': self.folder_two, 'files': [self.file_one]}
        ])

        self.sync.run()

        self.mock.assert_has_calls_exactly([
            call(self.file_one, self.folder_one.name, self.dest_storage),
            call(self.file_two, self.folder_two.name, self.dest_storage)
        ], any_order=True)

class TestSyncMerge(TestSyncBase):

    def test_should_copy_missing_files_in_existing_folder(self):
        setup_storage(self.src_storage, [{
            'folder': self.folder_one,
            'files': [self.file_one, self.file_two]
        }])
        setup_storage(self.dest_storage, [{
            'folder': self.folder_one,
            'files': []
        }])

        self.sync.run()

        self.mock.assert_has_calls_exactly([
            call(self.file_one, self.folder_one.name, self.dest_storage),
            call(self.file_two, self.folder_one.name, self.dest_storage)
        ], any_order=True)

    def test_should_copy_missing_files_from_all_folders(self):
        setup_storage(self.src_storage, [
            {'folder': self.folder_one, 'files': [self.file_one]},
            {'folder': self.folder_two, 'files': [self.file_two]}
        ])
        setup_storage(self.dest_storage, [
            {'folder': self.folder_one, 'files': []},
            {'folder': self.folder_two, 'files': []}
        ])

        self.sync.run()

        self.mock.assert_has_calls_exactly([
            call(self.file_one, self.folder_one.name, self.dest_storage),
            call(self.file_two, self.folder_two.name, self.dest_storage)
        ], any_order=True)

    def test_should_copy_missing_files_in_existing_folder_given_files_exist(self):
        setup_storage(self.src_storage, [{
            'folder': self.folder_one,
            'files': [self.file_one, self.file_two]
        }])
        setup_storage(self.dest_storage, [{
            'folder': self.folder_one,
            'files': [self.file_two]
        }])

        self.sync.run()

        self.mock.assert_called_once_with(self.file_one, self.folder_one.name, self.dest_storage)

    def test_should_not_copy_files_given_all_files_exist(self):
        setup_storage(self.src_storage, [{
            'folder': self.folder_one,
            'files': [self.file_one]
        }])
        setup_storage(self.dest_storage, [{
            'folder': self.folder_one,
            'files': [self.file_one]
        }])

        self.sync.run()

        self.mock.assert_not_called()

    def test_should_merge_files_in_root_folder_given_root_files_enabled(self):
        self.config.root_files = True
        setup_storage(self.src_storage, [
            {'folder': self.root_folder, 'files': [self.file_one, self.file_two]},
        ])
        setup_storage(self.dest_storage, [
            {'folder': self.root_folder, 'files': [self.file_two]},
        ])

        self.sync.run()

        self.mock.assert_has_calls_exactly([
            call(self.file_one, '', self.dest_storage),
        ], any_order=True)

class TestSyncDelete(TestSyncBase):

    def setup_method(self):
        super().setup_method()
        self.mock_delete_file = MagicMock()
        self.dest_storage.delete_file = self.mock_delete_file

    def test_should_delete_additional_files_in_destination(self):
        self.config.delete = True
        setup_storage(self.src_storage, [
            {'folder': self.folder_one, 'files': [self.file_one]}
        ])
        setup_storage(self.dest_storage, [
            {'folder': self.folder_one, 'files': [self.file_one, self.file_two]}
        ])

        self.sync.run()

        self.mock_delete_file.assert_called_once_with(self.file_two, self.folder_one.name)
        self.mock_delete_folder.assert_not_called()

    def test_should_not_delete_additional_files_given_delete_flag_false(self):
        self.config.delete = False
        setup_storage(self.src_storage, [
            {'folder': self.folder_one, 'files': [self.file_one]}
        ])
        setup_storage(self.dest_storage, [
            {'folder': self.folder_one, 'files': [self.file_one, self.file_two]}
        ])

        self.sync.run()

        self.mock_delete_file.assert_not_called()
        self.mock_delete_folder.assert_not_called()

    def test_should_delete_additional_files_in_destination_when_comparing_root_folders(self):
        self.config.root_files = True
        self.config.delete = True
        setup_storage(self.src_storage, [
            {'folder': self.root_folder, 'files': [self.file_one]}
        ])
        setup_storage(self.dest_storage, [
            {'folder': self.root_folder, 'files': [self.file_one, self.file_two]}
        ])

        self.sync.run()

        self.mock_delete_file.assert_called_once_with(self.file_two, '')
        self.mock_delete_folder.assert_not_called()

    def test_should_delete_additional_folders_in_destination(self):
        self.config.delete = True
        setup_storage(self.src_storage, [
            {'folder': self.folder_one, 'files': [self.file_one]}
        ])
        setup_storage(self.dest_storage, [
            {'folder': self.folder_one, 'files': [self.file_one]},
            {'folder': self.folder_two, 'files': [self.file_one, self.file_two]}
        ])

        self.sync.run()

        self.mock_delete_file.assert_has_calls_exactly([
            call(self.file_one, self.folder_two.name),
            call(self.file_two, self.folder_two.name)
        ], any_order=True)
        self.mock_delete_folder.assert_called_once_with(self.folder_two)

    def test_should_not_delete_additional_folders_given_delete_flag_false(self):
        self.config.delete = False
        setup_storage(self.src_storage, [
            {'folder': self.folder_one, 'files': [self.file_one]}
        ])
        setup_storage(self.dest_storage, [
            {'folder': self.folder_one, 'files': [self.file_one]},
            {'folder': self.folder_two, 'files': [self.file_one, self.file_two]}
        ])

        self.sync.run()

        self.mock_delete_file.assert_not_called()
        self.mock_delete_folder.assert_not_called()

    def test_should_not_delete_folder_in_destination_when_last_file_deleted(self):
        self.config.delete = True
        setup_storage(self.src_storage, [
            {'folder': self.folder_one, 'files': []}
        ])
        setup_storage(self.dest_storage, [
            {'folder': self.folder_one, 'files': [self.file_one, self.file_two]}
        ])

        self.sync.run()

        self.mock_delete_file.assert_has_calls_exactly([
            call(self.file_one, self.folder_one.name),
            call(self.file_two, self.folder_one.name)
        ], any_order=True)
        self.mock_delete_folder.assert_not_called()
