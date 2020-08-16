# Fast Servo

Contains:
  * basic DAC support
    * two channels of input data and interleaved output
  * basic PID implemented in IIR structure
    * tries to use Xilinx DSP48 slices; for the moment, it relies on Vivado's ability to infere them
    * two time domains - sys and dsp4 (four times faster clock to achieve results (adding, multiplying) from feedback path in one system clock period)
    * one and two independent channels support
    * each of the filter's coefficient has its own block RAM (it is shared with another channel's corresponding coefficient) - b0, b1, b2 - 3 BRAMs with 36 bit wide  word
  * basic ADC support with bitslip FSM (tested in VHDL)
  * tests of DSP modules and DAC

To be done:
  * code refactoring (especially of ADC)
  * integration
  * integration with ARTIQ and RTIO
  * core device drivers
  * different output modes (IIR and DAC)
  * scale coefficients and shift data vectors in IIR properly


# Minimal bootstrap
  * Clone this repo
  * Make sure you have ARTIQ properly installed
  * Append this repo's root to ARTIQ's PYTHONPATH
  * Execute python programs, e.g.:
  ```
  $ python fs_gateware/dsp_test.py
  ```