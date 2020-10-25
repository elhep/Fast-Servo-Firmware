from migen import *

from artiq.gateware.rtio import rtlink

class FastServo(Module):
    def __init__(self, servo):
        self.rtlink = rtlink.Interface(
            rtlink.OInterface(data_width=32, address_width=8,
                enable_replace=False),
            rtlink.IInterface(data_width=32))
        
        ###
        
        # reg addresses - starts with R/!W
        cases = {
            # control/config reg - rst, afe, dac_clr
            0x00: servo.ctrl[:4].eq(self.rtlink.o.data),
            # enable channels
            0x01: servo.ctrl[4:6].eq(self.rtlink.o.data),
            # enable ADC AFE X10 gain
            0x02: servo.ctrl[6:].eq(self.rtlink.o.data),
            # set dac
            0x03: servo.mode.eq(self.rtlink.o.data[-2:]), servo.dac_data.eq(self.rtlink.o.data[:-2])
            # init/status reg
            0x04: servo.init,
            # adc data
            0x05: servo.adc_data,
        }


        input_data = Signal(32, reset_less=True)

        self.sync.rio_phy += [
            If(self.rtlink.o.stb & ~self.rtlink.o.address[-1],
                Case(self.rtlink.o.address[:-1], cases)
            ),
            If(self.rtlink.i.stb,
                input_data.eq(Case(self.rtlink.o.address[:-1], cases))
            )
        ]

        self.comb += [
            self.rtlink.i.stb.eq(self.rtlink.o.stb & self.rtlink.o.address[-1]),
            self.rtlink.i.data.eq(input_data),
        ]

