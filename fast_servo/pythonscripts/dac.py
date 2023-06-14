# This file is part of Fast Servo Software Package.
#
# Copyright (C) 2023 Jakub Matyas
# Warsaw University of Technology <jakubk.m@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import mmap
import os

import spidev
from common import (
    CH0_HIGH_WORD_ADDR,
    CH0_LOW_WORD_ADDR,
    CH1_HIGH_WORD_ADDR,
    CH1_LOW_WORD_ADDR,
    CTRL_ADDR,
    MAP_MASK,
    PAGESIZE,
)

# /dev/spidev2.0  <=> spidev<BUS>.<DEVICE>
MAIN_DAC_BUS = 2
MAIN_DAC_DEVICE = 0

DAC_VERSION = 0x0A


def main_dac_init():
    spi = spidev.SpiDev()

    try:
        spi.open(MAIN_DAC_BUS, MAIN_DAC_DEVICE)
        spi.max_speed_hz = 5000
        spi.mode = 0b00  # CPOL = 0 CPHA = 0
        spi.cshigh = True

        spi_buffer = [0x00, 0x10]  # software reset
        spi.xfer2(spi_buffer)

        spi_buffer = [0x00, 0x00]  # release software reset
        spi.xfer2(spi_buffer)

        spi_buffer = [
            0x80,
            0x00,
        ]  # for some reason it is needed to read the reset address for reset to actually reset
        rx_buffer = spi.xfer2(spi_buffer)

        spi_buffer = [0x9F, 0x00]  # hardware version
        rx_buffer = spi.xfer2(spi_buffer)
        if rx_buffer[1] != DAC_VERSION:
            print(f"Unrecognized device: 0x{rx_buffer[1]:02X}")

        print("=== Contents of spi buffer after DAC VERSION read back: ===")
        print(f"0x{rx_buffer[0]:02X}{rx_buffer[1]:02X}")

        spi_buffer = [0x82, 00]
        rx_buffer = spi.xfer2(spi_buffer)
        print(f"0x{rx_buffer[0]:02X}{rx_buffer[1]:02X}")

        spi_buffer = [0x02, 0xB4]
        rx_buffer = spi.xfer2(spi_buffer)
        spi_buffer = [0x82, 00]
        rx_buffer = spi.xfer2(spi_buffer)
        print(f"0x{rx_buffer[0]:02X}{rx_buffer[1]:02X}")

        for i in range(10):
            spi_buffer = [0x94, 0x00]
            rx_buffer = spi.xfer2(spi_buffer)
            print(f"0x{rx_buffer[0]:02X}{rx_buffer[1]:02X}")

    finally:
        spi.close()


def read_from_memory(address, n_bytes):
    assert n_bytes <= 4
    addr = address

    try:
        f = os.open("/dev/mem", os.O_SYNC | os.O_RDWR)
        with mmap.mmap(
            f,
            PAGESIZE,
            mmap.MAP_SHARED,
            mmap.PROT_READ | mmap.PROT_WRITE,
            offset=addr & ~MAP_MASK,
        ) as mem:
            start_addr = addr & MAP_MASK
            stop_addr = start_addr + 4
            # print(f"addr: 0x{addr:x}\tstart_addr: 0x{start_addr}\tstop_addr: 0x{stop_addr}")
            contents = mem[start_addr:stop_addr]
            read_value = list(contents)[:n_bytes]
    finally:
        os.close(f)

    return read_value


def write_to_memory(address, value):
    value_bytes = value.to_bytes(4, "little")
    addr = address

    try:
        f = os.open("/dev/mem", os.O_SYNC | os.O_RDWR)
        with mmap.mmap(
            f,
            PAGESIZE,
            mmap.MAP_SHARED,
            mmap.PROT_READ | mmap.PROT_WRITE,
            offset=addr & ~MAP_MASK,
        ) as mem:
            start_addr = addr & MAP_MASK
            stop_addr = start_addr + 4
            mem[start_addr:stop_addr] = value_bytes
            contents = mem[start_addr:stop_addr]
    finally:
        os.close(f)


def manual_override(enable=True):
    reg_contents = read_from_memory(CTRL_ADDR, 1)[0]
    print(f"REG contents: 0b{reg_contents:03b}")
    to_write = reg_contents | 0b1 if enable else reg_contents & 0b110
    write_to_memory(CTRL_ADDR, to_write)


def power_down(channel, power_down=True):
    assert channel in (0, 1)

    bitmask = 1 << (channel + 1) & 0b111
    reg_contents = read_from_memory(CTRL_ADDR, 1)[0]
    value = (1 if power_down else 0) << (channel + 1)
    reg_contents &= ~bitmask

    to_write = reg_contents | value
    write_to_memory(CTRL_ADDR, to_write)
    reg_contents = read_from_memory(CTRL_ADDR, 1)[0]
    print(f"REG contents: 0b{reg_contents:03b}")


def write_sample(channel, sample):
    assert channel in (0, 1)
    if channel == 0:
        addresses = [CH0_HIGH_WORD_ADDR, CH0_LOW_WORD_ADDR]
    else:
        addresses = [CH1_HIGH_WORD_ADDR, CH1_LOW_WORD_ADDR]

    low_word_value = sample & 0xFF
    high_word_value = (sample >> 8) & 0x3F
    values = [high_word_value, low_word_value]
    for addr, value in zip(addresses, values):
        write_to_memory(addr, value)


def write_ramp():
    signal = [i for i in range(16384)]

    for value in signal:
        write_sample(0, value)


if __name__ == "__main__":
    main_dac_init()
    power_down(0, False)
    power_down(1, False)
