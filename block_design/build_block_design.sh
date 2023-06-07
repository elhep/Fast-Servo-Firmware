set -e
cd block_design
export LC_ALL=C
vivado -mode batch -source block_design.tcl
