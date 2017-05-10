import os

from gi.repository import Gtk
from aniwall.common import GuiBase, TreeViewData
from aniwall.logger import logger, debuginfo


class SettingsWindow(GuiBase):
	"""Main window constructor"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		self._mainwindow = mainapp.mainwindow

		# load GUI
		elements = (
			"window", "image-location-add-button", "image-location-add-button", "image-location-treeview",
			"image-location-add-button", "image-location-remove-button", "image-location-selection",
			"image-location-reload-button",
		)
		super().__init__("settings.ui", elements=elements, path=self._mainapp.resource_path)

		self.image_location_data = TreeViewData((
			dict(literal="INDEX", title="#", type=int, visible=False),
			dict(literal="LOCATION", title="Location", type=str)
		))

		self.image_location_data.build_columns(self.gui["image-location-treeview"])
		self.image_location_store = self.image_location_data.build_store()
		self.gui["image-location-treeview"].set_model(self.image_location_store)

		self._update_image_location_list()

		# accelerators
		self.accelerators = Gtk.AccelGroup()
		self.gui["window"].add_accel_group(self.accelerators)
		self.accelerators.connect(*Gtk.accelerator_parse("Escape"), Gtk.AccelFlags.VISIBLE, self.hide)

		# signals
		self.gui["window"].connect("delete-event", self.hide)
		self.gui["image-location-add-button"].connect("clicked", self._on_image_location_add_button_clicked)
		self.gui["image-location-remove-button"].connect("clicked", self._on_image_location_remove_button_clicked)
		self.gui["image-location-reload-button"].connect("clicked", self._on_image_location_reload_button_clicked)

	# noinspection PyUnusedLocal
	@debuginfo(False, False)
	def _on_image_location_add_button_clicked(self, button):
		"""GUI handler"""
		dialog = Gtk.FileChooserDialog(
			"Add new images location", self.gui["window"], Gtk.FileChooserAction.SELECT_FOLDER,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
		)
		dialog.set_current_folder(os.path.expanduser("~"))

		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			path = dialog.get_current_folder()
			self.image_location_store.append([len(self.image_location_store), path])
			logger.debug("Adding new image location: %s", path)

			locations = self._mainapp.settings.get_strv("images-location-list")
			locations.append(path)
			self._mainapp.settings.set_strv("images-location-list", locations)

		else:
			logger.debug("Adding new image location canceled")

		dialog.destroy()

	# noinspection PyUnusedLocal
	@debuginfo(False, False)
	def _on_image_location_remove_button_clicked(self, button):
		"""GUI handler"""
		model, sel = self.gui["image-location-selection"].get_selected()
		if sel is not None:
			index = model[sel][self.image_location_data.index.INDEX]

			locations = self._mainapp.settings.get_strv("images-location-list")
			del locations[index]
			self._mainapp.settings.set_strv("images-location-list", locations)

			self._update_image_location_list()

	# noinspection PyUnusedLocal
	@debuginfo(False, False)
	def _on_image_location_reload_button_clicked(self, button):
		"""GUI handler"""
		self._mainwindow.update_image_list()

	@debuginfo(False, False)
	def _update_image_location_list(self):
		"""Set image locations list for GUI treeview"""
		self.image_location_store.clear()
		for i, path in enumerate(self._mainapp.settings.get_strv("images-location-list")):
			self.image_location_store.append([i, path])
		self.gui["image-location-treeview"].set_cursor(0)

	# noinspection PyUnusedLocal
	@debuginfo(False, False)
	def show(self, *args):
		"""Show settings window"""
		self.gui["window"].show_all()

	# noinspection PyUnusedLocal
	def hide(self, *args):
		"""Hide settings window"""
		self.gui["window"].hide()
		return True
