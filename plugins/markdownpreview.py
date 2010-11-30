#!/usr/bin/python
# -*- coding: utf-8 -*-

# Le fichier markdownpreview.py fait partie de markdownpreview.
# HTML preview of Markdown formatted text in gedit
# Auteur: Michele Campeotto
# Copyright © Michele Campeotto, 2005, 2006.
# Copyright © Jean-Philippe Fleury, 2009. <contact@jpfleury.net>
# Copyright © Frédéric Bertolus, 2010. <fred.bertolus@gmail.com>

# Ce programme est un logiciel libre; vous pouvez le redistribuer ou le
# modifier suivant les termes de la GNU General Public License telle que
# publiée par la Free Software Foundation: soit la version 3 de cette
# licence, soit (à votre gré) toute version ultérieure.

# Ce programme est distribué dans l'espoir qu'il vous sera utile, mais SANS
# AUCUNE GARANTIE: sans même la garantie implicite de COMMERCIALISABILITÉ
# ni d'ADÉQUATION À UN OBJECTIF PARTICULIER. Consultez la Licence publique
# générale GNU pour plus de détails.

# Vous devriez avoir reçu une copie de la Licence publique générale GNU avec
# ce programme; si ce n'est pas le cas, consultez
# <http://www.gnu.org/licenses/>.

import gedit

import sys
import gtk
import webkit
import markdown
import gconf

DEFAULT_HTML_TEMPLATE = """<html><head><meta http-equiv="content-type"
content="text/html; charset=UTF-8" /><style type="text/css">
body { background-color: #fff; padding: 8px; }
p, div { margin: 0em; }
p + p, p + div, div + p, div + div { margin-top: 0.8em; }
blockquote { padding-left: 12px; padding-right: 12px; }
pre { padding: 12px; }
</style></head><body>%s</body></html>"""

CUSTOM_CSS_HTML_TEMPLATE = """<html><head><meta http-equiv="content-type"
content="text/html; charset=UTF-8" />
<link rel="stylesheet" type="text/css" href="%s">
</head><body>%s</body></html>"""

class MarkdownPreviewPlugin(gedit.Plugin):

	def __init__(self):
		gedit.Plugin.__init__(self)
			
	def activate(self, window):
		self.window = window
		self.gconf_root_dir = "/apps/gedit-2/plugins/markdownpreview"
		self.load_config()

		action = ("Markdown Preview",
			  None,
			  "Markdown Preview",
			  "<Control><Shift>M",
			  "Update the HTML preview",
			  lambda x, y: self.update_preview(y))
		
		# Store data in the window object
		windowdata = dict()
		window.set_data("MarkdownPreviewData", windowdata)
	
		self.scrolled_window = gtk.ScrolledWindow()
		self.scrolled_window.set_property("hscrollbar-policy",gtk.POLICY_AUTOMATIC)
		self.scrolled_window.set_property("vscrollbar-policy",gtk.POLICY_AUTOMATIC)
		self.scrolled_window.set_property("shadow-type",gtk.SHADOW_IN)

		html_doc = webkit.WebView()
		
		html_doc.load_string(DEFAULT_HTML_TEMPLATE % ("",), "text/html", "utf-8", "file:///")

		self.scrolled_window.add(html_doc)
		self.scrolled_window.show_all()
		
		self.generate_preview_panel()

		windowdata["preview_panel"] = self.scrolled_window
		windowdata["html_doc"] = html_doc
		
		windowdata["action_group"] = gtk.ActionGroup("MarkdownPreviewActions")
		windowdata["action_group"].add_actions ([action], window)

		manager = window.get_ui_manager()
		manager.insert_action_group(windowdata["action_group"], -1)

		windowdata["ui_id"] = manager.new_merge_id ()

		manager.add_ui (windowdata["ui_id"],
				"/MenuBar/ToolsMenu/ToolsOps_5",
				"Markdown Preview",
				"Markdown Preview",
				gtk.UI_MANAGER_MENUITEM, 
				True)
	
	def generate_preview_panel(self):

		self.window.get_side_panel().remove_item(self.scrolled_window)
		self.window.get_bottom_panel().remove_item(self.scrolled_window)

		if self.display_in_side_panel:
			panel = self.window.get_side_panel()
		else:
			panel = self.window.get_bottom_panel()

		image = gtk.Image()
		image.set_from_icon_name("gnome-mime-text-html", gtk.ICON_SIZE_MENU)
		panel.add_item(self.scrolled_window, "Markdown Preview", image)

	def deactivate(self, window):
		# Retreive the data of the window object
		windowdata = window.get_data("MarkdownPreviewData")
		
		# Remove the menu action
		manager = window.get_ui_manager()
		manager.remove_ui(windowdata["ui_id"])
		manager.remove_action_group(windowdata["action_group"])
		
		# Remove the preview panel
		if self.display_in_side_panel:
			panel = self.window.get_side_panel()
		else:
			panel = self.window.get_bottom_panel()
		panel.remove_item(windowdata["preview_panel"])
	
	def update_preview(self, window):
		# Retreive the data of the window object
		windowdata = window.get_data("MarkdownPreviewData")
		
		view = window.get_active_view()
		if not view:
			 return
		
		doc = view.get_buffer()
		
		start = doc.get_start_iter()
		end = doc.get_end_iter()
		
		if doc.get_selection_bounds():
			start = doc.get_iter_at_mark(doc.get_insert())
			end = doc.get_iter_at_mark(doc.get_selection_bound())
		
		text = doc.get_text(start, end)

		markdown_text = markdown.markdown(text)

		if self.css_path is None:
			html = DEFAULT_HTML_TEMPLATE % (markdown_text,)
		else:
			html = CUSTOM_CSS_HTML_TEMPLATE % (self.css_path, markdown_text)

		p = windowdata["preview_panel"].get_placement()
		
		html_doc  = windowdata["html_doc"]
		html_doc.load_string(html, "text/html", "utf-8", "file:///")
		
		windowdata["preview_panel"].set_placement(p)


	def is_configurable(self):
		return True

	def create_configure_dialog(self):
		dialog = gtk.Dialog("Markup preview Configuration")
		dialog.set_default_size(300, 200)

		button_bar = gtk.HButtonBox()
		button_bar.set_layout(gtk.BUTTONBOX_END)

		cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
		ok_button = gtk.Button(stock=gtk.STOCK_OK)

		display_in_side_panel_checkbox = gtk.CheckButton("Afficher dans le panneau latéral")
		display_in_side_panel_checkbox.set_active(self.display_in_side_panel)

		css_path_file_chooser = gtk.FileChooserButton("CSS path")
		css_path_label = gtk.Label("CSS path:")
		css_path_box = gtk.HBox()
		css_path_box.pack_start(css_path_label)
		css_path_box.pack_start(css_path_file_chooser)
		css_path_box.child_set_property(css_path_label, "fill",False)
		css_path_box.child_set_property(css_path_label, "expand",False)

		if self.css_path is not None:
			css_path_file_chooser.set_filename(self.css_path)


		button_bar.pack_start(cancel_button)
		button_bar.pack_start(ok_button)

		dialog.vbox.pack_start(display_in_side_panel_checkbox)
		dialog.vbox.child_set_property(display_in_side_panel_checkbox, "padding",5)




		dialog.vbox.pack_start(css_path_box)
		dialog.vbox.child_set_property(css_path_box, "padding",5)
		dialog.vbox.child_set_property(css_path_box, "expand",False)

		dialog.vbox.pack_start(button_bar)
		dialog.vbox.child_set_property(button_bar, "expand",False)

		def cancel_config(button):
			dialog.destroy()

		def valid_config(button):
			self.display_in_side_panel = display_in_side_panel_checkbox.get_active()
			self.css_path = css_path_file_chooser.get_filename()
			print self.css_path
			dialog.destroy()
			self.save_config()
			self.generate_preview_panel()


		cancel_button.connect("clicked", cancel_config)
		ok_button.connect("clicked", valid_config)


		dialog.vbox.show_all()

		return dialog


	def load_config(self):
		client = gconf.client_get_default()
		self.display_in_side_panel = client.get_bool(self.gconf_root_dir + "/display_in_side_panel")
		self.css_path = client.get_string(self.gconf_root_dir + "/css_path")
		if self.css_path == "":
			self.css_path = None

	def save_config(self):
		client = gconf.client_get_default()
		client.add_dir(self.gconf_root_dir, gconf.CLIENT_PRELOAD_NONE)

		client.set_bool(self.gconf_root_dir + "/display_in_side_panel", self.display_in_side_panel)
		if self.css_path is not None:
			client.set_string(self.gconf_root_dir + "/css_path", self.css_path)
		else:
			client.set_string(self.gconf_root_dir + "/css_path","")
