import os
import sys

from setuptools import setup, find_packages
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

hashers = []
for fname in os.listdir('hasher/hashes'):
    if fname not in ['__init__.py', 'base.py'] and not fname.endswith('.pyc'):
        hashers.append(fname.strip('.py'))

setup(
    name="hasher",
    version=".".join(map(str, __version__)),
    description="Print or check MD5 (128-bit) checksums.",
    long_description=read('README.rst'),
    url='',
    license='MIT',
    author='Walter Scheper',
    author_email='walter.scheper@gmail.com',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    entry_points={
        'console_scripts': ['{0}sum = hasher.main:main'.format(h)
                            for h in hashers],
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
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
)
