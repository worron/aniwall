import os
import shutil

from gi.repository import GLib, Gio, Gtk
from aniwall.logger import logger


class MainApp(Gtk.Application):
	"""Main application class"""
	def __init__(self, is_local):
		super().__init__(
			application_id="com.github.worron.aniwall", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
		)
		self.is_local = is_local
		self.mainwindow = None
		self.resource_path = "/com/github/worron/aniwall/"

		self.add_main_option(
			"log-level", ord("l"), GLib.OptionFlags.NONE, GLib.OptionArg.STRING,
			"Set log level", "LOG_LEVEL"
		)

	def _load_resources(self):
		"""
		Initialize resources.
		Use this one to make all setup AFTER command line parsing completed.
		"""
		logger.info("Loading resources...")
		# Set data files locations
		self.path = dict(
			data=os.path.join(os.path.abspath(os.path.dirname(__file__)), "data"),
			user=os.path.expanduser("~/.config/aniwall")
		)
		if logger.is_debug():
			logger.debug("Data files location:\n%s", "\n".join(k + ": " + v for k, v in self.path.items()))

		# init resources
		resource_path = os.path.join(self.path["data"], "aniwall.gresource")
		resource = Gio.Resource.load(resource_path)
		# noinspection PyProtectedMember
		resource._register()

		if logger.is_debug():
			resource_files = "\n".join(resource.enumerate_children(self.resource_path, Gio.ResourceLookupFlags.NONE))
			logger.debug("List of loaded resources files:\n%s" % resource_files)

		# init settings
		if not os.path.exists(self.path["user"]):
			logger.info("Creating user config location:\n%s" % self.path["user"])
			os.makedirs(self.path["user"])

		user_schema = os.path.join(self.path["user"], "gschemas.compiled")
		if not os.path.isfile(user_schema):
			shutil.copyfile(os.path.join(self.path["data"], "gschemas.compiled"), user_schema)
			logger.info("Set user config location:\n%s" % self.path["user"])

		schema_source = Gio.SettingsSchemaSource.new_from_directory(
			self.path["data"],
			Gio.SettingsSchemaSource.get_default(),
			False,
		)
		schema = schema_source.lookup("com.github.worron.aniwall", False)
		self.settings = Gio.Settings.new_full(schema, None, None)

		# set initial settings on first run
		if not self.settings.get_string("export-path"):
			self.settings.set_string("export-path", os.path.expanduser("~"))

		if not self.settings.get_strv("images-location-list"):
			self.settings.set_strv(
				"images-location-list",
				[os.path.join(os.path.abspath(os.path.dirname(__file__)), "images")]
			)

		if logger.is_debug():
			settings_list = "\n".join(k + ": " + str(self.settings.get_value(k)) for k in schema.list_keys())
			logger.debug("Current settings:\n%s", settings_list)

		logger.info("Loading resources completed")

	def _do_startup(self):
		"""
		Initialize application structure.
		Use this one to make all setup AFTER command line parsing completed.
		"""
		logger.info("Application modules initialization...")

		# set application actions
		action = Gio.SimpleAction.new("about", None)
		action.connect("activate", self.on_about)
		self.add_action(action)

		action = Gio.SimpleAction.new("quit", None)
		action.connect("activate", self.on_quit)
		self.add_action(action)

		action = Gio.SimpleAction.new("settings", None)
		action.connect("activate", self.on_settings)
		self.add_action(action)

		# lazy import application modules
		from aniwall.parser import ImageParser
		from aniwall.mainwindow import MainWindow
		from aniwall.settings import SettingsWindow

		# init application modules
		self.parser = ImageParser(self, os.path.join(self.path["data"], "images", "test.svg"))
		self.mainwindow = MainWindow(self)
		self.setwindow = SettingsWindow(self)
		self.mainwindow.update_image_list()

		# set application menu
		builder = Gtk.Builder.new_from_resource(self.resource_path + "ui/menu.ui")
		self.set_app_menu(builder.get_object("app-menu"))

		logger.info("Application modules initialization complete")

		# show window
		logger.info("Application GUI startup")
		self.mainwindow.gui["window"].show_all()
		self.mainwindow.update_preview()

	def do_command_line(self, command_line):
		if not self.mainwindow:
			# set log level
			options = command_line.get_options_dict()
			log_level = options.lookup_value("log-level").get_string() if options.contains("log-level") else "WARNING"
			logger.setLevel(log_level)

			# init app structure
			logger.info("Start aniwall application")
			self._load_resources()
			self._do_startup()

		return 0

	def do_shutdown(self):
		logger.info("Exit aniwall application")
		Gtk.Application.do_shutdown(self)

	# noinspection PyUnusedLocal
	def on_about(self, *args):
		# about_dialog = Gtk.AboutDialog(transient_for=self.mainwindow.gui["window"], modal=True)
		# about_dialog.show_all()
		pass

	# noinspection PyUnusedLocal
	def on_quit(self, *args):
		self.quit()

	# noinspection PyUnusedLocal
	def on_settings(self, *args):
		self.setwindow.show()
