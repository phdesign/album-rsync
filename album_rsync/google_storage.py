import os
import re
from tempfile import NamedTemporaryFile
from .file_info import FileInfo
from .folder_info import FolderInfo
from .google_api import GoogleApi
from .storage import RemoteStorage

class GoogleStorage(RemoteStorage):

    def __init__(self, config):
        self._config = config
        self._api = GoogleApi(config)
        self._folders = {}

    def list_folders(self):
        """
        Lists all albums in Google

        Returns:
            A lazy loaded generator function of FolderInfo objects
        """
        walker = self._api.list_albums()
        for album in walker['albums']:
            folder = FolderInfo(id=album['id'], name=album['title'])
            self._folders[folder.id] = folder
            if self._should_include(folder.name, self._config.include_dir, self._config.exclude_dir):
                yield folder

    def list_files(self, folder):
        """
        Lists all photos within an album.
        Note that Google Photos does not support listing 'root' items, e.g. photos not in an album

        Args:
            folder: The FolderInfo object of the folder to list (from list_folders)

        Returns:
            A lazy loaded generator function of FileInfo objects

        Raises:
            KeyError: If folder.id is unrecognised
            NotImplementedError: If folder is the root folder
        """
        media_items = self._api.get_media_in_folder(folder.id)
        return filter(lambda x: self._should_include(x.name, self._config.include, self._config.exclude),
                      (self._get_file_info(photo) for photo in media_items))

    def download(self, fileinfo, dest):
        """
        Downloads a photo to local file system

        Args:
            fileinfo: The file info object (as returned by list_files) of the file to download
            dest: The file system path to save the file to

        Raises:
            KeyError: If the fileinfo.id is unrecognised
        """
        self.mkdirp(dest)
        self._api.download(fileinfo.url, dest)

    def upload(self, src, folder_name, file_name, checksum):
        """
        Uploads a photo from local file system

        Args:
            src: The file system path to upload the photo from
            folder_name: The photset name to add the photo to
            file_name: The name of the photo, any extension will be removed

        Raises:
            KeyError: If the file_info.id is unrecognised
        """

        if folder_name:
            folder = self._get_folder_by_name(folder_name)
            if not folder:
                album = self._api.create_album(folder_name)
                folder = FolderInfo(id=album['id'], name=album['title'])
                self._folders[folder.id] = folder
            folder_id = folder.id
        self._api.upload(src, file_name, folder_id)

    def copy_file(self, fileinfo, folder_name, dest_storage):
        if isinstance(dest_storage, RemoteStorage):
            temp_file = NamedTemporaryFile()
            self.download(fileinfo, temp_file.name)
            dest_storage.upload(temp_file.name, folder_name, fileinfo.name, fileinfo.checksum)
            temp_file.close()
        else:
            dest = os.path.join(dest_storage.path, folder_name, fileinfo.name)
            self.download(fileinfo, dest)

    def _get_folder_by_name(self, name):
        return next((x for x in self._folders.values() if x.name.lower() == name.lower()), None)

    def _get_file_info(self, photo):
        name = photo['filename'] if photo['filename'] else photo['id']
        return FileInfo(id=photo['id'], name=name, url=photo['baseUrl'] + '=d')

    def _should_include(self, name, include_pattern, exclude_pattern):
        return ((not include_pattern or re.search(include_pattern, name, flags=re.IGNORECASE)) and
                (not exclude_pattern or not re.search(exclude_pattern, name, flags=re.IGNORECASE)))
