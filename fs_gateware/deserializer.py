from migen import *

#  There is a need for at least two clock domains in serdes. 
#  On DCO pin ADC sends coming back clock which indicates when the incoming data is valid. It is 2 times faster than 
#  clock sent to the ADC IC. 
#  DCO2D is clock that is two times slower than DCO (the same frequency as the one fed to the ADC). It validates 
#  exiting data from the Serdes module. 

class DeserializerDDR(Module):
    def __init__(self, mode="DDR"):
        self.o_data = Signal(4)
        self.i_sdo = Signal()
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
                i_CLKDIV=ClockSignal("dco2d"), i_RST=ResetSignal("sys"),
                i_CLK=ClockSignal("dco"), i_CLKB=~ClockSignal("dco"),
                i_BITSLIP = self.i_bitslip,
                o_Q1=self.o_data[0],
                o_Q2=self.o_data[1],
                o_Q3=self.o_data[2],
                o_Q4=self.o_data[3]
            )
        ]

if __name__ == "__main__":
    from migen.fhdl.verilog import convert

    m = DeserializerDDR()

    convert(m, {m.i_sdo, m.i_bitslip, m.o_data}, name="deserializer").write("deser_verilog.v")

