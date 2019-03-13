from html import unescape
from .file import File
from .folder import Folder, RootFolder
from .storage import RemoteStorage

class GoogleStorage(RemoteStorage):

    def __init__(self, config, api):
        self._config = config
        self._api = api
        self._folders = None

    def list_folders(self):
        """Lists all albums in Google.

        Returns:
            A lazy loaded generator function of Folder objects.
        """
        return (folder for folder in self._list_all_folders_with_cache()
                if self._should_include(folder.name, self._config.include_dir, self._config.exclude_dir))

    def list_files(self, folder):
        """Lists all photos within an album.

        Note that Google Photos does not support listing 'root' items, e.g. photos not in an album

        Args:
            folder: The Folder object of the folder to list (from list_folders).

        Returns:
            A lazy loaded generator function of File objects.

        Raises:
            KeyError: If folder.id is unrecognised.
            NotImplementedError: If folder is the root folder.
        """
        if isinstance(folder, RootFolder):
            raise NotImplementedError("Google Photos API does not support listing photos not in an album")
        media_items = self._api.get_media_in_folder(folder.id)
        for item in media_items:
            file_ = self._get_file(item)
            if self._should_include(file_.name, self._config.include, self._config.exclude):
                yield file_

    def download(self, file_, dest):
        """Downloads a photo to local file system.

        Args:
            file_: The file info object (as returned by list_files) of the file to download.
            dest: The file system path to save the file to.

        Raises:
            KeyError: If the file_.id is unrecognised.
        """
        self.mkdirp(dest)
        self._api.download(file_.url, dest)

    def upload(self, src, folder_name, file_name, checksum):
        """Uploads a photo from local file system.

        Args:
            src: The file system path to upload the photo from.
            folder_name: The photset name to add the photo to.
            file_name: The name of the photo, any extension will be removed.

        Raises:
            KeyError: If the file_.id is unrecognised.
        """

        if folder_name:
            folder = self._get_folder_by_name(folder_name)
            if not folder:
                album = self._api.create_album(folder_name)
                folder = Folder(id=album['id'], name=unescape(album['title']))
                self._folders.append(folder)
        self._api.upload(src, file_name, folder.id)

    def delete_file(self, file_, folder_name):
        raise NotImplementedError("Google Photos API does not support deleting photos")

    def delete_folder(self, folder):
        raise NotImplementedError("Google Photos API does not support deleting photos")

    def logout(self):
        self._config.save_tokens(self._config.PATH_GOOGLE, {})

    def _get_folder_by_name(self, name):
        folders = self._list_all_folders_with_cache()
        return next((x for x in folders if x.name.lower() == name.lower()), None)

    def _get_file(self, photo):
        name = photo['filename'] if photo['filename'] else photo['id']
        return File(id=photo['id'], name=unescape(name), url=photo['baseUrl'] + '=d')

    def _list_all_folders_with_cache(self):
        """List all folders using a cache.

        This assumes that the list of folders won't change by an external party while this
        program is running

        Returns:
            A list of all folders from the server, caching the list for subsequent calls.
        """
        if not self._folders:
            albums = self._api.list_albums()
            self._folders = [Folder(id=album['id'], name=unescape(album['title'])) for album in albums]
        return self._folders
