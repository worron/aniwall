#!/usr/bin/python3

import os
import subprocess
import sys

COMPILE_RESOURCE_CMD = "glib-compile-resources"
COMPILE_SCHEMA_CMD = "glib-compile-schemas"
RESOURCE_FILE = "aniwall.gresource.xml"

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))


def _do_shell(cmd_list, directory=None):
	try:
		subprocess.check_call(cmd_list, cwd=directory)
	except Exception as e:
		print("Can't compile resources:\n", e)
		sys.exit()


if __name__ == "__main__":
	_do_shell([COMPILE_SCHEMA_CMD, os.path.join(LOCAL_DIR, "aniwall", "data")])
	_do_shell([COMPILE_RESOURCE_CMD, RESOURCE_FILE], os.path.join(LOCAL_DIR, "aniwall", "data"))
