import os

from gi.repository import Gtk
import aniwall.version as version
from aniwall.logger import logger


class FileDialog:
	"""Dialog constructor base"""
	def __init__(self, parent, title, action=Gtk.FileChooserAction.SAVE, action_button=Gtk.STOCK_SAVE):
		self.parent = parent
		self.title = title
		self.action = action
		self.action_button = action_button
		self.homedir = os.path.expanduser("~")

	def run(self, path_suggest=None, name_suggest=None):
		"""Activate dialog"""
		dialog = Gtk.FileChooserDialog(
			self.title, self.parent, self.action,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, self.action_button, Gtk.ResponseType.OK)
		)

		# set initial location and file name
		if path_suggest is not None:
			dialog.set_current_folder(path_suggest)
		else:
			dialog.set_current_folder(self.homedir)
		if name_suggest is not None:
			dialog.set_current_name(name_suggest)

		# listen response
		is_ok, path, filename = False, None, None
		response = dialog.run()

		if response == Gtk.ResponseType.OK:
			# get data
			is_ok = True
			path = dialog.get_current_folder()
			if self.action != Gtk.FileChooserAction.SELECT_FOLDER:
				filename = dialog.get_filename()

		# clean up
		dialog.destroy()
		return is_ok, path, filename


class AboutDialog:
	"""About dialog manager"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		self._version = version.get_current()
		self.about_dialog = None

		self.rebuild()

	def _build_dialog(self):
		self.about_dialog = Gtk.AboutDialog(transient_for=self._mainapp.mainwindow.gui["window"])
		self.about_dialog.set_program_name("Aniwall")
		# TODO: add application icon
		self.about_dialog.set_logo(self.about_dialog.render_icon_pixbuf(Gtk.STOCK_ABOUT, Gtk.IconSize.DIALOG))
		# noinspection SpellCheckingInspection
		self.about_dialog.set_authors(["worron <worrongm@gmail.com>"])
		self.about_dialog.set_version(self._version)
		self.about_dialog.set_license_type(Gtk.License.GPL_3_0)
		self.about_dialog.set_comments("Create user colored wallpaper from patterns.")

	def _set_artists(self):
		credits_ = []
		for path in self._mainapp.settings.get_strv("images-location-list"):
			file_ = os.path.join(path, "credits")
			if os.path.isfile(file_):
				with open(file_, "r") as credits_file:
					# TODO: is it possible to add raw string without link formatting?
					credits_ += [line for line in credits_file.read().split("\n") if line]
		logger.debug("Artist credits for current images:\n%s", credits_)

		if credits_:
			self.about_dialog.add_credit_section("Wallpapers artists", credits_)

	# noinspection PyUnusedLocal
	def _on_close(self, *args):
		self.about_dialog.hide()

	def rebuild(self):
		if self.about_dialog is not None:
			self.about_dialog.destroy()

		self._build_dialog()
		self._set_artists()
		self.about_dialog.connect("response", self._on_close)

	def show(self):
		self.about_dialog.show()
