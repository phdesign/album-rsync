import os
import webbrowser
import logging
import flickr_api
from .storage import RemoteStorage
from .file import File
from .folder import Folder
from .config import __packagename__
from .utils import choice

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
"""     #pylint: disable=pointless-string-statement
CHECKSUM_PREFIX = 'checksum:md5'
EXTENSION_PREFIX = 'flickrrsync:extn'
OAUTH_PERMISSIONS_WRITE = 'write'
OAUTH_PERMISSIONS_DELETE = 'delete'
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
            A lazy loaded generator function of Folder objects
        """
        self._authenticate()

        walker = self._resiliently.call(flickr_api.objects.Walker, self._user.getPhotosets)     #pylint: disable=no-member
        for photoset in walker:
            self._photosets[photoset.id] = photoset
            folder = Folder(id=photoset.id, name=photoset.title)
            if self._should_include(folder.name, self._config.include_dir, self._config.exclude_dir):
                yield folder

    def list_files(self, folder):
        """
        Lists all photos within a photoset

        Args:
            folder: The Folder object of the folder to list (from list_folders), or None to list all photos not
                in a photoset

        Returns:
            A lazy loaded generator function of File objects

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
            file_ = self._get_file(photo)
            if self._should_include(file_.name, self._config.include, self._config.exclude):
                yield file_

    def download(self, file_, dest):
        """
        Downloads a photo from Flickr to local file system

        Args:
            file_: The file info object (as returned by list_files) of the file to download
            dest: The file system path to save the file to

        Raises:
            KeyError: If the file_.id is unrecognised
        """
        self.mkdirp(dest)
        photo = self._photos[file_.id]
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
            KeyError: If the file_.id is unrecognised
        """
        title, extension = os.path.splitext(file_name)
        tags = '{} "{}={}"'.format(self._config.flickr_tags, EXTENSION_PREFIX, extension[1:])
        if checksum:
            tags = '{} {}={}'.format(tags, CHECKSUM_PREFIX, checksum)

        # Have to pass arguments as a dict because `async` is a keyword
        photo = self._resiliently.call(flickr_api.upload, **{
            'photo_file': src,
            'title': title,
            'tags': tags.strip(),
            'is_public': self._config.flickr_is_public,
            'is_friend': self._config.flickr_is_friend,
            'is_family': self._config.flickr_is_family,
            'async': 0})

        if folder_name:
            photoset = self._get_folder_by_name(folder_name)
            if not photoset:
                photoset = self._resiliently.call(flickr_api.Photoset.create, title=folder_name, primary_photo=photo)
                self._photosets[photoset.id] = photoset
            else:
                self._resiliently.call(photoset.addPhoto, photo=photo)

    def delete_file(self, file_, folder_name):
        photo = self._photos[file_.id]
        self._resiliently.call(photo.delete)
        del self._photos[file_.id]

    def delete_folder(self, folder):
        photoset = self._photosets[folder.id]
        self._resiliently.call(photoset.delete)
        del self._photosets[folder.id]

    def logout(self):
        self._config.save_tokens(self._config.PATH_FLICKR, {})

    def _get_folder_by_name(self, name):
        return next((x for x in self._photosets.values() if x.title.lower() == name.lower()), None)

    def _get_file(self, photo):
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
        return File(id=photo.id, name=name, checksum=checksum)

    def _authenticate(self):
        if self._is_authenticated:
            return

        try:
            flickr_api.set_keys(api_key=self._config.flickr_api_key, api_secret=self._config.flickr_api_secret)
            tokens = self._config.load_tokens(self._config.PATH_FLICKR)
            if tokens:
                auth_handler = flickr_api.auth.AuthHandler.fromdict(tokens)

            else:
                print("logging in...")
                auth_handler = flickr_api.auth.AuthHandler()
                can_delete = choice("request permission to delete files?", "no")
                permissions_requested = OAUTH_PERMISSIONS_DELETE if can_delete else OAUTH_PERMISSIONS_WRITE
                url = auth_handler.get_authorization_url(permissions_requested)
                webbrowser.open(url)
                print("Please enter the OAuth verifier tag once logged in:")
                verifier_code = input("> ")
                auth_handler.set_verifier(verifier_code)
                self._config.save_tokens(self._config.PATH_FLICKR, auth_handler.todict())

            flickr_api.set_auth_handler(auth_handler)
            self._user = flickr_api.test.login()
            self._is_authenticated = True

        except Exception as err:    #pylint: disable=broad-except
            logger.error(
                "Unable to authenticate with Flickr\n"
                f"{err}\n"
                "Use -v / --verbose to list the ensure the correct settings are being used\n"
                "Go to http://www.flickr.com/services/apps/create/apply to apply for a Flickr API key")
            exit(1)
