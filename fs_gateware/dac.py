from migen import *
from migen.genlib.io import DifferentialOutput, DifferentialInput, DDROutput


class DAC(Module):
    def __init__(self):

        self.idata = Signal(14)
        self.qdata = Signal(14)

        interleaved_data = Signal(28)
        self.db = Signal(14)

        self.dclkio = Signal()

        self.sync += [
            interleaved_data.eq(Cat(self.qdata, self.idata)),
            ]
        
        self.comb += [
            self.dclkio.eq(ClockSignal("dac")),
            self.db.eq(Mux(ClockSignal("sys"), interleaved_data[:14], interleaved_data[14:]))
        ]
        
    


        

