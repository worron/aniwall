import os

from gi.repository import Gtk
from aniwall.logger import logger


class DialogBase:
	"""Dialog constructor base"""
	def __init__(self, parent, title, action=Gtk.FileChooserAction.SAVE, action_button=Gtk.STOCK_SAVE):
		self.parent = parent
		self.title = title
		self.action = action
		self.action_button = action_button

	def _build_dialog(self):
		return Gtk.FileChooserDialog(
			self.title, self.parent, self.action,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, self.action_button, Gtk.ResponseType.OK)
		)


class ExportDialog(DialogBase):
	"""Image export dialog constructor"""
	def run(self, path_suggest, name_suggest):
		"""Activate dialog"""
		dialog = self._build_dialog()
		dialog.set_current_folder(path_suggest)
		dialog.set_current_name(name_suggest)

		is_ok, path, name = False, None, None
		response = dialog.run()

		if response == Gtk.ResponseType.OK:
			is_ok = True
			path, name = os.path.split(dialog.get_filename())
			name = os.path.splitext(name)[0]
			logger.debug("New export settings: [path: %s], [name: %s]" % (path, name))
		else:
			logger.debug("Image export canceled")

		dialog.destroy()
		return is_ok, path, name


class ImageLocationDialog(DialogBase):
	"""Image export dialog constructor"""
	def run(self):
		"""Activate dialog"""
		dialog = self._build_dialog()
		dialog.set_current_folder(os.path.expanduser("~"))

		is_ok, path = False, None
		response = dialog.run()

		if response == Gtk.ResponseType.OK:
			is_ok = True
			path = dialog.get_current_folder()
			logger.debug("Adding new image location: %s", path)
		else:
			logger.debug("Adding new image location canceled")

		dialog.destroy()
		return is_ok, path
