from migen import *

class TimeMGMT(Module):
    def __init__(self):
        self.i_dco = Signal()
        self.i_rst = Signal()



        self.clock_domains.cd_dco = ClockDomain()
        self.clock_domains.cd_dco2d = ClockDomain()

        self.mmcm_locked = Signal()
        mmcm_feedback = Signal()

        self.specials += [
            Instance("MMCME2_BASE",
            # params
            
            # Artix 7 VCO has to operate with the frequency > 600 MHz, Fvco = Fclkin *MULT_F/DIVCLK 
            # so Fvco = 800 MHz
                p_CLKFBOUT_MULT_F = 4.0,    
                p_CLKFBOUT_PHASE = 0.0,
                p_CLKIN1_PERIOD = 5.0,  # 5 ns if 200 MHz, 4 ns if 250 MHz
                
                p_CLKOUT1_DIVIDE = 4,   # DCO (frequency)
                p_CLKOUT2_DIVIDE = 8,  # DCO/2  

                p_CLKOUT1_DUTY_CYCLE = 0.5,
                p_CLKOUT2_DUTY_CYCLE = 0.5,
                
                p_CLKOUT1_PHASE = 0.0,
                p_CLKOUT2_PHASE = 0.0,

                p_DIVCLK_DIVIDE = 1,   

            # MMCM ports
                i_CLKIN1 = self.i_dco,
                i_RST = self.i_rst,

                o_CLKOUT1 = self.cd_dco.clk,
                o_CLKOUT2 = self.cd_dco2d.clk,
                
                i_CLKFBIN = mmcm_feedback,
                o_CLKFBOUT = mmcm_feedback, 

                o_LOCKED = self.mmcm_locked
            )
        ]
