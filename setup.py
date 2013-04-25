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

import hashlib
import os
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

from hasher.version import __version__


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
    version=".".join(map(str, __version__)),
    description="Print or check MD5 (128-bit) checksums.",
    long_description=read('README.rst'),
    url='',
    license='MIT',
    author='Walter Scheper',
    author_email='walter.scheper@gmail.com',
    packages=[
        'hasher',
        ],
    include_package_data=True,
    entry_points={
        'console_scripts': ['{0}hash = hasher.main:main'.format(h)
                            for h in hashlib.algorithms],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires=requirements,
    test_suite='hasher',
    tests_require=['pytest', 'mock'],
    cmdclass={'test': PyTest},
    )
