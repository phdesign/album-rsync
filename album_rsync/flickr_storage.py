import os
import re
import webbrowser
import logging
from tempfile import NamedTemporaryFile
import flickr_api
from .storage import RemoteStorage
from .file_info import FileInfo
from .folder_info import FolderInfo
from .local_storage import mkdirp
from .config import __packagename__

TOKEN_FILENAME = __packagename__ + '.token'
"""
About Tags
----------

Normal Tags
With normal tags, the accepted characters for uniqueness checking are [A-Za-z0-9] (in regex form) - so all other
characters are stripped out (and uppercase characters are downcased eg: A->a) *but* they're maintained for
"viewing" (reading) - a way of maintaining ease of use for users and ease of indexing/searching etc for the system.

Machine Tags
Have been developed to support intra-application tagging (eg: delicious, upcoming, last.fm, dopplr and more).
They have the following structure:
namespace:predicate=value

a namespace, i.e. upcoming [who is going to care about this tag]
a predicate, i.e. event [what does this apply to]
a value, i.e. 123456 [which one is this]
"""
CHECKSUM_PREFIX = 'checksum:md5'
EXTENSION_PREFIX = 'flickrrsync:extn'
OAUTH_PERMISSIONS = 'write'
logger = logging.getLogger(__name__)

class FlickrStorage(RemoteStorage):

    def __init__(self, config, resiliently):
        self._config = config
        self._resiliently = resiliently
        self._is_authenticated = False
        self._user = None
        self._photosets = {}
        self._photos = {}

    def list_folders(self):
        """
        Lists all photosets in Flickr

        Returns:
            A lazy loaded generator function of FolderInfo objects
        """
        self._authenticate()

        walker = self._resiliently.call(flickr_api.objects.Walker, self._user.getPhotosets)     #pylint: disable=no-member
        for photoset in walker:
            self._photosets[photoset.id] = photoset
            folder = FolderInfo(id=photoset.id, name=photoset.title)
            if self._should_include(folder.name, self._config.include_dir, self._config.exclude_dir):
                yield folder

    def list_files(self, folder):
        """
        Lists all photos within a photoset

        Args:
            folder: The FolderInfo object of the folder to list (from list_folders), or None to list all photos not
                in a photoset

        Returns:
            A lazy loaded generator function of FileInfo objects

        Raises:
            KeyError: If folder.id is unrecognised
        """
        self._authenticate()

        if not folder.is_root:
            walker = self._resiliently.call(
                flickr_api.objects.Walker,
                self._photosets[folder.id].getPhotos,
                extras='original_format,tags')
        else:
            walker = self._resiliently.call(
                flickr_api.objects.Walker,
                self._user.getNotInSetPhotos,     #pylint: disable=no-member
                extras='original_format,tags')

        for photo in walker:
            self._photos[photo.id] = photo
            fileinfo = self._get_file_info(photo)
            if self._should_include(fileinfo.name, self._config.include, self._config.exclude):
                yield fileinfo

    def download(self, fileinfo, dest):
        """
        Downloads a photo from Flickr to local file system

        Args:
            fileinfo: The file info object (as returned by list_files) of the file to download
            dest: The file system path to save the file to

        Raises:
            KeyError: If the fileinfo.id is unrecognised
        """
        mkdirp(dest)
        photo = self._photos[fileinfo.id]
        is_video = photo.media == 'video'
        size = 'Video Original' if is_video else 'Original'
        dest_without_extn = os.path.splitext(dest)[0]
        self._resiliently.call(photo.save, dest_without_extn, size_label=size)

    def upload(self, src, folder_name, file_name, checksum):
        """
        Uploads a photo to Flickr from local file system

        Args:
            src: The file system path to upload the photo from
            folder_name: The photset name to add the photo to
            file_name: The name of the photo, any extension will be removed

        Raises:
            KeyError: If the fileinfo.id is unrecognised
        """
        title, extension = os.path.splitext(file_name)
        tags = '{} "{}={}"'.format(self._config.tags, EXTENSION_PREFIX, extension[1:])
        if checksum:
            tags = '{} {}={}'.format(tags, CHECKSUM_PREFIX, checksum)

        # Have to pass arguments as a dict because `async` is a keyword
        photo = self._resiliently.call(flickr_api.upload, **{
            'photo_file': src,
            'title': title,
            'tags': tags.strip(),
            'is_public': self._config.is_public,
            'is_friend': self._config.is_friend,
            'is_family': self._config.is_family,
            'async': 0})

        if folder_name:
            photoset = self._get_folder_by_name(folder_name)
            if not photoset:
                photoset = self._resiliently.call(flickr_api.Photoset.create, title=folder_name, primary_photo=photo)
                self._photosets[photoset.id] = photoset
            else:
                self._resiliently.call(photoset.addPhoto, photo=photo)

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
        return next((x for x in self._photosets.values() if x.title.lower() == name.lower()), None)

    def _get_file_info(self, photo):
        name = photo.title if photo.title else photo.id
        checksum = None
        extension = None
        if photo.tags:
            # If we've just pulled the photo, tags is a string, if we've inspected any properties like 'media', it becomes a list
            tags = photo.tags.split() if isinstance(photo.tags, str) else [tag.text for tag in photo.tags]
            checksum = next((parts[1] for parts in (tag.split('=') for tag in tags) if parts[0] == CHECKSUM_PREFIX), None)
            extension = next((parts[1] for parts in (tag.split('=') for tag in tags) if parts[0] == EXTENSION_PREFIX), None)
        if not extension:
            extension = photo.originalformat
        if extension:
            name += "." + extension
        return FileInfo(id=photo.id, name=name, checksum=checksum)

    def _should_include(self, name, include_pattern, exclude_pattern):
        return ((not include_pattern or re.search(include_pattern, name, flags=re.IGNORECASE)) and
                (not exclude_pattern or not re.search(exclude_pattern, name, flags=re.IGNORECASE)))

    def _authenticate(self):
        if self._is_authenticated:
            return

        flickr_api.set_keys(api_key=self._config.api_key, api_secret=self._config.api_secret)

        token_path = self._config.locate_datafile(TOKEN_FILENAME)
        try:
            if token_path:
                auth_handler = flickr_api.auth.AuthHandler.load(token_path)

            else:
                token_path = self._config.default_datafile(TOKEN_FILENAME)
                auth_handler = flickr_api.auth.AuthHandler()
                permissions_requested = OAUTH_PERMISSIONS
                url = auth_handler.get_authorization_url(permissions_requested)
                webbrowser.open(url)
                print("Please enter the OAuth verifier tag once logged in:")
                verifier_code = input("> ")
                auth_handler.set_verifier(verifier_code)
                auth_handler.save(token_path)

            flickr_api.set_auth_handler(auth_handler)
            self._user = flickr_api.test.login()
            self._is_authenticated = True
        except (ValueError, flickr_api.flickrerrors.FlickrError) as err:
            print(f"""{err}
Use -v / --verbose to list the ensure the correct settings are being used
Go to http://www.flickr.com/services/apps/create/apply to apply for a Flickr API key""")
            exit(1)
