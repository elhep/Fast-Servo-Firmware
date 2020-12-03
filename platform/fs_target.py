
#!/usr/bin/env python3

import argparse

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.genlib.cdc import MultiReg
from migen.genlib.io import DifferentialOutput

from misoc.interconnect.csr import *
from misoc.cores import gpio
from misoc.cores.a7_gtp import *
from misoc.integration.builder import builder_args, builder_argdict

from artiq.gateware.amp import AMPSoC
from artiq.gateware import rtio
from artiq.gateware.rtio.phy import ttl_simple, ttl_serdes_7series, edge_counter
from artiq.gateware import eem
from artiq.gateware.drtio.transceiver import gtp_7series
from artiq.gateware.drtio.siphaser import SiPhaser7Series
from artiq.gateware.drtio.wrpll import WRPLL, DDMTDSamplerGTP
from artiq.gateware.drtio.rx_synchronizer import XilinxRXSynchronizer
from artiq.gateware.drtio import *
from artiq.build_soc import *

from fs_misoc_target import (
    BaseSoC, MiniSoC, soc_fast_servo_args, soc_fast_servo_argdict)


import fast_servo

class _FastServoCRG(Module, AutoCSR):
    def __init__(self, platform):
        self.clock_domains.cd_fs = ClockDomain()
        self.clock_domains.cd_dac = ClockDomain()
        self.clock_domains.cd_dsp4x = ClockDomain()
        self.clock_domains.cd_dco = ClockDomain()

        # clk_adc = platform.request("Si5340_clk1")
        # platform.add_period_constraint(clk_adc, 10.)
        clk_dac = platform.request("Si5340_clk2")
        platform.add_period_constraint(clk_dac, 10.)

        adc_ctrl = platform.request("adc_ctrl")
        clk_dco_n, clk_dco_p = adc_ctrl.dco_n, adc_ctrl.dco_p
        platform.add_period_constraint(clk_dco_n, 5.)
        platform.add_period_constraint(clk_dco_p, 5.)
        
        
        self.clk_dco_buf = Signal()

        self.specials += Instance("IBUFGDS",
            i_I=clk_dco_p, i_IB=clk_dco_n,
            o_O=self.clk_dco_buf)

        self.clk_dac_buf = Signal()
        self.specials += Instance("IBUFGDS",
            i_I=clk_dac.p, i_IB=clk_dac.n,
            o_O=self.clk_dac_buf)
            
        # self.clk_adc_buf = Signal()
        # self.specials += Instance("IBUFGDS",
        #     i_CEB=0,
        #     i_I=clk_adc.p, i_IB=clk_adc.n,
        #     o_O=self.clk_adc_buf)


        mmcm_locked = Signal()
        mmcm_fb = Signal()
        mmcm_fs_sys = Signal()
        mmcm_dsp4x = Signal()
        mmcm_dco = Signal()

        self.specials += [
            Instance("MMCME2_BASE",
                p_CLKIN1_PERIOD=5.0,           # assuming adc in signal 100 MHz
                i_CLKIN1=self.clk_dco_buf,

                i_CLKFBIN=mmcm_fb,
                o_CLKFBOUT=mmcm_fb,
                o_LOCKED=mmcm_locked,

                # VCO @ 1GHz with MULT=10
                p_CLKFBOUT_MULT_F=5, p_DIVCLK_DIVIDE=1,

                # ~100MHz
                p_CLKOUT0_DIVIDE_F=8.0, p_CLKOUT0_PHASE=0.0, o_CLKOUT0=mmcm_fs_sys,

                # ~400MHz. 
                p_CLKOUT1_DIVIDE=2.5, p_CLKOUT1_PHASE=0.0, o_CLKOUT1=mmcm_dsp4x,

                # ~200MHz
                p_CLKOUT2_DIVIDE=5, p_CLKOUT2_PHASE=0.0, o_CLKOUT2=mmcm_dco,
            ),
            Instance("BUFG", i_I=mmcm_fs_sys, o_O=self.cd_fs.clk),
            Instance("BUFG", i_I=mmcm_dsp4x, o_O=self.cd_dsp4x.clk),
            Instance("BUFG", i_I=self.clk_dac_buf, o_O=self.cd_dac.clk),
            Instance("BUFG", i_I=mmcm_dco, o_O=self.cd_dco.clk),
            # Instance("BUFG", i_I=self.clk_adc_buf, o_O=self.cd_adc.clk),
            # Instance("BUFG", i_I=self.clk_dac_buf, o_O=self.cd_dac.clk),
        ]

class _RTIOCRG(Module, AutoCSR):
    def __init__(self, platform):
        self.pll_reset = CSRStorage(reset=1)
        self.pll_locked = CSRStatus()
        self.clock_domains.cd_rtio = ClockDomain()
        self.clock_domains.cd_rtiox4 = ClockDomain(reset_less=True)

        clk_synth = platform.request("Si5338_clk0")
        clk_synth_se = Signal()
        platform.add_period_constraint(clk_synth.p, 8.0)
        self.specials += [
            Instance("IBUFGDS",
                p_DIFF_TERM="TRUE", p_IBUF_LOW_PWR="FALSE",
                i_I=clk_synth.p, i_IB=clk_synth.n, o_O=clk_synth_se),
        ]

        pll_locked = Signal()
        rtio_clk = Signal()
        rtiox4_clk = Signal()
        fb_clk = Signal()
        self.specials += [
            Instance("PLLE2_ADV",
                     p_STARTUP_WAIT="FALSE", o_LOCKED=pll_locked,
                     p_BANDWIDTH="HIGH",
                     p_REF_JITTER1=0.001,
                     p_CLKIN1_PERIOD=8.0, p_CLKIN2_PERIOD=8.0,
                     i_CLKIN2=clk_synth_se,
                     # Warning: CLKINSEL=0 means CLKIN2 is selected
                     i_CLKINSEL=0,

                     # VCO @ 1.5GHz when using 125MHz input
                     p_CLKFBOUT_MULT=12, p_DIVCLK_DIVIDE=1,
                     i_CLKFBIN=fb_clk,
                     i_RST=self.pll_reset.storage,

                     o_CLKFBOUT=fb_clk,

                     p_CLKOUT0_DIVIDE=3, p_CLKOUT0_PHASE=0.0,
                     o_CLKOUT0=rtiox4_clk,

                     p_CLKOUT1_DIVIDE=12, p_CLKOUT1_PHASE=0.0,
                     o_CLKOUT1=rtio_clk),
            Instance("BUFG", i_I=rtio_clk, o_O=self.cd_rtio.clk),
            Instance("BUFG", i_I=rtiox4_clk, o_O=self.cd_rtiox4.clk),

            AsyncResetSynchronizer(self.cd_rtio, ~pll_locked),
            MultiReg(pll_locked, self.pll_locked.status)
        ]


def fix_serdes_timing_path(platform):
    # ignore timing of path from OSERDESE2 through the pad to ISERDESE2
    platform.add_platform_command(
        "set_false_path -quiet "
        "-through [get_pins -filter {{REF_PIN_NAME == OQ || REF_PIN_NAME == TQ}} "
            "-of [get_cells -filter {{REF_NAME == OSERDESE2}}]] "
        "-to [get_pins -filter {{REF_PIN_NAME == D}} "
            "-of [get_cells -filter {{REF_NAME == ISERDESE2}}]]"
    )


class StandaloneBase(MiniSoC, AMPSoC):
    mem_map = {
        "cri_con":       0x10000000,
        "rtio":          0x20000000,
        "rtio_dma":      0x30000000,
        "mailbox":       0x70000000
    }
    mem_map.update(MiniSoC.mem_map)

    def __init__(self, gateware_identifier_str=None, **kwargs):
        MiniSoC.__init__(self,
                         cpu_type="or1k",
                         sdram_controller_type="minicon",
                         l2_size=128*1024,
                         integrated_sram_size=8192,
                         ethmac_nrxslots=2,
                         ethmac_ntxslots=2,
                         **kwargs)
        AMPSoC.__init__(self)
        add_identifier(self,gateware_identifier_str=gateware_identifier_str)

        # if self.platform.fpga_family == "v2.0":
        #     self.submodules.error_led = gpio.GPIOOut(Cat(
        #         self.platform.request("error_led")))
        #     self.csr_devices.append("error_led")

        i2c = self.platform.request("i2c")
        self.submodules.i2c = gpio.GPIOTristate([i2c.scl, i2c.sda])
        self.csr_devices.append("i2c")
        self.config["I2C_BUS_COUNT"] = 2
        # self.config["HAS_SI5324"] = None
        # self.config["SI5324_SOFT_RESET"] = None

    def add_rtio(self, rtio_channels):
        self.submodules.rtio_crg = _RTIOCRG(self.platform)
        self.submodules.fs_crg = _FastServoCRG(self.platform)
        self.csr_devices.append("rtio_crg")
        self.csr_devices.append("fs_crg")
        
        fix_serdes_timing_path(self.platform)
        self.submodules.rtio_tsc = rtio.TSC("async", glbl_fine_ts_width=3)
        self.submodules.rtio_core = rtio.Core(self.rtio_tsc, rtio_channels)
        self.csr_devices.append("rtio_core")
        self.submodules.rtio = rtio.KernelInitiator(self.rtio_tsc)
        self.submodules.rtio_dma = ClockDomainsRenamer("sys_kernel")(
            rtio.DMA(self.get_native_sdram_if()))
        self.register_kernel_cpu_csrdevice("rtio")
        self.register_kernel_cpu_csrdevice("rtio_dma")
        self.submodules.cri_con = rtio.CRIInterconnectShared(
            [self.rtio.cri, self.rtio_dma.cri],
            [self.rtio_core.cri])
        self.register_kernel_cpu_csrdevice("cri_con")

        # Only add MonInj core if there is anything to monitor
        if any([len(c.probes) for c in rtio_channels]):
            self.submodules.rtio_moninj = rtio.MonInj(rtio_channels)
            self.csr_devices.append("rtio_moninj")

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.rtio_crg.cd_rtio.clk)

        self.submodules.rtio_analyzer = rtio.Analyzer(self.rtio_tsc, self.rtio_core.cri,
                                                      self.get_native_sdram_if())
        self.csr_devices.append("rtio_analyzer")

class Tester(StandaloneBase):
    """
    Configuration for CI tests. Contains the maximum number of different EEMs.
    """
    def __init__(self, fpga_family=None, **kwargs):
        if fpga_family is None:
            fpga_family = "Artix"
        StandaloneBase.__init__(self, **kwargs)

        # self.config["SI5324_AS_SYNTHESIZER"] = None
        # self.config["SI5324_EXT_REF"] = None
        self.config["RTIO_FREQUENCY"] = "125.0"
        # if fpga_family == "v1.0":
        #     # EEM clock fan-out from Si5324, not MMCX
        #     self.comb += self.platform.request("clk_sel").eq(1)

        self.rtio_channels = []
        eem.DIO.add_std(self, 0,
            ttl_serdes_7series.InOut_8X, ttl_serdes_7series.Output_8X,
            edge_counter_cls=None)

        self.config["HAS_RTIO_LOG"] = None
        self.config["RTIO_LOG_CHANNEL"] = len(self.rtio_channels)
        self.rtio_channels.append(rtio.LogChannel())
        self.add_rtio(self.rtio_channels)

VARIANTS = {cls.__name__.lower(): cls for cls in [Tester]}


def main():
    parser = argparse.ArgumentParser(
        description="ARTIQ device binary builder for Kasli systems")
    builder_args(parser)
    soc_fast_servo_args(parser)
    parser.set_defaults(output_dir="fast_servo")
    parser.add_argument("-V", "--variant", default="tester",
                        help="variant: {} (default: %(default)s)".format(
                            "/".join(sorted(VARIANTS.keys()))))
    parser.add_argument("--with-wrpll", default=False, action="store_true")
    parser.add_argument("--gateware-identifier-str", default=None,
                        help="Override ROM identifier")
    args = parser.parse_args()

    argdict = dict()
    argdict["gateware_identifier_str"] = args.gateware_identifier_str
    variant = args.variant.lower()
    try:
        cls = VARIANTS[variant]
    except KeyError:
        raise SystemExit("Invalid variant (-V/--variant)")

    soc = cls(**soc_fast_servo_argdict(args), **argdict)
    build_artiq_soc(soc, builder_argdict(args))


if __name__ == "__main__":
    main()
