from urllib.error import URLError
import logging

from .config import Config
from .sync import Sync
from .resiliently import Resiliently
from .flickr_storage import FlickrStorage
from .google_storage import GoogleStorage
from .local_storage import LocalStorage
from .fake_storage import FakeStorage
from .tree_walker import TreeWalker
from .csv_walker import CsvWalker
from .google_api import GoogleApi

logger = logging.getLogger(__name__)

def _get_storage(config, path, count):
    """Storage provider factory.

    Args:
        config: Current configuration.
        path: Storage provider path, e.g. `flickr`, `google` or a file path.
        count: Provider instance count (used for fake storage).

    Returns:
        A storage provider.
    """
    if path.lower() == Config.PATH_GOOGLE:
        resiliently = Resiliently(config)
        api = GoogleApi(config, resiliently)
        return GoogleStorage(config, api)
    if path.lower() == Config.PATH_FLICKR:
        resiliently = Resiliently(config)
        return FlickrStorage(config, resiliently)
    if path.lower() == Config.PATH_FAKE:
        return FakeStorage(config, count)
    return LocalStorage(config, path)

def _get_walker(config, storage, list_format):
    """File walker factory.

    Args:
        config: Current configuration.
        storage: The storage provider.
        list_format: The type of walker to create.

    Returns:
        A file walker.
    """
    if list_format == Config.LIST_FORMAT_TREE:
        return TreeWalker(config, storage)
    if list_format == Config.LIST_FORMAT_CSV:
        return CsvWalker(config, storage)
    raise ValueError(f"Unrecognised value for list-format: {list_format}")

def main():
    try:
        config = Config()
        config.read()

        src_storage = _get_storage(config, config.src, 0)
        if config.logout:
            print("logging out...")
            src_storage.logout()
            exit()
        elif config.list_only or config.list_folders:
            walker = _get_walker(config, src_storage, config.list_format)
            walker.walk()
        else:
            dest_storage = _get_storage(config, config.dest, 1)
            sync = Sync(config, src_storage, dest_storage)
            sync.run()

    except URLError as err:
        logger.error(f"error connecting to server: {err}")
        exit(1)
    except NotImplementedError as err:
        logger.error(f"feature not supported: {err}")
        exit(1)
    except KeyboardInterrupt:
        exit()

if __name__ == '__main__':
    main()
