from migen import *
from collections import namedtuple
from adc import ADC, ADCParams
from fs_gateware.deserializer import DeserializerDDR
from fs_gateware.time_mgmt import TimeMGMT
from fs_gateware.bitslip import Bitslip


import logging

logger = logging.getLogger(__name__)

adc_p = ADCParams(out_width=16)

class Deser(Module):
    def __init__(self):
        self.o_data = Signal(4)
        self.i_sdo = Signal()
        self.i_rst = Signal(reset=1)
        self.i_bitslip = Signal()

        self.undertest = Signal()
        self.test_data = Signal((4, True))
        sr = Signal(4)
        cnt = Signal(2)
        cnt_done = Signal()

        ###

        self.comb += cnt_done.eq(cnt==0)
        self.comb += self.o_data.eq(Mux(self.undertest, self.test_data, sr))

        self.sync += [
            If(cnt_done,
                cnt.eq(3)
            ).Else(
                cnt.eq(cnt-1)
            ),
            sr.eq(Cat(self.i_sdo, sr)),
        ]

class TB(Module):
    def __init__(self, params):
        self.params = p = params
        self.o_bitslip = Signal()
        
        for i in "abcd":
            sdo = Signal()
            setattr(self, f"i_sdo{i}", sdo)

        self.o_enc = Signal() # encode signal; 
        self.i_dco = Signal() # incoming clock
        self.i_fr = Signal() # framing signal

        
        for i in "abcd":
            d = Deser()
            setattr(self.submodules, f"deser_{i}", d)
    
    def iter_vals(self, sdoa, sdob, sdoc, sdod):
        for i in range(4):
            yield self.i_sdoa.eq(int(sdoa[i]))
            yield self.i_sdob.eq(int(sdob[i]))
            yield self.i_sdoc.eq(int(sdoc[i]))
            yield self.i_sdod.eq(int(sdod[i]))
            yield

def adc_test():
    tb = TB(adc_p)
    adc = ADC(adc_p, tb)
    tb.submodules += adc
    # cd_dsp4 = ClockDomain("dsp4", reset_less=True)
    # tb.clock_domains += cd_dsp4      

    def run(tb):

        dut = tb
        yield tb.i_sdoa.eq(1)
        yield tb.i_sdob.eq(1)
        yield
        yield tb.i_sdob.eq(0)
        yield tb.i_sdoc.eq(1)
        yield tb.i_sdod.eq(1)
        yield
        yield tb.i_sdoc.eq(0)
        yield
        yield tb.i_sdod.eq(0)
        yield
        yield dut.o_bitslip.eq(1)
        yield
        yield dut.o_bitslip.eq(0)
        for i in range(3):
            yield
        yield dut.o_bitslip.eq(1)
        for i in range(3):
            yield
        yield dut.o_bitslip.eq(0)
        yield
        # yield dut.bitslip_done.eq(1)
        # yield dut.i_start.eq(1)


        yield from dut.iter_vals("{:04b}".format(12), "{:04b}".format(2), "{:04b}".format(1), "{:04b}".format(7))
    run_simulation(tb, run(tb), 
            vcd_name="adc_test.vcd",
            clocks = {
                "sys":   (8, 0),
                # "dsp4":   (2, 0),
            },
        )

def main():
    adc_test()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()