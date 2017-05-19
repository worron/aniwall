import os
import types

import aniwall.version as version
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
		self.add_main_option(
			"version", ord("v"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
			"Show application version", None
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
		)
		if logger.is_debug():
			logger.debug("Data files location:\n%s", "\n".join(k + ": " + v for k, v in self.path.items()))

		# init resources
		resource_path = os.path.join(self.path["data"], "aniwall.gresource")
		resource = Gio.Resource.load(resource_path)
		# noinspection PyProtectedMember
		resource._register()

		if logger.is_debug():
			ui_resource_path = self.resource_path + "ui/"
			resource_files = "\n".join(resource.enumerate_children(ui_resource_path, Gio.ResourceLookupFlags.NONE))
			logger.debug("List of loaded resources files:\n%s" % resource_files)

		# init settings
		if self.is_local:
			schema_source = Gio.SettingsSchemaSource.new_from_directory(
				self.path["data"],
				Gio.SettingsSchemaSource.get_default(),
				False,
			)
			schema = schema_source.lookup("com.github.worron.aniwall", False)

			self.settings = Gio.Settings.new_full(schema, None, None)

			# FIXME: get child for local settings
			def get_local_child(inst, name):
				child_schema = inst.get_property("schema") + "." + name
				return Gio.Settings.new_full(schema_source.lookup(child_schema, False), None, None)

			# noinspection PyArgumentList
			self.settings.get_child = types.MethodType(get_local_child, self.settings)
		else:
			self.settings = Gio.Settings.new("com.github.worron.aniwall")

		# set initial settings on first run
		if not self.settings.get_string("export-path"):
			self.settings.set_string("export-path", os.path.expanduser("~"))

		if not self.settings.get_strv("images-location-list") and self.is_local:
			self.settings.set_strv(
				"images-location-list",
				[os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "images")]
			)

		if logger.is_debug():
			schema = self.settings.get_property("settings-schema")
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
		from aniwall.dialog import AboutDialog

		# init application modules
		self.parser = ImageParser(self, os.path.join(self.path["data"], "images", "test.svg"))
		self.mainwindow = MainWindow(self)
		self.setwindow = SettingsWindow(self)
		self.aboutdialog = AboutDialog(self)
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
			options = command_line.get_options_dict()

			# set log level
			level = options.lookup_value("log-level").get_string() if options.contains("log-level") else "WARNING"
			logger.setLevel(level)

			if options.contains("version"):
				# show version
				print(version.get_current())
			else:
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
		"""Action handler"""
		self.aboutdialog.show()

	# noinspection PyUnusedLocal
	def on_quit(self, *args):
		self.quit()

	# noinspection PyUnusedLocal
	def on_settings(self, *args):
		self.setwindow.show()
