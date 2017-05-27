import os
import subprocess

from aniwall.logger import logger

_FALLBACK_VERSION = 1.0
# noinspection SpellCheckingInspection
_DEVELOPMENT_BRANCH = "devel"
_MASTER_BRANCH = "master"
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
		describe = str(output, "utf-8").strip()
		output = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.PIPE, cwd=cwd_)
		branch = str(output, "utf-8").strip()

		v, n, commit = describe.split('-')

		if branch == _MASTER_BRANCH or n == "0":
			# assume no fast forward merge used and first commit is "empty"
			if int(n) <= 1:
				version = v
			else:
				version = "%s.post%d" % (v, int(n) - 1)
		elif branch == _DEVELOPMENT_BRANCH:
			version = "%.1f.dev%s-%s" % (float(v) + 0.1, n, commit)
		else:
			version = "%s-%s-%s" % (v, branch, commit)
	except Exception as e:
		logger.debug("Can't read git output:\n%s", e)

		if os.path.isfile(_version_file):
			with open(_version_file, 'r') as file_:
				version = file_.read()
			logger.debug("Set version from package file: %s", version)

	return version
