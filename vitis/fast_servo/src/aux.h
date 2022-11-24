/*
 * aux.h
 *
 *  Created on: Sep 27, 2022
 *      Author: Jakub Matyas
 */

#ifndef SRC_AUX_H_
#define SRC_AUX_H_

#include <xgpiops.h>
#include <xspips.h>



uint32_t aux_dac_read_reg(XSpiPs *SPI_Instance, uint8_t reg, uint8_t addr);
void aux_dac_config(XSpiPs *SPI_Instance, XGpioPs *GPIO_Instance);
void aux_dac_set(XSpiPs *SPI_Instance, XGpioPs *GPIO_Instance, uint8_t dac_no, uint16_t value);
void adc_aux_config(XGpioPs *GPIO_Instance);
uint16_t adc_aux_read(XSpiPs *SPI_Instance, XGpioPs *GPIO_Instance, uint8_t port, uint8_t type, uint8_t pin);

int config_adc_aux_spi(XSpiPs *SPI_Istance);
int config_dac_aux_spi(XSpiPs *SPI_Istance, uint8_t slave_no);
#endif /* SRC_AUX_H_ */
