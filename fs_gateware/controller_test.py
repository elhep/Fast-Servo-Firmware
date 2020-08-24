from migen import *
from dsp import DSPWidths
from controller import PID

import logging

logger = logging.getLogger(__name__)

filter_p = DSPWidths(data=25, coeff=18, accu=48, adc=16, dac=14, norm_factor=8, coeff_shift=11)


def pid_test():
    tb = PID(filter_p)
    cd_dac = ClockDomain("dac", reset_less=True)
    tb.clock_domains += cd_dac
    cd_dsp4 = ClockDomain("dsp4", reset_less=True)
    tb.clock_domains += cd_dsp4

    def test(dut):
        x0 = -3
        x1 = 6
        x2 = -10
        
        b0 = -2
        b1 = 3
        b2 = 1
        a1 = 1

        x3 = 1
        x4 = -2
        x5 = 17


        ys = dict()
        ys["ch0"] = list()
        ys["ch0"].append(b0*x0)
        ys["ch0"].append(b0*x1 + b1*x0 - a1*ys["ch0"][0])
        ys["ch0"].append(b0*x2 + b1*x1 + b2*x0 - a1*ys["ch0"][1])
        ys["ch0"].append(b1*x2 + b2*x1 - a1*ys["ch0"][2])
        ys["ch0"].append(b2*x2 - a1*ys["ch0"][3])
        ys["ch0"].append(- a1*ys["ch0"][4])

        ys["ch1"] = list()
        ys["ch1"].append(b0*x3)
        ys["ch1"].append(b0*x4 + b1*x3 - a1*ys["ch1"][0])
        ys["ch1"].append(b0*x5 + b1*x4 + b2*x3 - a1*ys["ch1"][1])
        ys["ch1"].append(b1*x5 + b2*x4 - a1*ys["ch1"][2])
        ys["ch1"].append(b2*x5- a1*ys["ch1"][3])
        ys["ch1"].append(- a1*ys["ch1"][4])

        yield from dut.iir.set_iir_coeff("b0", ch0=b0<<filter_p.coeff_shift)
        yield from dut.iir.set_iir_coeff("b1", ch0=b1<<filter_p.coeff_shift)
        yield from dut.iir.set_iir_coeff("b2", ch0=b2<<filter_p.coeff_shift)
        yield from dut.iir.set_iir_coeff("a1", ch0=a1<<filter_p.coeff_shift)

        yield
        
        yield from dut.iir.set_iir_coeff("b0", ch1=b0<<filter_p.coeff_shift)
        yield from dut.iir.set_iir_coeff("b1", ch1=b1<<filter_p.coeff_shift)
        yield from dut.iir.set_iir_coeff("b2", ch1=b2<<filter_p.coeff_shift)
        yield from dut.iir.set_iir_coeff("a1", ch1=a1<<filter_p.coeff_shift)

        yield dut.iir.use_fback.eq(1)
        yield 
        yield dut.datain1.eq(x3)
        yield dut.datain0.eq(x0)
        yield
        yield dut.datain1.eq(x4)
        yield dut.datain0.eq(x1)
        yield
        yield dut.datain1.eq(x5)
        yield dut.datain0.eq(x2)
        yield
        yield dut.datain1.eq(0)
        yield dut.datain0.eq(0)
        while not (yield dut.iir.dac[0]):
            yield
        for ix, _ in enumerate("y0 y1 y2 y3 y4 y5".split()):
            val0 = yield from dut.iir.get_output(channel=0)
            assert val0 == ys["ch0"][ix]
            val1 = yield from dut.iir.get_output(channel=1)
            assert val1 ==ys["ch1"][ix]
            yield
        yield
        for i in range(10):
            yield



        print(ys)
        
    run_simulation(tb, [test(tb)],
            vcd_name="pid_test.vcd",
            clocks = {
                "sys":   (8, 0),
                "dac":   (4, 0),
                "dsp4":  (2, 0),
            },
    )

def main():
    pid_test()

if __name__ == "__main__":
    main()

