import os
import time
import logging
from itertools import tee
from urllib.error import URLError
from .root_folder_info import RootFolderInfo
from .utils import choice

logger = logging.getLogger(__name__)

class Sync:

    def __init__(self, config, src, dest):
        self._config = config
        self._src = src
        self._dest = dest
        self._copy_count = 0
        self._skip_count = 0
        self._delete_count = 0

    def run(self):
        if self._config.dry_run:
            logger.info("dry run enabled, no files will be copied")
        elif self._config.delete:
            if not choice("really delete any additional files?", "no"):
                exit()
        logger.info("building folder list...")
        start = time.time()

        src_folders, src_folders_memo = tee(self._src.list_folders(), 2)
        dest_folders = {f.name.lower(): f for f in self._dest.list_folders()}
        for src_folder in src_folders:
            dest_folder = dest_folders.get(src_folder.name.lower())
            print(src_folder.name + os.sep)
            if dest_folder:
                self._merge_folders(src_folder, dest_folder)
            else:
                self._copy_folder(src_folder)

        # Remove extra folders
        if self._config.delete:
            src_folder_names = [f.name.lower() for f in src_folders_memo]
            extra_folders = (folder for name_lower, folder in dest_folders.items() \
                if name_lower not in src_folder_names)
            for folder in extra_folders:
                self._delete_folder(folder)

        # Merge root files if requested
        if self._config.root_files:
            self._merge_folders(RootFolderInfo(), RootFolderInfo())

        self._print_summary(time.time() - start, self._copy_count, self._skip_count, self._delete_count)

    def _copy_folder(self, folder):
        src_files = self._src.list_files(folder)
        for src_file in src_files:
            path = os.path.join(folder.name, src_file.name)
            self._copy_count += 1
            self._copy_file(folder, src_file, path)

    def _merge_folders(self, src_folder, dest_folder):
        src_files, src_files_memo = tee(self._src.list_files(src_folder), 2)
        dest_files = list(self._dest.list_files(dest_folder))
        dest_filenames = [f.name.lower() for f in dest_files]

        # Copy new files
        for src_file in src_files:
            lower_filename = src_file.name.lower()
            file_exists = lower_filename in dest_filenames
            # Fix for flickr converting .jpeg to .jpg.
            if lower_filename.endswith(".jpeg"):
                file_exists = file_exists or "{}.jpg".format(lower_filename[:-5]) in dest_filenames
            path = os.path.join(src_folder.name, src_file.name)
            if not file_exists:
                self._copy_count += 1
                self._copy_file(src_folder, src_file, path)
            else:
                self._skip_count += 1
                logger.debug("{}...skipped, file exists".format(path))

        # Remove extra files
        if self._config.delete and not dest_folder.is_root:
            src_filenames = [f.name.lower() for f in src_files_memo]
            extra_files = [f for f in dest_files if f.name.lower() not in src_filenames]
            # If deleting all files, remove folder as well
            if not set(dest_files) - set(extra_files):
                self._delete_folder(dest_folder)
            else:
                for f in extra_files:
                    path = os.path.join(dest_folder.name, f.name)
                    print(f"deleting {path}")
                    if not self._config.dry_run:
                        self._dest.delete_file(f, dest_folder.name)
                    self._delete_count += 1
                    logger.debug("{}...deleted".format(path))

    def _delete_folder(self, folder):
        print(f"deleting {folder.name + os.sep}")
        if not self._config.dry_run:
            self._delete_count += self._dest.delete_folder(folder)
        else:
            self._delete_count += len(self._dest.list_files(folder))
        logger.debug("{}...deleted".format(folder.name + os.sep))

    def _copy_file(self, folder, file_, path):
        print(path)
        if not self._config.dry_run:
            try:
                self._src.copy_file(file_, folder and folder.name, self._dest)
            except (URLError, FileNotFoundError) as err:
                logger.error("Error connecting to server, skipping. {!r}".format(err))

        logger.debug("{}...copied".format(path))

    def _print_summary(self, elapsed, files_copied, files_skipped, files_deleted):
        skipped_msg = f", skipped {files_skipped} files(s) that already exist" if files_skipped > 0 else ""
        deleted_msg = f", deleted {files_deleted} additional files(s)" if files_deleted > 0 else ""
        logger.info(f"\ntransferred {files_copied} file(s){skipped_msg}{deleted_msg} in {round(elapsed, 2)} sec")
