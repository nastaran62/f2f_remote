# This file is part of Octopus Sensing <https://octopus-sensing.nastaran-saffar.me/>
# Copyright © Nastaran Saffaryazdi 2020
#
# Octopus Sensing is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
#  either version 3 of the License, or (at your option) any later version.
#
# Octopus Sensing is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Octopus Sensing.
# If not, see <https://www.gnu.org/licenses/>.

from screeninfo import get_monitors
from gi.repository import Gtk, GdkPixbuf, GLib, Gst
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')


Gst.init(None)
Gst.init_check(None)


FONT_STYLE = "<span font_desc='Tahoma 18'>{}</span>"

class MessageButtonWindow(Gtk.Window):
    '''
    Creating a message window using Gtk
    It has an OK button which by clicking on it, The window will be closed

    Attributes
    -----------

    Parameters
    ----------
    title: str
        Window title
    
    message: str
        The message text
    
    width: int, default: 400
        The width of questionnaire window in pixel
    
    height: int, default: 200
        The height of questionnaire window in pixel

    '''
    def __init__(self, title: str, message: str,
                 width: int = 400, height: int = 200):
        Gtk.Window.__init__(self, title=title)
        self.set_default_size(width, height)
        self._message = message


    def show(self) -> None:
        '''
        Shows the questionnaire
        '''
        grid = Gtk.Grid(column_homogeneous=False,
                        column_spacing=30,
                        row_spacing=30)
        self.add(grid)

        ok_button = Gtk.Button.new_with_label("Ok")
        ok_button.connect("clicked", self._on_click_ok_button)
        ok_button.get_child().set_markup(FONT_STYLE.format(self._message))
        Gtk.Widget.set_size_request(ok_button, 600, 300)
        grid.attach(ok_button, 0, 0, 1, 1)
        self.connect("destroy", Gtk.main_quit)
        self.show_all()
        Gtk.main()

    def _on_click_ok_button(self, button: Gtk.Button) -> None:
        '''
        Close the message dialog

        Parameters
        ----------
        button: Gtk.Button
            by clicking this button, this method will call

        '''
        self.destroy()


class ImageWindow(Gtk.Window):
    '''
    Creates a Gtk window with a message for informing the participant about something
    It has a continue button which by clicking on it, the window will be destroyed

    Attributes
    ----------

    Parameters
    ----------

    image_path: str
        The path of image
    
    timeout: int
        The time period for displaying the image
    
    monitor_no: int, default: 0
        The ID of monitor for displaying of image. It can be 0, 1, ...

    '''
    def __init__(self, title, monitor_no=0):
        Gtk.Window.__init__(self, title=title)

        self._image_box = Gtk.Box()
        monitors = get_monitors()
        self._image_width = monitors[monitor_no].width
        self._image_height = monitors[monitor_no].height
        self._image = Gtk.Image()
        self._image_box.pack_start(self._image, False, False, 0)
        self.add(self._image_box)
        self.modal = True
        self.fullscreen()
    
    def set_image(self, image_path):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            image_path, self._image_width, self._image_height, False)
        self._image.set_from_pixbuf(pixbuf)
        #self.set_screen(monitor_no)
        self._image_box.show()
        self._image.show()


    def show_and_destroy_window(self, timeout):
        GLib.timeout_add_seconds(timeout, self.destroy)
        self.show()
    
    def show_window(self):
        self.show()
