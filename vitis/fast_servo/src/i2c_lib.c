/*
 * i2c_lib.c
 *
 *  Created on: Sep 27, 2022
 *      Author: Jakub Matyas
 */
#include "i2c_lib.h"

#define DEBUG_PRINT

static XIicPs I2CInstance;

//static u8 ReadBuffer[2];	/* Read buffer for reading a page. */
static u8 SendBuffer[2];


void i2c_write(XIicPs *I2CInstance, u8 slave_addr, u8 reg_addr, u8 reg_value) {
	int Status;

	SendBuffer[0] = reg_addr;
	SendBuffer[1] = reg_value;

	Status = XIicPs_MasterSendPolled(I2CInstance, SendBuffer, 2, slave_addr);
	if (Status != XST_SUCCESS) {
		return XST_FAILURE;
	}

	while (XIicPs_BusIsBusy(I2CInstance)) {
		//		NOP
	}
}

void i2c_read(XIicPs *I2CInstance, u8 *read_buffer, u8 reg_addr, u8 slave_addr) {
	int Status;

	SendBuffer[0] = reg_addr;
	XIicPs_SetOptions(I2CInstance, XIICPS_REP_START_OPTION);
	Status = XIicPs_MasterSendPolled(I2CInstance, SendBuffer, 1, slave_addr);
	if (Status != XST_SUCCESS) {
		print("I2C read failed on send\r\n");
		return XST_FAILURE;
	}


	Status = XIicPs_MasterRecvPolled(I2CInstance, read_buffer, 1, slave_addr);
	if (Status != XST_SUCCESS) {
		print("I2C read Failed on Receive\r\n");
		return XST_FAILURE;
	}

	XIicPs_ClearOptions(I2CInstance, XIICPS_REP_START_OPTION);
	while(XIicPs_BusIsBusy(I2CInstance)) {
		// NOP
	}
}
