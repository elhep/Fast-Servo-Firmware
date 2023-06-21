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

import os

from migen import *
from misoc.interconnect import csr_bus
from misoc.interconnect.csr import AutoCSR, CSRStorage

from fast_servo.gateware.cores.adc import ADC, AUX_ADC_CTRL
from fast_servo.gateware.cores.dac import AUX_DAC_CTRL, DAC
from fast_servo.gateware.cores.pitaya_ps import Axi2Sys, Sys2CSR, SysCDC, SysInterconnect
from fast_servo.gateware.cores.ps7 import PS7
from fast_servo.gateware.cores.spi_phy import SpiInterface, SpiPhy


class CRG(Module):
    def __init__(self, platform):
        self.ps_rst         = Signal()
        self.locked         = Signal()
        self.clock_domains.cd_sys         = ClockDomain()
        self.clock_domains.cd_sys_double  = ClockDomain()
        self.clock_domains.cd_idelay      = ClockDomain()

        # # #

        # Clk.
        clk100 = platform.request("clk100")
        platform.add_period_constraint(clk100, 10.0)
        self.clkin = clk100
        clk100_buf = Signal()
        self.specials += Instance("IBUFG", i_I=clk100, o_O=clk100_buf)

        clk_feedback = Signal()
        clk_feedback_buf = Signal()

        clk_sys = Signal()
        clk_idelay = Signal()

        self.specials += [
            Instance(
                "PLLE2_BASE",
                p_BANDWIDTH="OPTIMIZED",
                p_DIVCLK_DIVIDE=1,
                p_CLKFBOUT_PHASE=0.0,
                p_CLKFBOUT_MULT=10,
                p_CLKIN1_PERIOD=10.0,
                p_REF_JITTER1=0.01,
                p_STARTUP_WAIT="FALSE",
                i_CLKIN1=clk100_buf,
                i_PWRDWN=0,
                i_RST=self.ps_rst,
                i_CLKFBIN=clk_feedback_buf,
                o_CLKFBOUT=clk_feedback,
                p_CLKOUT0_DIVIDE=10,
                p_CLKOUT0_PHASE=0.0,
                p_CLKOUT0_DUTY_CYCLE=0.5,
                o_CLKOUT0=clk_sys,           # 100 MHz <- sys_clk
                p_CLKOUT1_DIVIDE=5,
                p_CLKOUT1_PHASE=0.0,
                p_CLKOUT1_DUTY_CYCLE=0.5,
                o_CLKOUT1=clk_idelay,       # 200 MHZ <- 2 * sys_clk = 2*100 MHz
                o_LOCKED=self.locked,
            )
        ]

        self.specials += Instance("BUFG", i_I=clk_feedback, o_O=clk_feedback_buf)
        self.specials += Instance("BUFG", i_I=clk_sys, o_O=self.cd_sys.clk)
        self.specials += Instance("BUFG", i_I=clk_idelay, o_O=self.cd_idelay.clk)
        self.specials += Instance("BUFG", i_I=clk_idelay, o_O=self.cd_sys_double.clk)


        # Ignore sys_clk to pll clkin path created by SoC's rst.
        platform.add_false_path_constraints(self.cd_sys.clk, self.clkin)

        self.specials += Instance("FD", p_INIT=1, i_D=~self.locked, i_C=self.cd_sys.clk, o_Q=self.cd_sys.rst)


class BaseSoC(PS7, AutoCSR):
    def __init__(self, platform, passthrouh=False):
        PS7.__init__(self, platform)

        # TODO: 
        # LINIEN SPECIFIC csr_map - in the future should be moved
        # to csr_devices list
        self.csr_map = {
            "adc": 9,
            "fp_led0": 10,
            "fp_led1": 11,
            "fp_led2": 12,
            "fp_led3": 13,
            "dac": 14,
            "adc_aux_ctrl": 15,
            "dac_aux_ctrl": 16,
        }
        self.soc_name = "FastServo"
        self.interconnect_slaves = []
        self.csr_devices = []
        
        self.platform = platform

        self.submodules.crg = CRG(platform)

        # # # AXI to system bus bridge
        self.submodules.axi2sys = Axi2Sys()
        self.submodules.sys2csr = Sys2CSR()
        self.submodules.syscdc = SysCDC()
        self.add_axi_gp_master(self.axi2sys.axi)

        self.comb += [
            self.axi2sys.axi.aclk.eq(ClockSignal("sys")),
            self.axi2sys.axi.arstn.eq(self.frstn),
            self.syscdc.target.connect(self.sys2csr.sys),
        ]
        
        # ETH LEDS
        self.comb += [
            platform.request("eth_led", 0).eq(platform.request("from_eth_phy", 0)),
            platform.request("eth_led", 1).eq(platform.request("from_eth_phy", 1)),
        ]

        # I2C0 to Si5340 on Fast Servo
        self.add_i2c_emio(platform, "ps7_i2c", 0)

        # SPI0 - interface to main ADC and auxiliary ADC
        self.add_spi_interface(platform, SpiInterface.ADC)

        # SPI1 - interface to main DAC and auxiliary DAC
        self.add_spi_interface(platform, SpiInterface.DAC)

        # self.add_main_adc(platform)
        self.submodules.adc = ADC(platform)
        self.csr_devices.append("adc")

        # self.add_main_dac(platform)
        self.submodules.dac = DAC(platform)
        self.csr_devices.append("dac")
        
        # DEBUG
        if passthrouh:
            DAC_DATA_WIDTH = 14
            for ch in range(2):
                saturate = Signal()
                adc_signal = self.adc.data_out[ch]
                self.comb += [
                    saturate.eq(adc_signal[-3:] != Replicate(adc_signal[-1], 3)),
                    self.dac.data_in[ch].eq(Mux(saturate,
                            Cat(Replicate(~adc_signal[-1], DAC_DATA_WIDTH-1), adc_signal[-1]),
                            adc_signal[:-2]))
                ]

        si_5340_nrst = platform.request("nrst")
        self.comb += si_5340_nrst.eq(1)

        for i in range(4):
            led_pin = platform.request("fp_led", i)
            setattr(self.submodules, f"fp_led{i}", LED(led_pin))
            self.csr_devices.append(f"fp_led{i}")

        self.submodules.adc_aux_ctrl = AUX_ADC_CTRL(platform)
        self.csr_devices.append("adc_aux_ctrl")

        self.submodules.dac_aux_ctrl = AUX_DAC_CTRL(platform)
        self.csr_devices.append("dac_aux_ctrl")

    def add_spi_interface(self, platform, spi_type):
        assert isinstance(spi_type, SpiInterface)
        n = spi_type.value

        ps7_spi_pads = platform.request("spi", spi_type.value)
        spi_phy = SpiPhy(spi_type, ps7_spi_pads)
        self.submodules += spi_phy

        ps7_config_spi = {
            f"PCW_SPI{n}_GRP_SS0_ENABLE"       : "1",
            f"PCW_SPI{n}_GRP_SS0_IO"           : "EMIO",
            f"PCW_SPI{n}_GRP_SS1_ENABLE"       : "1",
            f"PCW_SPI{n}_GRP_SS1_IO"           : "EMIO",
            f"PCW_SPI{n}_GRP_SS2_ENABLE"       : "1",
            f"PCW_SPI{n}_GRP_SS2_IO"           : "EMIO",
            f"PCW_SPI{n}_PERIPHERAL_ENABLE"    : "1",
            f"PCW_SPI{n}_SPI{n}_IO"              : "EMIO",
            f"PCW_SPI_PERIPHERAL_CLKSRC"     : "IO PLL",
            f"PCW_SPI_PERIPHERAL_DIVISOR0"   : "10",
            f"PCW_SPI_PERIPHERAL_FREQMHZ"    : "166.666666",
        }
        self.add_ps7_config(ps7_config_spi)

        self.cpu_params.update({
            f"o_SPI{n}_MISO_O"      : spi_phy.ps_miso_o,
            f"o_SPI{n}_MISO_T"      : spi_phy.ps_miso_t,
            f"o_SPI{n}_MOSI_O"      : spi_phy.ps_mosi_o,
            f"o_SPI{n}_MOSI_T"      : spi_phy.ps_mosi_t,
            f"o_SPI{n}_SCLK_O"      : spi_phy.ps_sclk_o,
            f"o_SPI{n}_SCLK_T"      : spi_phy.ps_sclk_t,

            f"i_SPI{n}_SCLK_I"      : spi_phy.ps_sclk_i,
            f"i_SPI{n}_MOSI_I"      : spi_phy.ps_mosi_i,
            f"i_SPI{n}_MISO_I"      : spi_phy.ps_miso_i,
            f"i_SPI{n}_SS_I"        : spi_phy.ps_ss_i,
            f"o_SPI{n}_SS_O"        : spi_phy.ps_ss[0],
            f"o_SPI{n}_SS1_O"       : spi_phy.ps_ss[1],
            f"o_SPI{n}_SS2_O"       : spi_phy.ps_ss[2],
            f"o_SPI{n}_SS_T"        : spi_phy.ps_ss_t,
        })
    
    def add_interconnect_slave(self, slave):
        self.interconnect_slaves.append(slave)

    def get_csr_dev_address(self, name, memory):     
        # TODO: switch to MiSoC-like address retriving from 
        # the list of CSR devices  
        if memory is not None:
            name = name + "_" + memory.name_override
        try:
            return self.csr_map[name]
        except KeyError:
            return None
        
    def soc_finalize(self):
        # Overload this method to customize SystemInterconnect
        # and csrbanks - especially useful in Linien
        self.add_interconnect_slave(self.syscdc.source)
        self.submodules.interconnect = SysInterconnect(
            self.axi2sys.sys,
            *self.interconnect_slaves
        )
        self.submodules.csrbanks = csr_bus.CSRBankArray(self,
            self.get_csr_dev_address)
        self.submodules.csrcon = csr_bus.Interconnect(
            self.sys2csr.csr, self.csrbanks.get_buses()
        )
        
    def do_finalize(self):
        self.soc_finalize()
        PS7.do_finalize(self)

    def build(self, *args, **kwargs):
        self.platform.build(self, *args, **kwargs)

class LED(Module, AutoCSR):
    def __init__(self, led):
        
        self.led_out = CSRStorage(1)

        self.comb += led.eq(self.led_out.storage)


if __name__ == "__main__":
    import subprocess
    from fast_servo.gateware.fast_servo_platform import Platform
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False, help="Hardwire ADC data to DAC")
    args = parser.parse_args()

    
    root_path = os.getcwd()
    platform = Platform()
    fast_servo = BaseSoC(platform, passthrouh=args.debug)

    build_dir = "builds/fast_servo_gw_debug" if args.debug else"builds/fast_servo_gw"
    build_name = "top"
    fast_servo.build(build_dir=build_dir, build_name=build_name, run=True)
    os.chdir(os.path.join(root_path, build_dir))
    with open(f"{build_name}.bif", "w") as f:
        f.write(f"all:\n{{\n\t{build_name}.bit\n}}")
    
    cmd = f"bootgen -image {build_name}.bif -arch zynq -process_bitstream bin -w on".split(" ")
    subprocess.run(cmd)

    

