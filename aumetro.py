# code inspired by :
# https://medium.com/@jackhuang.wz/building-a-metronome-in-python-c8e16826fe4f
# simpleaudio fix for py.3.12 (see 'cexen' commentt):
# https://github.com/hamiltron/py-simple-audio/issues/72
# flake8: noqa: E402, F401
import time
import threading
import sys
import simpleaudio  # type: ignore
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib  # type: ignore


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_path("./css/style.css")
        self.display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(
            self.display,
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self.set_title("aumetronom")
        self.set_default_size(100, -1)
        # icon_path = "/home/mua/.local/share/icons/hicolor/scalable/apps/org.aumetro.app.svg"
        # constants
        # event to stop metronome
        self.stop_event = threading.Event()
        self.running = False
        self.beats = 4
        self.bpm = 60
        self.temponame = "adagio"
        # main box
        box_main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        box_main.set_size_request(-1, -1)
        self.set_child(box_main)
        # top row with time signature buttons
        self.box_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        self.box_controls.set_halign(Gtk.Align.CENTER)
        # hotkey info
        self.btn_info = Gtk.Button(label="?")
        self.btn_info.set_can_focus(False)
        self.btn_info.set_tooltip_text(
            """
hotkeys :\n
[tab] = next, [shift-tab] = previous field
this will move focus between bpm & [play] & beats
when focus on bpm or beats : arrow up / down : change value
when focus on [play] : [space] will toggle play / stop metronome
mouse-over & mouse-scroll will also change bpm & beats value
esc : quit application

note :
tempo names (markings) are modified from wiki 'tempo'
                """
        )
        self.box_controls.append(self.btn_info)
        # bpm label
        self.lbl_bpm = Gtk.Label(label="bpm : ")
        self.lbl_bpm.set_tooltip_text(
            """beats per minute = tempo speed
[tab] = next, [shift-tab] = previous field"""
        )
        # bpm adjustment
        self.bpm_adjustment = Gtk.Adjustment(
            value=self.bpm,
            lower=30,
            upper=300,
            step_increment=1,
        )
        # bpm spinner
        self.spn_bpm = Gtk.SpinButton(adjustment=self.bpm_adjustment)
        self.spn_bpm.connect("value-changed", self.on_bpm_changed)
        # start button
        self.btn_play = Gtk.Button(label="start")
        self.btn_play.add_css_class("button-play")
        self.btn_play.connect("clicked", self.on_toggle_play)
        # append to box
        self.box_controls.append(self.lbl_bpm)
        self.box_controls.append(self.spn_bpm)
        self.box_controls.append(self.btn_play)
        # time signature entries
        self.lbl_tSign = Gtk.Label(label="beats : ")
        self.lbl_tSign.set_tooltip_text(
            """a beats numerator of time signature
[tab] = next, [shift-tab] = previous field"""
        )
        # append
        self.box_controls.append(self.lbl_tSign)
        # beats adjustment
        self.beats_adjustment = Gtk.Adjustment(
            value=self.beats,
            lower=1,
            upper=12,
            step_increment=1,
        )
        # bpm spinner
        self.spn_beats = Gtk.SpinButton(adjustment=self.beats_adjustment)
        self.spn_beats.connect("value-changed", self.on_beats_changed)
        # append
        self.box_controls.append(self.spn_beats)
        # attach to main box
        box_main.append(self.box_controls)
        #  --- bottom row ---
        # paned window
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_wide_handle(True)
        self.paned.set_size_request(-1, -1)
        # box tempo
        self.box_tempo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box_tempo.set_size_request(-1, -1)
        # label top - tempo
        self.lbl_tempo = Gtk.Label(label=f"{self.bpm}")
        self.lbl_tempo.add_css_class("label-tempo")
        self.lbl_temponame = Gtk.Label()
        self.lbl_temponame.add_css_class("label-temponame")
        self.get_temponame()
        self.lbl_temponame.set_label(self.temponame)
        # add labels to box
        self.box_tempo.append(self.lbl_tempo)
        self.box_tempo.append(self.lbl_temponame)
        # label beat
        self.lbl_beat = Gtk.Label(label="1")
        self.lbl_beat.add_css_class("label-beat")
        self.lbl_beat.set_size_request(-1, -1)
        # add to paned window
        self.paned.set_start_child(self.box_tempo)
        self.paned.set_resize_start_child(False)
        self.paned.set_end_child(self.lbl_beat)
        self.paned.set_resize_end_child(False)
        # put into main box
        box_main.append(self.paned)

    def get_temponame(self):
        # tempo names / markings ; modified from wiki tempo
        temponames = {
            "grave": [30, 40],
            "largo": [41, 49],
            "adagio": [50, 66],
            "lento": [67, 71],
            "andante": [72, 80],
            "andante moderato": [81, 108],
            "moderato": [109, 120],
            "allegro": [121, 147],
            "allegro vivace": [148, 156],
            "vivace": [157, 171],
            "presto": [172, 200],
            "prestissimo": [201, 300],
        }
        for key in temponames.keys():
            if self.bpm >= temponames[key][0] and self.bpm <= temponames[key][1]:
                self.temponame = key
                break

    def on_bpm_changed(self, spinner):
        self.bpm = self.spn_bpm.get_value_as_int()
        self.lbl_tempo.set_text(f"{self.bpm}")
        self.get_temponame()
        self.lbl_temponame.set_text(f"{self.temponame}")

    def on_beats_changed(self, widget):
        self.beats = self.spn_beats.get_value_as_int()
        if self.running:
            self.on_toggle_play(widget)
            self.on_toggle_play(widget)

    def on_toggle_play(self, widget):
        self.running = not self.running
        # print(f"self.running : {self.running}")
        if self.running:
            self.btn_play.set_label("stop")
            self.btn_play.remove_css_class("button-play")
            self.btn_play.add_css_class("button-stop")
            self.stop_event.clear()
            self.metronome_thread = threading.Thread(target=self.run_metronome)
            self.metronome_thread.start()
        else:
            self.btn_play.set_label("play")
            self.btn_play.remove_css_class("button-stop")
            self.btn_play.add_css_class("button-play")
            self.stop_event.set()
            self.metronome_thread.join()

    def run_metronome(self):
        # simpleaudio
        accent = simpleaudio.WaveObject.from_wave_file("audio/glass.wav")
        beat = simpleaudio.WaveObject.from_wave_file("audio/stick.wav")
        while not self.stop_event.is_set():
            for i in range(self.beats):
                if self.stop_event.is_set():
                    break
                if i == 0:
                    accent_obj = accent.play()
                    accent_obj.wait_done()
                    accent_obj.stop()
                else:
                    beat_obj = beat.play()
                    beat_obj.wait_done()
                    beat_obj.stop()
                self.lbl_beat.set_text(f"{i + 1}")
                time.sleep(60 / self.bpm)


class AumetronomApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()


if __name__ == "__main__":
    app = AumetronomApp(
        application_id="org.aumetro.app",
    )
    app.run(None)
