import rp2
from machine import Pin, SPI, mem32
from array import array
from uctypes import addressof
import sdcard, uos

# DMA register addresses from RP2040 datasheet pages 108-109
# https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
#
# DMA11 is used as MicroPython uses DMA0 and DMA1 when performing >=32 byte transfers via hardware SPI.
# As there is no known way to call the MicroPython C function dma_claim_unused_channel()
# DMA11 is being used in the hope that it doesn't collide with MicroPython's allocation.
# Hardware SPI DMA use is undocumented; see source for details
# machine_spi.c, line 218f: https://github.com/micropython/micropython/blob/master/ports/rp2/machine_spi.c

DMA_BASE=0x50000000
CH11_READ_ADDR  =DMA_BASE+0x2c0
CH11_WRITE_ADDR =DMA_BASE+0x2c4
CH11_TRANS_COUNT=DMA_BASE+0x2c8
CH11_CTRL_TRIG  =DMA_BASE+0x2cc
CH11_AL1_CTRL   =DMA_BASE+0x2d0

PIO0_BASE      =0x50200000
PIO0_TXF0      =PIO0_BASE+0x10
PIO0_SM0_CLKDIV=PIO0_BASE+0xc8

class Makerverse_wavPlayer():
    def __init__(self, rate=44100, buffer = 4096):
        self.BUFLENHALF = 4096
        self.BUFLEN = self.BUFLENHALF*2        
        self.ar1 = array("I", [0]*self.BUFLENHALF)
        self.ar2 = array("I", [0]*self.BUFLENHALF)
        # Init state machine to set its level to half scale; removes pop upon wav play start
        self.rate = rate
        self.dac = rp2.StateMachine(0, self.dacPio, freq=rate, out_base=Pin(6))
        self.dac.active(1)
        self.dac.put(512)
        
    def mountSD(self, path = '/sd', spiDev = 0, sck=Pin(18), mosi=Pin(19), miso=Pin(16), cs = Pin(17)):
        spi = SPI(spiDev, sck=sck, mosi=mosi, miso=miso)
        sd = sdcard.SDCard(spi, cs, baudrate=10000000)
        uos.mount(sd, path)
        
    def playWav(self, fileName):
        self.f = open(fileName, "rb")
        self.f.seek(34)
        bits = self.f.read(2)
        print("Bit depth: ", bits[0]+bits[1]*256)
        if bits[0] != 16 or bits[1] != 0:
            print("This wav player only supports 16-bit files.")
            return
        self.f.seek(22)
        ch = self.f.read(2)
        print("Channel count: ", ch[0] + ch[1]*256)
        if ch[0] != 1 or ch[1] != 0:
            print("This wav player only supports mono files.")
            return
        
        self.f.seek(24)
        rateData = self.f.read(4)
        rate = rateData[1]*256 + rateData[0]
        print("Rate: ", rate)
        if rate is not self.rate:
            print("Warning: Player is configured for ", self.rate,"Hz but file is ", rate, "Hz.")
            print("This causes a 'pop'.")
            self.dac = rp2.StateMachine(0, self.dacPio, freq=rate, out_base=Pin(6))
            self.dac.active(1)
            self.rate = rate
            print("Output sample rate reconfigured to ", rate, "Hz.")
        self.stream()
        self.f.close()

    @rp2.asm_pio(out_init=(rp2.PIO.OUT_HIGH,)*10, out_shiftdir=rp2.PIO.SHIFT_RIGHT, autopull=True, pull_thresh=10)
    def dacPio():
        out(pins, 10)

    def voltage(v):
        if v > 3.3:
            v = 3.3
            print("Warning: voltage output is only valid from 0V to 3.3V. Clamping to 3.3V")
        if v < 0:
            v = 0
            print("Warning: voltage output is only valid from 0V to 3.3V. Clamping to 0V")
        self.dac.put(int(v/3.3*1024))

    # DMA code modified from AWG_v1.py, by Rolf Oldeman
    # See: https://www.instructables.com/Arbitrary-Wave-Generator-With-the-Raspberry-Pi-Pic/
    def startDMA(self,ar,nword):
        while mem32[CH11_TRANS_COUNT] > 0:
            continue
        mem32[CH11_READ_ADDR]=addressof(ar)
        mem32[CH11_WRITE_ADDR]=PIO0_TXF0
        mem32[CH11_TRANS_COUNT]=nword
        IRQ_QUIET=0x1 #do not generate an interrupt
        TREQ_SEL=0x00 #wait for PIO0_TX0
        CHAIN_TO=11
        RING_SEL=0
        RING_SIZE=0   #no wrapping
        INCR_WRITE=0  #for write to array
        INCR_READ=1   #for read from array
        DATA_SIZE=2   #32-bit word transfer
        HIGH_PRIORITY=1
        EN=1
        CTRL0=(IRQ_QUIET<<21)|(TREQ_SEL<<15)|(CHAIN_TO<<11)|(RING_SEL<<10)|(RING_SIZE<<9)|(INCR_WRITE<<5)|(INCR_READ<<4)|(DATA_SIZE<<2)|(HIGH_PRIORITY<<1)|(EN<<0)
        mem32[CH11_CTRL_TRIG]=CTRL0

    @micropython.viper()
    def stream(self):
        f = self.f
        f.seek(43)
        dac = self.dac
        ar1 = self.ar1
        ar2 = self.ar2
        ar = ar1

        while True:
            x = f.read(self.BUFLEN)

            if int(len(x)) < int(self.BUFLEN): 
                break
            k=0
            
            for j in range(0, int(self.BUFLEN), 2):
                # +32 allows for centered rounding under bit shift truncation
                # Provides approx 5dB boost to spurious free dynamic range
                sample0 = ((int(x[j+0]) << 2) + ((int(x[j+1]) + 32) >> 6))
                                
                #FIXME: Something is wrong with this 16-bit to 10-bit conversion & rounding
                if sample0 < 512:
                    sample0 = sample0 + 512
                else: 
                    sample0 = sample0 - 512
        
                ar[k] = sample0 
                k += 1

            self.startDMA(ar, self.BUFLENHALF)
            
            if ar == ar1:
                ar = ar2
            else:
                ar = ar1
                
        while int(mem32[CH11_TRANS_COUNT]) > 0:
            continue
        # Leave DC value at half scale
        self.dac.put(512)
