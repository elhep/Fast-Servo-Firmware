from migen import *
from collections import namedtuple
import logging

logger = logging.getLogger(__name__)

DSPWidths = namedtuple("DSPWidths", [
    "data",
    "coeff",
    "out",
    "adc",
    "dac",
    "norm_factor",
    "coeff_shift",
    ]
)

class DSP(Module):
    def __init__(self, widths, double_registered=False, feedback = False):

        self.data = Signal((widths.data, True))
        self.coeff = Signal((widths.coeff, True))
        self.offset = Signal((widths.data, True))
        self.carryin = Signal((widths.out, True))

        self.acout = Signal((widths.data, True))

        self.output = Signal((widths.out, True))

        a = Signal((widths.data, True))
        d = Signal((widths.data, True))
        ad = Signal((widths.data, True))
        b = Signal((widths.coeff, True))
        c = Signal((widths.out, True))
        m = Signal((widths.out, True))
        p = Signal((widths.out, True))

        ###
        self.comb += self.acout.eq(ad), p.eq(m>>(12))

        if feedback:
            self.sync.dsp4 += [
                b.eq(self.coeff),
                m.eq(ad*b),
            ]
            self.sync += self.output.eq(m)

            if double_registered:
                self.sync.dsp4 += [
                    a.eq(self.data),
                    d.eq(self.offset),
                    ad.eq(a+d)
                ]
            else:
                self.sync.dsp4 += [
                    ad.eq(self.data)
                ]

        else:
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
        self.i_data = Signal((widths.data, True))
        self.i_offset = Signal((widths.data, True))
        self.i_carryin = Signal((widths.out, True))

        self.acout = Signal((widths.out, True))
        self.o_out = Signal((widths.out, True))
        

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
    def __init__(self, widths, channels=2):
        self.widths = widths
        self.adc = [Signal((widths.adc, True), reset_less=True) for ch in range (channels)]

        self.i_offset = Signal((widths.data, True))

        self.dac = [Signal((widths.dac, True), reset_less=True) for ch in range (channels)]

        mem_ports = dict()

        for ch in range(channels):
            f = FIR(widths)
            setattr(self.submodules, f"fir{ch}", f)
            
            d = DSP(widths, True, True)
            setattr(self.submodules, f"feedback{ch}", d)
            

        for _ in "a1 b0 b1 b2".split():
            m = Memory(width=channels*widths.coeff, depth=2)
            setattr(self.specials, f"mem_{_}", m)
            port = getattr(self, f"mem_{_}").get_port()
            self.specials += port
            mem_ports[_] = port


        ### 

        for ch in range(channels):
            fir = getattr(self, f"fir{ch}")
            feedback = getattr(self, f"feedback{ch}")

            self.comb += [
                fir.i_data.eq(self.adc[ch]<<widths.norm_factor),
                fir.i_offset.eq(self.i_offset),
                fir.i_carryin.eq(0),

                fir.coeff0.eq(mem_ports["b0"].dat_r[ch*widths.coeff:(ch+1)*widths.coeff]),
                fir.coeff1.eq(mem_ports["b1"].dat_r[ch*widths.coeff:(ch+1)*widths.coeff]),
                fir.coeff2.eq(mem_ports["b2"].dat_r[ch*widths.coeff:(ch+1)*widths.coeff]),

                feedback.coeff.eq(mem_ports["a1"].dat_r[ch*widths.coeff:(ch+1)*widths.coeff]),

                feedback.data.eq((fir.o_out>>(widths.norm_factor+widths.coeff_shift))[:widths.data]),
                feedback.offset.eq(-(feedback.output>>widths.coeff_shift)[:widths.data]),
                feedback.coeff.eq(1<<(widths.coeff_shift)),

                self.dac[ch].eq((feedback.output>>widths.coeff_shift)[:widths.dac])
            ]

    def get_coeff(self, coeff):
        w = self.widths
        mem = getattr(self, f"mem_{coeff}")
        word = yield mem[0]
        return word

    def fmt_word(self, mem_word, coeff, **kwargs):
        assert coeff in "a1 b0 b1 b2".split()
        assert (len(kwargs)>0 & (len(kwargs)<=2))
        assert [ch in "ch0 ch1".split() for ch in kwargs.keys()]
        w = self.widths

        mask = (1<<w.coeff)-1

        if "ch1" not in kwargs.keys():
            mask = mask<<w.coeff
            word = (kwargs["ch0"])
        elif "ch0" not in kwargs.keys():
            mask = ((0<<w.coeff) | mask)
            word = (kwargs["ch1"]<<w.coeff)
        else:
            mask = 0<<2*w.coeff
            logger.debug("Mask: {:036b}".format(mask))
            word = ((kwargs["ch1"]<<w.coeff) | kwargs["ch0"])

        logger.debug("Mask: {:036b}".format(mask))
        logger.debug("Word: {:036b}".format(word))

        word = ((mem_word & mask) | word)
        logger.debug("Formatted word: {:036b}".format(word))
        
        return word
    
    def set_iir_coeff(self, coeff, **kwargs):
        assert coeff in "a1 b0 b1 b2".split()
        assert [ch in "ch0 ch1".split() for ch in kwargs.keys()]

        mem = getattr(self, f"mem_{coeff}")
        mem_word = yield mem[0]
        logger.debug("Word from memory: {:036b}".format(mem_word))

        ch_word = self.fmt_word(mem_word, coeff, **kwargs)
        yield mem[0].eq(ch_word)


    def set_pid_coeff(self, Kp, Ki, Kd):
        w = self.widths
        coeff_norm = 1<<w.coeff_shift

        Kp *= coeff_norm
        if Ki == 0. and Kd == 0.:
            # pure P
            a1 = 0
            b1 = 0
            b0 = int(round(Kp))
            b2 = 0

        else:
            Ki *= coeff_norm*8e-9/2.
            Kd *= coeff_norm/8e-9
            c = 1.
            a1 = int(round((2.*c - 1.)*coeff_norm))
            b0 = int(round(Kp*c + Ki*c + Kd))
            b1 = int(round((Ki*c - Kp*c - 2*Kd)*c))
            b2 = int(round(Kd))
        
        yield from self.set_iir_coeff("a1", ch0=b0)

        yield from self.set_iir_coeff("b0", ch0=b0)
        yield from self.set_iir_coeff("b1", ch0=b1)
        yield from self.set_iir_coeff("b2", ch0=b2)
