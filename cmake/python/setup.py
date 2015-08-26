#Thanks to Andreas Knoeckler for providing stand-alone boost.python
#through PyOpenCL and PyCUDA

import os, sys
from distutils.ccompiler import show_compilers,new_compiler
from distutils.command.build_ext import build_ext
from distutils.command.build_py import build_py
from distutils.core import setup, Extension
from distutils.sysconfig import get_python_inc
from distutils import sysconfig
from imp import find_module
from glob import glob
from os.path import dirname

platform_cflags = {}
platform_ldflags = {}
platform_libs = {}

class build_ext_subclass(build_ext):
    def build_extensions(self):
        c = self.compiler.compiler_type
        if c in platform_cflags.keys():
            for e in self.extensions:
                e.extra_compile_args = platform_cflags[c]
        if c in platform_ldflags.keys():
            for e in self.extensions:
                e.extra_link_args = platform_ldflags[c]
        if c in platform_libs.keys():
            for e in self.extensions:
                try:
                    e.libraries += platform_libs[c]
                except:
                    e.libraries = platform_libs[c]
        build_ext.build_extensions(self)

def main():

    def recursive_glob(rootdir='.', suffix=''):
        return [os.path.join(looproot, filename)
                for looproot, _, filenames in os.walk(rootdir)
                for filename in filenames if filename.endswith(suffix)]

    def remove_prefixes(optlist, bad_prefixes):
        for bad_prefix in bad_prefixes:
            for i, flag in enumerate(optlist):
                if flag.startswith(bad_prefix):
                    optlist.pop(i)
                    break
        return optlist

    #Tweaks warning, because boost-numpy and boost-python won't compile cleanly without these changes
    cvars = sysconfig.get_config_vars()
    cvars['OPT'] = str.join(' ', remove_prefixes(cvars['OPT'].split(), ['-g', '-Wstrict-prototypes']))
    cvars["CFLAGS"] = cvars["BASECFLAGS"] + ' ' + cvars['OPT']
    cvars["LDFLAGS"] = '-Wl,--no-as-needed ' + cvars["LDFLAGS"]

    #Check Android
    for_android = '-mandroid' in cvars['PY_CFLAGS']

    #Dynamic load for backend switching
    libraries = ['dl']

    #Include directories
    numpy_include = os.path.join(find_module("numpy")[1], "core", "include")
    include ='${INCLUDE_DIRECTORIES_STR}'.split() + ['external/boost/', 'external/boost/boost/', numpy_include]

    #Android
    if for_android:
      ANDROID_ROOT = os.environ['ANDROIDNDK'] + '/sources/cxx-stl/gnu-libstdc++/' + os.environ['TOOLCHAIN_VERSION']
      library_dirs += [ANDROID_ROOT + '/libs/armeabi']
      include += [ANDROID_ROOT + '/include/', ANDROID_ROOT + '/libs/armeabi/include/']
      libraries += ['gnustl_shared']

    #Source files
    src =  '${LIBISAAC_SRC_STR}'.split() + [os.path.join('src', 'bind', sf)  for sf in ['_isaac.cpp', 'core.cpp', 'driver.cpp', 'kernels.cpp', 'exceptions.cpp']]
    boostsrc = 'external/boost/libs/'
    for s in ['numpy','python','smart_ptr','system','thread']:
        src = src + [x for x in recursive_glob('external/boost/libs/' + s + '/src/','.cpp') if 'win32' not in x and 'pthread' not in x]


    extensions = []
    
    #isaac
    extensions += [Extension(
                    '_isaac',src,
                    extra_compile_args= ['-std=c++11', '-Wno-unused-function', '-Wno-unused-local-typedefs',  '-Wno-sign-compare', '-Wno-attributes', '-DBOOST_PYTHON_SOURCE '],
		    extra_link_args=['-Wl,-soname=_isaac.so'],
                    undef_macros=[],
                    include_dirs=include,
                    library_dirs=[],
                    libraries=libraries)]
    
    #External
    extensions += [Extension('external.sklearn._tree',
                             ['external/sklearn/_tree.c'],
                             include_dirs = [numpy_include])]

    #Setup
    setup(
                name='isaac',
                version='1.0',
                description="Input-specific architecture-aware computations",
                author='Philippe Tillet',
                author_email='ptillet@g.harvard.edu',
                license='MPL 2.0',
                packages=['isaac', 'isaac.external', 'isaac.external.sklearn'],
                ext_package="isaac",
                ext_modules=extensions,
                cmdclass={'build_py': build_py, 'build_ext': build_ext_subclass},
                classifiers=[
                    'Environment :: Console',
                    'Development Status :: 1 - Experimental',
                    'Intended Audience :: Developers',
                    'Intended Audience :: Other Audience',
                    'Intended Audience :: Science/Research',
                    'License :: OSI Approved :: MIT License',
                    'Natural Language :: English',
                    'Programming Language :: C++',
                    'Programming Language :: Python',
                    'Programming Language :: Python :: 3',
                    'Topic :: Scientific/Engineering',
                    'Topic :: Scientific/Engineering :: Mathematics',
                    'Topic :: Scientific/Engineering :: Physics',
                    'Topic :: Scientific/Engineering :: Machine Learning',
                ]
    )

if __name__ == "__main__":
    main()
