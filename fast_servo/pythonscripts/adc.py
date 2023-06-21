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
    ADC_AFE_CTRL_ADDR,
    ADC_BITSLIP_ADDR,
    ADC_CH0_HIGH_ADDR,
    ADC_CH0_LOW_ADDR,
    ADC_CH1_HIGH_ADDR,
    ADC_CH1_LOW_ADDR,
    ADC_DELAY_ADDR,
    ADC_FRAME_ADDR,
    AUX_ADC_ADDR,
    MAP_MASK,
    PAGESIZE,
)

# /dev/spidev1.0  <=> spidev<BUS>.<DEVICE>
MAIN_ADC_BUS = 1
MAIN_ADC_DEVICE = 1

AUX_ADC_BUS = 1
AUX_ADC_PORT_A = 2
AUX_ADC_PORT_B = 3


def main_adc_config(test_pattern):
    high_word = (test_pattern & 0xFF00) >> 8
    low_word = test_pattern & 0xFF

    spi = spidev.SpiDev()

    try:
        spi.open(MAIN_ADC_BUS, MAIN_ADC_DEVICE)
        spi.max_speed_hz = 50000
        spi.mode = 0b00  # CPOL = 0 CPHA = 0
        spi.cshigh = True
        # spi.read0 = False

        spi_buffer = [0x00, 0x80]  # reset
        rx_buffer = [0x00, 0x00]

        spi.xfer2(spi_buffer)

        # REGISTER A1
        spi_buffer = [0x01, 0x20]  # set to Two's complement Data Format
        spi.xfer2(spi_buffer)

        # read values back
        spi_buffer = [0x81, 0x00]
        rx_buffer = spi.xfer2(spi_buffer)
        print(f"Spi readback register 0x01: 0x{rx_buffer[1]:02x}")
        if rx_buffer[1] != 0x20:
            print("Different value read than sent in reg 0x02")

        # REGISTER A2
        spi_buffer = [
            0x02,
            0x15,
        ]  # set to LVDS output, set 4 data lanes and turn on test mode
        spi.xfer2(spi_buffer)

        # read values back
        spi_buffer = [0x82, 0x00]
        rx_buffer = spi.xfer2(spi_buffer)
        print(f"Spi readback register 0x02: 0x{rx_buffer[1]:02x}")
        if rx_buffer[1] != 0x15:
            print("Different value read than sent in reg 0x02")

        # REGISTER A3
        # test pattern high word
        spi_buffer = [0x03, high_word]
        spi.xfer2(spi_buffer)

        # read balues back
        spi_buffer = [0x83, 0x00]
        rx_buffer = spi.xfer2(spi_buffer)
        print(f"Spi readback register 0x03: 0x{rx_buffer[1]:02x}")
        if rx_buffer[1] != high_word:
            print("Different value read than sent in reg 0x03")

        # REGISTER A4
        # test pattern low word
        spi_buffer = [0x04, low_word]
        spi.xfer2(spi_buffer)

        # read balues back
        spi_buffer = [0x84, 0x00]
        rx_buffer = spi.xfer2(spi_buffer)
        print(f"Spi readback register 0x04: 0x{rx_buffer[1]:02x}")
        if rx_buffer[1] != low_word:
            print("Different value read than sent in reg 0x04")
    finally:
        spi.close()


def main_adc_test_mode(enable):
    spi = spidev.SpiDev()

    try:
        spi.open(MAIN_ADC_BUS, MAIN_ADC_DEVICE)
        spi.max_speed_hz = 50000
        spi.mode = 0b00  # CPOL = 0 CPHA = 0
        spi.cshigh = True
        # spi.read0 = True

        reg_contents = (
            0x15 if enable else 0x11
        )  # set to LVDS output, set 4 data lanes and turn on or off test mode
        spi_buffer = [0x02, reg_contents]
        spi.xfer2(spi_buffer)

        # read values back
        spi_buffer = [0x82, 0x00]
        rx_buffer = spi.xfer2(spi_buffer)
        print(f"Spi readback register 0x02: 0x{rx_buffer[1]:02x}")
        if rx_buffer[1] != reg_contents:
            print("Different value read than sent in reg 0x02")
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
            # print("Read value: ", read_value)
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
            # print(f"addr: 0x{addr:x}\tstart_addr: 0x{start_addr}\tstop_addr: 0x{stop_addr}")
            mem[start_addr:stop_addr] = value_bytes
            contents = mem[start_addr:stop_addr]
            # print("Read value: ", list(contents), " written value: ", list(value_bytes))
    finally:
        os.close(f)


def word_align():

    value = 0
    edge_detected = False
    transition = False
    tap_delay = 0

    for i in range(4):
        current_frame = read_from_memory(ADC_FRAME_ADDR, 1)[0]
        if current_frame != 0x0C:
            print(
                f"Performing bitslip (bitslip iteration: {i}). Reason: current_frame is 0x{current_frame:02x} instead of 0x0C"
            )
            write_to_memory(ADC_BITSLIP_ADDR, 1)
        else:
            print(f"No bitslip required; Currernt frame = 0x{current_frame:02x}")
            break

    current_frame = read_from_memory(ADC_FRAME_ADDR, 1)[0]
    prev_frame = current_frame

    for i in range(32):
        write_to_memory(ADC_DELAY_ADDR, tap_delay)
        if edge_detected == 1:
            break
        current_frame = read_from_memory(ADC_FRAME_ADDR, 1)[0]

        print(f"Tap delay: {tap_delay}")
        print(f"Current frame: 0x{current_frame:02x}")

        if current_frame == prev_frame:
            tap_delay += 1
        elif not transition:
            tap_delay += 1
            transition = True
        elif transition:
            tap_delay = i // 2
            edge_detected = True

        prev_frame = current_frame

    if not edge_detected:
        tap_delay = 11  # empirically tested to work best
        write_to_memory(ADC_DELAY_ADDR, tap_delay)
        print(f"No edge detected; setting iDelay to: {tap_delay}")
    if edge_detected:
        write_to_memory(ADC_DELAY_ADDR, tap_delay + 2)
        print(f"Edge detected; setting iDelay to (tap_delay + 2): {tap_delay} + 2")

    adc_ch0 = read_from_memory(ADC_CH0_HIGH_ADDR, 4)
    print(f"ADC_CH0: 0x{adc_ch0}")

    adc_ch0 = (read_from_memory(ADC_CH0_HIGH_ADDR, 1)[0] << 8) | read_from_memory(
        ADC_CH0_LOW_ADDR, 1
    )[0]
    adc_ch1 = (read_from_memory(ADC_CH1_HIGH_ADDR, 1)[0] << 8) | read_from_memory(
        ADC_CH1_LOW_ADDR, 1
    )[0]
    print(f"Final ADC_CH0: 0x{adc_ch0:04x}")
    print(f"Final ADC_CH1: 0x{adc_ch1:04x}")


def modify_bit(original_value, position, bit_value):
    mask = 1 << position
    return (original_value & ~mask) | (bit_value << position)


def adc_aux_config():
    # MSB to LSB
    # | RANGE | ADDR [2:0] | DIFF |
    #       DIFF = 0    =>  configure as single ended (it is negated in gateware)
    #       RANGE = 0   =>  configure as 0-2.5 Vref
    to_write = 0b00000
    write_to_memory(AUX_ADC_ADDR, to_write)


def adc_aux_read(port, type, pin):
    # port:
    #   1 - port A
    #   2 - port B
    # type:
    #   0 - single-ended
    #   1 - differential
    # pin:
    #   0b000   - VA1/VB1
    #   0b001   - VA2/VB2
    #   0b010   - VA3/VB3
    #   0b011   - VA4/VB4

    assert type in (0, 1)
    assert port in (1, 2)

    write_buffer = [0, 0]
    read_buffer = [0, 0]

    aux_config_reg = read_from_memory(AUX_ADC_ADDR, 1)[0]
    aux_config = (aux_config_reg & 0b10001) | pin << 1
    write_to_memory(AUX_ADC_ADDR, aux_config)

    spi = spidev.SpiDev()
    try:
        spi.open(1, 3)  # AUX ADC 1?
        spi.max_speed_hz = 5000
        spi.mode = 0b00
        spi.cshigh = True

        read_buffer = spi.xfer2(write_buffer)
        mu_voltage = read_buffer[0] << 8 | read_buffer[1] >> 2
        print(f"MU_voltage: 0x{mu_voltage:04X}")
        print(f"Read_buffer[0]: 0x{read_buffer[0]:02X}")
        print(f"Read_buffer[1]: 0x{read_buffer[1]:02X}")
        return mu_voltage * 2.5 / 4096

    finally:
        spi.close()


def main():
    main_adc_config(0x811F)
    word_align()

    main_adc_test_mode(False)

    write_to_memory(ADC_AFE_CTRL_ADDR, 0b1100) # {-, -, ch2_X10, ch1_X10}
    print(read_from_memory(ADC_AFE_CTRL_ADDR, 1)[0])


if __name__ == "__main__":
    main()