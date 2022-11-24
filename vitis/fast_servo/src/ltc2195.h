/*
 * ltc2195.h
 *
 *  Created on: Oct 5, 2022
 *      Author: Jakub Matyas
 */

#ifndef SRC_LTC2195_H_
#define SRC_LTC2195_H_

#include <xspips.h>

int config_main_adc_spi(XSpiPs *SPI_Instance, uint8_t slave_no);
void main_adc_config(XSpiPs *SPI_Instance, uint8_t test_mode);
uint16_t main_adc_set_test_pattern(XSpiPs *SPI_Instance, uint16_t pattern);



#endif /* SRC_LTC2195_H_ */
