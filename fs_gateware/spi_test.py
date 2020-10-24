from migen import *
from collections import namedtuple
from fs_gateware.spi import SPI, SPIParams


spi_params = SPIParams(data_width=16, clk_width=3, msb_first=1)

addr = 0xAA<<8
data = 0xFA

class SPISim(Module):
    def __init__(self, params):
        self.params = params
        self.sdi = Signal(reset=1)
        self.cs = Signal(reset=1)
        self.sclk = Signal(reset=1)


def spi_test():

    spiPads = SPISim(spi_params)

    tb = SPI(spiPads, spi_params)
    spiPads.submodules += tb

    def run(tb):
        dut = tb
        yield dut.data.eq((addr | data))
        yield
        yield
        yield
        yield dut.enable.eq(1)
        yield
        yield dut.enable.eq(0)
        
        yield
        while not (yield dut.ready):
            yield
        yield

    run_simulation(tb, run(tb), vcd_name="spi_test.vcd")

if __name__ == "__main__":
    
    spi_test()
