from Makerverse_R2R_DAC import WAV_player
from machine import Pin

player = WAV_player(buffer=8192)

player.mountSD(path = '/sd', spiDev = 0, sck=Pin(2), mosi=Pin(3), miso=Pin(4), cs = Pin(5))

player.play("/sd/sneaky-snitch-by-kevin-macleod-from-filmmusic-io.wav")