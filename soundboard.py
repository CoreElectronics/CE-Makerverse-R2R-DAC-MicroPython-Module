from Makerverse_R2R_DAC import Makerverse_wavPlayer

player = Makerverse_wavPlayer(buffer=8192)

sounds = ["drum.wav", "pluck.wav"]

while True:
    player.soundboard(sounds)