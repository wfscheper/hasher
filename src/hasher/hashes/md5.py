'''
Created on Jan 21, 2013

@author: wscheper
'''
from hashlib import md5

from . import Hasher


def run(args):
    hasher = MD5Hasher(args)
    hasher.run()


class MD5Hasher(Hasher):
    
    def __init__(self, args):
        super(MD5Hasher, self).__init__(args)
        self.hashlib = md5()
        