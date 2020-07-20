from migen import *
from migen.genlib import io
from fs_gateware.deserializer import DeserializerDDR
from fs_gateware.time_mgmt import TimeMGMT
from fs_gateware.bitslip import Bitslip



class ADC(Module):
    def __init__(self):
        # self.o_self.done = Signal() 
        self.i_start = Signal()
        self.i_rst = Signal()

        self.o_enc = Signal() # encode signal; 
        self.i_dco = Signal() # incoming clock
        self.i_fr = Signal() # framing signal
        
        for i in "a":
            sdo = Signal()
            setattr(self, f"i_sdo{i}", sdo)

        self.done = Signal()

        self.o_data = Signal(4)
        self.locked = Signal()
        
        frame = Signal(4)
        bitslip = Signal()

        self.submodules.time_mgmt = TimeMGMT()
        self.submodules.bitslip = Bitslip()

        for i in "a":
            setattr(self.submodules, f"deser_{i}", DeserializerDDR())
        

        self.comb += [
            self.deser_a.i_sdo.eq(self.i_sdoa),
            # self.deser_b.i_sdo.eq(self.i_sdob),
            # self.deser_c.i_sdo.eq(self.i_sdoc),
            # self.deser_d.i_sdo.eq(self.i_sdod),

            self.deser_a.i_bitslip.eq(bitslip),
            # self.deser_b.i_bitslip.eq(bitslip),

            self.bitslip.i_fr.eq(self.i_fr),
            bitslip.eq(self.bitslip.o_bitslip),
            self.done.eq(self.bitslip.bitslip_done),

            
            self.deser_a.i_rst.eq(self.i_rst),
            # self.deser_b.i_rst.eq(self.i_rst),
            # self.deser_c.i_rst.eq(self.i_rst),
            # self.deser_d.i_rst.eq(self.i_rst),

            self.bitslip.i_rst.eq(self.i_rst),
            self.bitslip.i_start.eq(self.locked),

            self.o_data[0:4].eq(self.deser_a.o_data),
            # self.o_data[4:8].eq(self.deser_b.o_data),
            # self.o_data[8:12].eq(self.deser_c.o_data),
            # self.o_data[12:16].eq(self.deser_d.o_data),

            # frame.eq(self.bitslip_fsm.o_data),

            self.time_mgmt.i_rst.eq(self.i_rst),
            self.time_mgmt.i_dco.eq(self.i_dco),

            self.locked.eq(self.time_mgmt.mmcm_locked)
        ]  


if __name__ == "__main__":
    from migen.fhdl.verilog import convert
    # plat = kasli.Platform(hw_rev = "v1.1")
    #
    m = ADC()

    convert(m, {m.i_rst, m.i_sdoa,  m.i_dco, m.i_fr, m.o_data, m.done, m.locked}).write("adc.v")
