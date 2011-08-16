#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from distutils.core import setup, Command
from setuptools import setup, Command
from distutils.command.install_data import install_data
from distutils.command.install import INSTALL_SCHEMES
import os
import sys
import codecs


class osx_install_data(install_data):
    # On MacOS, the platform-specific lib dir is /System/Library/Framework/Python/.../
    # which is wrong. Python 2.5 supplied with MacOS 10.5 has an Apple-specific fix
    # for this in distutils.command.install_data#306. It fixes install_lib but not
    # install_data, which is why we roll our own install_data class.

    def finalize_options(self):
        # By the time finalize_options is called, install.install_lib is set to the
        # fixed directory, so we set the installdir to install_lib. The
        # install_data class uses ('install_data', 'install_dir') instead.
        self.set_undefined_options('install', ('install_lib', 'install_dir'))
        install_data.finalize_options(self)

if sys.platform == 'darwin':
    cmdclasses = {'install_data': osx_install_data}
else:
    cmdclasses = {'install_data': install_data}

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)

def add_dir(source_dir):
    for dirpath, dirnames, filenames in os.walk(source_dir):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'): del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(fullsplit(dirpath)))
        elif filenames:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

add_dir('risiko')
add_dir('impact')

# Small hack for working with bdist_wininst.
# See http://mail.python.org/pipermail/distutils-sig/2004-August/004134.html
if len(sys.argv) > 1 and sys.argv[1] == 'bdist_wininst':
    for file_info in data_files:
        file_info[0] = '\\PURELIB\\%s' % file_info[0]

# Dynamically calculate the version based on risiko.VERSION.
distmeta = __import__('risiko')

class RunTests(Command):
    """Overall test runner for the project
    """

    description = 'Run the django test suite from the testproj dir.'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        this_dir = os.getcwd()
        testproj_dir = os.path.join(this_dir, 'risiko')
        os.chdir(testproj_dir)
        sys.path.append(testproj_dir)
        from django.core.management import execute_manager
        os.environ['DJANGO_SETTINGS_MODULE'] = os.environ.get(
            'DJANGO_SETTINGS_MODULE', 'settings')
        settings_file = os.environ['DJANGO_SETTINGS_MODULE']
        settings_mod = __import__(settings_file, {}, {}, [''])
        execute_manager(settings_mod, argv=[
            __file__, 'test'])
        os.chdir(this_dir)


if os.path.exists('README.rst'):
    long_description = codecs.open('README.rst', 'r', 'utf-8').read()
else:
    long_description = 'See http://github.com/AIFDR/riab'


setup(
    name='risiko',
    version=distmeta.__version__,
    description=distmeta.__doc__,
    author=distmeta.__author__,
    author_email=distmeta.__contact__,
    url=distmeta.__homepage__,
    platforms=['any'],
    license=distmeta.__license__,
    packages=packages,
    data_files=data_files,
   #zip_safe=False,
#    install_requires=[
        # For the core, installed with apt-get
        # 'numpy', 'scipy', 'gdal',

        # for the web api
#        'Django==1.3',

        # for the storage
#        'owslib',

        # for the documentation
#        'sphinx',

        # for testing
#        'nose>=0.11', 'coverage>=3.4', 'unittest2>=0.4.0',
#        'nose-cover3', 'mock', 'django-nose',

        # for improving source code quality
#        'pylint', 'pep8'],
    cmdclass = {'test': RunTests},
    scripts = ['scripts/risiko',
               'scripts/risiko-test',
               'scripts/risiko-start',
               'scripts/risiko-stop',
               'scripts/risiko-clean',
               'scripts/risiko-lint',
               'scripts/risiko-upload',
               'scripts/risiko-js',
              ],
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
   ],
   long_description=long_description,
)
