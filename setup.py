#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import io
import re
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop


def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def enable_extension_after_install():
    from jupyter_tensorboard.application import (
        EnableJupyterTensorboardApp,
    )
    EnableJupyterTensorboardApp.launch_instance(argv=[])


class EnableExtensionDevelop(develop):

    def run(self):
        develop.run(self)
        enable_extension_after_install()


class EnableExtensionInstall(install):

    def run(self):
        install.run(self)
        enable_extension_after_install()


name = 'jupyter_tensorboard'

setup(
    name=name,
    version=find_version(name, '__init__.py'),
    author='lspvic',
    author_email='lspvic@qq.com',
    url='http://github.com/lspvic/jupyter_tensorboard',
    license='MIT License',
    description=(
        'Start tensorboard in Jupyter! '
        'Jupyter notebook integration for tensorboard.'),
    long_description=read("README.rst"),
    keywords=['Jupyter', 'Notebook', 'Tensorboard', 'Tensorflow', ],
    packages=[name],
    package_data={name: ["static/*"]},
    platforms="Linux, Mac OS X, Windows",
    entry_points={
        'console_scripts': [
            'jupyter-tensorboard = jupyter_tensorboard.application:main',
         ],
    },
    scripts=[os.path.join('scripts', p) for p in [
        'jupyter-tensorboard',
    ]],
    install_requires=[
        'notebook>=5.0',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    cmdclass={
        'install': EnableExtensionInstall,
        'develop': EnableExtensionDevelop,
    },
)
