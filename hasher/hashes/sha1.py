'''
Created on Feb 6, 2013

@author: wscheper
'''
from hashlib import sha1

from .base import Hasher


def run(args):
    hasher = SHA1Hasher(args)
    hasher.run()


class SHA1Hasher(Hasher):

    def __init__(self, args):
        super(SHA1Hasher, self).__init__(args)
        self.hashlib = sha1()
        self.name = 'sha1sum'
