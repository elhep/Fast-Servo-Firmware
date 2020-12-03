#!/usr/bin/env python3

import argparse

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from misoc.cores.sdram_settings import MT41J256M16
from misoc.cores.sdram_phy import a7ddrphy
from misoc.cores import virtual_leds, spi_flash
from misoc.cores.a7_gtp import *
# from misoc.cores.liteeth_mini.phy.rgmii import LiteEthPHYRGMII
from misoc.cores.liteeth_mini.mac import LiteEthMAC
from misoc.integration.soc_sdram import *
from misoc.integration.builder import *

import fast_servo
from rmii import LiteEthPHYRMII

class AsyncResetSynchronizerBUFG(Module):
    def __init__(self, cd, async_reset):
        if not hasattr(async_reset, "attr"):
            i, async_reset = async_reset, Signal()
            self.comb += async_reset.eq(i)
        rst_meta = Signal()
        rst_unbuf = Signal()
        self.specials += [
            Instance("FDPE", p_INIT=1, i_D=0, i_PRE=async_reset,
                i_CE=1, i_C=cd.clk, o_Q=rst_meta,
                attr={"async_reg", "ars_ff1"}),
            Instance("FDPE", p_INIT=1, i_D=rst_meta, i_PRE=async_reset,
                i_CE=1, i_C=cd.clk, o_Q=rst_unbuf,
                attr={"async_reg", "ars_ff2"}),
            Instance("BUFG", i_I=rst_unbuf, o_O=cd.rst)
        ]


class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys4x_dqs = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200 = ClockDomain()
        self.clock_domains.cd_eth_ref = ClockDomain()

        clk50 = platform.request("Si5338_clk1b")
        platform.add_period_constraint(clk50, 20.)
        self.clk50_buf = Signal()
        self.specials += Instance("IBUFG",
            i_I=clk50, o_O=self.clk50_buf)

        mmcm_locked = Signal()
        mmcm_fb = Signal()
        mmcm_sys = Signal()
        mmcm_sys4x = Signal()
        mmcm_sys4x_dqs = Signal()
        pll_locked = Signal()
        pll_fb = Signal()
        pll_clk200 = Signal()
        self.specials += [
            Instance("MMCME2_BASE",
                p_CLKIN1_PERIOD=20.0,
                i_CLKIN1=self.clk50_buf,

                i_CLKFBIN=mmcm_fb,
                o_CLKFBOUT=mmcm_fb,
                o_LOCKED=mmcm_locked,

                # VCO @ 1GHz with MULT=20
                p_CLKFBOUT_MULT_F=20.0, p_DIVCLK_DIVIDE=1,

                # ~125MHz
                p_CLKOUT0_DIVIDE_F=8.0, p_CLKOUT0_PHASE=0.0, o_CLKOUT0=mmcm_sys,

                # ~500MHz. Must be more than 400MHz as per DDR3 specs.
                p_CLKOUT1_DIVIDE=2, p_CLKOUT1_PHASE=0.0, o_CLKOUT1=mmcm_sys4x,
                p_CLKOUT2_DIVIDE=2, p_CLKOUT2_PHASE=90.0, o_CLKOUT2=mmcm_sys4x_dqs,
            ),
            Instance("PLLE2_BASE",
                p_CLKIN1_PERIOD=20.0,
                i_CLKIN1=self.clk50_buf,

                i_CLKFBIN=pll_fb,
                o_CLKFBOUT=pll_fb,
                o_LOCKED=pll_locked,

                # VCO @ 1GHz
                p_CLKFBOUT_MULT=20, p_DIVCLK_DIVIDE=1,

                # 200MHz for IDELAYCTRL
                p_CLKOUT0_DIVIDE=5, p_CLKOUT0_PHASE=0.0, o_CLKOUT0=pll_clk200,
            ),
            Instance("BUFG", i_I=mmcm_sys, o_O=self.cd_sys.clk),
            Instance("BUFG", i_I=mmcm_sys4x, o_O=self.cd_sys4x.clk),
            Instance("BUFG", i_I=mmcm_sys4x_dqs, o_O=self.cd_sys4x_dqs.clk),
            Instance("BUFG", i_I=pll_clk200, o_O=self.cd_clk200.clk),
            Instance("BUFG", i_I=self.clk50_buf, o_O=self.cd_eth_ref.clk),

            AsyncResetSynchronizer(self.cd_clk200, ~pll_locked),
        ]
        self.submodules += AsyncResetSynchronizerBUFG(self.cd_sys, ~mmcm_locked),

        reset_counter = Signal(4, reset=15)
        ic_reset = Signal(reset=1)
        self.sync.clk200 += \
            If(reset_counter != 0,
                reset_counter.eq(reset_counter - 1)
            ).Else(
                ic_reset.eq(0)
            )
        self.specials += Instance("IDELAYCTRL", i_REFCLK=ClockSignal("clk200"), i_RST=ic_reset)


class BaseSoC(SoCSDRAM):
    def __init__(self, sdram_controller_type="minicon", fpga_family=None,
                 **kwargs):
        if fpga_family is None:
            fpga_family = "Artix"
        platform = fast_servo.Platform(fpga_family=fpga_family)

        SoCSDRAM.__init__(self, platform,
                          clk_freq=125e6, cpu_reset_address=0x400000,
                          **kwargs)

        self.config["fpga_family"] = fpga_family

        self.submodules.crg = _CRG(platform)
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/self.clk_freq)

        self.submodules.ddrphy = a7ddrphy.A7DDRPHY(platform.request("ddram"))
        # DDRAM on TE0712 - IM4G16D3EABG is compatible with MT41J256M16 https://www.intelligentmemory.com/dram_ALT/ddr3-sdram/
        sdram_module = MT41J256M16(self.clk_freq, "1:4")        
        self.register_sdram(self.ddrphy, sdram_controller_type,
                            sdram_module.geom_settings, sdram_module.timing_settings)
        self.csr_devices.append("ddrphy")

        # self.submodules.virtual_leds = virtual_leds.VirtualLeds()
        # self.csr_devices.append("virtual_leds")

        if not self.integrated_rom_size:
            spiflash_pads = platform.request("spiflash2x")
            spiflash_pads.clk = Signal()
            self.specials += Instance("STARTUPE2",
                                      i_CLK=0, i_GSR=0, i_GTS=0, i_KEYCLEARB=0, i_PACK=0,
                                      i_USRCCLKO=spiflash_pads.clk, i_USRCCLKTS=0, i_USRDONEO=1, i_USRDONETS=1)
            self.submodules.spiflash = spi_flash.SpiFlash(spiflash_pads, dummy=5, div=2)
            self.config["SPIFLASH_PAGE_SIZE"] = 256
            self.config["SPIFLASH_SECTOR_SIZE"] = 0x10000
            self.flash_boot_address = 0x450000
            self.register_rom(self.spiflash.bus, 16*1024*1024)
            self.csr_devices.append("spiflash")


class MiniSoC(BaseSoC):
    mem_map = {
        "ethmac": 0x30000000,  # (shadow @0xb0000000)
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, *args, ethmac_nrxslots=2, ethmac_ntxslots=2, **kwargs):
        BaseSoC.__init__(self, *args, **kwargs)
        # self.create_qpll()

        self.csr_devices += ["ethphy", "ethmac"]
        self.interrupt_devices.append("ethmac")

        eth = self.platform.request("eth")

        self.submodules.ethphy = LiteEthPHYRMII(ClockSignal("eth_ref"), eth)
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_tx.clk, 20.0)
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_rx.clk, 20.0)
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk)

        # sfp = self.platform.request("sfp", 0)
        # self.submodules.ethphy = A7_1000BASEX(self.ethphy_qpll_channel, sfp, self.clk_freq)
        # self.platform.add_period_constraint(self.ethphy.txoutclk, 16.)
        # self.platform.add_period_constraint(self.ethphy.rxoutclk, 16.)
        # self.platform.add_false_path_constraints(
        #     self.crg.cd_sys.clk,
        #     self.ethphy.txoutclk, self.ethphy.rxoutclk)

        # if self.platform.fpga_family in ("v1.0", "v1.1"):
        #     sfp_ctl = self.platform.request("sfp_ctl", 0)
        #     if hasattr(sfp_ctl, "mod_present"):
        #         mod_present = sfp_ctl.mod_present
        #     else:
        #         mod_present = ~sfp_ctl.mod_present_n
        #     self.comb += [
        #         sfp_ctl.rate_select.eq(0),
        #         sfp_ctl.tx_disable.eq(0),
        #         sfp_ctl.led.eq(~sfp_ctl.los & ~sfp_ctl.tx_fault & mod_present &
        #             self.ethphy.link_up),
        #     ]
        # if self.platform.fpga_family == "v2.0":
        #     self.comb += self.virtual_leds.get(0).eq(self.ethphy.link_up)
        self.submodules.ethmac = LiteEthMAC(
                phy=self.ethphy, dw=32, interface="wishbone",
                nrxslots=ethmac_nrxslots, ntxslots=ethmac_ntxslots)
        ethmac_len = (ethmac_nrxslots + ethmac_ntxslots) * 0x800
        self.add_wb_slave(self.mem_map["ethmac"], ethmac_len, self.ethmac.bus)
        self.add_memory_region("ethmac",
                self.mem_map["ethmac"] | self.shadow_base, ethmac_len)

    # def create_qpll(self):
    #     qpll_settings = QPLLSettings(
    #         refclksel=0b001,
    #         fbdiv=4,
    #         fbdiv_45=5,
    #         refclk_div=1)
    #     qpll = QPLL(self.crg.clk50_buf, qpll_settings)
    #     self.submodules += qpll
    #     self.ethphy_qpll_channel = qpll.channels[0]


def soc_fast_servo_args(parser):
    soc_sdram_args(parser)


def soc_fast_servo_argdict(args):
    r = soc_sdram_argdict(args)
    # r["fpga_family"] = args.fpga_family
    return r


def main():
    parser = argparse.ArgumentParser(description="MiSoC port to Fast Servo")
    builder_args(parser)
    soc_fast_servo_args(parser)
    parser.add_argument("--with-ethernet", action="store_true",
                        help="enable Ethernet support")
    args = parser.parse_args()

    cls = MiniSoC if args.with_ethernet else BaseSoC
    soc = cls(**soc_fast_servo_argdict(args))
    builder = Builder(soc, **builder_argdict(args))
    builder.build()


if __name__ == "__main__":
    main()

