import os
import hashlib
import shutil
import logging
from .storage import Storage
from .remote_storage import RemoteStorage
from .file_info import FileInfo
from .folder_info import FolderInfo

logger = logging.getLogger(__name__)

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
        logger.debug(f"copying files from {self.path}")
        return [
            FolderInfo(id=i, name=name, full_path=path)
            for i, (name, path) in enumerate((x, os.path.join(self.path, x)) for x in os.listdir(self.path))
            if self._should_include(name, self._config.include_dir, self._config.exclude_dir) and os.path.isdir(path)
        ]

    def list_files(self, folder):
        folder_path = os.path.join(self.path, folder.name)
        return [
            FileInfo(
                id=i,
                name=name,
                full_path=path,
                checksum=self.md5_checksum(path) if self._config.checksum else None)
            for i, (name, path) in enumerate((x, os.path.join(folder_path, x)) for x in os.listdir(folder_path))
            if self._should_include(name, self._config.include, self._config.exclude) and os.path.isfile(path)
        ]

    def delete_file(self, fileinfo, folder_name):
        file_path = os.path.join(self.path, folder_name, fileinfo.name)
        os.remove(file_path)

    def delete_folder(self, folder):
        folder_path = os.path.join(self.path, folder.name)
        if os.listdir(folder_path):
            return False
        os.rmdir(folder_path)
        return True

    def copy_file(self, fileinfo, folder_name, dest_storage):
        src = fileinfo.full_path
        if isinstance(dest_storage, RemoteStorage):
            dest_storage.upload(src, folder_name, fileinfo.name, fileinfo.checksum)
        else:
            relative_path = os.path.join(folder_name, fileinfo.name)
            dest = os.path.join(dest_storage.path, relative_path)
            self.mkdirp(dest)
            shutil.copyfile(src, dest)

    def logout(self):
        raise NotImplementedError()
