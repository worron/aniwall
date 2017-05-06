import os
import shutil

from gi.repository import GLib, Gio, Gtk
from aniwall.common import AttributeDict
from aniwall.mainwindow import MainWindow
from aniwall.logger import logger
from aniwall.parser import ImageParser


class MainApp(Gtk.Application):
	"""Main application class"""
	def __init__(self, is_local):
		super().__init__(
			application_id="com.github.worron.aniwall", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
		)
		self.is_local = is_local
		self.mainwindow = None

		self.add_main_option(
			"log-level", ord("l"), GLib.OptionFlags.NONE, GLib.OptionArg.STRING,
			"Set log level", "LOG_LEVEL"
		)

	def _do_startup(self):
		"""
		Initialize application structure.
		Use this one to make all setup AFTER command line parsing completed.
		"""
		# set application actions
		action = Gio.SimpleAction.new("about", None)
		action.connect("activate", self.on_about)
		self.add_action(action)

		action = Gio.SimpleAction.new("quit", None)
		action.connect("activate", self.on_quit)
		self.add_action(action)

		# init application modules
		self.parser = ImageParser(self)
		self.mainwindow = MainWindow(self)

		self.mainwindow.update_image_list()

		# set application menu
		builder = Gtk.Builder.new_from_resource("/com/github/worron/aniwall/menu.ui")
		self.set_app_menu(builder.get_object("app-menu"))

		# show window
		self.mainwindow.gui["window"].show_all()
		self.mainwindow.update_preview()

	def _load_resources(self):
		"""
		Initialize resources.
		Use this one to make all setup AFTER command line parsing completed.
		"""
		# Set data files locations
		self.path = AttributeDict(
			data=os.path.join(os.path.abspath(os.path.dirname(__file__)), "data"),
			images=os.path.join(os.path.abspath(os.path.dirname(__file__)), "images"),
			user=os.path.expanduser("~/.config/aniwall")
		)

		# init resources
		if self.is_local:
			resource_path = os.path.join(self.path.data, "aniwall.gresource")
			resource = Gio.Resource.load(resource_path)
			# noinspection PyProtectedMember
			resource._register()

		# init settings
		if not os.path.exists(self.path.user):
			os.makedirs(self.path.user)

		user_schema = os.path.join(self.path.user, "gschemas.compiled")
		if not os.path.isfile(user_schema):
			shutil.copyfile(os.path.join(self.path.data, "gschemas.compiled"), user_schema)
			logger.info("Set user config location:\n%s" % self.path.user)

		schema_source = Gio.SettingsSchemaSource.new_from_directory(
			self.path.data,
			Gio.SettingsSchemaSource.get_default(),
			False,
		)
		schema = schema_source.lookup("com.github.worron.aniwall", False)
		self.settings = Gio.Settings.new_full(schema, None, None)

		# set export path
		export_path = self.settings.get_string("export-path")
		if not export_path:
			self.settings.set_string("export-path", os.path.expanduser("~"))

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
		logger.info("Exit aniwall")
		Gtk.Application.do_shutdown(self)

	# noinspection PyUnusedLocal,PyUnusedLocal
	def on_about(self, *args):
		# about_dialog = Gtk.AboutDialog(transient_for=self.mainwindow.gui["window"], modal=True)
		# about_dialog.show_all()
		pass

	# noinspection PyUnusedLocal,PyUnusedLocal
	def on_quit(self, *args):
		self.quit()
