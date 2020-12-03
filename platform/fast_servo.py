from migen.build.generic_platform import *
from migen.build.xilinx import XilinxPlatform

_io = [
    ("user_led", 0, Pins("C15"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("D19"), IOStandard("LVCMOS33")),
    ("user_led", 2, Pins("E19"), IOStandard("LVCMOS33")),


    ("fp_leds", 0, 
        Subsignal("led0", Pins("F19")),
        Subsignal("led1", Pins("E18")),
        Subsignal("led2", Pins("A19")),
        Subsignal("led3", Pins("D20")),
        IOStandard("LVCMOS25")
    ),
    #("clk100", 0, Pins("C19"), IOStandard("LVCMOS33")),
    
    ("Si5338_clk0", 0,
        Subsignal("p", Pins("K4")),
        Subsignal("n", Pins("J4")),
        IOStandard("DIFF_SSTL15")
    ),
    ("Si5338_clk3", 0,
        Subsignal("p", Pins("H4")),
        Subsignal("n", Pins("G4")),
        IOStandard("DIFF_SSTL15")
    ),

    ("Si5338_clk1b", 0, Pins("R4"), IOStandard("LVCMOS15")),

    ("Si5340_clk1", 0,
        Subsignal("p", Pins("W20")),
        Subsignal("n", Pins("W19")),
        IOStandard("LVDS")   #?
    ),

    ("Si5340_clk2", 0,
        Subsignal("p", Pins("J21")),
        Subsignal("n", Pins("J20")),
        IOStandard("LVDS_25")   
    ),

    ("clk125_gtp", 0,
        Subsignal("p", Pins("F6")),
        Subsignal("n", Pins("E6")),
    ),
    
    ("i2c", 0,
        Subsignal("scl", Pins("R17")),
        Subsignal("sda", Pins("U21")),
        IOStandard("LVCMOS33")
    ),

    ("serial", 0,
        Subsignal("rx", Pins("T21")), 
        Subsignal("tx", Pins("Y22")),
        IOStandard("LVCMOS33")
    ),

    ("at_event", 0, Pins("V20"), IOStandard("LVCMOS18")),
    
    ("eth_leds", 0,
        Subsignal("led1", Pins("C20")),
        Subsignal("led2", Pins("B20")),
        IOStandard("LVCMOS25")
    ),
    # ("eth_clocks", 0,
    #     Subsignal("tx", Pins("M22")),
    #     Subsignal("rx", Pins("AG11")),
    #     IOStandard("LVCMOS33"), Misc("SLEW=FAST"), Drive(16)
    # ),
    ("eth", 0,
        Subsignal("rx_dv", Pins("P20")),
        Subsignal("rx_data", Pins("N13 N14")),
        Subsignal("tx_en", Pins("R14")),
        Subsignal("tx_data", Pins("P14 P15")),
        Subsignal("mdc", Pins("R16")),
        Subsignal("mdio", Pins("P17")),
        IOStandard("LVCMOS33")
    ),

    ("usb_otg", 0,
        Subsignal("d_p", Pins("P19"), IOStandard("LVDS")),
        Subsignal("d_n", Pins("R19"), IOStandard("LVDS")),
        Subsignal("id", Pins("R18"), IOStandard("LVCMOS33")),
        Subsignal("vbus_en", Pins("T18"), IOStandard("LVCMOS33")),
    ),

    ("spiflash", 0,
        Subsignal("cs_n", Pins("T19")),
        Subsignal("dq", Pins("P22 R22 P21 R21")),
        # "clk" is on CCLK
        IOStandard("LVCMOS33")
    ),
    ("spiflash2x", 0,
        Subsignal("cs_n", Pins("T19")),
        Subsignal("dq", Pins("P22 R22")),
        Subsignal("wp", Pins("P21")),
        Subsignal("hold", Pins("R21")),
        # "clk" is on CCLK
        IOStandard("LVCMOS33")
    ),

    ("si5340_ctrl", 0,
        Subsignal("intr_n", Pins("V18")),
        Subsignal("lol_n", Pins("AA18")),
        Subsignal("los", Pins("AB18")),
        Subsignal("rst_n", Pins("U20")),
        IOStandard("LVCMOS25"),
    ),
    
    ("si5340_i2c", 0,
        Subsignal("scl", Pins("AB22")),
        Subsignal("sda", Pins("AB21")),
        IOStandard("LVCMOS18")
    ),
    
    # ("si5338_intr", 0, Pins("B2"), IOStandard("")),

    ("si5338_i2c", 0,
        Subsignal("scl", Pins("T20")),
        Subsignal("sda", Pins("W21")),
        IOStandard("LVCMOS33")
    ),
    

    ("ddram", 0,
        Subsignal("a", Pins(
            "J1 P6 N5 N3 G1 M3 N2 J5 "
            "L1 P2 L4 P5 K2 M1 M5"),
            IOStandard("SSTL15")),
        Subsignal("ba", Pins("P4 H5 H2"), IOStandard("SSTL15")),
        Subsignal("ras_n", Pins("M6"), IOStandard("SSTL15")),
        Subsignal("cas_n", Pins("M2"), IOStandard("SSTL15")),
        Subsignal("we_n", Pins("J2"), IOStandard("SSTL15")),
        # Subsignal("cs_n", Pins("K1"), IOStandard("SSTL15")),
        Subsignal("dm", Pins("W2 Y7 V4 V5"), IOStandard("SSTL15")),
        Subsignal("dq", Pins(
            "T1 U3 U2 U1 Y2 W1 Y1 V2 "
            "V7 W9 AB7 AA8 AB8 AB6 Y8 Y9 "
            "AB1 AB5 AB3 AA1 Y4 AA5 AB2 W4 "
            "T4 U6 T6 AA6 Y6 T5 U5 R6"),
            IOStandard("SSTL15"),
            Misc("IN_TERM=UNTUNED_SPLIT_50")),
        Subsignal("dqs_p", Pins("R3 V9 Y3 W6"), IOStandard("DIFF_SSTL15")),
        Subsignal("dqs_n", Pins("R2 V8 AA3 W5"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_p", Pins("R1"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_n", Pins("P1"), IOStandard("DIFF_SSTL15")),
        Subsignal("cke", Pins("L3"), IOStandard("SSTL15")),
        Subsignal("odt", Pins("K3"), IOStandard("SSTL15")),
        Subsignal("reset_n", Pins("H3"), IOStandard("LVCMOS15")),
        Misc("SLEW=FAST"),
    ),

]

_io_adc = [
    ("adc_ctrl", 0,
        Subsignal("fr_n", Pins("H20")),
        Subsignal("fr_p", Pins("G20")),
        Subsignal("dco_n", Pins("K19")),
        Subsignal("dco_p", Pins("K18")),
        IOStandard("LVDS_25")
    ),
    ("adc_data", 0,
        Subsignal("sdoa_n", Pins("J14")),
        Subsignal("sdoa_p", Pins("H14")),
        Subsignal("sdob_n", Pins("K13")),
        Subsignal("sdob_p", Pins("K14")),
        Subsignal("sdoc_n", Pins("L16")),
        Subsignal("sdoc_p", Pins("K16")),
        Subsignal("sdod_n", Pins("K21")),
        Subsignal("sdod_p", Pins("K22")),
        IOStandard("LVDS_25")
    ),
    ("adc_data", 1,
        Subsignal("sdoa_n", Pins("J22")),
        Subsignal("sdoa_p", Pins("H22")),
        Subsignal("sdob_n", Pins("H19")),
        Subsignal("sdob_p", Pins("J19")),
        Subsignal("sdoc_n", Pins("M21")),
        Subsignal("sdoc_p", Pins("L21")),
        Subsignal("sdod_n", Pins("M20")),
        Subsignal("sdod_p", Pins("N20")),
        IOStandard("LVDS_25")
    ),
    ("adc_spi", 0,
        Subsignal("sck", Pins("W17")),
        Subsignal("sdi", Pins("AA19")),
        Subsignal("sdo", Pins("AB20")),
        Subsignal("cs_n", Pins("V17")),
        IOStandard("LVCMOS18")
    ),
    ("adc_afe", 0,
        Subsignal("nshdn", Pins("L14")),
        Subsignal("gain", Pins("F20")),
        Subsignal("term_stat", Pins("M22")),
        IOStandard("LVCMOS25")
    ),
    ("adc_afe", 1,
        Subsignal("nshdn", Pins("L15")),
        Subsignal("gain", Pins("A18")),
        Subsignal("term_stat", Pins("N22")),
        IOStandard("LVCMOS25")
    ),
]

_io_dac = [
    ("dac_spi", 0,
        Subsignal("sck", Pins("V19")),
        Subsignal("sdio", Pins("AA20")),
        # Subsignal("sdo", Pins("")),
        Subsignal("cs_n", Pins("AA21")),
        IOStandard("LVCMOS18")
    ),
    ("dac_ctrl", 0, 
        Subsignal("dclkio", Pins("W12")),
        Subsignal("rst", Pins("V14")),
        IOStandard("LVCMOS18")
    ),
    ("dac_data", 0,
        Subsignal("db0", Pins("V13")),
        Subsignal("db1", Pins("W11")),
        Subsignal("db2", Pins("AB17")),
        Subsignal("db3", Pins("AB16")),
        Subsignal("db4", Pins("AB15")),
        Subsignal("db5", Pins("AA16")),
        Subsignal("db6", Pins("W16")),
        Subsignal("db7", Pins("T15")),
        Subsignal("db8", Pins("V10")),
        Subsignal("db9", Pins("AA15")),
        Subsignal("db10", Pins("T14")),
        Subsignal("db11", Pins("Y16")),
        Subsignal("db12", Pins("W15")),
        Subsignal("db13", Pins("W10")),
        IOStandard("LVCMOS18")
    ),
    ("dac_afe", 0,
        Subsignal("ch1_pd_n", Pins("Y18")),
        Subsignal("ch2_pd_n", Pins("Y19")),
        IOStandard("LVCMOS18")
    ),
]

_io_adc_aux = [
    ("adc_aux", 0,
        Subsignal("douta", Pins("C17")),
        Subsignal("doutb", Pins("B18")),
        Subsignal("cs_n", Pins("D17")),
        Subsignal("range", Pins("D14")),
        Subsignal("sclk", Pins("E13")),
        Subsignal("sgl", Pins("E17")),
        Subsignal("a0", Pins("A13")),
        Subsignal("a1", Pins("C13")),
        Subsignal("a2", Pins("B13")),
        IOStandard("LVCMOS33")
    )
]

_io_aux_dac = [
    ("aux_dac_ctrl", 0,
        Subsignal("ldac_n", Pins("E14")),
        Subsignal("bin", Pins("D16")),
        Subsignal("clr_n", Pins("D15")),
        IOStandard("LVCMOS33")
    ),
    ("aux_dac_spi", 0,
        Subsignal("sclk", Pins("F16")),
        Subsignal("sdi", Pins("F14")),
        Subsignal("sdo", Pins("F13")),
        Subsignal("sync_n", Pins("E16")),
        IOStandard("LVCMOS33")
    )
]

_io_sd_card = [
    ("sd_card", 0,
        Subsignal("dat3", Pins("AA13")),
        Subsignal("dat2", Pins("AB13")),
        Subsignal("dat1", Pins("Y12")),
        Subsignal("dat0", Pins("Y11")),
        Subsignal("cmd", Pins("AA11")),
        Subsignal("clk", Pins("AA10")),
        IOStandard("LVCMOS18")
    )   
]

_connectors = [
    ("eem0", {
        "d0_cc_n": "L20",
        "d0_cc_p": "L19",
        "d1_n": "M16",
        "d1_p": "M15",
        "d2_n": "H15",
        "d2_p": "J15",
        "d3_n": "H18",
        "d3_p": "H17",
        "d4_n": "G18",
        "d4_p": "G17",
        "d5_n": "G16",
        "d5_p": "G15",
        "d6_n": "L18",
        "d6_p": "M18",
        "d7_n": "N19",
        "d7_p": "N18",
    }),

    ("gpio", {
        "QSPI_IO3": "C18",
        "QSPI_IO2": "A21",
        "QSPI_IO1": "B21",
        "QSPI_IO0": "C22",
        "QSPI_CLK": "B22",
        "QSPI_CS_N": "E21",
        "HRTIM_CHE1": "G21",
        "HRTIM_CHE2": "D22",
        "HRTIM_CHA1": "E22",
        "HRTIM_CHA2": "F18",
        "LPTIM2_OUT": "D21",
        "UART4_TX": "C14",
        "SPI1_MOSI": "A16",
        "SPI1_MISO": "A15",
        "SPI1_NSS": "B16",
        "SPI1_SCK": "B15",
        "I2C1_SDA": "B17",
        "I2C1_SCL": "A14",
    }),

    ("d_inputs", {
        "di0": "A20",
        "di1": "G22",
    }),
]


class Platform(XilinxPlatform):
    default_clk_name = "Si5388_clk1b"
    default_clk_period = 20.0
    userid = 0xffffffff

    def __init__(self, fpga_family="Artix"):
        if fpga_family == "Artix":
            io = _io + _io_adc + _io_dac + _io_adc_aux + _io_aux_dac + _io_sd_card
            connectors = _connectors
            fpga = "xc7a100t-fgg484-2"
        elif fpga_family == "Kintext":
            pass
        else:
            raise ValueError("Unknown FPGA device ", fpga_family)
        self.fpga_family = fpga_family

        XilinxPlatform.__init__(
            self, fpga, io, connectors, toolchain="vivado"
        )
        self.add_platform_command(
            "set_property PULLDOWN true [get_ports reset]"
        )
        self.toolchain.bitstream_commands.extend([
            "set_property BITSTREAM.CONFIG.UNUSEDPIN PULLDOWN [current_design]",
            "set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]",
            "set_property BITSTREAM.CONFIG.CONFIGRATE 66 [current_design]",
            "set_property CONFIG_VOLTAGE 3.3 [current_design]",
            "set_property CFGBVS VCCO [current_design]",
            "set_property CONFIG_MODE SPIx4 [current_design]",
            "set_property BITSTREAM.CONFIG.SPI_32BIT_ADDR YES [current_design]",
            "set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]",
            "set_property BITSTREAM.CONFIG.M1PIN PULLNONE [current_design]",
            "set_property BITSTREAM.CONFIG.M2PIN PULLNONE [current_design]",
            "set_property BITSTREAM.CONFIG.M0PIN PULLNONE [current_design]",
            "set_property BITSTREAM.CONFIG.USR_ACCESS TIMESTAMP [current_design]",
            "set_property BITSTREAM.CONFIG.USERID \"{:#010x}\" [current_design]".format(self.userid),
        ])

# if __name__ == "__main__":
    # from migen import *
    # from migen.build.generic_platform import *
    # from migen.genlib.io import DifferentialInput

    # class M(Module):
    #     def __init__(self):
    #         self.clock_domains.cd_sys = ClockDomain()
    #         self.led = Signal()

    #         self.sync += [
    #             self.led.eq(~self.led)
    #         ]
        
    # plat = Platform()
    # m = M()
    # m.comb += plat.request("user_led", 0).eq(m.led)
    # clk125 = plat.request("clk125_gtp")
    # #
    # transSignal = Signal()
    # m.specials += \
    #     [Instance("IBUFDS_GTE2",
    #     i_I = clk125.p, i_IB = clk125.n,
    #     o_O = transSignal)]
    
    # m.specials += \
    #     [Instance("BUFG",
    #     i_I = transSignal,
    #     o_O = m.cd_sys.clk)]
    

    # plat.build(m, run=True)
