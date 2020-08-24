from migen import *
from dsp import DSPWidths
from controller import PID
from adc import ADCParams
import adc_test
import dsp_test

import logging

logger = logging.getLogger(__name__)


class PIDSimulation(PID):
    def __init__(self):
        self.filter_p = filter_p = DSPWidths(data=25, coeff=18, accu=48, adc=16, dac=14, norm_factor=8, coeff_shift=11)
        self.adc_p = adc_p = ADCParams(out_width=16)

        self.submodules.adc_tb = adc_test.TB(self.adc_p)
        self.iir_tb = dsp_test.IIRSimulation()
        
        PID.__init__(self, filter_p, adc_p, self.adc_tb, None)

        cd_dac = ClockDomain("dac", reset_less=True)
        self.clock_domains += cd_dac
        cd_dsp4 = ClockDomain("dsp4", reset_less=True)
        self.clock_domains += cd_dsp4


    def test_pid(self):
        filter_p = self.filter_p

        Kp = 15
        Ki = 0
        Kd = 0
        # Ki = 1
        # Kd = 1e-7

        yield from self.iir.set_pid_coeff(0, Kp, Ki, Kd)
        
        # abstraction layer useful for testing
        yield self.adc_tb.deser_a.undertest.eq(1) 
        yield self.adc_tb.deser_b.undertest.eq(1) 
        yield self.adc_tb.deser_c.undertest.eq(1) 
        yield self.adc_tb.deser_d.undertest.eq(1) 
        yield 

        # first sample
        sdoa = 15-9
        sdob = 15
        sdoc = 15
        sdod = 15
        x0 = (sdod<<12 | sdoc <<8 | sdob << 4 | sdoa)

        yield self.adc_tb.deser_a.test_data.eq(sdoa)
        yield self.adc_tb.deser_b.test_data.eq(sdob)
        yield self.adc_tb.deser_c.test_data.eq(sdoc)
        yield self.adc_tb.deser_d.test_data.eq(sdod)
        yield
        
        # second sample
        sdoa = 0
        sdob = 15
        sdoc = 15
        sdod = 15
        x1 = (sdod<<12 | sdoc <<8 | sdob << 4 | sdoa)

        yield self.adc_tb.deser_a.test_data.eq(sdoa)
        yield self.adc_tb.deser_b.test_data.eq(sdob)
        yield self.adc_tb.deser_c.test_data.eq(sdoc)
        yield self.adc_tb.deser_d.test_data.eq(sdod)
        yield
        
        # third sample
        sdoa = 1
        sdob = 2
        sdoc = 15
        sdod = 0
        x2 = (sdod<<12 | sdoc <<8 | sdob << 4 | sdoa)

        yield self.adc_tb.deser_a.test_data.eq(sdoa)
        yield self.adc_tb.deser_b.test_data.eq(sdob)
        yield self.adc_tb.deser_c.test_data.eq(sdoc)
        yield self.adc_tb.deser_d.test_data.eq(sdod)
        yield
        
        yield self.adc_tb.deser_a.test_data.eq(0)
        yield self.adc_tb.deser_b.test_data.eq(0)
        yield self.adc_tb.deser_c.test_data.eq(0)
        yield self.adc_tb.deser_d.test_data.eq(0)
        yield
        for i in range(20):
            yield


    def run(self):
        run_simulation(self, [self.test_pid()],
                vcd_name="pid_test.vcd",
                clocks = {
                    "sys":   (8, 0),
                    "dac":   (4, 0),
                    "dsp4":  (2, 0),
                },
        )


def main():
    pid = PIDSimulation()
    pid.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

