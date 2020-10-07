from migen import *
from fs_gateware.deserializer import DeserializerDDR

class Bitslip(Module):
    def __init__(self):
        self.i = Signal()
        self.o_bitslip = Signal()

        self.bitslip_done = Signal()
    

        frame_buffer = Signal(4)

        bitslip = Signal()

        i = self.i

        self.submodules.deser = DeserializerDDR(mode="DDR")

        ###

        bitslip_state = Signal()
        cnt = Signal(max=3)
        bitslip_cnt = Signal(max=3, reset=3)
        
        self.sync.dco2d += [
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
        ]

        self.sync.dco2d += [
            If(bitslip_cnt != 0,
                If(bitslip,
                    bitslip_cnt.eq(bitslip_cnt - 1)
                )
            )
        ]
        
        self.comb += [
            self.deser.i_sdo.eq(self.i),
            self.deser.i_bitslip.eq(bitslip),
            self.o_bitslip.eq(bitslip),
            self.bitslip_done.eq(bitslip_cnt == 0),

            frame_buffer.eq(self.deser.o_data),
        ]


if __name__ == "__main__":
    from migen.fhdl.verilog import convert
    m = Bitslip()

    convert(m, {m.i, m.o_bitslip}, name="bitslip").write("fs_gateware/tbSrc/bitslip_verilog.v")


