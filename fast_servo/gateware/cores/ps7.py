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


class PS7(Module):
    def __init__(self, platform, ps7_name=None):
        self.frstn = Signal()
        self.ps7_tcl = []
        self.platform = platform

        self.ps7_name = "Zynq" if ps7_name is None else ps7_name

        ps7_clk         =   platform.request("ps7_clk")
        ps7_porb        =   platform.request("ps7_porb")
        ps7_srstb       =   platform.request("ps7_srstb")
        ps7_mio         =   platform.request("ps7_mio")
        ps7_ddram       =   platform.request("ps7_ddram")

        self.cpu_params = dict(
            # Clk / Rst.
            io_PS_CLK       = ps7_clk,
            io_PS_PORB      = ps7_porb,
            io_PS_SRSTB     = ps7_srstb,

            # MIO.
            io_MIO          = ps7_mio,

            # DDRAM.
            io_DDR_Addr     = ps7_ddram.addr,
            io_DDR_BankAddr = ps7_ddram.ba,
            io_DDR_CAS_n    = ps7_ddram.cas_n,
            io_DDR_Clk_n    = ps7_ddram.ck_n,
            io_DDR_Clk      = ps7_ddram.ck_p,
            io_DDR_CKE      = ps7_ddram.cke,
            io_DDR_CS_n     = ps7_ddram.cs_n,
            io_DDR_DM       = ps7_ddram.dm,
            io_DDR_DQ       = ps7_ddram.dq,
            io_DDR_DQS_n    = ps7_ddram.dqs_n,
            io_DDR_DQS      = ps7_ddram.dqs_p,
            io_DDR_ODT      = ps7_ddram.odt,
            io_DDR_RAS_n    = ps7_ddram.ras_n,
            io_DDR_DRSTB    = ps7_ddram.reset_n,
            io_DDR_WEB      = ps7_ddram.we_n,
            io_DDR_VRN      = ps7_ddram.vrn,
            io_DDR_VRP      = ps7_ddram.vrp,

            # USB0.
            # i_USB0_VBUS_PWRFAULT = 0,

            # Fabric Clk / Rst.
            # o_FCLK_CLK0     = ClockSignal("ps7"),
            o_FCLK_RESET0_N = self.frstn
        )

        self.set_ps7(name=self.ps7_name,
            config={
                **self.platform.ps7_config
            })

    def add_ps7_config(self, config):
        # Config must be provided as a config, value dict.
        assert isinstance(config, dict)
        # Add configs to PS7.
        self.ps7_tcl.append("set_property -dict [list \\")
        for config, value in config.items():
            self.ps7_tcl.append("CONFIG.{} {} \\".format(config, '{{' + str(value) + '}}'))
        self.ps7_tcl.append(f"] [get_ips {self.ps7_name}]")

    def set_ps7(self, name=None, config=None, preset=None):
        self.ps7_name = name
        self.ps7_tcl.append(f"set ps7 [create_ip -vendor xilinx.com -name processing_system7 -module_name {self.ps7_name}]")
        self.add_ps7_config(config)

    def add_axi_gp_master(self, interface):
        # assert type(interface) is Axi2Sys

        axi_interface = interface

        self.cpu_params.update({
            # AXI GP clk.
            f"i_M_AXI_GP0_ACLK"    : axi_interface.aclk,

            # AXI GP aw.
            f"o_M_AXI_GP0_AWVALID" : axi_interface.awvalid,
            f"i_M_AXI_GP0_AWREADY" : axi_interface.awready,
            f"o_M_AXI_GP0_AWADDR"  : axi_interface.awaddr,
            f"o_M_AXI_GP0_AWBURST" : axi_interface.awburst,
            f"o_M_AXI_GP0_AWLEN"   : axi_interface.awlen,
            f"o_M_AXI_GP0_AWSIZE"  : axi_interface.awsize,
            f"o_M_AXI_GP0_AWID"    : axi_interface.awid,
            f"o_M_AXI_GP0_AWLOCK"  : axi_interface.awlock,
            f"o_M_AXI_GP0_AWPROT"  : axi_interface.awprot,
            f"o_M_AXI_GP0_AWCACHE" : axi_interface.awcache,
            f"o_M_AXI_GP0_AWQOS"   : axi_interface.awqos,

            # AXI GP w.
            f"o_M_AXI_GP0_WVALID"  : axi_interface.wvalid,
            f"o_M_AXI_GP0_WLAST"   : axi_interface.wlast,
            f"i_M_AXI_GP0_WREADY"  : axi_interface.wready,
            f"o_M_AXI_GP0_WID"     : axi_interface.wid,
            f"o_M_AXI_GP0_WDATA"   : axi_interface.wdata,
            f"o_M_AXI_GP0_WSTRB"   : axi_interface.wstrb,

            # AXI GP b.
            f"i_M_AXI_GP0_BVALID"  : axi_interface.bvalid,
            f"o_M_AXI_GP0_BREADY"  : axi_interface.bready,
            f"i_M_AXI_GP0_BID"     : axi_interface.bid,
            f"i_M_AXI_GP0_BRESP"   : axi_interface.bresp,

            # AXI GP ar.
            f"o_M_AXI_GP0_ARVALID" : axi_interface.arvalid,
            f"i_M_AXI_GP0_ARREADY" : axi_interface.arready,
            f"o_M_AXI_GP0_ARADDR"  : axi_interface.araddr,
            f"o_M_AXI_GP0_ARBURST" : axi_interface.arburst,
            f"o_M_AXI_GP0_ARLEN"   : axi_interface.arlen,
            f"o_M_AXI_GP0_ARID"    : axi_interface.arid,
            f"o_M_AXI_GP0_ARLOCK"  : axi_interface.arlock,
            f"o_M_AXI_GP0_ARSIZE"  : axi_interface.arsize,
            f"o_M_AXI_GP0_ARPROT"  : axi_interface.arprot,
            f"o_M_AXI_GP0_ARCACHE" : axi_interface.arcache,
            f"o_M_AXI_GP0_ARQOS"   : axi_interface.arqos,

            # AXI GP r.
            f"i_M_AXI_GP0_RVALID"  : axi_interface.rvalid,
            f"o_M_AXI_GP0_RREADY"  : axi_interface.rready,
            f"i_M_AXI_GP0_RLAST"   : axi_interface.rlast,
            f"i_M_AXI_GP0_RID"     : axi_interface.rid,
            f"i_M_AXI_GP0_RRESP"   : axi_interface.rresp,
            f"i_M_AXI_GP0_RDATA"   : axi_interface.rdata,
        })
    
    def add_i2c_emio(self, platform, i2c_name, i2c_number):
        ps7_i2c_pads = platform.request(i2c_name, i2c_number) #, loose=True)
        if ps7_i2c_pads is not None:
            o_i2c_scl = Signal()
            i_i2c_scl = Signal()
            t_i2c_scl = Signal()
            o_i2c_sda = Signal()
            i_i2c_sda = Signal()
            t_i2c_sda = Signal()

            self.specials += Instance("IOBUF", 
                i_T     = t_i2c_sda,
                i_I     = o_i2c_sda,
                io_IO   = ps7_i2c_pads.sda,
                o_O     = i_i2c_sda,
            )

            self.specials += Instance("IOBUF",
                i_T     = t_i2c_scl,
                i_I     = o_i2c_scl,
                io_IO   = ps7_i2c_pads.scl,
                o_O     = i_i2c_scl,
            )

            self.cpu_params.update({
                f"i_I2C{i2c_number}_SCL_I"    : i_i2c_scl,
                f"o_I2C{i2c_number}_SCL_T"    : t_i2c_scl,
                f"o_I2C{i2c_number}_SCL_O"    : o_i2c_scl,

                f"i_I2C{i2c_number}_SDA_I"    : i_i2c_sda,
                f"o_I2C{i2c_number}_SDA_T"    : t_i2c_sda,
                f"o_I2C{i2c_number}_SDA_O"    : o_i2c_sda,
            })

    def do_finalize(self):
        if len(self.ps7_tcl):
            self.ps7_tcl += [
                f"upgrade_ip [get_ips {self.ps7_name}]",
                f"generate_target all [get_ips {self.ps7_name}]",
                f"synth_ip [get_ips {self.ps7_name}]"
            ]
            self.platform.toolchain.pre_synthesis_commands += self.ps7_tcl

        self.specials += Instance(self.ps7_name, **self.cpu_params)
