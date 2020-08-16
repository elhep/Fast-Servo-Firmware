from migen import *
from dsp import DSPWidths, IIR
from dac import DAC
from adc import ADC

class PID(Module):
    def __init__(self, filter_widths):
        # for ch in range(2):
        #     adc = ADC()
        #     setattr(self.submodules, f"adc{ch}", adc)     ## needs improvement and refactor
        self.submodules.iir = IIR(filter_widths, channels=2)
        self.submodules.dac = DAC()

        self.datain0 = Signal(filter_widths.data)
        self.datain1 = Signal(filter_widths.data)

        self.comb += [
            self.iir.adc[0].eq(self.datain0),
            self.iir.adc[1].eq(self.datain1),
            self.dac.idata.eq(self.iir.dac[0]),
            self.dac.qdata.eq(self.iir.dac[1]),
            ]