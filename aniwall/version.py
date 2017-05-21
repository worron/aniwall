import os
import re
import subprocess

from aniwall.logger import logger

_FALLBACK_VERSION = 0.8
_version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "version")


def get_current():
	"""
	Try to find current version of package.
	Use git output, package file or fallback variable in the designated order.
	"""
	version = _FALLBACK_VERSION
	try:
		output = subprocess.check_output(
			["git", "describe", "--tags", "--long"],
			stderr=subprocess.PIPE,
			cwd=os.path.dirname(os.path.abspath(__file__))
		)
		version = str(output, "utf-8").strip()

		commit_num = re.search("-(\d)", version).group(1)
		if commit_num == "0":
			version = version.split('-')[0]
	except Exception as e:
		logger.debug("Can't read git output:\n%s", e)

		if os.path.isfile(_version_file):
			with open(_version_file, 'r') as file_:
				version = file_.read()
			logger.debug("Set version from package file: %s", version)

	return version
