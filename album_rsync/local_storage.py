import os
import re
import hashlib
import shutil
import logging
from .storage import Storage, RemoteStorage
from .file_info import FileInfo
from .folder_info import FolderInfo

logger = logging.getLogger(__name__)

def mkdirp(path):
    """
    Creates all missing folders in the path

    Args:
        path: A file system path to create, may include a filename (ignored)
    """
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path), exist_ok=True)

class LocalStorage(Storage):

    def __init__(self, config, path):
        self.path = path
        self._config = config

    def md5_checksum(self, file_path):
        with open(file_path, 'rb') as f:
            checksum = hashlib.md5()
            while True:
                data = f.read(8192)
                if not data:
                    break
                checksum.update(data)
            return checksum.hexdigest()

    def list_folders(self):
        logger.debug("copying files from {}".format(self.path))
        return [
            FolderInfo(id=i, name=name, full_path=path)
            for i, (name, path) in enumerate((x, os.path.join(self.path, x)) for x in os.listdir(self.path))
            if self._should_include(name, self._config.include_dir, self._config.exclude_dir) and os.path.isdir(path)
        ]

    def list_files(self, folder):
        folder_abs = os.path.join(self.path, folder.name)
        return [
            FileInfo(
                id=i,
                name=name,
                full_path=path,
                checksum=self.md5_checksum(path) if self._config.checksum else None)
            for i, (name, path) in enumerate((x, os.path.join(folder_abs, x)) for x in os.listdir(folder_abs))
            if self._should_include(name, self._config.include, self._config.exclude) and os.path.isfile(path)
        ]

    def copy_file(self, fileinfo, folder_name, dest_storage):
        src = fileinfo.full_path
        if isinstance(dest_storage, RemoteStorage):
            dest_storage.upload(src, folder_name, fileinfo.name, fileinfo.checksum)
        else:
            relative_path = os.path.join(folder_name, fileinfo.name)
            dest = os.path.join(dest_storage.path, relative_path)
            mkdirp(dest)
            shutil.copyfile(src, dest)

    def _should_include(self, name, include_pattern, exclude_pattern):
        return ((not include_pattern or re.search(include_pattern, name, flags=re.IGNORECASE)) and
                (not exclude_pattern or not re.search(exclude_pattern, name, flags=re.IGNORECASE)))
