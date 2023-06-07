
# Creates a project
create_project -force -name top -dir ../builds/fast_servo_bd -part xc7z015-clg485-1

set origin_dir ".."
set_property -name "board_part_repo_paths" -value "[file normalize "$origin_dir/block_design/board_files"]" -objects [current_project]
set_property -name "board_part" -value "trenz.biz:te0715_15_1c:part0:1.1" -objects [current_project]
set_property -name "platform.board_id" -value "te0715_15_1c" -objects [current_project]



# Create block design

create_bd_design zynq

set ip_obj [get_ipdefs -all xilinx.com:ip:processing_system7:5.5]
set parentCell [get_bd_cells /]
set parentObj [get_bd_cells $parentCell]
set parentType [get_property TYPE $parentObj]

# Save current instance; Restore later
set oldCurInst [current_bd_instance .]

# Set parent object as current

current_bd_instance $parentObj

# Set ports 
set I2C0 [ create_bd_intf_port -mode Master -vlnv xilinx.com:interface:iic_rtl:1.0 I2C0 ]
set DDR [ create_bd_intf_port -mode Master -vlnv xilinx.com:interface:ddrx_rtl:1.0 DDR ]
set MIO [ create_bd_intf_port -mode Master -vlnv xilinx.com:display_processing_system7:fixedio_rtl:1.0 MIO ]
set SPI0 [ create_bd_intf_port -mode Master -vlnv xilinx.com:interface:spi_rtl:1.0 SPI0 ]
set SPI1 [ create_bd_intf_port -mode Master -vlnv xilinx.com:interface:spi_rtl:1.0 SPI1 ]
set FCLK_RESET0_N [ create_bd_port -dir O -type rst FCLK_RESET0_N ]
set M_AXI_GP0_ACLK [ create_bd_port -dir I -type clk M_AXI_GP0_ACLK ]

create_bd_port -dir IO DDR_VRN
create_bd_port -dir IO DDR_VRP

create_bd_port -dir IO PS_CLK
create_bd_port -dir IO PS_PORB
create_bd_port -dir IO PS_SRSTB


set M_AXI_GP0 [ create_bd_intf_port -mode Master -vlnv xilinx.com:interface:aximm_rtl:1.0 M_AXI_GP0 ]
set_property -dict [ list CONFIG.ASSOCIATED_BUSIF {M_AXI_GP0} CONFIG.FREQ_HZ {100000000}  ] $M_AXI_GP0_ACLK

# Processing System instance
set ps7 [ create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7 ]

# TODO: parameterize properties
# Same properties as in gateware
set_property -dict [list \
CONFIG.PCW_PRESET_BANK0_VOLTAGE {LVCMOS 3.3V} \
CONFIG.PCW_PRESET_BANK1_VOLTAGE {LVCMOS 1.8V} \
CONFIG.PCW_CRYSTAL_PERIPHERAL_FREQMHZ {33.333333} \
CONFIG.PCW_QSPI_PERIPHERAL_ENABLE {1} \
CONFIG.PCW_QSPI_GRP_SINGLE_SS_ENABLE {1} \
CONFIG.PCW_SINGLE_QSPI_DATA_MODE {x4} \
CONFIG.PCW_QSPI_QSPI_IO {MIO 1 .. 6} \
CONFIG.PCW_QSPI_GRP_FBCLK_ENABLE {1} \
CONFIG.PCW_SD0_PERIPHERAL_ENABLE {1} \
CONFIG.PCW_SD0_SD0_IO {MIO 40 .. 45} \
CONFIG.PCW_MIO_40_PULLUP {disabled} \
CONFIG.PCW_MIO_41_PULLUP {disabled} \
CONFIG.PCW_MIO_42_PULLUP {disabled} \
CONFIG.PCW_MIO_43_PULLUP {disabled} \
CONFIG.PCW_MIO_44_PULLUP {disabled} \
CONFIG.PCW_MIO_45_PULLUP {disabled} \
CONFIG.PCW_UART0_PERIPHERAL_ENABLE {1} \
CONFIG.PCW_UART0_UART0_IO {MIO 10 .. 11} \
CONFIG.PCW_ACT_ENET0_PERIPHERAL_FREQMHZ {125} \
CONFIG.PCW_ENET0_PERIPHERAL_ENABLE {1} \
CONFIG.PCW_ENET0_ENET0_IO {MIO 16 .. 27} \
CONFIG.PCW_ENET0_GRP_MDIO_ENABLE {1} \
CONFIG.PCW_ENET0_GRP_MDIO_IO {MIO 52 .. 53} \
CONFIG.PCW_USB0_PERIPHERAL_ENABLE {1} \
CONFIG.PCW_USB0_USB0_IO {MIO 28 .. 39} \
CONFIG.PCW_WDT_PERIPHERAL_ENABLE {1} \
CONFIG.PCW_TTC0_PERIPHERAL_ENABLE {1} \
CONFIG.PCW_I2C1_PERIPHERAL_ENABLE {1} \
CONFIG.PCW_I2C1_I2C1_IO {MIO 12 .. 13} \
CONFIG.PCW_UIPARAM_DDR_MEMORY_TYPE {DDR 3 (Low Voltage)} \
CONFIG.PCW_UIPARAM_DDR_PARTNO {MT41J256M16 RE-125} \
CONFIG.PCW_GPIO_MIO_GPIO_ENABLE {1} \
CONFIG.PCW_ENET_RESET_ENABLE {1} \
CONFIG.PCW_ENET0_RESET_ENABLE {1} \
CONFIG.PCW_ENET0_RESET_IO {MIO 50} \
CONFIG.PCW_USB_RESET_ENABLE {1} \
CONFIG.PCW_ENET0_PERIPHERAL_CLKSRC {ARM PLL} \
CONFIG.PCW_USB0_RESET_ENABLE {1} \
CONFIG.PCW_USB0_RESET_IO {MIO 51} \
CONFIG.PCW_I2C_RESET_ENABLE {0} \
CONFIG.PCW_I2C0_GRP_INT_ENABLE {1} \
CONFIG.PCW_I2C0_GRP_INT_IO {EMIO} \
CONFIG.PCW_I2C0_I2C0_IO {EMIO} \
CONFIG.PCW_I2C0_PERIPHERAL_ENABLE {1} \
CONFIG.PCW_I2C_RESET_POLARITY {Active Low} \
] $ps7
set_property -dict [list \
CONFIG.PCW_ACT_SPI_PERIPHERAL_FREQMHZ {10} \
CONFIG.PCW_SPI0_GRP_SS0_ENABLE {1} \
CONFIG.PCW_SPI0_GRP_SS0_IO {EMIO} \
CONFIG.PCW_SPI0_GRP_SS1_ENABLE {1} \
CONFIG.PCW_SPI0_GRP_SS1_IO {EMIO} \
CONFIG.PCW_SPI0_GRP_SS2_ENABLE {1} \
CONFIG.PCW_SPI0_GRP_SS2_IO {EMIO} \
CONFIG.PCW_SPI0_PERIPHERAL_ENABLE {1} \
CONFIG.PCW_SPI0_SPI0_IO {EMIO} \
CONFIG.PCW_SPI_PERIPHERAL_DIVISOR0 {10} \
CONFIG.PCW_SPI_PERIPHERAL_FREQMHZ {166.666666} \
] $ps7
set_property -dict [list \
CONFIG.PCW_ACT_SPI_PERIPHERAL_FREQMHZ {10} \
CONFIG.PCW_SPI1_GRP_SS0_ENABLE {1} \
CONFIG.PCW_SPI1_GRP_SS0_IO {EMIO} \
CONFIG.PCW_SPI1_GRP_SS1_ENABLE {1} \
CONFIG.PCW_SPI1_GRP_SS1_IO {EMIO} \
CONFIG.PCW_SPI1_GRP_SS2_ENABLE {1} \
CONFIG.PCW_SPI1_GRP_SS2_IO {EMIO} \
CONFIG.PCW_SPI1_PERIPHERAL_ENABLE {1} \
CONFIG.PCW_SPI1_SPI1_IO {EMIO} \
CONFIG.PCW_SPI_PERIPHERAL_DIVISOR0 {10} \
CONFIG.PCW_SPI_PERIPHERAL_FREQMHZ {166.666666} \
] $ps7


connect_bd_intf_net -intf_net DDR [get_bd_intf_ports DDR] [get_bd_intf_pins ps7/DDR]
connect_bd_net [get_bd_pins /ps7/DDR_VRN] [get_bd_ports DDR_VRN]
connect_bd_net [get_bd_pins /ps7/DDR_VRP] [get_bd_ports DDR_VRP]

connect_bd_net [get_bd_pins /ps7/PS_SRSTB] [get_bd_ports PS_SRSTB]
connect_bd_net [get_bd_pins /ps7/PS_CLK] [get_bd_ports PS_CLK]
connect_bd_net [get_bd_pins /ps7/PS_PORB] [get_bd_ports PS_PORB]

connect_bd_intf_net -intf_net MIO [get_bd_intf_ports MIO] [get_bd_intf_pins ps7/FIXED_IO]
connect_bd_intf_net -intf_net I2C0 [get_bd_intf_ports I2C0] [get_bd_intf_pins ps7/IIC_0]

connect_bd_intf_net -intf_net SPI0 [get_bd_intf_ports SPI0] [get_bd_intf_pins ps7/SPI_0]
connect_bd_intf_net -intf_net SPI1 [get_bd_intf_ports SPI1] [get_bd_intf_pins ps7/SPI_1]


set_property -dict [list \
CONFIG.PROTOCOL [get_property CONFIG.PROTOCOL [get_bd_intf_pins ps7/M_AXI_GP0]] \
CONFIG.HAS_REGION [get_property CONFIG.HAS_REGION [get_bd_intf_pins ps7/M_AXI_GP0]] \
CONFIG.NUM_READ_OUTSTANDING [get_property CONFIG.NUM_READ_OUTSTANDING [get_bd_intf_pins ps7/M_AXI_GP0]] \
CONFIG.NUM_WRITE_OUTSTANDING [get_property CONFIG.NUM_WRITE_OUTSTANDING [get_bd_intf_pins ps7/M_AXI_GP0]]] $M_AXI_GP0

connect_bd_intf_net -intf_net M_AXI_GP0 [get_bd_intf_ports M_AXI_GP0] [get_bd_intf_pins ps7/M_AXI_GP0]

connect_bd_net -net M_AXI_GP0_ACLK [get_bd_ports M_AXI_GP0_ACLK] [get_bd_pins ps7/M_AXI_GP0_ACLK]
connect_bd_net -net ps7_FCLK_RESET0_N [get_bd_ports FCLK_RESET0_N] [get_bd_pins ps7/FCLK_RESET0_N]

assign_bd_address -offset 0x40000000 -range 8K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs  M_AXI_GP0/Reg] -force

current_bd_instance $oldCurInst
validate_bd_design
save_bd_design

generate_target all [get_files  "[file normalize "$origin_dir/builds/fast_servo_bd/top.srcs/sources_1/bd/zynq/zynq.bd"]"]
make_wrapper -files [get_files "[file normalize "$origin_dir/builds/fast_servo_bd/top.srcs/sources_1/bd/zynq/zynq.bd"]"] -top
read_verilog [file normalize "$origin_dir/builds/fast_servo_bd/top.gen/sources_1/bd/zynq/hdl/zynq_wrapper.v"]
update_compile_order -fileset sources_1

# Export platform

write_hw_platform -fixed -force -file "$origin_dir/builds/fast_servo_hw.xsa"
