from migen import *
from collections import namedtuple
from dac import DAC



def dac_test():
    tb = DAC()
    cd_dac = ClockDomain("dac", reset_less=True)
    tb.clock_domains += cd_dac

    def run(tb):
        ida = 0x28FC
        qda = 0x3CFC
        dut = tb
        for i in range(12):
            yield dut.idata.eq(ida)
            yield dut.qdata.eq(qda)
            yield
            yield dut.idata.eq(ida + 10)
            yield dut.qdata.eq(qda - 20)
            yield
            yield dut.idata.eq(ida + 20)
            yield dut.qdata.eq(qda - 30)
            yield
        for i in range(20):
            yield
    
    run_simulation(tb, run(tb), 
            vcd_name="dac_test.vcd",
            clocks = {
                "sys":   (8, 0),
                "dac":   (4, 0),
            },
        )



def main():
    dac_test()

if __name__ == "__main__":
    main()