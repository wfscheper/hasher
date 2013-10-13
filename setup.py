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

import os
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

from hasher import __version__


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

requirements = []

setup(
    name="hasher",
    version="{0}.{1}.{2}{3}".format(*__version__),
    description="Provide multiple hashing algorithms from a single code base",
    long_description=read('README.rst'),
    url='https://github.com/wfscheper/hasher.git',
    license='Apache Software License',
    author='Walter Scheper',
    author_email='walter.scheper@gmail.com',
    packages=[
        'hasher',
        ],
    entry_points={
        'console_scripts': [
            'hasher = hasher.main:main',
            ],
        'hasher': [
            'md5 = hasher.hashes:MD5Hasher',
            'sha1 = hasher.hashes:SHA1Hasher',
            'sha256 = hasher.hashes:SHA256Hasher',
            ],
        },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
        ],
    install_requires=requirements,
    test_suite='hasher',
    tests_require=['pytest', 'mock'],
    cmdclass={'test': PyTest},
    )
