import os
from tempfile import NamedTemporaryFile
from abc import abstractmethod
from .storage import Storage

class RemoteStorage(Storage):

    @abstractmethod
    def download(self, fileinfo, dest):
        pass

    @abstractmethod
    def upload(self, src, folder_name, file_name, checksum):
        pass

    def copy_file(self, fileinfo, folder_name, dest_storage):
        if isinstance(dest_storage, RemoteStorage):
            temp_file = NamedTemporaryFile()
            self.download(fileinfo, temp_file.name)
            dest_storage.upload(temp_file.name, folder_name, fileinfo.name, fileinfo.checksum)
            temp_file.close()
        else:
            dest = os.path.join(dest_storage.path, folder_name, fileinfo.name)
            self.download(fileinfo, dest)

    @abstractmethod
    def logout(self):
        pass
