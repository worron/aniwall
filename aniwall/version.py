import os
import re
import subprocess

from aniwall.logger import logger

# noinspection SpellCheckingInspection
_DEVELOPMENT_BRANCH = "devel"
_FALLBACK_VERSION = 0.8
_version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "version")


def get_current():
	"""
	Try to find current version of package.
	Use git output, package file or fallback variable in the designated order.
	"""
	version = _FALLBACK_VERSION
	try:
		cwd_ = os.path.dirname(os.path.abspath(__file__))

		output = subprocess.check_output(["git", "describe", "--tags", "--long"], stderr=subprocess.PIPE, cwd=cwd_)
		version = str(output, "utf-8").strip()
		output = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.PIPE, cwd=cwd_)
		branch = str(output, "utf-8").strip()

		commit_num = re.search("-(\d)", version).group(1)
		if commit_num == "0":
			version = version.split('-')[0]
		elif branch == _DEVELOPMENT_BRANCH:
			vl = version.split('-')
			vl[0] = ("%.1f" % (float(vl[0]) + 0.1)) + ".dev"
			version = "-".join(vl)

	except Exception as e:
		logger.debug("Can't read git output:\n%s", e)

		if os.path.isfile(_version_file):
			with open(_version_file, 'r') as file_:
				version = file_.read()
			logger.debug("Set version from package file: %s", version)

	return version
