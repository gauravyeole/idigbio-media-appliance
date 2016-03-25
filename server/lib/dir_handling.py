import os
import uuid
import re
import datetime

from functools import partial

from lib.file_handling import file_types, calcFileHash

from models import Media
from api.appuser import get_current_user
from lib.file_handling import check_update

guid_mode = {
    "regex": lambda regex, tmpl, path: regex.match(path).expand(tmpl),
    "uuid": lambda path: str(uuid.uuid4()),
    "hash": lambda path: calcFileHash(path),
}


class NotAuthorizedException(Exception):
    pass


def recursive_walk(directory):
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.rsplit(".", 1)[-1] in file_types:
                yield os.path.join(root, f)


def simple_walk(directory):
    for f in os.listdir(directory):
        if f.rsplit(".", 1)[-1] in file_types:
            yield os.path.join(directory, f)


def scan_dir(directory, guid_type="uuid", guid_params=None, recursive=True):
    if guid_type == "regex":
        ref_func = partial(re.compile(guid_params[0]), guid_params[1])
    else:
        ref_func = guid_mode[guid_type]

    directory = os.path.abspath(directory)
    dir_objects = {m.path: m for m in Media.query.filter(
        Media.path.like(directory + "%")).all()}

    current_user = get_current_user()
    if current_user is None:
        raise NotAuthorizedException

    if os.path.exists(directory):

        dir_iter = simple_walk
        if recursive:
            dir_iter = recursive_walk

        for p in dir_iter(directory):
            m = None
            if p in dir_objects:
                m = check_update(dir_objects[p], p, current_user, guid_type)
            else:
                m = Media(path=p, file_reference=ref_func(p),
                          appuser=current_user)

            yield m
    else:
        raise FileNotFoundError("No Such Directory {}".format(directory))

if __name__ == '__main__':
    for m in scan_dir("/home/godfoder/Downloads"):
        print(m)
