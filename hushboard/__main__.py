#!/usr/bin/env python3
import sys
import os
import gi
import queue
import threading
from . import pulsectl

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk, GLib, GdkPixbuf

gi.require_version('AppIndicator3', '0.1')
from gi.repository import AppIndicator3 as AppIndicator

from Xlib import X, display
from Xlib.ext import record
from Xlib.protocol import rq

APP_ID = 'hushboard'
APP_NAME = 'Hushboard'
APP_LICENCE = """
MIT License

Copyright (c) 2021 Stuart Langridge

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
APP_VERSION = os.environ.get("SNAP_VERSION", "latest")

record_dpy = display.Display()


def record_callback(reply, key_press_handler):
    if reply.category != record.FromServer:
        return
    if reply.client_swapped:
        print("* received swapped protocol data, cowardly ignored")
        return
    if not len(reply.data):
        # not an event
        return
    if reply.data[0] < 2:  # reply.data is bytes
        return

    data = reply.data
    while len(data):
        event, data = rq.EventField(None).parse_binary_value(data, record_dpy.display, None, None)

        if event.type in [X.KeyPress, X.KeyRelease]:
            GLib.idle_add(key_press_handler)


def xcallback(key_press_handler):
    def inner(reply):
        record_callback(reply, key_press_handler)
    return inner


def xlistener(key_press_handler):
    ctx = record_dpy.record_create_context(
        0,
        [record.AllClients],
        [{
            'core_requests': (0, 0),
            'core_replies': (0, 0),
            'ext_requests': (0, 0, 0, 0),
            'ext_replies': (0, 0, 0, 0),
            'delivered_events': (0, 0),
            'device_events': (X.KeyPress, X.KeyPress),
            'errors': (0, 0),
            'client_started': False,
            'client_died': False,
        }])
    record_dpy.record_enable_context(ctx, xcallback(key_press_handler))
    record_dpy.record_free_context(ctx)


class PulseHandler(object):
    def __init__(self, q):
        self.queue = q
        self.pulse = pulsectl.Pulse('stuart-muter')
        self.verbose = "--verbose" in sys.argv

    def wait(self, *args):
        while True:
            instruction = self.queue.get()
            if instruction["op"] == "mute":
                self.mute()
            elif instruction["op"] == "unmute":
                self.unmute()
            else:
                self.print("Didn't understand", instruction)

    def print(self, *args):
        if self.verbose: print(*args)

    def mute(self):
        active_sources = [s for s in self.pulse.source_list() if s.port_active]
        if not active_sources:
            self.print("There are no active microphones, so not muting anything")
        else:
            if len(active_sources) > 1:
                self.print("There are {} active mics".format(len(active_sources)))
            for m in active_sources:
                self.print("Muting active mic", m)
                self.pulse.source_mute(m.index, 1)

    def unmute(self):
        active_sources = [s for s in self.pulse.source_list() if s.port_active]
        if not active_sources:
            self.print("There are no active microphones, so not unmuting anything")
        else:
            if len(active_sources) > 1:
                self.print("There are {} active mics".format(len(active_sources)))
            for m in active_sources:
                self.print("Unmuting active mic", m)
                self.pulse.source_mute(m.index, 0)


class HushboardIndicator(GObject.GObject):
    def __init__(self):
        GObject.GObject.__init__(self)

        self.mute_time_ms = 250

        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "icons"))
        self.muted_icon = os.path.abspath(os.path.join(icon_path, "muted-symbolic.svg"))
        self.unmuted_icon = os.path.abspath(os.path.join(icon_path, "unmuted-symbolic.svg"))
        self.paused_icon = os.path.abspath(os.path.join(icon_path, "paused-symbolic.svg"))
        self.app_icon = os.path.abspath(os.path.join(icon_path, "hushboard.svg"))

        self.ind = AppIndicator.Indicator.new(
            APP_ID, self.unmuted_icon,
            AppIndicator.IndicatorCategory.HARDWARE)
        self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.ind.set_attention_icon(self.muted_icon)
        self.ind.set_title(APP_NAME)

        self.menu = Gtk.Menu()
        self.ind.set_menu(self.menu)

        self.mpaused = Gtk.CheckMenuItem.new_with_mnemonic("_Pause")
        self.mpaused.connect("toggled", self.toggle_paused, None)
        self.mpaused.show()
        self.menu.append(self.mpaused)

        mabout = Gtk.MenuItem.new_with_mnemonic("_About")
        mabout.connect("activate", self.show_about, None)
        mabout.show()
        self.menu.append(mabout)

        mquit = Gtk.MenuItem.new_with_mnemonic("_Quit")
        mquit.connect("activate", self.quit, None)
        mquit.show()
        self.menu.append(mquit)

        self.unmute_timer = None

        self.queue = queue.Queue()
        pulsehandler = PulseHandler(self.queue)
        thread = threading.Thread(target=pulsehandler.wait)
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=xlistener, args=(self.key_pressed,))
        thread.daemon = True
        thread.start()

    def toggle_paused(self, widget, *args):
        if widget.get_active():
            self.ind.set_icon(self.paused_icon)
        else:
            self.ind.set_icon(self.unmuted_icon)

    def key_pressed(self, *args):
        if self.mpaused.get_active(): return
        self.ind.set_status(AppIndicator.IndicatorStatus.ATTENTION)
        if self.unmute_timer:
            GLib.source_remove(self.unmute_timer)
        else:
            self.queue.put_nowait({"op": "mute"})
        self.unmute_timer = GLib.timeout_add(
            self.mute_time_ms, self.unmute)

    def quit(self, *args):
        self.unmute()
        GLib.timeout_add_seconds(1, lambda *args: Gtk.main_quit())

    def unmute(self):
        self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.unmute_timer = None
        self.queue.put_nowait({"op": "unmute"})

    def show_about(self, *args):
        dialog = Gtk.AboutDialog()
        dialog.set_program_name(APP_NAME)
        dialog.set_copyright('Stuart Langridge')
        dialog.set_license(APP_LICENCE)
        dialog.set_version(APP_VERSION)
        dialog.set_website('https://kryogenix.org')
        dialog.set_website_label('kryogenix.org')
        dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file(self.app_icon))
        dialog.connect('response', lambda *largs: dialog.destroy())
        dialog.run()

    @staticmethod
    def run():
        Gtk.main()


def main():
    try:
        HushboardIndicator().run()
    except KeyboardInterrupt:
        # unmute if interrupted by ^c because the ^c keypress will have muted!
        PulseHandler(None).unmute()


if __name__ == "__main__":
    main()
