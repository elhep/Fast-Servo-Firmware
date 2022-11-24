/*
 * i2c_lib.h
 *
 *  Created on: Sep 27, 2022
 *      Author: Jakub Matyas
 */

#ifndef SRC_I2C_LIB_H_
#define SRC_I2C_LIB_H_

#include <xiicps.h>
#include <xil_types.h>
#include <xstatus.h>

void i2c_write(XIicPs *I2CInstance, u8 slave_addr, u8 reg_addr, u8 reg_value);
void i2c_read(XIicPs *I2CInstance, u8 *read_buffer, u8 reg_addr, u8 slave_addr);
//void i2c_write_read(XIicPs *I2CInstance, u8 slave_addr, u8 *write_buffer, u8 write_length, u8 *read_buffer, u8 read_length);

#endif /* SRC_I2C_LIB_H_ */
