from migen import *
from collections import namedtuple
from dsp import DSP, FIR, DSPWidths

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


def main():
    dsp_test()
    fir_test()

if __name__ == "__main__":
    main()

