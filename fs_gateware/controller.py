from migen import *
from dsp import DSPWidths, IIR
from dac import DAC
from adc import ADC

class PID(Module):
    def __init__(self, filter_widths, adc_params, adc_pads, dac_pads):
        for ch in range(2):
            adc = ADC(adc_params, adc_pads)
            setattr(self.submodules, f"adc{ch}", adc)     
        self.submodules.iir = IIR(filter_widths, channels=2)
        self.submodules.dac = DAC()

        self.comb += [
            self.iir.adc[0].eq(self.adc0.o_data),
            self.iir.adc[1].eq(self.adc1.o_data),
            self.dac.idata.eq(self.iir.dac[0]),
            self.dac.qdata.eq(self.iir.dac[1]),
            ]