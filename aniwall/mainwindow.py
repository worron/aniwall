import os

from gi.repository import Gtk, GdkPixbuf
from aniwall.logger import logger, debuginfo
from aniwall.common import TreeViewData, GuiBase, hex_from_rgba, pixbuf_from_hex


class MainWindow(GuiBase):
	"""Main window constructor"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		self._parser = mainapp.parser

		# load GUI
		elements = (
			"window", "headerbar", "image-box", "image-list-treeview", "image-list-selection",
			"preview", "color-box", "color-list-treeview", "color-list-selection", "image-search-entry",
			"shift-x-spinbutton", "shift-y-spinbutton", "shift-x-spinbutton", "shift-y-spinbutton",
			"scale-spinbutton", "color-list-scrolledwindow", "export-button", "export-as-button",
		)
		super().__init__("mainwindow.ui", elements=elements, path=self._mainapp.resource_path)

		self.image_view_data = TreeViewData((
			dict(literal="INDEX", title="#", type=int, visible=False),
			dict(literal="FILE", title="File", type=str, visible=False),
			dict(literal="NAME", title="Image", type=str, visible=True),
			dict(literal="LOCATION", title="Location", type=str, visible=True)
		))

		self.color_view_data = TreeViewData((
			dict(literal="INDEX", title="#", type=int, visible=False),
			dict(literal="NAME", title="Tag", type=str, visible=True, maintain=True),
			dict(literal="COLOR", title="Color", type=GdkPixbuf.Pixbuf, visible=True, maintain=True),
			dict(literal="HEX", title="Hex", type=str, visible=False)
		))

		self.IMAGE_OFFSET = 12
		self.MIN_COLUMN_WIDTH = 120
		self.pixbuf_pattern_width = self.MIN_COLUMN_WIDTH - 24

		self.image_search_text = None
		self._build_store()

		# set application main window
		self.gui["window"].set_application(mainapp)

		# signals
		self.handler = {}
		self.handler["selection"] = self.gui["image-list-selection"].connect(
			"changed", self._on_image_selection_changed
		)

		self.gui["color-list-treeview"].connect("row_activated", self._on_color_activated)
		self.gui["window"].connect("size-allocate", self._on_image_resize)
		self.gui["image-search-entry"].connect("activate", self._on_image_search_activate)
		self.gui["shift-x-spinbutton"].connect("value-changed", self._on_shift_spinbutton_value_changed, 0)
		self.gui["shift-y-spinbutton"].connect("value-changed", self._on_shift_spinbutton_value_changed, 1)
		self.gui["scale-spinbutton"].connect("value-changed", self._on_scale_spinbutton_value_changed)
		self.gui["export-button"].connect("clicked", self._on_export_button_clicked)
		self.gui["export-as-button"].connect("clicked", self._on_export_as_button_clicked)

	def _build_store(self):
		"""Build GUI stores"""
		# image list store
		for i, title in enumerate(self.image_view_data.titles):
			column = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
			column.set_visible(self.image_view_data.visible[i])
			column.set_min_width(self.MIN_COLUMN_WIDTH)
			self.gui["image-list-treeview"].append_column(column)

		self.image_store = Gtk.ListStore(*self.image_view_data.types)
		self.image_store_filter = self.image_store.filter_new()
		self.image_store_filter.set_visible_func(self._image_search_filter_func)
		self.gui["image-list-treeview"].set_model(self.image_store_filter)

		# image colors store
		max_column_width = self.gui["color-list-scrolledwindow"].get_property("width_request") - self.MIN_COLUMN_WIDTH
		for i, title in enumerate(self.color_view_data.titles):
			if i == self.color_view_data.column.COLOR:
				column = Gtk.TreeViewColumn(title, Gtk.CellRendererPixbuf().new(), pixbuf=i)
			else:
				column = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)

			column.set_resizable(True)
			column.set_max_width(max_column_width)
			column.set_min_width(self.MIN_COLUMN_WIDTH)

			column.set_visible(self.color_view_data.visible[i])
			self.gui["color-list-treeview"].append_column(column)

		self.color_store = Gtk.ListStore(*self.color_view_data.types)
		self.gui["color-list-treeview"].set_model(self.color_store)

	@debuginfo(False, False)
	def update_image_list(self):
		"""Set list of SVG images for GUI treeview"""
		self.image_store.clear()
		for i, image in enumerate(self._parser.image_list):
			path, name = os.path.split(image)
			self.image_store.append([i, image, os.path.splitext(name)[0], path])
		self.gui["image-list-treeview"].set_cursor(0)

	@debuginfo(False, False)
	def update_color_list(self):
		"""Set color palette for GUI treeview"""
		self.color_store.clear()
		for line in self._parser.current.get_palette():
			pixbuf = pixbuf_from_hex(line["hex"], width=self.pixbuf_pattern_width)
			self.color_store.append([line["index"], line["name"], pixbuf, line["hex"]])

		self.gui["color-list-treeview"].set_cursor(0)

	def update_preview(self):
		"""Update current image preview"""
		if self._parser.current is not None:
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
				self._parser.temporary.name,
				max(self.gui["preview"].get_allocated_width() - 2 * self.IMAGE_OFFSET, 1),
				max(self.gui["preview"].get_allocated_height() - 2 * self.IMAGE_OFFSET, 1),
				True
			)
			self.gui["preview"].set_from_pixbuf(pixbuf)

	# noinspection PyUnusedLocal
	def _image_search_filter_func(self, model, treeiter, data):
		"""Function to filter images list by search text"""
		if not self.image_search_text:
			return True
		else:
			return self.image_search_text.lower() in model[treeiter][self.image_view_data.column.FILE].lower()

	@debuginfo(False, False)
	def _on_image_selection_changed(self, selection):
		"""GUI handler"""
		model, sel = selection.get_selected()
		if sel is not None:
			# update image preview
			file_ = model[sel][self.image_view_data.column.FILE]
			self._parser.set_image(file_)
			self.update_preview()
			self.update_color_list()
			# update image data
			self.gui["scale-spinbutton"].set_value(float(self._parser.current.scale))
			self.gui["shift-x-spinbutton"].set_value(float(self._parser.current.shift[0]))
			self.gui["shift-y-spinbutton"].set_value(float(self._parser.current.shift[1]))

	# noinspection PyUnusedLocal
	def _on_image_resize(self, window, rectangle):
		"""GUI handler"""
		self.update_preview()

	# noinspection PyUnusedLocal
	@debuginfo(False, False)
	def _on_image_search_activate(self, *args):
		"""GUI handler"""
		self.image_search_text = self.gui["image-search-entry"].get_text()
		with self.gui["image-list-selection"].handler_block(self.handler["selection"]):
			self.image_store_filter.refilter()
			self.gui["image-list-treeview"].set_cursor(0)

	# noinspection PyUnusedLocal
	@debuginfo(False, False)
	def _on_color_activated(self, tree, path, column):
		"""GUI handler"""
		color_dialog = Gtk.ColorChooserDialog("Choose Color", self._mainapp.mainwindow.gui["window"], use_alpha=False)
		response = color_dialog.run()

		if response == Gtk.ResponseType.OK:
			hex_color = hex_from_rgba(color_dialog.get_rgba())
			treeiter = self.color_store.get_iter(path)
			color_index = self.color_store[treeiter][self.color_view_data.column.INDEX]
			logger.debug("New color %s in line %s", hex_color, color_index)

			self.color_store[treeiter][self.color_view_data.column.HEX] = hex_color
			self.color_store[treeiter][self.color_view_data.column.COLOR] = pixbuf_from_hex(
				hex_color, width=self.pixbuf_pattern_width
			)
			self._parser.current.change_color(hex_color, color_index)
			self._parser.apply_changes()
			self.update_preview()

		color_dialog.destroy()

	@debuginfo(False, False)
	def _on_shift_spinbutton_value_changed(self, button, index):
		"""GUI handler"""
		value = button.get_value()
		self._parser.current.change_shift(value, index)
		self._parser.apply_changes()
		self.update_preview()

	@debuginfo(False, False)
	def _on_scale_spinbutton_value_changed(self, button):
		"""GUI handler"""
		value = "%.2f" % button.get_value()
		self._parser.current.change_scale(value)
		self._parser.apply_changes()
		self.update_preview()

	# noinspection PyUnusedLocal
	@debuginfo(False, False)
	def _on_export_button_clicked(self, button):
		"""GUI handler"""
		self._parser.export_image()

	# noinspection PyUnusedLocal
	@debuginfo(False, False)
	def _on_export_as_button_clicked(self, button):
		"""GUI handler"""
		dialog = Gtk.FileChooserDialog(
			"Export image as", self.gui["window"], Gtk.FileChooserAction.SAVE,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
		)
		dialog.set_current_folder(self._mainapp.settings.get_string("export-path"))
		dialog.set_current_name(self._parser.current.name)

		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			path, name = os.path.split(dialog.get_filename())
			name = os.path.splitext(name)[0]
			logger.debug("New export settings: [path: %s], [name: %s]" % (path, name))
			self._mainapp.settings.set_string("export-path", path)
			self._parser.current.name = name
			self._parser.export_image()

		dialog.destroy()
