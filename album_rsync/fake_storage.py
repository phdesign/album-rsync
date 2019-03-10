import time
import random
from .storage import Storage
from .file import File
from .folder import Folder, RootFolder

class FakeStorage(Storage):
    def __init__(self, config, instance_count):
        self.path = ''
        self._config = config
        self._instance = instance_count
        self._folders = self._fake_data()

    def list_folders(self):
        return (self._intense_calculation(f['folder']) for f in self._folders if not f['folder'].is_root)

    def list_files(self, folder):
        files = next((f['files'] for f in self._folders \
            if f['folder'] == folder or (f['folder'].is_root and folder.is_root)), [])
        return (self._intense_calculation(f) for f in files)

    def copy_file(self, file_, folder_name, dest_storage):
        self._intense_calculation(None)

    def delete_file(self, file_, folder_name):
        folder = next((f for f in self._folders \
            if f['folder'].name == folder_name or (not folder_name and f['folder'].is_root)))
        folder['files'].remove(file_)

    def delete_folder(self, folder):
        to_delete = next(f for f in self._folders \
            if f['folder'] == folder or (f['folder'].is_root and folder.is_root))
        if to_delete['files']:
            return False
        self._folders.remove(to_delete)
        return True

    def logout(self):
        pass

    def _intense_calculation(self, value):
        # sleep for a random short duration between 0.5 to 2.0 seconds to simulate a long-running calculation
        time.sleep(random.randint(2, 6) * .1)
        return value

    def _fake_data(self):
        if self._instance == 0:
            return [
                {'folder': RootFolder(), 'files': [File(id=10, name='A File')]},
                {'folder': Folder(id=2, name='A Folder'), 'files': [File(id=20, name='A File')]},
                {'folder': Folder(id=3, name='B Folder'), 'files': [File(id=30, name='A File'), File(id=31, name='B File')]},
                {'folder': Folder(id=4, name='C Folder'), 'files': [File(id=40, name='A File'), File(id=41, name='B File')]},
            ]

        return [
            {'folder': RootFolder(), 'files': [File(id=10, name='A File'), File(id=31, name='B File')]},
            {'folder': Folder(id=2, name='A Folder'), 'files': [File(id=20, name='A File')]},
            {'folder': Folder(id=4, name='C Folder'), 'files': [File(id=41, name='B File')]},
            {'folder': Folder(id=5, name='D Folder'), 'files': [File(id=50, name='A File')]},
        ]
