import hashlib


def get_md5hash_from_str(str_input):
    m = hashlib.md5()
    m.update(str_input.encode())
    return m.hexdigest()
