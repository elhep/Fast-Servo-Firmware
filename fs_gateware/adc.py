from collections import namedtuple

from migen import *


ADCParams = namedtuple("ADCParams", [
    "out_width",
])


class ADC(Module):
    def __init__(self, adc_params, pads):
        self.o_data = Signal((adc_params.out_width, True), reset_less=True)
        
        bitslip = Signal()

        self.comb += [
            pads.deser_a.i_sdo.eq(pads.i_sdoa),
            pads.deser_b.i_sdo.eq(pads.i_sdob),
            pads.deser_c.i_sdo.eq(pads.i_sdoc),
            pads.deser_d.i_sdo.eq(pads.i_sdod),

            pads.deser_a.i_bitslip.eq(bitslip),
            pads.deser_b.i_bitslip.eq(bitslip),
            pads.deser_c.i_bitslip.eq(bitslip),
            pads.deser_d.i_bitslip.eq(bitslip),


            bitslip.eq(pads.o_bitslip),

            self.o_data[0:4].eq(pads.deser_a.o_data),
            self.o_data[4:8].eq(pads.deser_b.o_data),
            self.o_data[8:12].eq(pads.deser_c.o_data),
            self.o_data[12:16].eq(pads.deser_d.o_data),

        ]  
