# code inspired by :
# https://medium.com/@jackhuang.wz/building-a-metronome-in-python-c8e16826fe4f
# simpleaudio fix for py.3.12 (see 'cexen' commentt):
# https://github.com/hamiltron/py-simple-audio/issues/72
# flake8: noqa: E402, F401
import gi
import time
import threading
import sys
import simpleaudio  # type: ignore

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw, Gio  # type: ignore


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
        # self.set_default_size(500, 300)
        icon_path = "/home/mua/.local/share/icons/hicolor/128x128/apps/aumetronom.svg"
        # self.set_icon(Gio.FileIcon.new(Gio.File.new_for_path(icon_path)))
        # hotkey for exit
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_close_app)
        self.add_controller(key_controller)
        # constants
        # event to stop metronome
        self.stop_event = threading.Event()
        self.running = False
        self.beats = 4
        self.bpm = 60
        self.temponame = "adagio"
        # main grid
        self.grid = Gtk.Grid()
        self.grid.set_hexpand(True)
        self.grid.set_halign(Gtk.Align.FILL)
        self.grid.set_vexpand(True)
        self.grid.set_valign(Gtk.Align.FILL)
        self.set_child(self.grid)
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
            """
beats per minute = tempo speed
[tab] = next, [shift-tab] = previous field
            """
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
            """
a beats numerator of time signature
[tab] = next, [shift-tab] = previous field
            """
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
        # attach to grid
        self.grid.attach(self.box_controls, 0, 0, 1, 1)
        #  --- bottom row ---
        # paned window
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_wide_handle(True)
        self.paned.set_hexpand(True)
        self.paned.set_halign(Gtk.Align.FILL)
        self.paned.set_vexpand(True)
        self.paned.set_valign(Gtk.Align.FILL)
        # center panes on init - ko
        # box tempo
        self.box_tempo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # label top - tempo
        self.lbl_tempo = Gtk.Label(label=f"{self.bpm}")
        # expand label bgnd color
        self.lbl_tempo.set_vexpand(True)
        self.lbl_tempo.set_valign(Gtk.Align.FILL)
        # position label text : 0-top 1-bottom
        self.lbl_tempo.set_yalign(0.9)
        self.lbl_tempo.set_justify(Gtk.Justification.CENTER)
        self.lbl_tempo.add_css_class("label-tempo")
        # label bottom - tempo name
        self.lbl_temponame = Gtk.Label()
        self.lbl_temponame.set_vexpand(True)
        self.lbl_temponame.set_valign(Gtk.Align.FILL)
        self.lbl_temponame.set_yalign(0.1)
        # self.lbl_temponame.set_wrap(True)
        self.lbl_temponame.set_justify(Gtk.Justification.CENTER)
        self.lbl_temponame.add_css_class("label-temponame")
        self.get_temponame()
        self.lbl_temponame.set_label(self.temponame)
        # add labels to box
        self.box_tempo.append(self.lbl_tempo)
        self.box_tempo.append(self.lbl_temponame)
        # label beat
        self.lbl_beat = Gtk.Label(label="1")
        self.lbl_beat.set_vexpand(True)
        self.lbl_beat.set_valign(Gtk.Align.FILL)
        # self.lbl_beat.set_yalign(0.9)  # 0-top 1-bottom
        self.lbl_beat.set_justify(Gtk.Justification.CENTER)
        self.lbl_beat.add_css_class("label-beat")
        # add to paned window
        self.paned.set_start_child(self.box_tempo)
        self.paned.set_resize_start_child(False)
        self.paned.set_shrink_start_child(True)
        self.paned.set_end_child(self.lbl_beat)
        self.paned.set_resize_end_child(False)
        # self.paned.set_resize_end_child(True)
        self.paned.set_shrink_end_child(True)
        # put into grid
        self.grid.attach(self.paned, 0, 1, 1, 1)

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
                self.lbl_beat.set_text(f"{i+1}")
                time.sleep(60 / self.bpm)

    def on_close_app(self, controller, keyval, keycode, state):
        key = Gdk.keyval_name(keyval)
        if key == "Escape":
            print("closing app ...")
            self.close()
            return True
        return False


class AumetronomApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("activate", self.on_activate)
        self.style_manager = Adw.StyleManager.get_default()
        self.style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()


app = AumetronomApp(
    application_id="org.aumetronom.app",
)
app.run(sys.argv)
