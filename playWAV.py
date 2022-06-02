from Makerverse_R2R_DAC import Makerverse_wavPlayer
from machine import Pin

player = Makerverse_wavPlayer(buffer=8192)

player.mountSD(path = '/sd', spiDev = 0, sck=Pin(2), mosi=Pin(3), miso=Pin(4), cs = Pin(5))

player.playWav("/sd/sneaky-snitch-by-kevin-macleod-from-filmmusic-io.wav")