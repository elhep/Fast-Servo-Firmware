from smbus2 import SMBus

BUS_NO = 0
IC_ADDR = 0x74

PAGE_ADDR = 0x1

OUT0_MUX_SEL_ADDR = 0x15
OUT1_MUX_SEL_ADDR = 0x1A
OUT2_MUX_SEL_ADDR = 0x29
OUT3_MUX_SEL_ADDR = 0x2E

OUT2_AMPL_ADDR = 0x28

OUT3_PDN_ADDR = 0x2B
OUT3_FORMAT_ADDR = 0x2C
OUT3_AMPL_ADDR = 0x2D


N1_DIVIDER_UPDATE_ADDR = 0x17

data_to_write = 0
clk_out_addr = [
    OUT0_MUX_SEL_ADDR,
    OUT1_MUX_SEL_ADDR,
    OUT2_MUX_SEL_ADDR,
    OUT3_MUX_SEL_ADDR,
]


with SMBus(BUS_NO) as bus:

    bus.write_byte_data(IC_ADDR, PAGE_ADDR, 0x0)  # setting page to page 0

    # read device id
    low_word = bus.read_byte_data(IC_ADDR, 0x2)
    high_word = bus.read_byte_data(IC_ADDR, 0x3)

    print(f"DEV ID: 0x{high_word:2x}{low_word:2x}")

    data_to_write = 0x1
    bus.write_byte_data(
        IC_ADDR, PAGE_ADDR, data_to_write
    )  # change to page 1 for output settings

    readback = bus.read_byte_data(IC_ADDR, PAGE_ADDR)
    if data_to_write != readback:
        raise ValueError(f"Failed to set page.")

    for addr in clk_out_addr:
        bus.write_byte_data(IC_ADDR, addr, 1)  # set source to N1

    bus.write_byte_data(IC_ADDR, OUT2_AMPL_ADDR, 13)
    readback = bus.read_byte_data(IC_ADDR, OUT2_AMPL_ADDR)
    # if data_to_write != readback:
    #     raise ValueError(f"Problematic read: {readback}.")

    bus.write_byte_data(IC_ADDR, OUT2_AMPL_ADDR, 0x6B)  # setting OUT2 to LVDS25

    bus.write_byte_data(IC_ADDR, OUT3_FORMAT_ADDR, 0xCC)  # SETTING out3 to LVCMOS 18
    # bus.write_byte_data(IC_ADDR, 0x2E, 0x09)		# SETTING out3 to LVCMOS 33

    readback = bus.read_byte_data(IC_ADDR, OUT3_PDN_ADDR)
    print(f"Si5340 OUTx_PDN CLK3: 0x{readback}")

    readback = bus.read_byte_data(IC_ADDR, OUT3_FORMAT_ADDR)
    print(f"Si5340 OUTx_FORMAT CLK3: 0x{readback}")

    readback = bus.read_byte_data(IC_ADDR, OUT3_AMPL_ADDR)
    print(f"Si5340 OUTx_AMPL CLK3: 0x{readback}")

    readback = bus.read_byte_data(IC_ADDR, OUT3_MUX_SEL_ADDR)
    print(f"Si5340 OUTx_CM CLK3: 0x{readback}")

    bus.write_byte_data(
        IC_ADDR, PAGE_ADDR, 0x3
    )  # setting page to 3 to change dividers values

    n1_numerator = [0x0, 0x0, 0x0, 0x60, 0x22, 0x0]
    n1_numerator_10M = [0x0, 0x0, 0x0, 0xC0, 0x57, 0x1]
    n1_num_addr = [0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12]
    n1_denom_addr = [0x13, 0x14, 0x15, 0x16]
    for addr, value in zip(n1_num_addr, n1_numerator):
        bus.write_byte_data(IC_ADDR, addr, value)

    bus.write_byte_data(IC_ADDR, N1_DIVIDER_UPDATE_ADDR, 1)

    for addr in n1_num_addr:
        readback = bus.read_byte_data(IC_ADDR, addr)
        print(f"Numerator buffer: 0x{readback:02x}")

    for addr in n1_denom_addr:
        readback = bus.read_byte_data(IC_ADDR, addr)
        print(f"Denominator buffer: 0x{readback:02x}")

    bus.write_byte_data(IC_ADDR, PAGE_ADDR, 0x0)  # setting page to page 0
