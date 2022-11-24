/*
 * lm75.h
 *
 *  Created on: Oct 26, 2022
 *      Author: Jakub Matyas
 */

#ifndef SRC_LM75_H_
#define SRC_LM75_H

#include <xiicps.h>
#include "i2c_lib.h"

#define LM75_0_ADDR		0x48
#define LM75_1_ADDR		0x49


#define TEMPERATURE_REG     0x00
#define CONFIG_REG          0x01
#define HYSTERESIS_REG      0x02
#define SHUTDOWN_REG        0x03

int get_lm75_hysteresis(XIicPs *I2CInstance, uint8_t lm_address);

#endif /* SRC_LM75_H_ */

