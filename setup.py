#!/usr/bin/python3

import os
import subprocess
import sys

from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
import aniwall.version as version


"""
Installation routines.

Install:
$ python3 setup.py install --record log.txt
Uninstall:
$ cat log.txt | xargs rm -rf
"""

COMPILE_RESOURCE_CMD = "glib-compile-resources"
COMPILE_SCHEMA_CMD = "glib-compile-schemas"
RESOURCE_FILE = "aniwall.gresource.xml"
SCHEMA_FILE = "com.github.worron.aniwall.gschema.xml"
SYSTEM_SCHEMA_DIRECTORY = "/usr/share/glib-2.0/schemas/"

_cwd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aniwall", "data")
_version_file = os.path.join(_cwd, "version")
_version = version.get_current()


def _do_shell(cmd_list, directory=None):
	try:
		subprocess.check_call(cmd_list, cwd=directory)
	except Exception as e:
		print("Can't compile resources:\n", e)
		sys.exit()


def _pre_install():
	_do_shell([COMPILE_RESOURCE_CMD, RESOURCE_FILE], _cwd)
	_do_shell(["cp", os.path.join(_cwd, SCHEMA_FILE), SYSTEM_SCHEMA_DIRECTORY])
	_do_shell([COMPILE_SCHEMA_CMD, SYSTEM_SCHEMA_DIRECTORY])

	with open(_version_file, 'w') as file_:
		file_.write(_version)

	print("Resources compiled successfully")


class InstallWithResources(install):
	"""Compile settings and resources before install"""
	def run(self):
		_pre_install()
		install.run(self)
		# FIXME: why egg missed without manual install?
		install.do_egg_install(self)


class DevelopWithResources(develop):
	"""Compile settings and resources before develop install"""
	def run(self):
		_pre_install()
		develop.run(self)


setup(
	name="aniwall",
	version=_version,
	packages=["aniwall"],
	url="",
	license="GPLv3",
	author="worron",
	author_email="worrongm@gmail.com",
	description="Application for color modding of some specific images",
	entry_points={"console_scripts": ["aniwall=aniwall.run:run"]},
	package_data={"aniwall": ["data/images/*.svg", "data/aniwall.gresource", "data/version"]},
	cmdclass={
		"install": InstallWithResources,
		"develop": DevelopWithResources
	}
)
