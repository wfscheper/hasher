# Copyright 2013 Walter Scheper
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
