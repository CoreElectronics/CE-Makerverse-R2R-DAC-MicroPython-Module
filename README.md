# Makerverse Audio Kit Python Module

This is the firmware repo for the Makerverse [R2R DAC](https://core-electronics.com.au/catalog/product/view/sku/ce08391) Python module, featured in the [Makerverse Audio Kit](https://core-electronics.com.au/catalog/product/view/sku/ce08484)

# Usage

## Wav File Example
[playWAV.py] is a simple example to confirm the module is wired correctly. It uses I2C pins sda = GP0 and scl = GP1.
```
from Makerverse_R2R_DAC import wavPlayer

player = Makerverse_wavPlayer()

player.playWav("example.wav")

player.mountSD() # Mounts to /sd/ by default
player.playWav("/sd/example.wav")
```

## Keyboard Example

## Details - Makerverse_keyboard Class

### Makerverse_Keyboard(rate = 16383)

Makerverse_Keyboard object constructor. Returns a Makerverse_Keyboard object.

The rate can be modified however the 16383Hz default rate is tuned for creating standard Western musical notes tuned to A=440Hz.

It is recommended that the rate not be increased - distortion due to buffer underruns can occur.

This method configures GP16 to GP22, GP26, and GP27 for use with the Makerverse Keyboard for Raspberry Pi Pico. Specifically the pull-down is configured for GP16 to GP26 and GP27 is configured as an output in the HIGH state.

Note that GP27 is used as a "Vcc" for the keyboard. It provides +3.3V to the switches so that pressing a switch reads as a logic 1.

### Makerverse_Keyboard.playSine()

This method continuously scans the keyboard's GPIO pins and generates a different frequency sine wav for each key.

The method is configured for the C-Major scale.

## Details - Makerverse_wavPlayer Class

This module is designed to stream wav files from an SD card (or Raspberry Pi Pico flash memory) to the Makerverse R2R DAC.

The wav files must be in the following format:

Channels: 1 (mono)
Data format: 16-bit PCM (signed integer)
Sample rate: 44.1kHz or less
Size: 4GB or less (limited by the FAT filesystem)

As above, the SD card must be formatted with a FAT filesystem.


### Makerverse_wavPlayer(rate = 44100 buffer = 4096)

wavPlayer object constructor. Returns a Makerverse_wavPlayer object.

Parameter | Type | Default | Description
--- | --- | --- | ---
rate | Integer | 44100 | The initial sample rate of played wav files. The rate is automatically adjusted when playing files of different sample rates.
buffer | Integer | 4096 | The size of the internal buffers in PCM samples. Each sample is stored as a 16-bit integer and there are two buffers. At least 4\*buffer bytes of RAM are used by this object.

### Makerverse_wavPlayer.playWav(fileName)

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

### Makerverse_wavPlayer.mountSD(path = '/sd', spiDev = 0, sck=Pin(18), mosi=Pin(19), miso=Pin(16), cs = Pin(17))

Mount the SD card to the MicroPython filesystem. Wave files stored on the SD card can then be read with the standard built-in functions open() and read().

Due to the R2R DAC occupying GPIO pins GP6 to GP15 the SD card's SPI interface must be connected to either the default pins or pins GP2 (SCK), GP3 (MOSI), GP4 (MISO), and GP5 (CS).

Parameter | Type | Default | Description
--- | --- | --- | ---
path | String | '/sd' | The filesystem path where the SD card will be mounted.
spiDev | Integer | 0 | The SPI peripheral to use. This should always be set to 0 but can be set to 1 if this function is used without the DAC (ie: if GPIOs GP7 to GP15 are available)
sck | Pin object | Pin(18) | The GPIO pin used for the SPI clock signal
mosi | Pin object | Pin(19) | The GPIO pin used for the SPI MOSI (Tx) signal
miso | Pin object | Pin(16) | The GPIO pin used for the SPI MISO (Rx) signal
cs | Pin object | Pin(17) | The GPIO pin used for the SPI CS signal

### Makerverse_wavPlayer.voltage(v)

This method allows the R2R DAC to be used as a voltage-output DAC. The single argument is a value from 0 to 3.3, representing a target output voltage.

Note that the precision of the output voltage is dependent on the accuracy of the Raspberry Pi Pico's 3.3V power supply. Typically this function will have an absolute accuracy of approximately +/-0.05V.

Parameter | Type | Default | Description
--- | --- | --- | ---
v | Float | - | The voltage to generate with the R2R DAC

### Makerverse_wavPlayer.dac.put()

This is a low-level method which writes a single output value to the DAC via the PIO.

Using this method allows for the Makerverse_wavPlayer module to be used as a general purpose DAC with a bandwidth of 1MHz (limited by the MCP6001 op-amp on the DAC PCB).

This method will accept any 32-bit value but only the 10 LSBs will be used. The valid decimal input range is therefore 0 to 1023, inclusive, producing voltages from 0 to 3.3 V.

Example:

```
from Makerverse_R2R_DAC import wavPlayer

player = Makerverse_wavPlayer()

player.dac.put(100) # Set the DAC output voltage to 3.3 * 100 / 1023 = 0.3226 V
```

## Attribution

This project adapts code from AWG_v1.py by Rolf Oldeman, published on Instructables: https://www.instructables.com/Arbitrary-Wave-Generator-With-the-Raspberry-Pi-Pic/

Example wav file "sneaky-snitch-by-kevin-macleod-from-filmmusic-io.wav" converted from:

Sneaky Snitch by Kevin MacLeod
Link: https://incompetech.filmmusic.io/song/4384-sneaky-snitch
License: https://filmmusic.io/standard-license

## License
This project is open source - please review the LICENSE.md file for further licensing information.

If you have any technical questions, or concerns about licensing, please contact technical support on the [Core Electronics forums](https://forum.core-electronics.com.au/).

*\"Makerverse\" and the Makerverse logo are trademarks of Core Electronics Pty Ltd.*
