import os
import sys
import importlib
import stat
from pathlib import Path
from types import ModuleType

from fuse import FUSE, Operations  # pip install fusepy


def _import_obj(path):
    # Try to import an object from a path e.g.
    # 'sklearn.tree.DecisionTreeClassifier'
    # Mostly heuristic-based and 100% dirty

    try:
        spec = importlib.util.find_spec(path)
        # could be None e.g. sklearn.tree.DecisionTreeClassifier
    except ModuleNotFoundError:
        # happens for attributes of modules that are files e.g. sklearn.pipeline.make_pipeline
        spec = None

    if spec is not None:
        return importlib.import_module(path)
    else:
        # for stuff like 'sklearn.tree.DecisionTreeClassifier', try to do
        # from sklearn.tree import DecisionTreeClassifier
        parts = path.split(".")
        base = ".".join(parts[:-1])
        end = parts[-1]
        try:
            return getattr(importlib.import_module(base), end)
        except:
            # Can't import, probably not a proper object anyway
            return None


class APIDocReader(Operations):
    def __init__(self, package_name):
        self.package_name = package_name

    def _get_obj_path(self, partial):
        # convert partial file path to a python path
        # e.g. /pipeline/make_pipeline to sklearn.pipeline.make_pipeline
        return self.package_name + ".".join(partial.split("/")).rstrip(".")

    def _get_docstring(self, path):
        obj = _import_obj(self._get_obj_path(path))
        if obj is None or not obj.__doc__ or isinstance(obj, ModuleType):
            return "".encode("UTF-8")
        else:
            return (obj.__doc__ + "\n").encode("UTF-8")

    def getattr(self, path, fh=None):
        # Return file attributes from a path. Modules are folders, functions or
        # classes are regular files.
        # TODO: set file date lololol

        obj = _import_obj(self._get_obj_path(path))

        # read permission only
        st_mode = stat.S_IRUSR | stat.S_IROTH | stat.S_IRGRP

        if isinstance(obj, ModuleType):
            st_mode |= stat.S_IFDIR  # make it a folder
            st_size = 0  # probably incorrect but still works
        else:
            st_mode |= stat.S_IFREG  # regular file
            st_size = len(self._get_docstring(path))

        return {"st_mode": st_mode, "st_size": st_size}

    def readdir(self, path, fh):
        # return names of public attributes of a module
        # path should be that of a proper module unless something went wrong
        module = _import_obj(self._get_obj_path(path))
        public_attributes = getattr(
            module,
            "__all__",
            [attr for attr in vars(module) if not attr.startswith("_")],
        )
        return public_attributes

    def read(self, path, length, offset, fh):
        # Return docstring of object specified by given path
        # object should be a proper function or class unless something went wrong
        return self._get_docstring(path)[offset : offset + length]


if __name__ == "__main__":
    usage = "usage: python mount_the_docs.py package_name [mount_point]"
    if len(sys.argv) not in (2, 3) or '-help' in sys.argv[1]:
        print(usage)
        exit(1)

    package_name = sys.argv[1]
    if len(sys.argv) == 2:
        mount_point = package_name + "_docs"
        print(f"mount point unspecified, trying to create and use {mount_point}")
        Path(mount_point).mkdir(parents=True, exist_ok=True)
    else:
        mount_point = sys.argv[2]

    # import module early just to get a decent error message if it's incorrect
    importlib.import_module(package_name)

    FUSE(APIDocReader(package_name), mount_point, nothreads=True, foreground=True)
