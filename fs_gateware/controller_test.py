from migen import *
from dsp import DSPWidths
from controller import ServoController
from adc import ADCParams

iir_params = DSPWidths(data=25, coeff=18, accu=48, adc=16, dac=14, norm_factor=8, coeff_shift=11)
adc_params = ADCParams(out_width=16, channels=2, lanes=4)


class dac_spi_tb(Module):
    def __init__(self):
        self.sdi = Signal(reset=1)
        self.cs = Signal(reset=1)
        self.sclk = Signal(reset=1)
        self.shdn_n = Signal(reset=0)

class adc_spi_tb(Module):
    def __init__(self):
        self.sdi = Signal(reset=1)
        self.cs = Signal(reset=1)
        self.sclk = Signal(reset=1)
        self.shdn_n = Signal(reset=0)

        self.gainx10 = Signal(2, reset=0)
        self.o_data = [Signal((adc_params.out_width, True), reset_less=True) for i in range(adc_params.channels)]



class ControllerSim(ServoController):
    def __init__(self):
        self.iir_p = iir_p = DSPWidths(data=25, coeff=18, accu=48, adc=16, dac=14, norm_factor=8, coeff_shift=11)
        self.adc_p = adc_p = ADCParams(out_width=16, channels=2, lanes=4)

        self.submodules.adc_tb = adc_spi_tb()
        self.submodules.dac_tb = dac_spi_tb()
        
        ServoController.__init__(self, self.dac_tb, self.adc_tb, adc_p, iir_p)

        cd_dac = ClockDomain("dac", reset_less=True)
        self.clock_domains += cd_dac
        cd_dsp4 = ClockDomain("dsp4", reset_less=True)
        self.clock_domains += cd_dsp4


    def test_pid(self):
        iir_p = self.iir_p

        Kp = 2
        Ki = 0
        Kd = 0
        # Ki = 1
        # Kd = 1e-7

        # first samples
        x0 = 3
        x1 = 5
        x2 = 19

        # initialize adc and dac through SPI
        while not (yield self.init.dac_init & self.init.adc_init):
            yield
        
        yield from self.iir.set_pid_coeff(0, Kp, Ki, Kd)
        yield
        yield from self.iir.set_pid_coeff(1, 5, 0, 0)
        yield self.adc_tb.o_data[0].eq(x0)
        yield self.adc_tb.o_data[1].eq(0x0F)
        yield
        yield self.adc_tb.o_data[0].eq(x1)
        yield
        yield self.adc_tb.o_data[0].eq(x2)
        yield
        yield self.adc_tb.o_data[0].eq(0)
        for i in range(15):
            yield

        # try setting dac value skipping IIR output
        yield self.dac_data.eq((0x28FC << 14) | 0x3CFC)
        for i in range(10):
            yield
        # set dac outputs to 0
        yield self.ctrl.dac_clr.eq(1)
        for i in range(10):
            yield
        # try setting dac value skipping IIR output again
        # but set mode register first
        yield self.dac_data.eq((0x28FC << 14) | 0x3CFC)
        yield  self.mode.set_dac.eq(1)
        for i in range(10):
            yield
        yield self.ctrl.dac_clr.eq(1)
        for i in range(6):
            yield
        

    def run(self):
        run_simulation(self, [self.test_pid()],
                vcd_name="pid_test.vcd",
                clocks = {
                    "sys":   (8, 0),
                    "dac":   (4, 0),
                    "dsp4":  (2, 0),
                },
        )


def main():
    pid = ControllerSim()
    pid.run()

if __name__ == "__main__":
    main()

