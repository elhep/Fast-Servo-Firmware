from migen import *
from collections import namedtuple
import logging

logger = logging.getLogger(__name__)

CLK_PERIOD = 8e-9

DSPWidths = namedtuple("DSPWidths", [
    "data",         # data width, signed (25 bits)
    "coeff",        # coefficient width, signed (18 bits)
    "accu",         # accumulator width, signed (48 bits)
    "adc",          # adc data width, signed (16 bits)
    "dac",          # dac data width, signed (14 bits)
    "norm_factor",  # normalization factor of sampled data
    "coeff_shift",  # coefficients normalization factor
    ]
)

class DSP(Module):
    def __init__(self, widths, double_registered=False, feedback = False):

        self.data = Signal((widths.data, True))
        self.coeff = Signal((widths.coeff, True))
        self.offset = Signal((widths.data, True))
        self.carryin = Signal((widths.accu, True))

        self.acout = Signal((widths.data, True))

        self.output = Signal((widths.data, True))
        self.pcout = Signal((widths.accu, True))

        a = Signal((widths.data, True))
        d = Signal((widths.data, True))
        ad = Signal((widths.data, True))
        b = Signal((widths.coeff, True))
        c = Signal((widths.accu, True))
        m = Signal((widths.accu, True))
        p = Signal((widths.accu, True))

        ###
        self.comb += self.acout.eq(ad),

        # bit layout (MSB to LSB)
        # sign | guard bits | GB + data | shift
        #  1   |      4     |  7 +  25  |   11
        # DSP guard bits + first actual data bit (sign bit)
        guard_bits = widths.accu - widths.coeff_shift - widths.data + 3 + 1
        pout_guard_bits = 4

        self.underflow = Signal()
        self.overflow = Signal()
        self.clip = Signal()
        self.pcout_clip = Signal()

        # if underflow or overflow occurrs, data is clipped: widths.shift+widths.data LSB remain
        # output is shifted by the widths.shift normalization factor, whereas pcout is not - it is 
        # used when providing data to another DSP slices
        self.comb += [
            self.clip.eq(p[-guard_bits:] != Replicate(p[-1], guard_bits)),
            self.output.eq(Mux(self.clip, 
                    Cat(Replicate(~p[-1], widths.data - 3 - 1), Replicate(p[-1], 4)),
                    p[widths.coeff_shift:])),
            self.pcout_clip.eq(p[-pout_guard_bits:] != Replicate(p[-1], pout_guard_bits)),
            self.pcout.eq(Mux(self.pcout_clip, 
                    Cat(Replicate(~p[-1], widths.accu - 1), p[-1]), p)),
            
            If (self.clip,
                If(~p[-1],
                    self.overflow.eq(1)
                ).Else(
                    self.underflow.eq(1)
                )
            )
        ]

        # new clock domain - to provide IIR calculations in the feedback path, they have to be performed
        # four times faster than general system clock
        if feedback:
            self.sync.dsp4 += [
                b.eq(self.coeff),
                m.eq(ad*b),
            ]
            self.sync += p.eq(m)

            if double_registered:
                self.sync.dsp4 += [
                    a.eq(self.data),
                    d.eq(self.offset),
                    ad.eq(a-d)
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
                p.eq(m+self.carryin)
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
        self.i_carryin = Signal((widths.accu, True))

        self.acout = Signal((widths.data, True))
        self.o_out = Signal((widths.data, True))
        

        # creating taps amount of DSP slices
        for i in range(taps):
            coeff = Signal(widths.coeff)
            if i == 0:
                dsp = DSP(widths, False)
            else:
                dsp = DSP(widths, True)
            setattr(self.submodules, f"dsp{i}", dsp)
            setattr(self, f"coeff{i}", coeff)

        # connecting outputs and inputs properly - previous output to current input
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
                        dsp.carryin.eq(dsp_prev.pcout),
                        dsp.data.eq(dsp_prev.acout)
                    ]
                else:
                    dsp_prev = getattr(self, f"dsp{i-1}")
                    self.comb += [
                        dsp.data.eq(dsp_prev.acout),
                        dsp.carryin.eq(dsp_prev.pcout)
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
        self.channels = channels
        self.adc = [Signal((widths.adc, True), reset_less=True) for ch in range (channels)]

        self.i_offset = Signal((widths.data, True))

        self.iir_out = [Signal((widths.data, True), reset_less=True) for ch in range (channels)]
        self.dac = [Signal((widths.dac, True), reset_less=True) for ch in range (channels)]

        self.use_fback = [Signal(reset_less=True) for ch in range(channels)]

        # self.dac_clip = [Signal() for ch in range(channels)]

        mem_ports = dict()

        for ch in range(channels):
            f = FIR(widths)
            setattr(self.submodules, f"fir{ch}", f)
            
            d = DSP(widths, True, True)
            setattr(self.submodules, f"feedback{ch}", d)
            

        # BRAMs to store coefficients
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

                feedback.data.eq(fir.o_out),
                feedback.offset.eq(feedback.output),

                self.iir_out[ch].eq(Mux(self.use_fback[ch], 
                            feedback.output,
                            fir.o_out)),
                self.dac[ch].eq(self.iir_out[ch][widths.norm_factor:])
            ]

            # # output from DSP is 25 bits wide whereas DAC accepts only 14 bits
            # # iir_out bit layout (MSB-LSB):
            # # |     n_sign        |
            # # | sign | guard bits | widths.dac | widths.norm factor |
            # # |   1  |      2     |     14     |        8           |
            # n_sign = widths.data - widths.dac - widths.norm_factor + 1

            # self.comb += [
            #     self.dac_clip[ch].eq(self.iir_out[ch][-n_sign:] != Replicate(self.iir_out[ch][-1], n_sign)),
            #     self.dac[ch].eq(Mux(self.dac_clip[ch],
            #                 Cat(Replicate(~self.iir_out[ch][-1], widths.dac - 1), self.iir_out[ch][-1]), 
            #                 self.iir_out[ch][widths.norm_factor:]))
            # ]

    def get_coeff(self, coeff):
        w = self.widths
        mem = getattr(self, f"mem_{coeff}")
        word = yield mem[0]
        return word

    def get_output(self, channel):
        w = self.widths
        assert channel <= self.channels
        value = yield self.dac[channel]
        return value


    def fmt_word(self, mem_word, coeff, **kwargs):
        assert coeff in "a1 b0 b1 b2".split()
        assert (len(kwargs)>0 & (len(kwargs)<=2))
        assert [ch in "ch0 ch1".split() for ch in kwargs.keys()]
        w = self.widths

        mask = (1<<w.coeff)-1

        if "ch1" not in kwargs.keys():
            mask = mask<<w.coeff
            word = (kwargs["ch0"])
            if word < 0:
                word = ((1<<w.coeff) -1) + word
        elif "ch0" not in kwargs.keys():
            mask = ((0<<w.coeff) | mask)
            word = kwargs["ch1"]
            if word < 0:
                word = ((1<<w.coeff) - 1) + word
            word = word<<w.coeff
        else:
            mask = 0<<2*w.coeff
            temp = dict()
            for key, val in kwargs.items():
                if val < 0:
                    temp[key] = ((1<<w.coeff) -1) + val
                else:
                    temp[key] = val

            logger.debug("Mask: {:036b}".format(mask))
            word = ((temp["ch1"]<<w.coeff) | temp["ch0"])
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


    def set_pid_coeff(self, ch, Kp, Ki, Kd):
        w = self.widths
        a_norm = 1 <<(w.coeff_shift -1)
        coeff_norm = 1<<w.coeff_shift
        max_coeff = 1<<w.coeff-1
        Kp *= coeff_norm
        if Ki == 0. and Kd == 0.:
            # pure P
            a1 = 0
            b1 = 0
            b0 = int(round(Kp))
            b2 = 0
            logger.debug(f"Pure P: a1 -> {a1}, b0 -> {b0}, b1 -> {b1}, b2 -> {b2}")
            yield self.use_fback[ch].eq(0)

        elif Kd == 0.:
            # I or PI
            # CLK_PERIOD = 30e-6
            Ki *= coeff_norm*CLK_PERIOD/2.
            print(coeff_norm)
            print(Ki)
            c = 1.
            a1 = a_norm
            b0 = int(round(Kp + Ki*c))
            b1 = int(round(Kp + (Ki - 2.*Kp)*c))
            b2 = 0
            logger.debug(f"PI: a1 -> {a1}, b0 -> {b0}, b1 -> {b1}, b2 -> {b2}")
            yield self.use_fback[ch].eq(1)

            # if b1 == -b0:
            #     raise ValueError("low integrator gain and/or gain limit")

        elif Ki==0. and Kd!=0.:
            # D or PD
            Kd *= coeff_norm/CLK_PERIOD
            c = 1.
            a1 = int(round((2.*c - 1.)*(a_norm)))
            b0 = int(round(Kp*c + Kd*c))
            b1 = int(round((- Kp*c - 2*Kd)*c))
            b2 = int(round(Kd*c))
            logger.debug(f"PD: a1 -> {a1}, b0 -> {b0}, b1 -> {b1}, b2 -> {b2}")
            yield self.use_fback[ch].eq(0)

        else:
            # PID
            Ki *= coeff_norm*CLK_PERIOD/2.
            Kd *= coeff_norm/CLK_PERIOD
            c = 1.
            a1 = int(round((2.*c - 1.)*(a_norm)))
            b0 = int(round(Kp + Ki*c + Kd))
            b1 = int(round((Ki*c - Kp*c - 2*Kd)*c))
            b2 = int(round(Kd))

            logger.debug(f"PID: a1 -> {a1}, b0 -> {b0}, b1 -> {b1}, b2 -> {b2}")
            yield self.use_fback[ch].eq(1)
        

        if (b0 >= max_coeff or b0 < -max_coeff or
                b1 >= max_coeff or b1 < -max_coeff or
                b2 >= max_coeff or b2 < -max_coeff):
            logger.debug(f"max_coeff {max_coeff} b0 {b0} b1 {b1} b2 {b2}")
            raise ValueError("high gains")
        if ch==0:
            yield from self.set_iir_coeff("a1", ch0=a1)

            yield from self.set_iir_coeff("b0", ch0=b0)
            yield from self.set_iir_coeff("b1", ch0=b1)
            yield from self.set_iir_coeff("b2", ch0=b2)
        elif ch==1:
            yield from self.set_iir_coeff("a1", ch1=a1)

            yield from self.set_iir_coeff("b0", ch1=b0)
            yield from self.set_iir_coeff("b1", ch1=b1)
            yield from self.set_iir_coeff("b2", ch1=b2)

