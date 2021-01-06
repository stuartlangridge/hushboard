#!/usr/bin/env python3
import os
import gi
import time
import threading
from . import pulsectl

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk, GLib

gi.require_version('AppIndicator3', '0.1')
from gi.repository import AppIndicator3 as AppIndicator

from Xlib import X, display
from Xlib.ext import record
from Xlib.protocol import rq

APP_ID = 'unkeeb'
APP_NAME = 'Unkeeb'
APP_LICENCE = "no licence!"
APP_VERSION = "0.0.1"

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
    if reply.data[0] < 2: # reply.data is bytes
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


def mute():
    try:
        pulse = pulsectl.Pulse('stuart-muter')
    except pulsectl.PulseError:
        time.sleep(0.2)
        mute()
        return
    active_sources = [s for s in pulse.source_list() if s.port_active]
    if len(active_sources) == 1:
        # print("Muting active mic", active_sources[0])
        pulse.source_mute(active_sources[0].index, 1)
    elif len(active_sources) == 0:
        print("There are no active microphones!")
    else:
        print("There is more than one active microphone so I don't know which one to unmute")


def unmute():
    try:
        pulse = pulsectl.Pulse('stuart-muter')
    except pulsectl.PulseError:
        time.sleep(0.2)
        unmute()
        return
    active_sources = [s for s in pulse.source_list() if s.port_active]
    if len(active_sources) == 1:
        # print("Unmuting active mic", active_sources[0])
        pulse.source_mute(active_sources[0].index, 0)
    elif len(active_sources) == 0:
        print("There are no active microphones!")
    else:
        print("There is more than one active microphone so I don't know which one to unmute")


class UnkeebIndicator(GObject.GObject):
    def __init__(self):
        """Constructor."""
        GObject.GObject.__init__(self)

        self.mute_time_seconds = 2

        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "icons"))
        muted_icon = os.path.abspath(os.path.join(icon_path, "muted.svg"))
        unmuted_icon = os.path.abspath(os.path.join(icon_path, "unmuted.svg"))

        # Create the indicator object
        self.ind = AppIndicator.Indicator.new(
            APP_ID, unmuted_icon,
            AppIndicator.IndicatorCategory.HARDWARE)
        self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.ind.set_attention_icon(muted_icon)

        self.menu = Gtk.Menu()
        self.ind.set_menu(self.menu)
        mabout = Gtk.MenuItem.new_with_mnemonic("About")
        mabout.connect("activate", self.show_about, None)
        mabout.show()
        self.menu.append(mabout)

        mquit = Gtk.MenuItem.new_with_mnemonic("Quit")
        mquit.connect("activate", lambda *largs: Gtk.main_quit(), None)
        mquit.show()
        self.menu.append(mquit)

        self.unmute_timer = None

        thread = threading.Thread(target=xlistener, args=(self.key_pressed,))
        thread.daemon = True
        thread.start()

    def key_pressed(self, *args):
        # print("mute mic!")
        self.ind.set_status(AppIndicator.IndicatorStatus.ATTENTION)
        if self.unmute_timer:
            GLib.source_remove(self.unmute_timer)
        thread = threading.Thread(target=mute)
        thread.daemon = True
        thread.start()
        self.unmute_timer = GLib.timeout_add_seconds(
            self.mute_time_seconds, self.unmute)

    def unmute(self):
        # print("unmute mic!")
        self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.unmute_timer = None
        thread = threading.Thread(target=unmute)
        thread.daemon = True
        thread.start()

    def show_about(*args):
        dialog = Gtk.AboutDialog()
        dialog.set_program_name(APP_NAME)
        dialog.set_copyright('Stuart Langridge')
        dialog.set_license(APP_LICENCE)
        dialog.set_version(APP_VERSION)
        dialog.set_website('https://kryogenix.org')
        dialog.set_website_label('kryogenix.org')
        dialog.set_logo_icon_name('unkeeb')
        dialog.connect('response', lambda *largs: dialog.destroy())
        dialog.run()

    @staticmethod
    def run():
        Gtk.main()


if __name__ == "__main__":
    UnkeebIndicator().run()
