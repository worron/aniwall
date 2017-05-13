import os

from gi.repository import Gtk


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

