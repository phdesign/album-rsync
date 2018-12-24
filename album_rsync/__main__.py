# import sys
from urllib.error import URLError
import logging

from .config import Config
from .sync import Sync
from .resiliently import Resiliently
from .flickr_storage import FlickrStorage
from .local_storage import LocalStorage
from .fake_storage import FakeStorage
from .tree_walker import TreeWalker
from .csv_walker import CsvWalker

logger = logging.getLogger(__name__)

def _get_storage(config, path):
    if path.lower() == Config.PATH_FLICKR:
        resiliently = Resiliently(config)
        return FlickrStorage(config, resiliently)
    if path.lower() == Config.PATH_FAKE:
        return FakeStorage(config)
    return LocalStorage(config, path)

def _get_walker(config, storage, list_format):
    if list_format == Config.LIST_FORMAT_TREE:
        return TreeWalker(config, storage)
    if list_format == Config.LIST_FORMAT_CSV:
        return CsvWalker(config, storage)
    raise ValueError('Unrecognised value for list-format: {}'.format(list_format))

def main():
    try:
        config = Config()
        config.read()

        src_storage = _get_storage(config, config.src)
        if config.list_only or config.list_folders:
            walker = _get_walker(config, src_storage, config.list_format)
            walker.walk()
        else:
            dest_storage = _get_storage(config, config.dest)
            sync = Sync(config, src_storage, dest_storage)
            sync.run()

    except URLError as err:
        logger.error("Error connecting to server. {!r}".format(err))
        exit(1)
    except KeyboardInterrupt:
        exit()

if __name__ == '__main__':
    main()
