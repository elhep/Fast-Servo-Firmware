from migen import *

class Bitslip(Module):
    def __init__(self):
        self.i_fr = Signal()
        self.i_rst = Signal()
        self.o_bitslip = Signal()

        self.i_start = Signal()
        self.bitslip_done = Signal()
    

        frame_buffer = Signal(4)

        bitslip = Signal()

        self.specials += [
            Instance("ISERDESE2",
                p_DATA_WIDTH=4, 
                p_DATA_RATE="DDR",
                p_SERDES_MODE="MASTER",
                p_INTERFACE_TYPE="NETWORKING",
                p_NUM_CE=1,

                i_CE1=1,
                i_D = self.i_fr,
                i_CLKDIV=ClockSignal("dco2d"), i_RST=self.i_rst,
                i_CLK=ClockSignal("dco"), i_CLKB=~ClockSignal("dco"),
                i_BITSLIP = bitslip,
                o_Q1=frame_buffer[0],
                o_Q2=frame_buffer[1],
                o_Q3=frame_buffer[2],
                o_Q4=frame_buffer[3]
            )
        ]

        ###

        bitslip_state = Signal()
        cnt = Signal(max=3)
        bitslip_cnt = Signal(max=3, reset=3)
        self.sync.dco2d += [
            If(self.i_start,
                If(bitslip_state == 0,
                    If(frame_buffer!=0b1100,
                        bitslip.eq(1),
                        bitslip_state.eq(1),
                        cnt.eq(2)
                    )
                ).Else(
                    bitslip.eq(0),
                    If(cnt==0,
                        bitslip_state.eq(0),
                    ).Else(
                        cnt.eq(cnt - 1)
                    )
                )
            )
        ]

        self.sync.dco2d += [
            If(bitslip_cnt != 0,
                If(bitslip,
                    bitslip_cnt.eq(bitslip_cnt - 1)
                )
            )
        ]
        
        self.comb += self.o_bitslip.eq(bitslip), self.bitslip_done.eq(bitslip_cnt == 0)

if __name__ == "__main__":
    from migen.fhdl.verilog import convert
    # plat = kasli.Platform(hw_rev = "v1.1")
    #
    m = Bitslip_FSM()

    convert(m, {m.i_fr, m.i_rst, m.o_bitslip}, name="bitslip").write("bitslip.v")


