from typing import Dict, Any, Iterable, Callable, List, Optional, Union, Tuple, Hashable

import json
import logging
from pathlib import Path

from itertools import groupby, chain

from ruamel.yaml import YAML


log = logging.getLogger(__name__)
yaml = YAML()

# "__PATH__" is a default key added to the dict to hint the dict's
# source location
PATH_KEY = "__PATH__"
DEFAULT_PATH_KEY = "_"

# The default key to exclude a dict from being loaded to Dict.items
DISABLED_KEY = "disabled"
# The default dictionary key to use in Dict.key_by where
# Dict.key_by: List[Dicts] => Dict[str -> List[dict]]
DEFAULT_KEY = "name"


class Dicts:
    def __init__(
        self,
        path: Optional[Path] = None,
        dicts: Optional[List[Dict]] = None,
        skip_errors: bool = False,
        load_disabled: bool = False,
        disabled_key: str = DISABLED_KEY,
    ):
        log.debug(f"Loading dicts from {path}")

        self.skip_errors = skip_errors
        self.load_disabled = load_disabled
        self.disabled_key = disabled_key

        self.path = path.resolve() if path else None
        self.is_path, self.is_dir = self.__classify_path()

        self.__dicts = dicts
        self.__items = list(self.__load_items())
        self.keyed = False

    @property
    def items(self):
        """ Returns self.items which may have been cast or filtered downstream"""
        return self.__items

    def __classify_path(self):
        """ Classify a path as a file or directory"""
        if self.path:
            return (self.path.is_file(), self.path.is_dir())
        else:
            log.debug("No path supplied")
            return (False, False)

    def __load_items(self) -> Iterable[Dict]:
        """
        Loads dicts from a path (file or directory) or a List[dict]
        Removes disabled items before returning
        """

        if self.path and self.is_path:
            log.debug("Loading objects from single paths")
            items = Dicts.load_file(self.path)

        elif self.is_dir:
            log.debug("Loading objects from directory")
            items = self.load_directory()

        elif self.__dicts:
            log.debug("Loading supplied objects")
            items = chain(self.__dicts)

        else:
            e = "No objects found to load"
            log.warning(e)
            raise ValueError(e)

        return items if self.load_disabled else self.remove_disabled_items(items)

    def remove_disabled_items(self, items) -> Iterable[Dict]:
        """
        Yields only items which are not flagged as disabled via self.disabled_key
        """
        if items:
            n = 0
            n_removed = 0
            for n, item in enumerate(items):
                if not item.get(self.disabled_key, False):
                    yield item
                else:
                    n_removed += 1
            else:
                log.info(f"{n_removed} out of {n} items are enabled")
        else:
            log.warning("No items found or supplied to Dicts")

    @staticmethod
    def load_file(path: Path) -> Iterable[Dict]:
        """
        Load a single yaml or json file as dict.
        Location of path is also stored in the in PATH_KEY
        """
        with path.open() as f:
            full_path = path.as_posix()
            suffix = path.suffix

            if suffix in (".yaml", ".yml"):
                contents = yaml.load_all(f)

            elif suffix == ".json":
                contents = [json.load(f)]

            else:
                log.debug(f"Suffix {suffix} not loadable for path {full_path}")

            if contents:
                for item in contents:
                    # Add the source path for a dict to a predefined key
                    if isinstance(item, list):
                        for c in item:
                            c[PATH_KEY] = full_path
                            yield c
                    else:
                        item[PATH_KEY] = full_path
                        yield item

    def load_directory(self) -> Iterable[Dict]:
        """
        Load all json and yaml files from a directory
        """
        if self.path:
            paths = self.path.iterdir() if self.is_dir else iter([self.path])
        else:
            log.error("Tried to load a directory without a supplied path")

        for path in paths:
            path = path.resolve()

            if not path.is_file():
                log.debug(f"Path is not a file: {path}")
                continue

            try:
                for document in Dicts.load_file(path):
                    yield document

            except Exception as e:
                if not self.skip_errors:
                    raise e
                log.warning(f"Could not load {path}: {e}")
                log.exception(e)

    def items_as(self, f: Callable[[Dict], Any]):
        """Transform the Dicts to a class or by a function"""
        self.__items: map = map(f, self.__items)
        return self

    def filter(self, predicate: Callable[[Any], bool]):
        """Filter the Dicts according to some predicate"""
        self.__items: filter = filter(predicate, self.__items)
        return self

    def __make_callable(
        self, key: Union[Callable[[Dict], Hashable], str], default: Hashable
    ) -> Callable[[Dict], Hashable]:
        """Convenience function to convert a string to a dictionary accessor function

        Args:
            key: A grouping function to pass to itertools.groupby
                 or a dictionary key name that will be converted to an accessor

        Returns:
            A function by which a dictionary can be grouped
        """
        # return lambda d: d.get(key, default) if isinstance(key, str) else key
        if isinstance(key, str):
            return lambda d: d.get(key, default)
        else:
            return key

    def __key_by(
        self, key: Union[Callable[[Dict], Hashable], str], default: Hashable, map: bool
    ) -> Iterable[Tuple[Hashable, List[Any]]]:
        self.keyed = True
        callable_key = self.__make_callable(key, default)
        sorted_items = sorted(self.__items, key=callable_key)
        for k, v in groupby(sorted_items, key=callable_key):
            items = list(v)
            n = len(items)
            if n > 1:
                msg = f"Key {k} has {n} elements"
                if map:
                    log.error(msg)
                    raise ValueError(msg)
                else:
                    log.info(msg)
            yield (k, items)

    def key_by(
        self, key: Union[Callable[[Dict], str], str], default: str, map: bool = False
    ) -> Dict[Hashable, List[Any]]:
        """
        Keys a list of dicts by a function or dictionary key.
        If the key should result in a map (a 1-1 mapping) and does not,
        key_by will throw an error

        Args:
            key: To be converted to a grouper function
            default: The default grouping if the group function returns None
                     for an element
            map: If the key_by should result in a map (i.e., a 1-1 mapping )

        Returns:
            A dictionary
        """
        grouped_items = self.__key_by(key=key, default=default, map=False)
        return dict(grouped_items)

    def key_by_file(self) -> Dict[Hashable, List[Any]]:
        """Groups the supplied dicts by filepath"""
        grouped_items = self.__key_by(key=PATH_KEY, default=DEFAULT_PATH_KEY, map=False)
        return dict(grouped_items)

    def map_by(
        self, key: Union[Callable[[Dict], Hashable], str], default: Hashable
    ) -> Dict[Hashable, Any]:
        """Groups a list of dicts into key-value pairs of unique key to a
        single element

        Args:
            key: A dictionary key to group by
            default: The default group if the dictionary key does not exist
                     in a dict

        Returns:
            A map of unique values in some config to the config.
            For example, for a directory containing config files {path: config}
        """
        grouped_items = self.__key_by(key=key, default=default, map=True)
        return {k: head for (k, (head, *_)) in grouped_items}

    @staticmethod
    def from_path(
        path: Path,
        skip_errors: bool = False,
        load_disabled: bool = False,
        disabled_key: str = DISABLED_KEY,
    ):
        return Dicts(
            path=path,
            skip_errors=skip_errors,
            load_disabled=load_disabled,
            disabled_key=disabled_key,
        )

    @staticmethod
    def from_dicts(
        dicts: List[Dict],
        skip_errors: bool = False,
        load_disabled: bool = False,
        disabled_key: str = DISABLED_KEY,
    ):
        return Dicts(
            dicts=dicts,
            skip_errors=skip_errors,
            load_disabled=load_disabled,
            disabled_key=disabled_key,
        )
