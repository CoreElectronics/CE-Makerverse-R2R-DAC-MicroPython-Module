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

'''
GPIO notes:
Base addr: 0x40014000
Status offset: GPn * 8
Input bit: 17

Therefore: input on GPIO n = (mem32[0x40014000+n*8] >> 17) & 1
'''

class Makerverse_Keyboard():
    def __init__(self, rate = 16383):
        import array
        sine = [512,515,518,521,525,528,531,534,537,540,543,546,550,553,556,559,562,565,568,571,575,578,581,584,587,590,593,596,599,602,606,609,612,615,618,621,624,627,630,633,636,639,642,645,648,651,654,657,660,663,666,669,672,675,678,681,684,687,690,693,696,699,702,705,708,710,713,716,719,722,725,728,730,733,736,739,742,745,747,750,753,756,758,761,764,767,769,772,775,777,780,783,785,788,791,793,796,798,801,804,806,809,811,814,816,819,821,824,826,829,831,834,836,839,841,843,846,848,850,853,855,857,860,862,864,867,869,871,873,876,878,880,882,884,886,889,891,893,895,897,899,901,903,905,907,909,911,913,915,917,919,921,922,924,926,928,930,932,933,935,937,939,940,942,944,945,947,949,950,952,953,955,957,958,960,961,963,964,966,967,968,970,971,973,974,975,977,978,979,980,982,983,984,985,986,988,989,990,991,992,993,994,995,996,997,998,999,1000,1001,1002,1003,1004,1004,1005,1006,1007,1008,1008,1009,1010,1011,1011,1012,1013,1013,1014,1014,1015,1015,1016,1017,1017,1017,1018,1018,1019,1019,1020,1020,1020,1021,1021,1021,1021,1022,1022,1022,1022,1022,1023,1023,1023,1023,1023,1023,1023,1023,1023,1023,1023,1023,1023,1023,1023,1022,1022,1022,1022,1022,1021,1021,1021,1021,1020,1020,1020,1019,1019,1018,1018,1017,1017,1017,1016,1015,1015,1014,1014,1013,1013,1012,1011,1011,1010,1009,1008,1008,1007,1006,1005,1004,1004,1003,1002,1001,1000,999,998,997,996,995,994,993,992,991,990,989,988,986,985,984,983,982,980,979,978,977,975,974,973,971,970,968,967,966,964,963,961,960,958,957,955,953,952,950,949,947,945,944,942,940,939,937,935,933,932,930,928,926,924,922,921,919,917,915,913,911,909,907,905,903,901,899,897,895,893,891,889,886,884,882,880,878,876,873,871,869,867,864,862,860,857,855,853,850,848,846,843,841,839,836,834,831,829,826,824,821,819,816,814,811,809,806,804,801,798,796,793,791,788,785,783,780,777,775,772,769,767,764,761,758,756,753,750,747,745,742,739,736,733,730,728,725,722,719,716,713,710,708,705,702,699,696,693,690,687,684,681,678,675,672,669,666,663,660,657,654,651,648,645,642,639,636,633,630,627,624,621,618,615,612,609,606,602,599,596,593,590,587,584,581,578,575,571,568,565,562,559,556,553,550,546,543,540,537,534,531,528,525,521,518,515,512,509,506,503,499,496,493,490,487,484,481,478,474,471,468,465,462,459,456,453,449,446,443,440,437,434,431,428,425,422,418,415,412,409,406,403,400,397,394,391,388,385,382,379,376,373,370,367,364,361,358,355,352,349,346,343,340,337,334,331,328,325,322,319,316,314,311,308,305,302,299,296,294,291,288,285,282,279,277,274,271,268,266,263,260,257,255,252,249,247,244,241,239,236,233,231,228,226,223,220,218,215,213,210,208,205,203,200,198,195,193,190,188,185,183,181,178,176,174,171,169,167,164,162,160,157,155,153,151,148,146,144,142,140,138,135,133,131,129,127,125,123,121,119,117,115,113,111,109,107,105,103,102,100,98,96,94,92,91,89,87,85,84,82,80,79,77,75,74,72,71,69,67,66,64,63,61,60,58,57,56,54,53,51,50,49,47,46,45,44,42,41,40,39,38,36,35,34,33,32,31,30,29,28,27,26,25,24,23,22,21,20,20,19,18,17,16,16,15,14,13,13,12,11,11,10,10,9,9,8,7,7,7,6,6,5,5,4,4,4,3,3,3,3,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,3,3,3,3,4,4,4,5,5,6,6,7,7,7,8,9,9,10,10,11,11,12,13,13,14,15,16,16,17,18,19,20,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,38,39,40,41,42,44,45,46,47,49,50,51,53,54,56,57,58,60,61,63,64,66,67,69,71,72,74,75,77,79,80,82,84,85,87,89,91,92,94,96,98,100,102,103,105,107,109,111,113,115,117,119,121,123,125,127,129,131,133,135,138,140,142,144,146,148,151,153,155,157,160,162,164,167,169,171,174,176,178,181,183,185,188,190,193,195,198,200,203,205,208,210,213,215,218,220,223,226,228,231,233,236,239,241,244,247,249,252,255,257,260,263,266,268,271,274,277,279,282,285,288,291,294,296,299,302,305,308,311,314,316,319,322,325,328,331,334,337,340,343,346,349,352,355,358,361,364,367,370,373,376,379,382,385,388,391,394,397,400,403,406,409,412,415,418,422,425,428,431,434,437,440,443,446,449,453,456,459,462,465,468,471,474,478,481,484,487,490,493,496,499,503,506,509]
        self.sine = array.array('H', sine)
        self.rate = rate
        self.dac = rp2.StateMachine(0, self.dacPio, freq=rate, out_base=Pin(6))
        self.dac.active(1)
        self.dac.put(512)
        
        # Turn on power to keyboard
        PWR = Pin(27, Pin.OUT)
        PWR.on()
        
        # Enable pull-down on GP16 to GP26
        for i in range(16, 27):
            P = Pin(i, Pin.IN, Pin.PULL_DOWN)
        
    @micropython.native()
    def playSine(self):
        freq = 440
        phi1 = 0
        phi2 = 0
        phi3 = 0
        phi4 = 0
        phi5 = 0
        phi6 = 0
        phi7 = 0
        phi8 = 0
        dphi1 = int(65535.0/float(self.rate)*float(523.25))
        dphi2 = int(65535.0/float(self.rate)*float(587.33))
        dphi3 = int(65535.0/float(self.rate)*float(659.25))
        dphi4 = int(65535.0/float(self.rate)*float(698.46))
        dphi5 = int(65535.0/float(self.rate)*float(783.99))
        dphi6 = int(65535.0/float(self.rate)*float(880))
        dphi7 = int(65535.0/float(self.rate)*float(987.77))
        dphi8 = int(65535.0/float(self.rate)*float(1046.5))
        sine = self.sine
        dac = self.dac
        while True:
            sig1 = 0
            num = 0
            if (mem32[0x40014000+16*8] >> 17) & 1:
                phi1 = (phi1 + dphi1) & 0xFFFF
                #print(phi >> 6)
                sig1 += sine[phi1 >> 6]
            if (mem32[0x40014000+17*8] >> 17) & 1:
                phi2 = (phi2 + dphi2) & 0xFFFF
                #print(phi >> 6)
                sig1 += sine[phi2 >> 6]
            if (mem32[0x40014000+18*8] >> 17) & 1:
                phi3 = (phi3 + dphi3) & 0xFFFF
                #print(phi >> 6)
                sig1 += sine[phi3 >> 6]
            if (mem32[0x40014000+19*8] >> 17) & 1:
                phi4 = (phi4 + dphi4) & 0xFFFF
                #print(phi >> 6)
                sig1 += sine[phi4 >> 6]
            if (mem32[0x40014000+20*8] >> 17) & 1:
                phi5 = (phi5 + dphi5) & 0xFFFF
                #print(phi >> 6)
                sig1 += sine[phi5 >> 6]
            if (mem32[0x40014000+21*8] >> 17) & 1:
                phi6 = (phi6 + dphi6) & 0xFFFF
                #print(phi >> 6)
                sig1 += sine[phi6 >> 6]
            if (mem32[0x40014000+22*8] >> 17) & 1:
                phi7 = (phi7 + dphi7) & 0xFFFF
                #print(phi >> 6)
                sig1 += sine[phi7 >> 6]
            if (mem32[0x40014000+26*8] >> 17) & 1:
                phi8 = (phi8 + dphi8) & 0xFFFF
                #print(phi >> 6)
                sig1 += sine[phi8 >> 6]
            dac.put(sig1 >> 3)

    @rp2.asm_pio(out_init=(rp2.PIO.OUT_HIGH,)*10, out_shiftdir=rp2.PIO.SHIFT_RIGHT, autopull=True, pull_thresh=10)
    def dacPio():
        out(pins, 10)

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
