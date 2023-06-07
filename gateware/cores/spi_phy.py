# This file is part of Fast Servo board support package.
#
# Copyright (c) 2023 Jakub Matyas <jakubk.m@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause


from enum import Enum

from migen import *


class SpiInterface(Enum):
    ADC = 0
    DAC = 1


class SpiPhy(Module):
    def __init__(self, spi_type, ps7_spi_pads):
        assert isinstance(spi_type, SpiInterface)

        self.ps_ss = Signal(3, reset_less=True)
        
        self.ps_miso_o = Signal()
        self.ps_miso_t = Signal()
        self.ps_mosi_o = Signal()
        self.ps_mosi_t = Signal()
        self.ps_sclk_o = Signal()
        self.ps_sclk_t = Signal()
        self.ps_sclk_i = Signal()
        self.ps_mosi_i = Signal()
        self.ps_miso_i = Signal()
        self.ps_ss_i = Signal()
        self.ps_ss_t = Signal()

        if spi_type.name == "ADC":

            cs_translated = Signal(4, reset_less=True)
            
            main_adc_miso = Signal(reset_less=True)
            aux_adc_miso_a = Signal(reset_less=True)
            aux_adc_miso_b = Signal(reset_less=True)
            aux_dac_miso = Signal(reset_less=True)

            miso_signals = [main_adc_miso, aux_adc_miso_a, aux_adc_miso_b, aux_dac_miso]
        
            # MAIN ADC
            self.specials += Instance("OBUFT", i_I=self.ps_sclk_o, i_T=self.ps_sclk_t, o_O=ps7_spi_pads.sclk) 
            self.specials += Instance("OBUFT", i_I=self.ps_mosi_o, i_T=self.ps_mosi_t, o_O=ps7_spi_pads.mosi) 
            self.specials += Instance("IBUF", i_I=ps7_spi_pads.miso, o_O=main_adc_miso)

            # AUX ADC
            self.specials += Instance("OBUFT", i_I=self.ps_sclk_o, i_T=self.ps_sclk_t, o_O=ps7_spi_pads.aux_adc_sclk)
            self.specials += Instance("IBUF", i_I=ps7_spi_pads.aux_adc_miso_a, o_O=aux_adc_miso_a)
            self.specials += Instance("IBUF", i_I=ps7_spi_pads.aux_adc_miso_b, o_O=aux_adc_miso_b)

            # AUX DAC
            self.specials += Instance("OBUFT", i_I=self.ps_sclk_o, i_T=self.ps_sclk_t, o_O=ps7_spi_pads.aux_dac_sclk)
            self.specials += Instance("OBUFT", i_I=self.ps_mosi_o, i_T=self.ps_mosi_t, o_O=ps7_spi_pads.aux_dac_mosi)
            self.specials += Instance("IBUF", i_I=ps7_spi_pads.aux_dac_miso, o_O=aux_dac_miso)

            cases = {}
            # for i in range(4):
            #     case_mask = ~(1 << i) & 0xF
            #     print(f"Case mask: 0b{case_mask:04b}")
            #     cases[i + 1] = [
            #         cs_translated.eq(case_mask),
            #         self.ps_miso_i.eq(miso_signals[i])
            #     ]

            cases[0b001] = [
                cs_translated.eq(0b1110),
                self.ps_miso_i.eq(main_adc_miso),
            ]

            cases[0b010] = [
                cs_translated.eq(0b1101),
                self.ps_miso_i.eq(aux_adc_miso_a),
            ]

            cases[0b011] = [
                cs_translated.eq(0b1011),
                self.ps_miso_i.eq(aux_adc_miso_b),
            ]
            cases[0b100] = [
                cs_translated.eq(0b0111),
                self.ps_miso_i.eq(aux_dac_miso),
            ]

            cases["default"] = [
                cs_translated.eq(0b1111),
                self.ps_miso_i.eq(0b1),
            ]

            self.comb += [
                self.ps_ss_i.eq(1),
                Case(self.ps_ss, cases),
               
                ps7_spi_pads.cs.eq(cs_translated[0]),

                # only one CS line physically available to AUX ADC
                ps7_spi_pads.aux_adc_cs.eq(cs_translated[1] & cs_translated[2]),
                ps7_spi_pads.aux_dac_miso.eq(cs_translated[3]),
            
            ]
        else:
            self.specials += Instance(
                "spi2threewire",
                o_ps_sclk_i     =   self.ps_sclk_i,
                i_ps_sclk_o     =   self.ps_sclk_o,
                i_ps_sclk_t     =   self.ps_sclk_t,

                o_ps_mosi_i     =   self.ps_mosi_i,
                i_ps_mosi_o     =   self.ps_mosi_o,
                i_ps_mosi_t     =   self.ps_mosi_t,

                o_ps_miso_i     =   self.ps_miso_i,
                i_ps_miso_o     =   self.ps_miso_o,
                i_ps_miso_t     =   self.ps_miso_t,

                o_ps_ss_i       =   self.ps_ss_i,
                i_ps_ss         =   self.ps_ss,
                i_ps_ss_t       =   self.ps_ss_t,

                o_o_ss          =   ps7_spi_pads.cs,
                o_o_sclk        =   ps7_spi_pads.sclk,
                io_sdio         =   ps7_spi_pads.sdio,
            )

