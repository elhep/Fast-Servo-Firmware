from migen import *
from collections import namedtuple


SPIParams = namedtuple("SPIParams", [
    "data_width",   # width of one portion of data to be transferred
    "clk_width",    # clock half cycle width
    "msb_first",    # whether transmission should be MSB or LSB first (1/0)
])

class SPI(Module):
    def __init__(self, pads, params):
        
        self.data = Signal(params.data_width, reset_less=True)

        sr_data = Signal.like(self.data)    # shift register with input data latched in it

        self.enable = Signal()           
        self.ready = Signal()           

        msb_first = Signal()

        clk_counter = Signal(max=params.clk_width)
        clk_cnt_done = Signal()
        
        bits = Signal(max = params.data_width)
        
        cnt_load = Signal()
        cnt_done = Signal()

        data_load = Signal()

        
        ###

        assert params.clk_width >= 1
        assert params.msb_first == 0 or params.msb_first == 1

        # counter to generate clock enable signal every 2*clk_width sys_clk cycles
        self.comb += clk_cnt_done.eq(clk_counter == 0)
        self.sync += [
            If(clk_cnt_done, 
                If(cnt_load,
                    clk_counter.eq(params.clk_width - 1),
                )
            ).Else(
                clk_counter.eq(clk_counter-1)
            )
        ]
        
        self.submodules.fsm = fsm = CEInserter()(FSM("IDLE"))
        self.comb += fsm.ce.eq(clk_cnt_done)
    

        self.comb += [
            msb_first.eq(params.msb_first),
            pads.sdi.eq(Mux(msb_first, sr_data[-1], sr_data[0]))       
        ]
        
        fsm.act("IDLE",
            self.ready.eq(1),       
            pads.cs.eq(1),
            If(self.enable,
                NextState("START"),
                data_load.eq(1),         # signalling to latch the input data in the shift register
                cnt_load.eq(1),                
            )
        )

        fsm.act("START",
            pads.cs.eq(0),
            cnt_load.eq(1),
            NextState("SETUP"),
        )
        
        fsm.act("SETUP",
            cnt_load.eq(1),
            NextState("HOLD"),
         
            pads.cs.eq(0),           # chip select driven low
            pads.sclk.eq(0),            
                                        
        )

        fsm.act("HOLD",
            pads.cs.eq(0),
            pads.sclk.eq(1),
            If(bits == 0,               # if the whole word has been transmitted, go to IDLE
                NextState("IDLE")
            ).Else(
                cnt_load.eq(1),
                NextState("SETUP")
            )
        )

        self.sync += [
            If(fsm.ce,
                # counts down how many bits are left to be transmitted 
                # and shifts output register by one bit to the left
                If(fsm.before_leaving("HOLD"),
                
                    If(bits == 0,
                        bits.eq(params.data_width-1),
                    ).Else(
                        bits.eq(bits - 1),
                        sr_data.eq(Mux(msb_first, 
                                    Cat(0, sr_data[:-1]),
                                    Cat(sr_data[1:], 0)
                                    )),
                        # sr_data.eq(Cat(sr_data[1:], 0))         # LSB first
                        # sr_data.eq(Cat(0, sr_data[:-1])),         # MSB first
                    )
                ),

                If(fsm.ongoing("IDLE"),
                    bits.eq(params.data_width-1)
                ),
                
                # # Shiftin data is needed for multi-word transmissions
                # If(fsm.ongoing("DELAY"),
                #     bits.eq(params.data_width-1),
                    
                #     sr_data.eq(Mux(msb_first,
                #                 Cat(0, sr_data[:-1]),
                #                 Cat(sr_data[1:], 0)
                #                 )),
                #     # # sr_data.eq(Cat(sr_data[1:], 0))         # LSB first
                #     # sr_data.eq(Cat(0, sr_data[:-1]))         # MSB first
                # ),
                If(data_load,
                    sr_data.eq(self.data), 
                )
            )
        ]