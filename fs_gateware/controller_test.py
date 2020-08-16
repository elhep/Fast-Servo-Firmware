from migen import *
from dsp import DSPWidths
from controller import PID

filter_params = DSPWidths(data=25, coeff=18, out=48)


def pid_test():
    tb = PID(filter_params)
    cd_dac = ClockDomain("dac", reset_less=True)
    tb.clock_domains += cd_dac
    cd_dsp4 = ClockDomain("dsp4", reset_less=True)
    tb.clock_domains += cd_dsp4


    def run(tb):
        dut = tb

        yield dut.datain0.eq(3)
        yield dut.datain1.eq(1)
        yield from dut.iir.set_coeff("b0", ch0=1, ch1=2)
        yield from dut.iir.set_coeff("b1", ch0=1)
        yield from dut.iir.set_coeff("b2", ch0=1)
        yield
        yield
        yield dut.datain0.eq(0)
        for i in range (5):
            yield
        yield dut.datain0.eq(3)
        yield from dut.iir.set_coeff("b0", ch0=2, ch1=2)
        yield from dut.iir.set_coeff("b1", ch0=3)
        yield from dut.iir.set_coeff("b2", ch0=3)
        yield
        yield
        yield dut.datain0.eq(0)
        for i in range(10):
            yield


    run_simulation(tb, [run(tb)],
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

