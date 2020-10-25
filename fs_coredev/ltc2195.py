from artiq.language.core import kernel, delay, portable
from artiq.language.units import ns

from artiq.coredevice import spi2 as spi


SPI_CONFIG = (0*spi.SPI_OFFLINE | 0*spi.SPI_END |
              0*spi.SPI_INPUT | 0*spi.SPI_CS_POLARITY |
              0*spi.SPI_CLK_POLARITY | 0*spi.SPI_CLK_PHASE |
              0*spi.SPI_LSB_FIRST | 0*spi.SPI_HALF_DUPLEX)

SPI_CS = 0


LTC2195_REG_A0 = 0x00   # reset reg
LTC2195_REG_A1 = 0x01   # format and power down reg
LTC2195_REG_A2 = 0x02   # output mode reg
LTC2195_REG_A3 = 0x03   # test pattern high (MSB) reg
LTC2195_REG_A4 = 0x04   # test pattern low (LSB) reg

LTC2195_WRITE = 1<<15
LTC2195_READ = 0 <<15

# COMMANDS

# for RESET REG
LTC2195_RST_CMD = 1<<7

# for FORMAT AND POWR REG
LTC2195_DCSOFF_CMD = 1<<7   # clock duty cycle stabilizer on/off !it uses inverse logic: 1 is OFF while 0 is ON
LTC2195_RAND_CMD = 1<<6
LTC2195_BITMODE_CMD = 1<<5  # set to provide data in two's complement format; clear for offset binary (default)


# Commands for setting output current  in format: LTC2195_{xx}M, where XX means X.X mA output (see data sheet)
# for OUTPUT MODE REGISTER
LTC2195_35M_CMD = 0<<5  # default on reset
LTC2195_40M_CMD = 1<<5
LTC2195_45M_CMD = 2<<5
LTC2195_30M_CMD = 4<<5
LTC2195_25M_CMD = 5<<5
LTC2195_21M_CMD = 6<<5
LTC2195_17M_CMD = 7<<5  # 1.75 mA output

LTC2195_TRM_CMD = 1<<4  #   Internal termination ON/OFF; if ON, LVDS out driver is 2x the value set in the register
LTC2195_OUTOFF_CMD = 1<<3   # Disable digital outputs **Iverse logic**
LTC2195_OUTTST_CMD = 1<<2   # Digital output test patter

#Digital output lane mode
LTC2195_2LANE_CMD = 0
LTC2195_4LANE_CMD = 1
LTC2195_1LANE_CMD = 2


class LTC2195:
    """FastServo main ADC.

    Controls the LTC2195-16 2 channel 16 bit ADC with SPI interface

    :param spi_adc_device: ADC SPI bus device name
    :param div: SPI clock divider (default: 6)
    :param afe_device: AFE
    :param core_device: Core device name
    """
    kernel_invariants = {"bus_adc", "core", "div"}

    def __init__(self, dmgr, spi_adc_device, afe_device, div=6, core_device="core"):
        self.bus_adc = dmgr.get(spi_adc_device)
        self.bus_adc.update_xfer_duration_mu(div, 16)
        self.afe = dmgr.get(afe_device)
        self.core = dmgr.get(core_device)
        self.div = div

    @kernel
    def init(self):
        """Initialize the device.

        Sets up SPI channels, sets bit data format to 2's complement and lane mode to 4 lanes
        """
        self.bus_adc.set_config_mu(SPI_CONFIG | spi.SPI_END, 16, self.div, SPI_CS)
        self.bus_adc.write( LTC2195_WRITE | (LTC2195_REG_A0<<7) | LTC2195_RST_CMD)

        mask = 0xff
        bitmode2 = LTC2195_BITMODE_CMD & mask 
        self.bus_adc.write(LTC2195_WRITE | (LTC2195_REG_A1<<7) | bitmode2)  # 2's complement mode

        lanemode4 = LTC2195_4LANE_CMD & mask
        self.bus_adc.write(LTC2195_WRITE | (LTC2195_REG_A2<<7) | lanemode4) # 4 lanes

    @kernel
    def set_gain(self, channel, afe_gain_en=0):
        """Set main ADC AFE gain of a channel.

        :param channel: Channel index
        :param afe_gain_en: Enables AFE x10 signal amplification
        """
        pass
        
        if afe_gain_en == 0:
            self.afe.channel.off()
        else:
            self.afe.channel.on()



