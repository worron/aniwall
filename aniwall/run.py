import os
import sys
import gi
import signal

# check gi version
gi.require_version('Gtk', '3.0')

# set module for local run
is_local = __name__ == "__main__"
if is_local:
	sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# noinspection PyPep8
from aniwall.mainapp import MainApp

signal.signal(signal.SIGINT, signal.SIG_DFL)


def run():
	app = MainApp(is_local)
	exit_status = app.run(sys.argv)
	sys.exit(exit_status)


if __name__ == "__main__":
	run()
