from gi.repository import Gtk, Gio, GLib
from aniwall.common import GuiBase, TreeViewData
from aniwall.dialog import FileDialog
from aniwall.logger import logger, debuginfo


class SettingsWindow(GuiBase):
	"""Settings window constructor"""
	def __init__(self, app):
		self._app = app
		self._mainwindow = app.mainwindow

		# load GUI
		elements = (
			"window", "image-location-add-button", "image-location-add-button", "image-location-treeview",
			"image-location-add-button", "image-location-remove-button", "image-location-selection",
			"image-location-reload-button", "export-type-menu-button", "export-type-menu",
			"export-width-spinbutton", "export-height-spinbutton",
		)
		super().__init__("settings.ui", "export-type-menu.ui", elements=elements, path=self._app.resource_path)

		self.location_dialog = FileDialog(
			self.gui["window"], "Add new images location",
			Gtk.FileChooserAction.SELECT_FOLDER, Gtk.STOCK_OPEN
		)

		# image location list view
		self.image_location_data = TreeViewData((
			dict(literal="INDEX", title="#", type=int, visible=False),
			dict(literal="LOCATION", title="Location", type=str)
		))

		self.image_location_data.build_columns(self.gui["image-location-treeview"])
		self.image_location_store = self.image_location_data.build_store()
		self.gui["image-location-treeview"].set_model(self.image_location_store)

		# gui setup
		self.gui["export-width-spinbutton"].set_value(int(self._app.settings.get_string("export-width")))
		self.gui["export-height-spinbutton"].set_value(int(self._app.settings.get_string("export-height")))

		self.gui["export-type-menu-button"].set_menu_model(self.gui["export-type-menu"])
		self._update_image_location_list()

		# bind settings
		self._app.settings.bind(
			"export-width", self.gui["export-width-spinbutton"], "text", Gio.SettingsBindFlags.DEFAULT
		)
		self._app.settings.bind(
			"export-height", self.gui["export-height-spinbutton"], "text", Gio.SettingsBindFlags.DEFAULT
		)

		# actions
		self.actions = Gio.SimpleActionGroup()
		type_variant = GLib.Variant.new_string(self._app.settings.get_string("export-type"))
		action = Gio.SimpleAction.new_stateful("export_type", type_variant.get_type(), type_variant)
		action.connect("change-state", self._on_change_export_type)
		self.actions.add_action(action)
		self.gui["window"].insert_action_group("settings", self.actions)

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
		is_ok, path, _ = self.location_dialog.run()
		if is_ok:
			self.image_location_store.append([len(self.image_location_store), path])

			locations = self._app.settings.get_strv("images-location-list")
			locations.append(path)
			self._app.settings.set_strv("images-location-list", locations)

			logger.debug("Adding new image location: %s", path)
		else:
			logger.debug("Adding new image location canceled")

	# noinspection PyUnusedLocal
	@debuginfo(False, False)
	def _on_image_location_remove_button_clicked(self, button):
		"""GUI handler"""
		model, sel = self.gui["image-location-selection"].get_selected()
		if sel is not None:
			index = model[sel][self.image_location_data.index.INDEX]

			locations = self._app.settings.get_strv("images-location-list")
			del locations[index]
			self._app.settings.set_strv("images-location-list", locations)

			self._update_image_location_list()

	# noinspection PyUnusedLocal
	@debuginfo(False, False)
	def _on_image_location_reload_button_clicked(self, button):
		"""GUI handler"""
		self._mainwindow.update_image_list()
		self._app.aboutdialog.rebuild()

	def _on_change_export_type(self, action, value):
		"""Action handler"""
		action.set_state(value)
		type_ = value.get_string()
		self._app.settings.set_string("export-type", type_)
		logger.debug("Export type changed: %s", type_)

	@debuginfo(False, False)
	def _update_image_location_list(self):
		"""Set image locations list for GUI treeview"""
		self.image_location_store.clear()
		for i, path in enumerate(self._app.settings.get_strv("images-location-list")):
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
