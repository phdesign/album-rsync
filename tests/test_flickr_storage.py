#pylint: disable=wrong-import-position, attribute-defined-outside-init
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from unittest.mock import MagicMock, patch
import pytest
from album_rsync.resiliently import Resiliently
from album_rsync.flickr_storage import FlickrStorage
from album_rsync.folder import RootFolder

class TestFlickrStorage:

    def setup_method(self):
        def passthrough(func, *args, **kwargs):
            return func(*args, **kwargs)

        self.config = MagicMock()
        self.config.include = ''
        self.config.exclude = ''
        self.config.include_dir = ''
        self.config.exclude_dir = ''
        self.config.throttling = 0
        self.config.retry = 0
        self.user = MagicMock()
        self.flickr_api_patch = patch('album_rsync.flickr_storage.flickr_api', create=True)
        self.mock_flickr_api = self.flickr_api_patch.start()
        self.mock_flickr_api.test.login.return_value = self.user
        self.mock_flickr_api.objects.Walker = passthrough
        self.mock_flickr_api.Photoset.create = MagicMock()

    def teardown_method(self):
        self.flickr_api_patch.stop()

    @pytest.fixture
    def folders_fixture(self):
        return [
            MagicMock(id='123', title='Folder 1'),
            MagicMock(id='456', title='Folder 2')]

    def test_list_folders_should_return_folders_given_there_are_folders(self, folders_fixture):
        self.user.getPhotosets.return_value = folders_fixture
        storage = FlickrStorage(self.config, Resiliently(self.config))
        folders = list(storage.list_folders())

        assert len(folders) == 2

    def test_list_folders_should_not_list_folder_given_its_excluded(self, folders_fixture):
        self.config.exclude_dir = 'Folder 1'
        self.user.getPhotosets.return_value = folders_fixture
        storage = FlickrStorage(self.config, Resiliently(self.config))
        folders = list(storage.list_folders())

        assert len(folders) == 1
        assert folders[0].name == 'Folder 2'

    def test_list_folders_should_not_list_folder_given_its_not_included(self, folders_fixture):
        self.config.include_dir = 'Folder 1'
        self.user.getPhotosets.return_value = folders_fixture
        storage = FlickrStorage(self.config, Resiliently(self.config))
        folders = list(storage.list_folders())

        assert len(folders) == 1
        assert folders[0].name == 'Folder 1'

    def test_list_folders_should_return_nothing_given_there_are_no_folders(self):
        self.user.getPhotosets.return_value = []
        storage = FlickrStorage(self.config, Resiliently(self.config))
        folders = list(storage.list_folders())

        assert not folders

    @pytest.fixture
    def files_fixture(self):
        return [
            MagicMock(id='123', title='image1', tags='', originalformat='jpg'),
            MagicMock(id='456', title='image2', tags='', originalformat='jpg')]

    def test_list_files_should_return_files_given_there_are_files(self, folders_fixture, files_fixture):
        self.user.getPhotosets.return_value = folders_fixture
        folders_fixture[0].getPhotos.return_value = files_fixture
        storage = FlickrStorage(self.config, Resiliently(self.config))
        folders = list(storage.list_folders())
        files = list(storage.list_files(folders[0]))

        assert len(files) == 2

    def test_list_files_should_list_files_when_root_folder_is_passed(self, files_fixture):
        self.user.getNotInSetPhotos.return_value = files_fixture
        storage = FlickrStorage(self.config, Resiliently(self.config))
        folder = RootFolder()
        files = list(storage.list_files(folder))

        assert len(files) == 2

    def test_list_files_should_not_list_file_given_its_excluded(self, folders_fixture, files_fixture):
        self.config.exclude = 'image1'
        self.user.getPhotosets.return_value = folders_fixture
        folders_fixture[0].getPhotos.return_value = files_fixture
        storage = FlickrStorage(self.config, Resiliently(self.config))
        folders = list(storage.list_folders())
        files = list(storage.list_files(folders[0]))

        assert len(files) == 1
        assert files[0].name == 'image2.jpg'

    def test_list_files_should_not_list_file_given_its_not_included(self, folders_fixture, files_fixture):
        self.config.include = 'image1'
        self.user.getPhotosets.return_value = folders_fixture
        folders_fixture[0].getPhotos.return_value = files_fixture
        storage = FlickrStorage(self.config, Resiliently(self.config))
        folders = list(storage.list_folders())
        files = list(storage.list_files(folders[0]))

        assert len(files) == 1
        assert files[0].name == 'image1.jpg'

    def test_list_files_should_not_list_files_given_there_are_no_files(self, folders_fixture):
        self.user.getPhotosets.return_value = folders_fixture
        folders_fixture[0].getPhotos.return_value = []
        storage = FlickrStorage(self.config, Resiliently(self.config))
        folders = list(storage.list_folders())
        files = list(storage.list_files(folders[0]))

        assert not files

    def test_upload_should_not_create_folder_given_it_exists(self, folders_fixture):
        self.user.getPhotosets.return_value = folders_fixture
        folders_fixture[0].addPhoto = MagicMock()
        storage = FlickrStorage(self.config, Resiliently(self.config))
        folders = list(storage.list_folders())
        storage.upload('/', folders[0].name, 'micky.jpg', None)

        self.mock_flickr_api.Photoset.create.assert_not_called()
        folders_fixture[0].addPhoto.assert_called_once()

    def test_upload_should_create_folder_given_it_doesnt_exist(self):
        self.user.getPhotosets.return_value = []
        self.mock_flickr_api.Photoset.create.return_value = MagicMock()
        storage = FlickrStorage(self.config, Resiliently(self.config))
        _ = list(storage.list_folders())
        storage.upload('/', 'new', 'micky.jpg', None)

        self.mock_flickr_api.Photoset.create.assert_called_once()
