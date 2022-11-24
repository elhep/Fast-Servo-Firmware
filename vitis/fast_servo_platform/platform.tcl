# 
# Usage: To re-create this platform project launch xsct with below options.
# xsct /home/jmatyas/Develop/fast-digital-servo/vitis/fast_servo_platform/platform.tcl
# 
# OR launch xsct and run below command.
# source /home/jmatyas/Develop/fast-digital-servo/vitis/fast_servo_platform/platform.tcl
# 
# To create the platform in a different location, modify the -out option of "platform create" command.
# -out option specifies the output directory of the platform project.

platform create -name {fast_servo_platform}\
-hw {/home/jmatyas/Develop/fast-digital-servo/vitis/hw_desc/design_1_wrapper.xsa}\
-proc {ps7_cortexa9_0} -os {standalone} -fsbl-target {psu_cortexa53_0} -out {/home/jmatyas/Develop/fast-digital-servo/vitis}

platform write
platform generate -domains 
platform active {fast_servo_platform}
platform generate
platform clean
platform generate
platform generate
platform clean
platform clean
platform generate
