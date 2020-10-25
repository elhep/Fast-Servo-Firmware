from artiq.language.core import kernel, delay, delay_mu, portable
from artiq.language.units import us, ns
from artiq.coredevice.rtio import rtio_output, rtio_input_data
from fs_phy.fastservo import FastServo

class FastServo:
    def __init__(self, dmgr, channel, core_device="core"):
        self.channel = channel << 8
        self.core = dmgr.get(core_device)

    @kernel
    def init(self):
        """Initialize the device.

        Clears reset, unsets DAC_CLR and enables AFE power
        """
        self.set_cfg(reset=0, adc_afe_power_down=0, dac_afe_power_down=0, dac_clr=0)
        delay(1*us)

    @kernel
    def write(self, addr, data):
        """Write data to Fast Servo register
        
        :param addr: Address to write to.
        :param data: Data to write.
        """
        rtio_output(self.channel | addr, data)

    @kernel
    def read(self, addr):
        """Read from Fast Servo register

        :param addr: Address to read from.
        :return: The data read.
        """
        rtio_output(self.channel | addr | 0x80)
        return rtio_input_data(self.channel >> 8)
    
    @kernel
    def set_cfg(self, reset=0, adc_afe_power_down=0, dac_afe_power_down=0, dac_clr=0):
        """Set configuration bits
        
        :param reset: Reset SPI, SPI clock domain, ADC and DAC
        :param adc_afe_power_down: Disable ADC AFE power
        :param dac_afe_power_down: Disable DAC ADE power
        :param dac_clr: Assert both DAC channels setting them to mid-scale (0 V)
        """
        self.wrte(0x00, (reset << 0) | (adc_afe_power_down << 1) | (dac_afe_power_down << 2) | (dac_clr << 3))

    @kernel
    def set_dac_mu(self, dac, value):
        """Set chosen DAC channel to a given value in machine units.
        
        This does not change value from the other channel.
        :param dac: channel number to set.
        :param value: DAC output in machine units
        """
        if dac >= 2:
            raise ValueError("DAC channel must be in range [0:2]")

        self.write(0x03, (dac << 28) | (value << 14*dac_channel))


    @kernel
    def set_dac(self, dac, voltage):
        """Set chosen DAC channel to a given voltage.

        This does not change other channel's value.
        :param dac: channel to set.
        :param voltage: Desired output voltage
        """
        self.set_dac_mu(dac, self.voltage_to_mu(voltage))


    @portable
    def voltage_to_mu(self, voltage):
        """Convert SI Volts to DAC machine units.

        :param voltage: Voltage in SI Volts.
        :return: DAC data word in machine units, 14 bit integer.
        """
        return int(round((0x2000/10.)*voltage)) + 0x2000

    @portable
    def adc_mu_to_volt(self, data, gain=0):
        """Convert data from ADC in machine units to Volts.

        :param data: 16 bit signed ADC word
        :param gain: X10 gain setting (0 - gain disabled, 1 - gain enabled)
        :return: Voltage in Volts
        """
        if gain == 0:
            volts_per_bit = 2./(1<<16)
        elif gain == 1:
            volts_per_bit = .2/(1<<16)
        
        return data*volts_per_bit

    @kernel
    def get_adc_mu(self, adc):
        """Get the latest ADC reading in machine units.

        :param adc: ADC channel number (0-1)
        :return: 16 bit signed ADC output
        """
        mask = 0xFFFF
        return (self.read(0x05) & (mask<<16*adc))

    @kernel
    def get_adc(self, adc, gain):
        """Get the latest ADC reading in Volts.

        :param adc: ADC channel number (0-1)
        :param gain: Whether AFE X10 gain was enabled(1) or not (0)
        :return: ADC voltage
        """
        return self.adc_mu_to_volt(self.get_adc_mu(adc), gain))

    @kernel
    def set_adc_afe_gains(self, enable_adc0=0, enable_adc1=0):
        """Enable or disable X10 ADC AFE gain for each channel.

        :param enable_adc0: Set/clear adc0 AFE gain.
        :param enable_adc1: Set/clear adc1 AFE gain
        """

        self.write(0x02, (enable_adc0 << 0) | (enable_adc1 << 1))
