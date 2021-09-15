import os

from kgextractiontoolbox import config


def count_lines(filename):
    count = 0
    with open(filename, 'rb') as f:
        buffer = True
        while buffer:
            buffer = f.read(8192 * 1024)
            count += buffer.count(b'\n')
    return count


def proj_rel_path(path: str):
    return os.path.join(config.GIT_ROOT_DIR, path) if not path[0] == "/" else path


def read_if_path(path_or_str):
    if not path_or_str:
        return path_or_str
    if os.path.isfile(proj_rel_path(path_or_str)):
        with open(path_or_str) as f:
            return f.read()
    else:
        return path_or_str


def reverse_set_index(index_in):
    index_out = {}
    for k, vs in index_in.items():
        for v in vs:
            if v not in index_out:
                index_out[v] = set()
            index_out[v].add(k)
    return index_out
