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

CSR_SIZE = 0x800
MAP_SIZE = 0x1000
MAP_MASK = 0xFFF
PAGESIZE = 0x1000

LINIEN_OFFSET = 0x0
# LINIEN_OFFSET = 0x300000

# ----------------------------------------------------------------
# FRONT PANEL LEDS REGISTER ADDRESSES
LED0_BASE_ADDR = 0x40005000 + LINIEN_OFFSET
LED1_BASE_ADDR = 0x40005800 + LINIEN_OFFSET
LED2_BASE_ADDR = 0x40006000 + LINIEN_OFFSET
LED3_BASE_ADDR = 0x40006800 + LINIEN_OFFSET


# ----------------------------------------------------------------
# DAC REGISTER ADDRESSES
ADC_BASE_ADDR            =      0x40004800 + LINIEN_OFFSET
ADC_FRAME_OFFSET         =      0x0
ADC_CH0_HIGH_OFFSET      =      0x4
ADC_CH0_LOW_OFFSET       =      0x8
ADC_CH1_HIGH_OFFSET      =      0xC
ADC_CH1_LOW_OFFSET       =      0x10
ADC_TAP_DELAY_OFFSET     =      0x14
ADC_BITSLIP_OFFSET       =      0x18
ADC_AFE_CTRL_OFFSET     =       0x1C


ADC_FRAME_ADDR      =   ADC_BASE_ADDR + ADC_FRAME_OFFSET
ADC_CH0_HIGH_ADDR   =   ADC_BASE_ADDR + ADC_CH0_HIGH_OFFSET
ADC_CH0_LOW_ADDR    =   ADC_BASE_ADDR + ADC_CH0_LOW_OFFSET
ADC_CH1_HIGH_ADDR   =   ADC_BASE_ADDR + ADC_CH1_HIGH_OFFSET
ADC_CH1_LOW_ADDR    =   ADC_BASE_ADDR + ADC_CH1_LOW_OFFSET
ADC_DELAY_ADDR      =   ADC_BASE_ADDR + ADC_TAP_DELAY_OFFSET
ADC_BITSLIP_ADDR    =   ADC_BASE_ADDR + ADC_BITSLIP_OFFSET
ADC_AFE_CTRL_ADDR   =   ADC_BASE_ADDR + ADC_AFE_CTRL_OFFSET

AUX_ADC_ADDR        =   0x40007800 + LINIEN_OFFSET


# ----------------------------------------------------------------
# DAC REGISTER ADDRESSES
DAC_BASE_ADDR           =   0x40007000 + LINIEN_OFFSET
CTRL_OFFSET             =   0x0
CH0_HIGH_WORD_OFFSET    =   0x4
CH0_LOW_WORD_OFFSET     =   0x8
CH1_HIGH_WORD_OFFSET    =   0xC
CH1_LOW_WORD_OFFSET     =   0x10

CTRL_ADDR               =   DAC_BASE_ADDR + CTRL_OFFSET
CH0_HIGH_WORD_ADDR      =   DAC_BASE_ADDR + CH0_HIGH_WORD_OFFSET
CH0_LOW_WORD_ADDR       =   DAC_BASE_ADDR + CH0_LOW_WORD_OFFSET
CH1_HIGH_WORD_ADDR      =   DAC_BASE_ADDR + CH1_HIGH_WORD_OFFSET
CH1_LOW_WORD_ADDR       =   DAC_BASE_ADDR + CH1_LOW_WORD_OFFSET