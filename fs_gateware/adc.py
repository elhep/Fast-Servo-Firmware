from collections import namedtuple

from migen import *
from fs_gateware.deserializer import DeserializerDDR
from fs_gateware.bitslip import Bitslip


ADCParams = namedtuple("ADCParams", [
    "out_width",
    "channels",
    "lanes",
])

class ADCDeserializer(Module):
    def __init__(self, adc_params):
        self.params = p = adc_params
        self.i_sdo_vector = Signal(p.lanes)
        self.i_bitslip = Signal()
        
        self.ch_data = Signal((p.out_width, True), reset_less=True)

        assert p.lanes in [1, 2, 4]  # allowed values for data lanes

        # create a deserializer module for each data lane
        # and assign their bitslip port to an external bitslip signal
        for i, letter in enumerate("abcd"[0:p.lanes]):
            setattr(self.submodules, f"deser_{letter}", DeserializerDDR(mode="DDR"))
            deserializer = getattr(self, f"deser_{letter}")
            self.comb += [
                deserializer.i_sdo.eq(self.i_sdo_vector[i]),    # 0,1,2,3 => a,b,c,d
                deserializer.i_bitslip.eq(self.i_bitslip),
                self.ch_data[i*4:i*4+4].eq(deserializer.o_data)     # TODO: proper support for other numbers of data lanes
            ]


class ADC(Module):
    def __init__(self, adc_params, pads):
        self.params = p = adc_params
        self.o_data = [Signal((p.out_width, True), reset_less=True) for i in range(p.channels)]
        
        bitslip = Signal()

        # bitslip state machine and its deserializer module
        self.submodules.bitslipFSM = Bitslip()

        # adc deserializers
        adcs = []
        for ch in range(p.channels):
            setattr(self.submodules, f"adc_{ch}", ADCDeserializer(p))
            adcs.append(getattr(self, f"adc_{ch}"))

    
        ###

        # feed i_frame signal to the Bitslip module
        self.comb += [
            self.bitslipFSM.i.eq(pads.i_frame),
            bitslip.eq(self.bitslipFSM.o_bitslip),
        ]

        for ix, adcSub in enumerate(adcs):
            self.comb += [
                adcSub.i_bitslip.eq(bitslip),
                adcSub.i_sdo_vector.eq(pads.sdos[ix]),
                self.o_data[ix].eq(adcSub.ch_data)
            ]
