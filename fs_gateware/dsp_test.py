from migen import *
from collections import namedtuple
from dsp import DSP, FIR, IIR, DSPWidths

import logging

logger = logging.getLogger(__name__)

filter_params = DSPWidths(data=25, coeff=18, accu=48, adc=16, dac=14, norm_factor=8, coeff_shift=11)


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
    tb = IIR(filter_params, 1)
    cd_dsp4 = ClockDomain("dsp4", reset_less=True)
    tb.clock_domains += cd_dsp4      

    def run(tb):

        dut = tb
        yield
        yield dut.adc[0].eq(-3)
        # yield dut.adc[1].eq(1)
        # yield dut.i_carryin.eq(0)
        # yield from dut.set_iir_coeff("b0", ch0=1, ch1=1)
        # yield from dut.set_iir_coeff("b1", ch0=1, ch1=1)
        # yield from dut.set_iir_coeff("b2", ch0=1, ch1=1)
        yield from dut.set_pid_coeff(Kp = 2, Ki = 2, Kd = 0)
        # yield dut.coeff1.eq(1)
        # yield dut.coeff2.eq(1)
        yield
        # yield dut.mem_b0[0].eq(2)
        yield
        # yield
        yield dut.adc[0].eq(0)
        # yield dut.adc[1].eq(1)
        for i in range (15):
            yield
        yield dut.adc[0].eq(3)
        # yield from dut.set_iir_coeff("b1", ch0=2)
        # yield from dut.set_iir_coeff("b2", ch0=2)
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

class IIRSimulation(IIR):
    def __init__(self):
        self.filter_p = DSPWidths(data=25, coeff=18, accu=48, adc=16, dac=14, norm_factor=8, coeff_shift=11)

        self.submodules.iir  = IIR(self.filter_p, channels=1)
        cd_dsp4 = ClockDomain("dsp4", reset_less=True)
        self.iir.clock_domains += cd_dsp4

    def test (self):
        x0 = -30
        x1 = 16
        x2 = -132
        
        b0 = -2
        b1 = 5
        b2 = 1
        a1 = 1

        ys = list()
        ys.append(b0*x0)
        ys.append(b0*x1 + b1*x0 - a1*ys[0])
        ys.append(b0*x2 + b1*x1 + b2*x0 - a1*ys[1])
        ys.append(b1*x2 + b2*x1 - a1*ys[2])
        ys.append(b2*x2 - a1*ys[3])
        ys.append(- a1*ys[4])

        yield from self.iir.set_iir_coeff("b0", ch0=b0<<self.filter_p.coeff_shift)
        yield from self.iir.set_iir_coeff("b1", ch0=b1<<self.filter_p.coeff_shift)
        yield from self.iir.set_iir_coeff("b2", ch0=b2<<self.filter_p.coeff_shift)
        yield from self.iir.set_iir_coeff("a1", ch0=a1<<self.filter_p.coeff_shift)
        yield self.iir.use_fback.eq(1)
        yield 
        yield self.iir.adc[0].eq(x0)
        yield
        yield self.iir.adc[0].eq(x1)
        yield
        yield self.iir.adc[0].eq(x2)
        yield
        yield self.iir.adc[0].eq(0)
        while not (yield self.iir.dac[0]):
            yield
        for ix, _ in enumerate("y0 y1 y2 y3 y4 y5".split()):
            val = yield from self.iir.get_output(channel=0)
            assert val == ys[ix]
            yield
        yield

    def run(self):
        run_simulation(self, self.test(), vcd_name="fil.vcd",
                clocks={
                    "sys":   (8, 0),
                    "dsp4":   (2, 0),
                })

def main():
    # dsp_test()
    # fir_test()
    # iir_test()
    # feedback_test()

    fil = IIRSimulation()
    fil.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()

