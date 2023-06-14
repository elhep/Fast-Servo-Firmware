# This file is part of Fast Servo Software Package.
#
# Copyright (C) 2022-2023 Jakub Matyas
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

from migen.build.generic_platform import *
from migen.build.xilinx import XilinxPlatform

import os
from fast_servo.gateware import verilog_dir


# IOs ----------------------------------------------------------------------------------------------


_io = [
    # Front panel LEDs
    ("fp_led", 0, Pins("G7"), IOStandard("LVCMOS25")),
    ("fp_led", 1, Pins("G8"), IOStandard("LVCMOS25")),
    ("fp_led", 2, Pins("G2"), IOStandard("LVCMOS25")),
    ("fp_led", 3, Pins("G3"), IOStandard("LVCMOS25")),

    # LEDs
    ("user_led", 0, Pins("AB16"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("AA14"), IOStandard("LVCMOS33")),
    ("user_led", 2, Pins("AA15"), IOStandard("LVCMOS33")),

    # ETH LEDs
    ("eth_led", 0, Pins("V11"), IOStandard("LVCMOS33")),
    ("eth_led", 1, Pins("U13"), IOStandard("LVCMOS33")),

    ("from_eth_phy", 0, Pins("J3"), IOStandard("LVCMOS18")),
    ("from_eth_phy", 1, Pins("K8"), IOStandard("LVCMOS18")),


    # CLK 100 MHz from oscillator
    ("clk100", 0, Pins("Y14"), IOStandard("LVCMOS33")),

    # MGT clk from on-board Si5338A
    ("mgt_clk1", 0,
        Subsignal("p", Pins("U5")),
        Subsignal("n", Pins("V5")),
        IOStandard("LVDS_25"),
    ),

    # FCLK125 from on-board Si5338A
    ("fclk125", 0, Pins("K2"), IOStandard("LVCMOS18")),

    # # ADC CLK
    # ("fpga_clk", 0,
    #     Subsignal("p", Pins("C6")),
    #     Subsignal("n", Pins("C5")),
    #     IOStandard("LVDS_25"),
    # ),

    # DAC CLK
    ("fpga_clk", 1,
        Subsignal("p", Pins("J7")),
        Subsignal("n", Pins("J6")),
        IOStandard("LVDS_25"),
    ),

    # MAIN ADC LT2195
    ("adc", 0, 
        Subsignal("data0_p", Pins("F7 B7 E4 D1"), IOStandard("LVDS_25")),
        Subsignal("data0_n", Pins("E7 B6 E3 C1"), IOStandard("LVDS_25")),
        Subsignal("data1_p", Pins("A2 D5 F2 D7"), IOStandard("LVDS_25")),
        Subsignal("data1_n", Pins("A1 C4 F1 D6"), IOStandard("LVDS_25")),
        Subsignal("dco_p", Pins("B4"), IOStandard("LVDS_25")),
        Subsignal("dco_n", Pins("B3"), IOStandard("LVDS_25")),
        Subsignal("frame_p", Pins("B2"), IOStandard("LVDS_25")),
        Subsignal("frame_n", Pins("B1"), IOStandard("LVDS_25"))
    ),

    # ADC AFE
    ("adc_afe", 0,
        Subsignal("ch1_gain", Pins("AA12"), IOStandard("LVCMOS33")),
        Subsignal("ch2_gain", Pins("AB11"), IOStandard("LVCMOS33")),
        Subsignal("nshdn_ch1", Pins("G4"), IOStandard("LVCMOS25")),
        Subsignal("nshdn_ch2", Pins("F4"), IOStandard("LVCMOS25")),
    ),
    
    # P5 R5 N1 N4 L2 P6 N3 R4 P1 L1 M3 M4 U2 T2
    # MAIN DAC AD9117
    ("dac", 0,
        Subsignal("data", 
            Pins("T2 U2 M4 M3 L1 P1 R4 N3 P6 L2 N4 N1 R5 P5"),
            IOStandard("LVCMOS18")),
        Subsignal("dclkio", Pins("U1"), IOStandard("LVCMOS18")),
        Subsignal("rst", Pins("T1"), IOStandard("LVCMOS18")),
    ),

    # DAC AFE
    ("dac_afe", 0,
        Subsignal("ch1_pd_n", Pins("L5")),
        Subsignal("ch2_pd_n", Pins("L4")),
        IOStandard("LVCMOS18"),
    ),

    # AUXILIARY ADC
    ("aux_adc", 0,
        Subsignal("diff_n", Pins("W18")),
        Subsignal("a", Pins("AB18 AB19 W17")),
        Subsignal("range", Pins("U19")),
        IOStandard("LVCMOS33")
    ),

    # AUXILIARY DAC
    ("aux_dac", 0,
        Subsignal("nclr", Pins("V19")),
        Subsignal("bin", Pins("AA19")),
        Subsignal("nldac", Pins("AB21")),
        IOStandard("LVCMOS33")
    ),

    # ADC SPI
    ("spi", 0,
        Subsignal("sclk", Pins("J1"), IOStandard("LVCMOS18")),
        Subsignal("mosi", Pins("J5"), IOStandard("LVCMOS18")),
        Subsignal("miso", Pins("K5"), IOStandard("LVCMOS18")),
        Subsignal("cs", Pins("J2"), IOStandard("LVCMOS18")),
        Subsignal("aux_adc_sclk", Pins("AB22"), IOStandard("LVCMOS33")),
        Subsignal("aux_adc_miso_a", Pins("Y18"), IOStandard("LVCMOS33")),
        Subsignal("aux_adc_miso_b", Pins("AA16"), IOStandard("LVCMOS33")),
        Subsignal("aux_adc_cs", Pins("Y19"), IOStandard("LVCMOS33")),
        Subsignal("aux_dac_sclk", Pins("V18"), IOStandard("LVCMOS33")),
        Subsignal("aux_dac_mosi", Pins("U17"), IOStandard("LVCMOS33")),
        Subsignal("aux_dac_miso", Pins("U18"), IOStandard("LVCMOS33")),
        Subsignal("aux_dac_cs", Pins("AA20"), IOStandard("LVCMOS33")),
    ),

    # DAC SPI
    ("spi", 1,
        Subsignal("sclk", Pins("K3"), IOStandard("LVCMOS18")),
        Subsignal("sdio", Pins("R2"), IOStandard("LVCMOS18")),
        Subsignal("cs", Pins("R3"), IOStandard("LVCMOS18")),
        # Subsignal("sclk_aux", Pins("V18"), IOStandard("LVCMOS33")),
        # Subsignal("mosi_aux", Pins("U17"), IOStandard("LVCMOS33")),
        # Subsignal("miso_aux", Pins("U18"), IOStandard("LVCMOS33")),
        # Subsignal("cs_aux", Pins("AA20"), IOStandard("LVCMOS33")),
    ),
    #Pins("Y15 AB14 AB13 V13 V14 V15 U12 W13 W12 R17 W15 AB17 Y12 Y13 V16 W16 AA17 Y17"),
    ("gpio", 0,
        Subsignal("n", Pins("Y15 AB14 AB13 V13 V14 V15 U12 W13"), IOStandard("LVCMOS33")),
        Subsignal("p", Pins("W12 R17 W15 AB17 Y12 Y13 V16 W16"), IOStandard("LVCMOS33")),
    ),

    # PS7
    ("ps7_clk",   0, Pins("_" * 1)),
    ("ps7_porb",  0, Pins("_" * 1)),
    ("ps7_srstb", 0, Pins("_" * 1)),
    ("ps7_mio",   0, Pins("_" * 54)),
    ("ps7_ddram", 0,
        Subsignal("addr",    Pins("_" * 15)),
        Subsignal("ba",      Pins("_" * 3)),
        Subsignal("cas_n",   Pins("_" * 1)),
        Subsignal("ck_n",    Pins("_" * 1)),
        Subsignal("ck_p",    Pins("_" * 1)),
        Subsignal("cke",     Pins("_" * 1)),
        Subsignal("cs_n",    Pins("_" * 1)),
        Subsignal("dm",      Pins("_" * 4)),
        Subsignal("dq",      Pins("_" * 32)),
        Subsignal("dqs_n",   Pins("_" * 4)),
        Subsignal("dqs_p",   Pins("_" * 4)),
        Subsignal("odt",     Pins("_" * 1)),
        Subsignal("ras_n",   Pins("_" * 1)),
        Subsignal("reset_n", Pins("_" * 1)),
        Subsignal("we_n",    Pins("_" * 1)),
        Subsignal("vrn",     Pins("_" * 1)),
        Subsignal("vrp",     Pins("_" * 1)),

    ),

    # I2C0 to Si5340 on Fast Servo
    ("ps7_i2c", 0,
        Subsignal("sda", Pins("M2")),
        Subsignal("scl", Pins("M1")),
        IOStandard("LVCMOS18")
    ),

    # Si540 nRST
    ("nrst", 0, Pins("M7"), IOStandard("LVCMOS18")),

]



_connector_eem = [
    ("eem", {
        "d0_cc_n": "C3",
        "d0_cc_p": "D3",
        "d1_n": "A4",
        "d1_p": "A5",
        "d2_n": "F6",
        "d2_p": "G6",
        "d3_n": "A6",
        "d3_p": "A7",
        "d4_n": "E5",
        "d4_p": "F5",
        "d5_n": "H3",
        "d5_p": "H4",
        "d6_n": "B8",
        "d6_p": "C8",
        "d7_n": "D8",
        "d7_p": "E8",
    }),
]

_connector_gpio = [
    ("gpio", {
        "qspi_io3": "Y15",
        "qspi_io2": "AB14",
        "qspi_io1": "AB13",
        "qspi_io0": "V13",
        "qspi_clk": "V14",
        "qspi_ncs": "V15",
        "hrtim_che1": "U12",
        "hrtim_che2": "W13",
        "hrtim_cha1": "W12",
        "hrtim_cha2": "R17",
        "lptim2_out": "W15",
        "uart4_tx": "AB17",
        "spi1_mosi": "Y12",
        "spi1_miso": "Y13",
        "spi1_nss": "V16",
        "spi1_sck": "W16",
        "i2c1_sda": "AA17",
        "i2c1_scl": "Y17",
    })
]

# PS7 config ---------------------------------------------------------------------------------------

ps7_config_board_preset = {
    "PCW_PRESET_BANK0_VOLTAGE"          : "LVCMOS 3.3V",
    "PCW_PRESET_BANK1_VOLTAGE"          : "LVCMOS 1.8V",
    "PCW_CRYSTAL_PERIPHERAL_FREQMHZ"    : "33.333333",
    "PCW_QSPI_PERIPHERAL_ENABLE"        : "1",
    "PCW_QSPI_GRP_SINGLE_SS_ENABLE"     : "1",
    "PCW_SINGLE_QSPI_DATA_MODE"         : "x4",
    "PCW_QSPI_QSPI_IO"                  : "MIO 1 .. 6",
    "PCW_QSPI_GRP_FBCLK_ENABLE"         : "1",

    # SD Card
    "PCW_SD0_PERIPHERAL_ENABLE"         : "1",
    "PCW_SD0_SD0_IO"                    : "MIO 40 .. 45",
    "PCW_MIO_40_PULLUP"                 : "disabled",
    "PCW_MIO_41_PULLUP"                 : "disabled",
    "PCW_MIO_42_PULLUP"                 : "disabled",
    "PCW_MIO_43_PULLUP"                 : "disabled",
    "PCW_MIO_44_PULLUP"                 : "disabled",
    "PCW_MIO_45_PULLUP"                 : "disabled",
    
    # UART
    "PCW_UART0_PERIPHERAL_ENABLE"       : "1",
    "PCW_UART0_UART0_IO"                : "MIO 10 .. 11",

    # ETHERNET
    "PCW_ACT_ENET0_PERIPHERAL_FREQMHZ"  : "125",
    "PCW_ENET0_PERIPHERAL_CLKSRC"       : "ARM PLL",
    "PCW_ENET0_PERIPHERAL_ENABLE"       : "1",
    "PCW_ENET0_ENET0_IO"                : "MIO 16 .. 27",
    "PCW_ENET0_GRP_MDIO_ENABLE"         : "1",
    "PCW_ENET0_GRP_MDIO_IO"             : "MIO 52 .. 53",
    "PCW_ENET_RESET_ENABLE"             : "1",
    "PCW_ENET0_RESET_ENABLE"            : "1",
    "PCW_ENET0_RESET_IO"                : "MIO 50",

    # USB
    "PCW_USB0_PERIPHERAL_ENABLE"        : "1",
    "PCW_USB0_USB0_IO"                  : "MIO 28 .. 39",
    "PCW_USB_RESET_ENABLE"              : "1",
    "PCW_USB0_RESET_ENABLE"             : "1",
    "PCW_USB0_RESET_IO"                 : "MIO 51",

    "PCW_WDT_PERIPHERAL_ENABLE"         : "1",
    "PCW_TTC0_PERIPHERAL_ENABLE"        : "1",      # TTC0 required for Linux

    # I2C
    "PCW_I2C_RESET_ENABLE"              : "0",
    "PCW_I2C_RESET_POLARITY"            : "Active Low",

    # I2C0
    "PCW_I2C0_I2C0_IO"                  : "EMIO",
    "PCW_I2C0_PERIPHERAL_ENABLE"        : "1",
    "PCW_I2C0_GRP_INT_ENABLE"           : "1",
    "PCW_I2C0_GRP_INT_IO"               : "EMIO",

    # I2C1
    "PCW_I2C1_PERIPHERAL_ENABLE"        : "1",
    "PCW_I2C1_I2C1_IO"                  : "MIO 48 .. 49",
    "PCW_I2C1_I2C1_IO"                  : "MIO 12 .. 13",
    "PCW_I2C1_PERIPHERAL_ENABLE"        : "1",

    "PCW_UIPARAM_DDR_MEMORY_TYPE"       : "DDR 3 (Low Voltage)",
    "PCW_UIPARAM_DDR_PARTNO"            : "MT41J256M16 RE-125",
    "PCW_GPIO_MIO_GPIO_ENABLE"          : "1",

    "PCW_FPGA0_PERIPHERAL_FREQMHZ"      : "100",
    "PCW_EN_CLK0_PORT"                  : "0",              # dont use FCLK0 
}

class Platform(XilinxPlatform):
    default_clk_name = "clk100"
    default_clk_period = 10.0

    def __init__(self):
        XilinxPlatform.__init__(self, "xc7z015-clg485-1", _io, _connector_gpio + _connector_eem, toolchain="vivado")
        ps7_config = ps7_config_board_preset
        self.ps7_config = ps7_config

        verilog_sources = os.listdir(verilog_dir)
        self.add_sources(verilog_dir, *verilog_sources)

    def do_finalize(self, fragment):
        try:
            XilinxPlatform.do_finalize(self, fragment)
            self.add_period_constraint(self.lookup_request(self.default_clk_name, loose=True), self.default_clk_period)
        except ValueError:
            pass
        except ConstraintError:
            pass
