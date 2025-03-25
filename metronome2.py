# ruff: noqa : E402, F401
#!/usr/bin/env python3
# minimal metronome app using gtk4 and simpleaudio
import sys
import simpleaudio as sa  # type: ignore
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
        self.set_default_size(400, 200)
        self.beats = 4
        self.bpm = 80
        self.playing = False
        self.current_beat = 0
        self.tick_source = None
        # main vbox
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_child(vbox)
        # top row - controls
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox.append(top_box)
        # vertical box with controls
        # control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        # top_box.append(control_box)
        # button [ ? ]
        self.info_button = Gtk.Button(label="[ ? ]")
        self.info_button.set_tooltip_text("metronome app")
        self.info_button.set_sensitive(False)
        top_box.append(self.info_button)
        # control_box.append(self.info_button)

        # bpm label and spinbutton
        bpm_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        top_box.append(bpm_box)
        bpm_label = Gtk.Label(label="bpm :")
        bpm_label.set_tooltip_text("beats per minute")
        bpm_box.append(bpm_label)
        adjustment_bpm = Gtk.Adjustment(
            value=self.bpm,
            lower=30,
            upper=300,
            step_increment=1,
        )
        # adjustment_bpm = Gtk.Adjustment(120, 20, 300, 1, 10, 0)
        self.spin_bpm = Gtk.SpinButton(adjustment=adjustment_bpm)
        bpm_box.append(self.spin_bpm)
        # play button
        self.play_button = Gtk.Button(label="play")
        self.play_button.connect("clicked", self.on_toggle_play)
        top_box.append(self.play_button)
        # beats label and spinbutton
        beats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        top_box.append(beats_box)
        beats_label = Gtk.Label(label="beats :")
        beats_label.set_tooltip_text("beats of time signature")
        beats_box.append(beats_label)
        adjustment_beats = Gtk.Adjustment(
            value=self.beats,
            lower=1,
            upper=12,
            step_increment=1,
        )
        self.spin_beats = Gtk.SpinButton(adjustment=adjustment_beats)
        beats_box.append(self.spin_beats)
        # bottom row - paned display
        self.paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        # left pane - display bpm with green background
        self.bpm_display = Gtk.Label(label=f"bpm: {self.spin_bpm.get_value_as_int()}")
        # self.set_bg_color(self.bpm_display, "green")
        self.paned.set_start_child(self.bpm_display)
        # right pane - display current beat with dodgerblue background
        self.beats_display = Gtk.Label(
            label=f"beat: 0 / {self.spin_beats.get_value_as_int()}"
        )
        # self.set_bg_color(self.beats_display, "dodgerblue")
        self.paned.set_end_child(self.beats_display)
        # update display when spinbuttons change
        self.spin_bpm.connect("value-changed", self.on_bpm_changed)
        self.spin_beats.connect("value-changed", self.on_beats_changed)
        # load click sound
        self.click_tick()

    def click_tick(self):
        try:
            self.accent = sa.WaveObject.from_wave_file("audio/glass.wav")
            self.beat = sa.WaveObject.from_wave_file("audio/stick.wav")

            def tick():
                # play click sound
                beats_total = self.spin_beats.get_value_as_int()
                self.current_beat = (self.current_beat % beats_total) + 1
                self.beats_display.set_label(
                    f"beat: {self.current_beat} / {beats_total}"
                )
                if self.current_beat == 1:
                    self.accent.play()
                else:
                    self.beat.play()
                self.accent.play()
                return True

            # store tick function as instance attribute
            self.tick = tick

        except Exception as e:
            print("error loading .wav :\n\t", e)
            sys.exit(1)

    def on_bpm_changed(self, spin):
        if self.playing:
            self.stop_metronome()
        bpm = spin.get_value_as_int()
        self.bpm_display.set_label(f"bpm: {bpm}")
        # if playing, restart metronome with new tempo
        self.start_metronome()

    def on_beats_changed(self, spin):
        beats = spin.get_value_as_int()
        self.beats_display.set_label(f"beat: 0 / {beats}")

    def on_toggle_play(self, button):
        if self.playing:
            self.stop_metronome()
            self.play_button.set_label("play")
        else:
            self.start_metronome()
            self.play_button.set_label("stop")

    def start_metronome(self):
        self.playing = True
        self.current_beat = 0
        bpm = self.spin_bpm.get_value_as_int()
        interval = int(60000 / bpm)
        self.tick_source = GLib.timeout_add(interval, self.tick)

    def stop_metronome(self):
        self.playing = False
        if self.tick_source:
            GLib.source_remove(self.tick_source)
            self.tick_source = None


class MetronomeApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()


if __name__ == "__main__":
    app = MetronomeApp(application_id="aum.simple.metronome")
    app.run(sys.argv)
