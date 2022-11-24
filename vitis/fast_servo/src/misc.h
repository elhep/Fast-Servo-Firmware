/*
 * misc.h
 *
 *  Created on: Oct 5, 2022
 *      Author: Jakub Matyas
 */

#ifndef SRC_MISC_H_
#define SRC_MISC_H_

#include <xgpiops.h>
#include <xiicps.h>

#include "i2c_lib.h"
#include "config.h"

static uint8_t gpio_header_pins[18] = {
		QSPI_IO3, QSPI_IO2, QSPI_IO1,
		QSPI_IO0, QSPI_CLK, QSPI_NCS,
		HRTIM_CHE1, HRTIM_CHE2, HRTIM_CHA1,
		HRTIM_CHA2, LPTIM2_OUT, UART4_TX,
		SPI1_MOSI, SPI1_MISO, SPI1_NSS,
		SPI1_SCK, I2C1_SDA, I2C1_SCL
	};

static uint8_t lvds_header_pins[16] = {
		LVDS0_P, LVDS1_P, LVDS2_P, LVDS3_P,
		LVDS4_P, LVDS5_P, LVDS6_P, LVDS7_P,
		LVDS0_N, LVDS1_N, LVDS2_N, LVDS3_N,
		LVDS4_N, LVDS5_N, LVDS6_N, LVDS7_N
	};

void set_dio(XGpioPs *GPIO_Instance, uint8_t pin, uint8_t state);
uint32_t get_dio(XGpioPs *GPIO_Instance, uint8_t pin);
void si5340_config(XIicPs *I2CInstance);
void config_gpio_header(XGpioPs *GPIO_Instance, uint8_t *pins, uint8_t mode_first_half, uint8_t mode_second_half, uint8_t header_length);
uint16_t test_gpio_header(XGpioPs *GPIO_Instance, uint8_t *pins, uint8_t first_half_as_output, uint8_t header_length);


#endif /* SRC_MISC_H_ */
