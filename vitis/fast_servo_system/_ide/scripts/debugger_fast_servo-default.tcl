# Usage with Vitis IDE:
# In Vitis IDE create a Single Application Debug launch configuration,
# change the debug type to 'Attach to running target' and provide this 
# tcl script in 'Execute Script' option.
# Path of this script: /home/jmatyas/Develop/fast-digital-servo/vitis/fast_servo_system/_ide/scripts/debugger_fast_servo-default.tcl
# 
# 
# Usage with xsct:
# To debug using xsct, launch xsct and run below command
# source /home/jmatyas/Develop/fast-digital-servo/vitis/fast_servo_system/_ide/scripts/debugger_fast_servo-default.tcl
# 
connect -url tcp:127.0.0.1:3121
targets -set -nocase -filter {name =~"APU*"}
rst -system
after 3000
targets -set -filter {jtag_cable_name =~ "Digilent JTAG-HS3 210299A57926" && level==0 && jtag_device_ctx=="jsn-JTAG-HS3-210299A57926-0373b093-0"}
fpga -file /home/jmatyas/Develop/fast-digital-servo/vitis/fast_servo/_ide/bitstream/design_1_wrapper.bit
targets -set -nocase -filter {name =~"APU*"}
loadhw -hw /home/jmatyas/Develop/fast-digital-servo/vitis/fast_servo_platform/export/fast_servo_platform/hw/design_1_wrapper.xsa -mem-ranges [list {0x40000000 0xbfffffff}] -regs
configparams force-mem-access 1
targets -set -nocase -filter {name =~"APU*"}
source /home/jmatyas/Develop/fast-digital-servo/vitis/fast_servo/_ide/psinit/ps7_init.tcl
ps7_init
ps7_post_config
targets -set -nocase -filter {name =~ "*A9*#0"}
dow /home/jmatyas/Develop/fast-digital-servo/vitis/fast_servo/Debug/fast_servo.elf
configparams force-mem-access 0
targets -set -nocase -filter {name =~ "*A9*#0"}
con
