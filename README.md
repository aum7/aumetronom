simple metronome

hover over '?' & 'bpm' & 'beats' for info / hotkeys

simpleaudio package - use 'fixed' one :

https://github.com/hamiltron/py-simple-audio/issues/72

scroll down to 'cexen' comment

same link is in 'requirements.txt'

the original simpleaudio package gives error when playing audio

![aumetronom](imgs/aumetronom_app.png)

you will have to build it on your system, using standard practice for building gtk(4) apps

ie needed are PyGObject & introspection & audio (alsa) ... libraries

also included are additional files in 'audio' folder

select ones you like and change 'aumetronomgtk4.py' file, lines 225 & 226 (run_metronome function, 'accent' & 'beat') to use your selected audio files

it is possible to use 'beats : 1' and therefore mimic analog metronome - only 1 sound is played (accent one)

tempo goes from 30 to 300

to minimise possibility of audio overlaping & consequently runtime errors, all audio files are 10025 Hz, shortened to below 0.2 sec (60 / 300 bpm (max)) = 0.2
