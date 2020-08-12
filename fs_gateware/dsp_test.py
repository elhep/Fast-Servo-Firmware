from migen import *
from collections import namedtuple
from dsp import DSP, FIR, IIR, DSPWidths

import logging

logger = logging.getLogger(__name__)

filter_params = DSPWidths(data=25, coeff=18, out=48)


def dsp_test(double_reg = True):
    tb = DSP(filter_params, double_reg)
    def run(tb):
        dut = tb
        yield dut.data.eq(128)
        yield dut.carryin.eq(20)
        yield dut.coeff.eq(2)
        for i in range (20):
            yield
        yield

    run_simulation(tb, run(tb), vcd_name="dsp_test.vcd")

def fir_test():
    tb = FIR(filter_params, taps=2)
    def run(tb):
        dut = tb

        yield dut.i_data.eq(3)
        yield dut.i_carryin.eq(0)
        yield dut.coeff0.eq(1)
        yield dut.coeff1.eq(1)
        # yield dut.coeff2.eq(1)
        yield
        yield
        # yield
        yield dut.i_data.eq(0)
        for i in range (20):
            yield
        yield

    run_simulation(tb, run(tb), vcd_name="fir_test.vcd")

def feedback_test():
    tb = DSP(filter_params,True, True)
    cd_dsp4 = ClockDomain("dsp4", reset_less=True)
    tb.clock_domains += cd_dsp4
    tb.comb += tb.offset.eq(tb.output)

    def run(tb):
        dut = tb

        yield dut.data.eq(1)
        yield dut.coeff.eq(2)
        yield
        yield dut.data.eq(2)
        yield
        yield dut.data.eq(0)
        for i in range (20):
            yield
        yield

    run_simulation(tb, run(tb), 
            vcd_name="feedback_test.vcd",
            clocks = {
                "sys":   (8, 0),
                "dsp4":   (2, 0),
            },
    )

def iir_test():
    tb = IIR(filter_params, 2)
    cd_dsp4 = ClockDomain("dsp4", reset_less=True)
    tb.clock_domains += cd_dsp4

    def run(tb):

        dut = tb
        yield
        yield dut.adc[0].eq(3)
        yield dut.adc[1].eq(1)
        # yield dut.i_carryin.eq(0)
        yield from dut.set_coeff("b0", ch0=1, ch1=2)
        yield from dut.set_coeff("b1", ch0=1)
        yield from dut.set_coeff("b2", ch0=1)
        # yield dut.coeff1.eq(1)
        # yield dut.coeff2.eq(1)
        yield
        # yield dut.mem_b0[0].eq(2)
        yield
        yield dut.adc[0].eq(0)
        yield dut.adc[1].eq(1)
        for i in range (15):
            yield
        yield dut.adc[0].eq(3)
        yield from dut.set_coeff("b1", ch0=2)
        yield from dut.set_coeff("b2", ch0=2)
        yield
        yield
        yield dut.adc[0].eq(0)
        for i in range(10):
            yield


    run_simulation(tb, run(tb), 
            vcd_name="iir_test.vcd",
            clocks = {
                "sys":   (8, 0),
                "dsp4":   (2, 0),
            },
        )

def main():
    # dsp_test()
    # fir_test()
    iir_test()
    feedback_test()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

