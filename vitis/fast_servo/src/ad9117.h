/*
 * ad9117.h
 *
 *  Created on: Oct 6, 2022
 *      Author: Jakub Matyas
 */

#ifndef SRC_AD9117_H_
#define SRC_AD9117_H_

#include <xspips.h>
#include <xgpiops.h>

int config_main_dac_spi(XSpiPs *SPI_Instance, uint8_t slave_no);
void main_dac_init(XSpiPs *SPI_Instance, XGpioPs *GPIO_Instance);
uint8_t main_dac_read_reg(XSpiPs *SPI_Instance, uint8_t reg_addr);



#endif /* SRC_AD9117_H_ */
