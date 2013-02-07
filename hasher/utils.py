import hashlib
import re


check_re = re.compile(r'^(\S+)  (\*)?([ a-f0-9]+)$')


def calculate_md5(file_object):
    md5 = hashlib.md5()
    [md5.update(chunk) for chunk in read_chunks(file_object)]
    return md5.hexdigest()


def read_chunks(filename, chunk_size=8192):
    with open(filename) as file_object:
        for data in file_object.read(chunk_size):
            yield data
