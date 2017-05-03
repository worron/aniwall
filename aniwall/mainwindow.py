from gi.repository import Gtk, GdkPixbuf

from aniwall.common import AttributeDict, GuiBase, hex_from_rgba


class MainWindow(GuiBase):
	"""Main window constructor"""
	def __init__(self, mainapp):
		self._mainapp = mainapp
		self._parser = mainapp.parser

		# load GUI
		elements = (
			"window", "headerbar", "stack", "image-box", "image-list-treeview", "image-list-selection",
			"preview", "color-box", "color-list-treeview", "color-list-selection", "image-search-entry",
		)
		super().__init__("mainwindow.ui", "imagepage.ui", "colorpage.ui", elements=elements)

		self.IMAGE_STORE = AttributeDict(INDEX=0, FILE=1)
		self.COLOR_STORE = AttributeDict(INDEX=0, NAME=1, HEX=2)
		self.IMAGE_OFFSET = 12

		self.last_size = None
		self.image_search_text = None
		self._build_store()

		# set application main window
		self.gui["window"].set_application(mainapp)

		# construct stack
		self.gui["stack"].add_titled(self.gui["image-box"], "images", "Images")
		self.gui["stack"].add_titled(self.gui["color-box"], "colors", "Colors")

		# signals
		self.handler = {}
		self.handler["selection"] = self.gui["image-list-selection"].connect(
			"changed", self._on_image_selection_changed
		)

		self.gui["color-list-treeview"].connect("row_activated", self.on_color_activated)
		self.gui["window"].connect("check-resize", self._on_window_resize)
		self.gui["image-search-entry"].connect("activate", self.on_image_search_activate)

	def _build_store(self):
		"""Build GUI stores"""
		# image list store
		for i, title in enumerate(("#", "File")):
			column = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
			self.gui["image-list-treeview"].append_column(column)

		self.image_store = Gtk.ListStore(int, str)
		self.image_store_filter = self.image_store.filter_new()
		self.image_store_filter.set_visible_func(self.image_search_filter_func)
		self.gui["image-list-treeview"].set_model(self.image_store_filter)

		# image colors store
		for i, title in enumerate(("#", "Name", "HEX")):
			column = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
			self.gui["color-list-treeview"].append_column(column)

		self.color_store = Gtk.ListStore(int, str, str)
		self.gui["color-list-treeview"].set_model(self.color_store)

	def update_image_list(self):
		"""Set list of SVG images for GUI treeview"""
		self.image_store.clear()
		for i, image in enumerate(self._parser.image_list):
			self.image_store.append([i, image])
		self.gui["image-list-treeview"].set_cursor(0)

	def update_color_list(self):
		"""Set color palette for GUI treeview"""
		self.color_store.clear()
		for line in self._parser.current.get_palette():
			self.color_store.append(line)

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

	def _on_image_selection_changed(self, selection):
		"""GUI handler"""
		model, sel = selection.get_selected()
		if sel is not None:
			file_ = model[sel][self.IMAGE_STORE.FILE]
			self._parser.set_image(file_)
			self.update_preview()
			self.update_color_list()

	# noinspection PyUnusedLocal
	def _on_window_resize(self, *args):
		"""GUI handler"""
		size = self.gui["window"].get_size()
		if self.last_size != size:
			self.last_size = size
			self.update_preview()

	# noinspection PyUnusedLocal
	def image_search_filter_func(self, model, treeiter, data):
		"""Function to filter images list by search text"""
		if not self.image_search_text:
			return True
		else:
			return self.image_search_text.lower() in model[treeiter][self.IMAGE_STORE.FILE].lower()

	# noinspection PyUnusedLocal
	def on_image_search_activate(self, *args):
		"""GUI handler"""
		self.image_search_text = self.gui["image-search-entry"].get_text()
		with self.gui["image-list-selection"].handler_block(self.handler["selection"]):
			self.image_store_filter.refilter()
			self.gui["image-list-treeview"].set_cursor(0)

	# noinspection PyUnusedLocal
	def on_color_activated(self, tree, path, column):
		color_dialog = Gtk.ColorChooserDialog("Choose Color", self._mainapp.mainwindow.gui["window"], use_alpha=False)
		response = color_dialog.run()

		if response == Gtk.ResponseType.OK:
			hex_color = hex_from_rgba(color_dialog.get_rgba())
			treeiter = self.color_store.get_iter(path)
			color_index = self.color_store[treeiter][self.COLOR_STORE.INDEX]

			self.color_store[treeiter][self.COLOR_STORE.HEX] = hex_color
			self._parser.current.change_color(hex_color, color_index)
			self._parser.apply_changes()
			self.update_preview()

		color_dialog.destroy()
