from migen import *
from migen.genlib import io
from fs_gateware.adc import ADCParams



class ADCPads(Module):
    def __init__(self, adc_params):
        self.params = p = adc_params
        # self.o_enc = Signal() # encode signal;
        # self.i_dco = Signal() # incoming clock
        self.i_frame = Signal() # framing signal
        
        self.sdos = [Signal(p.lanes) for ch in range(p.channels)]
        
if __name__ == "__main__":
    from fs_gateware.adc import ADC
    from migen.fhdl.verilog import convert


    adc_params = ADCParams(out_width=16, channels=2, lanes=4)
    
    adcPads = ADCPads(adc_params)
    adc = ADC(adc_params, adcPads)
    adcPads.submodules += adc

    convert(adcPads, {adcPads.i_frame, adcPads.sdos[0], adcPads.sdos[1], adc.o_data[0], adc.o_data[1]}, name="adc").write("fs_gateware/tbSrc/adc_verilog.v")
