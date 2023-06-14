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
from misoc.interconnect.csr import AutoCSR, CSRStorage


class DAC(Module, AutoCSR):
    def __init__(self, platform):
        dac_pads = platform.request("dac")
        dac_afe_pads = platform.request("dac_afe")
        self.dac_ctrl = CSRStorage(3)
        self.output_value_ch0 = CSRStorage(14)
        self.output_value_ch1 = CSRStorage(14)

        manual_override = Signal()
        ch0_pd = Signal()
        ch1_pd = Signal()

        output_data_ch0 = Signal(14)
        output_data_ch1 = Signal(14)

        self.data_in = [Signal(14, reset_less=True), Signal(14, reset_less=True)]
        platform.add_period_constraint(dac_pads.dclkio, 10.0)

        self.comb += [
            Cat(manual_override, ch0_pd, ch1_pd).eq(self.dac_ctrl.storage),
            dac_pads.rst.eq(ResetSignal("sys")),
            dac_afe_pads.ch1_pd_n.eq(~ch0_pd),
            dac_afe_pads.ch2_pd_n.eq(~ch1_pd),
            output_data_ch0.eq(
                Mux(manual_override, self.output_value_ch0.storage, self.data_in[0])
            ),
            output_data_ch1.eq(
                Mux(manual_override, self.output_value_ch1.storage, self.data_in[1])
            ),
        ]

        self.specials += Instance(
            "AD9117",
            i_clk_in=ClockSignal("dco2d"),
            i_rst_in=ResetSignal("sys"),
            i_DAC0_in=output_data_ch0,
            i_DAC1_in=output_data_ch1,
            o_DCLKIO=dac_pads.dclkio,
            o_D_out=dac_pads.data,
        )


class AUX_DAC_CTRL(Module, AutoCSR):
    def __init__(self, platform):
        dac_aux_pads = platform.request("aux_dac")

        self.dac_aux_ctrl = CSRStorage(3)

        self.comb += [
            dac_aux_pads.nclr.eq(~self.dac_aux_ctrl.storage[0]),
            dac_aux_pads.bin.eq(self.dac_aux_ctrl.storage[1]),
            dac_aux_pads.nldac.eq(~self.dac_aux_ctrl.storage[2]),
        ]
