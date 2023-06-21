# This file is part of Fast Servo Software Package.
#
# Copyright (C) 2023 Jakub Matyas
# Warsaw University of Technology <jakubk.m@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from migen import *
from migen.genlib.cdc import MultiReg
from misoc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage


class _CRG(Module):
    def __init__(self, platform, dco_clk, dco_freq=200e6):
        self.clock_domains.cd_dco = ClockDomain()
        self.clock_domains.cd_dco2x = ClockDomain()
        self.clock_domains.cd_dco2d = ClockDomain()
        dco_clk_p, dco_clk_n = dco_clk

        dco_clk_buf = Signal()
        self.specials += Instance(
            "IBUFGDS", i_I=dco_clk_p, i_IB=dco_clk_n, o_O=dco_clk_buf
        )

        # # #
        clk_feedback = Signal()
        clk_feedback_buf = Signal()

        clk_dco = Signal()
        clk_dco2x = Signal()
        clk_dco2d = Signal()
        self.locked = Signal()

        platform.add_period_constraint(dco_clk_p, 1e9 / dco_freq)
        self.specials += [
            Instance(
                "PLLE2_BASE",
                p_BANDWIDTH="OPTIMIZED",
                p_DIVCLK_DIVIDE=1,
                p_CLKFBOUT_PHASE=0.0,
                p_CLKFBOUT_MULT=4,  # VCO @ 800 MHz
                p_CLKIN1_PERIOD=(1e9 / dco_freq),
                p_REF_JITTER1=0.01,
                p_STARTUP_WAIT="FALSE",
                i_CLKIN1=dco_clk_buf,
                i_PWRDWN=0,
                i_RST=ResetSignal("sys"),
                i_CLKFBIN=clk_feedback_buf,
                o_CLKFBOUT=clk_feedback,
                p_CLKOUT0_DIVIDE=4,
                p_CLKOUT0_PHASE=0.0,
                p_CLKOUT0_DUTY_CYCLE=0.5,
                o_CLKOUT0=clk_dco,  # 200 MHz <- dco_clk
                p_CLKOUT1_DIVIDE=2,
                p_CLKOUT1_PHASE=0.0,
                p_CLKOUT1_DUTY_CYCLE=0.5,
                o_CLKOUT1=clk_dco2x,  # 400 MHZ <- 2 * dco_clk = 2*200 MHz
                p_CLKOUT2_DIVIDE=8,
                p_CLKOUT2_PHASE=0.0,
                p_CLKOUT2_DUTY_CYCLE=0.5,
                o_CLKOUT2=clk_dco2d,  # 100 MHz <- dco_clk / 2 = 200 MHz / 2
                o_LOCKED=self.locked,
            )
        ]

        self.specials += Instance("BUFG", i_I=clk_feedback, o_O=clk_feedback_buf)
        self.specials += Instance("BUFG", i_I=clk_dco, o_O=self.cd_dco.clk)
        self.specials += Instance("BUFG", i_I=clk_dco2d, o_O=self.cd_dco2d.clk)
        self.specials += Instance("BUFG", i_I=clk_dco2x, o_O=self.cd_dco2x.clk)


class ADC(Module, AutoCSR):
    def __init__(self, platform, dco_freq=200e6):
        adc_pads = platform.request("adc")
        afe_pads = platform.request("adc_afe")

        self.frame_csr = CSRStatus(4)
        self.data_ch0 = CSRStatus(16)
        self.data_ch1 = CSRStatus(16)

        self.tap_delay = CSRStorage(5)
        self.bitslip_csr = CSRStorage(1)

        self.afe_ctrl = CSRStorage(4)

        tap_delay_val = Signal(5)
        bitslip = Signal()
        bitslip_re_dco_2d = Signal()

        ch1_gain_x10 = Signal()
        ch2_gain_x10 = Signal()
        ch1_shdn = Signal()
        ch2_shdn = Signal()

        self.data_out = [Signal(16, reset_less=True), Signal(16, reset_less=True)]
        self.s_frame = Signal(4)

        ###

        # DCO clock coming from LTC2195
        # dco_clk = Record([("p", 1), ("n", 1)])
        dco_clk =(adc_pads.dco_p, adc_pads.dco_n)
        self.comb += [
            # dco_clk.p.eq(adc_pads.dco_p),
            # dco_clk.n.eq(adc_pads.dco_n),
            tap_delay_val.eq(self.tap_delay.storage),
            Cat(ch1_gain_x10, ch2_gain_x10, ch1_shdn, ch2_shdn).eq(
                self.afe_ctrl.storage
            ),
        ]

        self.submodules._crg = _CRG(platform, dco_clk, dco_freq)

        self.specials += MultiReg(self.bitslip_csr.re, bitslip_re_dco_2d, "dco2d")
        self.sync.dco2d += [
            bitslip.eq(Mux(bitslip_re_dco_2d, self.bitslip_csr.storage, 0))
        ]

        self.comb += [
            self.frame_csr.status.eq(self.s_frame),
            self.data_ch0.status.eq(self.data_out[0]),
            self.data_ch1.status.eq(self.data_out[1]),
        ]

        self.comb += [
            afe_pads.ch1_gain.eq(ch1_gain_x10),
            afe_pads.ch2_gain.eq(ch2_gain_x10),
            afe_pads.nshdn_ch1.eq(~ch1_shdn),
            afe_pads.nshdn_ch2.eq(~ch2_shdn),
        ]

        dummy = Signal(8)
        dummy_idelay_rdy = Signal()

        self.specials += Instance(
            "LTC2195",
            i_rst_in=ResetSignal("sys"),
            i_clk200=ClockSignal("idelay"),
            i_DCO=ClockSignal("dco"),
            i_DCO_2D=ClockSignal("dco2d"),
            i_FR_in_p=adc_pads.frame_p,
            i_FR_in_n=adc_pads.frame_n,
            i_D0_in_p=adc_pads.data0_p,
            i_D0_in_n=adc_pads.data0_n,
            i_D1_in_p=adc_pads.data1_p,
            i_D1_in_n=adc_pads.data1_n,
            i_bitslip=bitslip,
            i_delay_val=tap_delay_val,
            o_ADC0_out=self.data_out[1],        # LANES swapped on hardware
            o_ADC1_out=self.data_out[0],
            o_FR_out=self.s_frame,
            o_o_data_from_pins=dummy,
            o_idelay_rdy=dummy_idelay_rdy,
        )


class AUX_ADC_CTRL(Module, AutoCSR):
    def __init__(self, platform):
        adc_aux_pads = platform.request("aux_adc")

        self.adc_aux_ctrl = CSRStorage(5)

        self.comb += [
            adc_aux_pads.diff_n.eq(~self.adc_aux_ctrl.storage[0]),
            adc_aux_pads.a.eq(self.adc_aux_ctrl.storage[1:4]),
            adc_aux_pads.range.eq(self.adc_aux_ctrl.storage[4]),
        ]
