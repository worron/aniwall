import os
import re
import subprocess

from aniwall.logger import logger

_FALLBACK_VERSION = 0.6


def get_current():
	"""
	Try to find current version of package.
	Use git output or fallback variable.
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

	return version
