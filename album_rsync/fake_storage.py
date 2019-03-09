import time
import random
from .storage import Storage
from .file_info import FileInfo
from .folder_info import FolderInfo
from .root_folder_info import RootFolderInfo

class FakeStorage(Storage):
    instance_count = 0

    def __init__(self, config):
        self.path = ''
        self._config = config
        self._instance = FakeStorage.instance_count
        self._folders = self._fake_data()
        FakeStorage.instance_count += 1

    def list_folders(self):
        return (self._intense_calculation(f['folder']) for f in self._folders if not f['folder'].is_root)

    def list_files(self, folder):
        files = next((f['files'] for f in self._folders \
            if f['folder'] == folder or (f['folder'].is_root and folder.is_root)), [])
        return (self._intense_calculation(f) for f in files)

    def copy_file(self, fileinfo, folder_name, dest_storage):
        self._intense_calculation(None)

    def delete_file(self, fileinfo, folder_name):
        folder = next((f for f in self._folders \
            if f['folder'].name == folder_name or (not folder_name and f['folder'].is_root)))
        folder['files'].remove(fileinfo)

    def delete_folder(self, folder):
        to_delete = next(f for f in self._folders \
            if f['folder'] == folder or (f['folder'].is_root and folder.is_root))
        if to_delete['files']:
            return False
        self._folders.remove(to_delete)
        return True

    def _intense_calculation(self, value):
        # sleep for a random short duration between 0.5 to 2.0 seconds to simulate a long-running calculation
        time.sleep(random.randint(2, 6) * .1)
        return value

    def _fake_data(self):
        if self._instance == 0:
            return [
                {'folder': RootFolderInfo(), 'files': [FileInfo(id=10, name='A File')]},
                {'folder': FolderInfo(id=2, name='A Folder'), 'files': [FileInfo(id=20, name='A File')]},
                {'folder': FolderInfo(id=3, name='B Folder'), 'files': [FileInfo(id=30, name='A File'), FileInfo(id=31, name='B File')]},
                {'folder': FolderInfo(id=4, name='C Folder'), 'files': [FileInfo(id=40, name='A File'), FileInfo(id=41, name='B File')]},
            ]

        return [
            {'folder': RootFolderInfo(), 'files': [FileInfo(id=10, name='A File'), FileInfo(id=31, name='B File')]},
            {'folder': FolderInfo(id=2, name='A Folder'), 'files': [FileInfo(id=20, name='A File')]},
            {'folder': FolderInfo(id=4, name='C Folder'), 'files': [FileInfo(id=41, name='B File')]},
            {'folder': FolderInfo(id=5, name='D Folder'), 'files': [FileInfo(id=50, name='A File')]},
        ]
