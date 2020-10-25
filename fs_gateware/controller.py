from collections import namedtuple

from migen import *
from fs_gateware.adc import ADC, ADCParams
from fs_gateware.dac import DAC
from fs_gateware.dsp import IIR, DSPWidths
from fs_gateware.spi import SPI, SPIParams


class ServoController(Module):
    def __init__(self, dac_pads, adc_pads, adc_params, iir_params):
        self.iir_params = iir_p = iir_params
        self.adc_params = adc_p = adc_params

        self.spi_params = spi_p = SPIParams(data_width=16, clk_width=3, msb_first=1)    # 3 cycles * 8 ns = 24ns <- half cycle of SPI

        # 0x00-0x02
        self.ctrl = Record([
            ("rst", 1),
            ("adc_afe_pwr", 1),
            ("dac_afe_pwr", 1),
            ("dac_clr", 1),
            ("en_ch0", 1),
            ("en_ch1", 1),
            ("adc_gainx10", 2),
        ])

        # 0x03
        self.mode = Record([
            ("read_adc", 1),
            ("set_dac", 1)
        ])

        # 0x04
        self.init = Record([
            ("dac_init", 1),
            ("adc_init", 1)
        ])

        self.adc_data = Signal((32, True))
        
        # dac_ctrl layout (MSB to LSB):
        # | 1   |   1   |   14  |   14  |
        # qdata load new | idata load new | qdata | idata|
        self.dac_ctrl = Signal((30, True))

        idata = Signal((14, True), reset_less=True)
        qdata = Signal((14, True), reset_less=True)

        # self.submodules.adc = ADC(adc_p, pads)
        self.submodules.dac = DAC()
        self.submodules.iir = IIR(iir_p, channels=2)

        self.submodules.dac_spi = SPI(dac_pads, spi_p)
        self.submodules.adc_spi = SPI(adc_pads, spi_p)


        old_adc_ready = Signal(reset=1)
        old_dac_ready = Signal(reset=1)

        ###

        self.comb += [
            self.adc_spi.data.eq((1<<16) | (0x00 << 8) | (1<<8)),   # RESET ADC
            self.dac_spi.data.eq((1<<16) | (0x00 << 8) | (1<<5)),   # RESET DAC
        ]

        # Initialize DAC and ADC via SPI (software reset)
        self.sync += [
            old_adc_ready.eq(self.adc_spi.ready),
            old_dac_ready.eq(self.dac_spi.ready),

            # Store in init register converters status
            If(Cat(old_dac_ready, self.dac_spi.ready) == 0b10,
                self.init.dac_init.eq(1),
            ),
            If(Cat(old_adc_ready, self.adc_spi.ready) == 0b10,
                self.init.adc_init.eq(1),
            ),
            self.adc_spi.enable.eq(~self.init.adc_init & old_adc_ready),
            self.dac_spi.enable.eq(~self.init.dac_init & old_dac_ready),

            # when dac clear asserted, set DAC outputs to middle point value of the full scale (0V)
            If(self.ctrl.dac_clr,
                self.ctrl.dac_clr.eq(0),
                self.dac_ctrl.eq(Cat(Replicate(0, 28), self.dac_ctrl[-2:]))
            )
        ]

        # feed DAC with out values - either provided by kernel or form IIR
        self.comb += [
            idata.eq(Mux(self.dac_ctrl[-2], self.dac_ctrl[:14], idata)),
            qdata.eq(Mux(self.dac_ctrl[-1], self.dac_ctrl[14:-2], qdata)),

            self.dac.idata.eq(Mux(self.ctrl.dac_clr, Replicate(0, 14), 
                                    Mux(self.mode.set_dac, idata, self.iir.dac[0]))),
            self.dac.qdata.eq(Mux(self.ctrl.dac_clr, Replicate(0, 14),
                                    Mux(self.mode.set_dac, qdata, self.iir.dac[1]))),
        ]

        self.sync += [
            self.adc_data.eq(Cat(adc_pads.o_data[0], adc_pads.o_data[1]))       # TODO: change adc_pads for self.adc module
        ]


        # control over external circuits as afe power down, afe gain
        self.comb += [
            adc_pads.shdn_n.eq(self.ctrl.adc_afe_pwr),
            dac_pads.shdn_n.eq(self.ctrl.dac_afe_pwr),
            
            adc_pads.gainx10.eq(self.ctrl.adc_gainx10),
        ]

        self.comb += [
            self.iir.adc[0].eq(adc_pads.o_data[0]),
            self.iir.adc[1].eq(adc_pads.o_data[1]),

        ]