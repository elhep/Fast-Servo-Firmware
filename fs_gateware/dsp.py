from migen import *
from collections import namedtuple

DSPWidths = namedtuple("DSPWidths", [
    "data",
    "coeff",
    "out",
    ]
)

class DSP(Module):
    def __init__(self, widths, double_registered=False):

        self.data = Signal(widths.data)
        self.coeff = Signal(widths.coeff)
        self.offset = Signal(widths.data)
        self.carryin = Signal(widths.out)

        self.acout = Signal(widths.data)

        self.output = Signal(widths.out)

        a = Signal(widths.data)
        d = Signal(widths.data)
        ad = Signal(widths.data)
        b = Signal(widths.coeff)
        c = Signal(widths.out)
        m = Signal(widths.out)
        p = Signal(widths.out)

        ###
        self.comb += self.acout.eq(ad)
        self.sync += [
            b.eq(self.coeff),

            m.eq(ad*b),
            # self.acout.eq(ad),
            
            self.output.eq(m+self.carryin)
        ]

        if double_registered:
            self.sync += [
                a.eq(self.data),
                d.eq(self.offset),
                ad.eq(a+d)
            ]
        else:
            self.sync += [
                ad.eq(self.data)
            ]

class FIR(Module):
    def __init__(self, widths, taps=3):
        self.i_data = Signal(widths.data)
        self.i_offset = Signal(widths.data)
        self.i_carryin = Signal(widths.out)

        self.acout = Signal(widths.out)
        self.o_out = Signal(widths.out)
        

        for i in range(taps):
            coeff = Signal(widths.coeff)
            if i == 0:
                dsp = DSP(widths, False)
            else:
                dsp = DSP(widths, True)
            setattr(self.submodules, f"dsp{i}", dsp)
            setattr(self, f"coeff{i}", coeff)

        if taps > 1:
            for i in range(taps):
                dsp = getattr(self, f"dsp{i}")
                coeff = getattr(self, f"coeff{i}")
                self.comb += [
                    dsp.offset.eq(self.i_offset),
                    dsp.coeff.eq(coeff)
                ]
                if i == 0:
                    self.comb += dsp.data.eq(self.i_data), dsp.carryin.eq(self.i_carryin)
                elif i == taps-1:
                    dsp_prev = getattr(self, f"dsp{i-1}")
                    self.comb += [
                        self.o_out.eq(dsp.output), 
                        self.acout.eq(dsp.acout),
                        dsp.carryin.eq(dsp_prev.output),
                        dsp.data.eq(dsp_prev.acout)
                    ]
                else:
                    dsp_prev = getattr(self, f"dsp{i-1}")
                    self.comb += [
                        dsp.data.eq(dsp_prev.acout),
                        dsp.carryin.eq(dsp_prev.output)
                    ]
        else:
            dsp = getattr(self, "dsp0")
            coeff = getattr(self, "coeff0")
            self.comb += [
                dsp.data.eq(self.i_data),
                dsp.offset.eq(self.i_offset),
                dsp.coeff.eq(coeff),
                self.o_out.eq(dsp.output)
            ]


class IIR(Module):
    def __init__(self, widths):
        self.i_data = Signal(widths.data)
        self.i_offset = Signal(widths.data)

        self.o_out = Signal(widths.out)

        self.submodules.fir += FIR(widths)
        self.submodules.feedback += DSP(widths, True)


        ### 
        
        self.comb += [
            self.fir.i_data.eq(self.i_data),
            self.fir.i_offset.eq(self.i_offset),
            self.fir.i_carryin.eq(0),

            self.feedback.data.eq(self.fir.o_out),
            self.feedback.offset.eq(self.feedback.output),
            self.feedback.coeff.eq()

            self.o_out.eq(self.feedback.output)
        ]
