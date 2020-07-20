from migen import *

#  There is a need for at least two clock domains in serdes. 
#  On DCO pin ADC sends coming back clock on wich the data is valid. It is 200 MHz or 250 Mhz
#  DDR serdes needs 2 times faster and 2 times sloer clock (in case of 1:4 deserialization) - 
#  clk2d is when the data is valid on the SERDES output and cl is faster clock  for DDR application

class DeserializerDDR(Module):
    def __init__(self, mode="DDR"):
        self.o_data = Signal(4)
        self.i_sdo = Signal()
        self.i_rst = Signal(reset=1)
        self.i_bitslip = Signal()

        ###

        self.specials += [
            Instance("ISERDESE2",
                p_DATA_WIDTH=4, 
                p_DATA_RATE=mode,
                p_SERDES_MODE="MASTER",
                p_INTERFACE_TYPE="NETWORKING",
                p_NUM_CE=1,

                i_CE1=1,
                i_D = self.i_sdo,
                i_CLKDIV=ClockSignal("dco2d"), i_RST=self.i_rst,
                i_CLK=ClockSignal("dco"), i_CLKB=~ClockSignal("dco"),
                i_BITSLIP = self.i_bitslip,
                o_Q1=self.o_data[0],
                o_Q2=self.o_data[1],
                o_Q3=self.o_data[2],
                o_Q4=self.o_data[3]
            )
        ]

if __name__ == "__main__":
    from migen.build.platforms.sinara import kasli
    plat = kasli.Platform(hw_rev = "v1.1")
    #
    m = DeserializerDDR()

    plat.build(m, run = True, build_dir = "deser")
