#pylint: disable=wrong-import-position, attribute-defined-outside-init
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from unittest.mock import MagicMock
import pytest
from album_rsync.google_storage import GoogleStorage

class TestGoogleStorage:

    def setup_method(self):
        self.config = MagicMock()
        self.config.include = ''
        self.config.exclude = ''
        self.config.include_dir = ''
        self.config.exclude_dir = ''
        self.api = MagicMock()

    @pytest.fixture
    def folders_fixture(self):
        return [
            {
                'id': '123',
                'title': 'Folder 1'
            },
            {
                'id': '456',
                'title': 'Folder 2'
            }]

    def test_should_list_folders_given_there_are_folders(self, folders_fixture):
        self.api.list_albums.return_value = {'albums': folders_fixture}
        storage = GoogleStorage(self.config, self.api)
        folders = list(storage.list_folders())
        assert len(folders) == 2

    def test_should_not_list_folder_given_its_excluded(self, folders_fixture):
        self.config.exclude_dir = 'Folder 1'
        self.api.list_albums.return_value = {'albums': folders_fixture}
        storage = GoogleStorage(self.config, self.api)
        folders = list(storage.list_folders())
        assert len(folders) == 1
        assert folders[0].name == 'Folder 2'

    def test_should_not_list_folder_given_its_not_included(self, folders_fixture):
        self.config.include_dir = 'Folder 1'
        self.api.list_albums.return_value = {'albums': folders_fixture}
        storage = GoogleStorage(self.config, self.api)
        folders = list(storage.list_folders())
        assert len(folders) == 1
        assert folders[0].name == 'Folder 1'

    def test_should_not_list_folders_given_there_are_no_folders(self):
        self.api.list_albums.return_value = {'albums': []}
        storage = GoogleStorage(self.config, self.api)
        folders = list(storage.list_folders())
        assert not folders

    def test_should_list_files_given_there_are_files(self, files_fixture):
        pass

    def test_should_raise_not_implemented_when_root_folder(self):
        pass

    def test_should_not_list_file_given_its_excluded(self, files_fixture):
        pass

    def test_should_not_list_file_given_its_not_included(self, files_fixture):
        pass

    def test_should_not_list_files_given_there_are_no_files(self):
        pass
    
