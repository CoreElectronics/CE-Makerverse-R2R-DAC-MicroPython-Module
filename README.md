# Makerverse Audio Kit Python Module

This is the firmware repo for the Makerverse [R2R DAC](https://core-electronics.com.au/catalog/product/view/sku/ce08391) Python module, featured in the [Makerverse Audio Kit](https://core-electronics.com.au/catalog/product/view/sku/ce08484)

# Usage

## Wav File Example
[playWAV.py](https://github.com/CoreElectronics/CE-Makerverse-R2R-DAC-MicroPython-Module/blob/main/playWAV.py) demonstrates streaming wav files from an SD card.

It will stream the wav file in real time and player.playWav() will return when the entire file has finished playing.

```
from Makerverse_R2R_DAC import WAV_player

player = WAV_player()

# Playing a wav file from the Pico's memory, saved to "root" folder.
player.play("pluck.wav")

# Playing a wav file which has been saved to the SD card.
# First, mount the SD
player.mountSD(path = '/sd', spi = 0, sck_pin = 2, mosi_pin = 3, miso_pin = 4, cs_pin = 5)

# Second, play the file. File path includes folder SD card is mounted to.
player.play("/sd/sneaky-snitch-by-kevin-macleod-from-filmmusic-io.wav")
```

## Keyboard Example

[keyboard.py](https://github.com/CoreElectronics/CE-Makerverse-R2R-DAC-MicroPython-Module/blob/main/keyboard.py) Turns the Makerverse Audio Kit into an 8-key electronic piano.

keyboard.playSine() contains an infinite loop - it does not return.

```
from Makerverse_R2R_DAC import keyboard

keyboard = keyboard()

keyboard.play()
```

## Details - keyboard Class

### keyboard(rate = 16383)

keyboard object constructor. Returns a keyboard object.

The rate can be modified however the 16383Hz default rate is tuned for creating standard Western musical notes tuned to A=440Hz.

It is recommended that the rate not be increased - distortion due to buffer underruns can occur.

This method configures GP16 to GP22, GP26, and GP27 for use with the Makerverse Keyboard for Raspberry Pi Pico. Specifically the pull-down is configured for GP16 to GP26 and GP27 is configured as an output in the HIGH state.

Note that GP27 is used as a "Vcc" for the keyboard. It provides +3.3V to the switches so that pressing a switch reads as a logic 1.

### keyboard.play()

This method continuously scans the keyboard's GPIO pins and generates a different frequency sine wav for each key.

The method is configured for the C-Major scale.

## Details - WAV_player Class

This module is designed to stream wav files from an SD card (or Raspberry Pi Pico flash memory) to the Makerverse R2R DAC.

The wav files must be in the following format:

Channels: 1 (mono)
Data format: 16-bit PCM (signed integer)
Sample rate: 44.1kHz or less
Size: 4GB or less (limited by the FAT filesystem)

As above, the SD card must be formatted with a FAT filesystem.

### WAV_player(rate = 44100, buffer = 8192)

WAV_player object constructor. Returns a WAV_player object.

Parameter | Type | Default | Description
--- | --- | --- | ---
rate | Integer | 44100 | The initial sample rate of played wav files. The rate is automatically adjusted when playing files of different sample rates.
buffer | Integer | 8192 | The combined length of the two internal buffers, in units of PCM samples. Each sample is stored as a 16-bit integer and there are two buffers. At least 2\*buffer bytes of RAM are used by this object.

### WAV_player.play(fileName)

Play a wav file. The fileName argument should be an absolute file path to a wav file.

This method performs some checks on the input file and prints an error if:

- The file format is not 16-bit
- The number of channels is not 1

The sample rate is also read and if the file's sample rate does not match the wavPlayer's sample rate it is reconfigured. The configuration step adds about 70ms of latency and causes an audible "pop".

The sample rate reconfiguration is persistent: further files can be played and the sample rate doesn't get reconfigured until a file with a different sample rate is played.

This method is blocking (ie: It does not return until the entire wav file has been played).

Parameter | Type | Default | Description
--- | --- | --- | ---
fileName | String | - | Absolute file path to the .wav file to be played.

### WAV_player.mountSD(path = '/sd', spi = 0, sck_pin = 18, mosi_pin = 19, miso_pin = 16, cs_pin = 17)

Mount the SD card to the MicroPython filesystem. Wave files stored on the SD card can then be read with the standard built-in functions open() and read().

Due to the R2R DAC occupying GPIO pins GP6 to GP15 the SD card's SPI interface must be connected to either the default pins or pins GP2 (SCK), GP3 (MOSI), GP4 (MISO), and GP5 (CS).

Parameter | Type | Default | Description
--- | --- | --- | ---
path | String | '/sd' | The filesystem path where the SD card will be mounted.
spi | Integer | 0 | The SPI peripheral to use. This should always be set to 0 but can be set to 1 if this function is used without the DAC (ie: if GPIOs GP7 to GP15 are available)
sck_pin | Pin object | 18 | The GPIO pin used for the SPI clock signal
mosi_pin | Pin object | 19 | The GPIO pin used for the SPI MOSI (Tx) signal
miso_pin | Pin object | 16 | The GPIO pin used for the SPI MISO (Rx) signal
cs_pin | Pin object | 17 | The GPIO pin used for the SPI CS signal

### WAV_player.soundboard(sounds)

Turns the Makerverse Keyboard for Raspberry Pi Pico into a soundboard with the ability to play one of eight different wav files.

The argument `sounds` is a list of filenames. The first entry is played when the keyboard's button 1 is pressed, the second is played when button 2 is pressed, etc.

The wav files are played to completion before the buttons are read again.

Example, with "drum.wav" and "pluck.wav" loaded into the Raspberry Pi Pico's filesystem:

```
from Makerverse_R2R_DAC import WAV_player

player = WAV_player(buffer=8192)

sounds = ["drum.wav", "pluck.wav"]

while True:
    player.soundboard(sounds)
```

The sounds list can include files loaded from the SD card by prefixing the filename with the absolute file path. Eg:

```
sounds = ["/sd/drum.wav"]
```

Parameter | Type | Default | Description
--- | --- | --- | ---
sounds | List of strings | None | Required, a list of filename strings.

### WAV_player.voltage(v)

This method allows the R2R DAC to be used as a voltage-output DAC. The single argument is a value from 0 to 3.3, representing a target output voltage.

Note that the precision of the output voltage is dependent on the accuracy of the Raspberry Pi Pico's 3.3V power supply. Typically this function will have an absolute accuracy of approximately +/-0.05V.

The R2R DAC is a 10-bit DAC so the step size is 3.3/1024 = 3.2mV. The DAC's differential and integral nonlinearities are less than 1 LSB.

Parameter | Type | Default | Description
--- | --- | --- | ---
v | Float | - | The voltage to generate with the R2R DAC

### WAV_player.dac.put()

This is a low-level method which writes a single output value to the DAC via the PIO.

Using this method allows for the WAV_player module to be used as a general purpose DAC with a bandwidth of 1MHz (limited by the MCP6001 op-amp on the DAC PCB).

This method will accept any 32-bit value but only the 10 LSBs will be used. The valid decimal input range is therefore 0 to 1023, inclusive, producing voltages from 0 to 3.3 V.

Example:

```
from Makerverse_R2R_DAC import WAV_player

player = WAV_player()

player.dac.put(100) # Set the DAC output voltage to 3.3 * 100 / 1023 = 0.3226 V
```

## Attribution

The MicroPython module (sdcard.py) has been modified from the MicroPython v1.17 release. When reading it polls the card's busy status at 0.1ms (down from 1ms) intervals. This was required to obtain read throughput for wav playback at 44.1kHz without buffer underruns.

This project adapts code from AWG_v1.py by Rolf Oldeman, published on Instructables: https://www.instructables.com/Arbitrary-Wave-Generator-With-the-Raspberry-Pi-Pic/

Example wav file "sneaky-snitch-by-kevin-macleod-from-filmmusic-io.wav" converted from:

Sneaky Snitch by Kevin MacLeod
Link: https://incompetech.filmmusic.io/song/4384-sneaky-snitch
License: https://filmmusic.io/standard-license

## License
This project is open source - please review the LICENSE.md file for further licensing information.

If you have any technical questions, or concerns about licensing, please contact technical support on the [Core Electronics forums](https://forum.core-electronics.com.au/).

*\"Makerverse\" and the Makerverse logo are trademarks of Core Electronics Pty Ltd.*
