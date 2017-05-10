from aniwall.common import GuiBase, TreeViewData
from aniwall.logger import logger, debuginfo


class SettingsWindow(GuiBase):
	"""Main window constructor"""
	def __init__(self, mainapp):
		self._mainapp = mainapp

		# load GUI
		elements = (
			"window", "image-location-add-button", "image-location-add-button", "image-location-treeview"
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

		# signals
		self.gui["window"].connect("delete-event", self.hide)

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
