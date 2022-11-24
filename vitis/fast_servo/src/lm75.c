#include "lm75.h"

int i2c_write_read(XIicPs *I2CInstance, uint8_t slave_addr, uint8_t *write_buffer, uint8_t write_length, uint8_t *read_buffer, uint8_t read_length) {
	int Status;

	XIicPs_SetOptions(I2CInstance, XIICPS_REP_START_OPTION);
	Status = XIicPs_MasterSendPolled(I2CInstance, write_buffer, write_length, slave_addr);
	if (Status != XST_SUCCESS) {
		print("I2C read failed on send\r\n");
		return XST_FAILURE;
	}


	Status = XIicPs_MasterRecvPolled(I2CInstance, read_buffer, read_length, slave_addr);
	if (Status != XST_SUCCESS) {
		print("I2C read Failed on Receive\r\n");
		return XST_FAILURE;
	}

	XIicPs_ClearOptions(I2CInstance, XIICPS_REP_START_OPTION);
	while(XIicPs_BusIsBusy(I2CInstance)) {
		// NOP
	}
}

int get_lm75_hysteresis(XIicPs *I2CInstance, uint8_t lm_address) {
	int ret_code;
	uint8_t reg_addr = HYSTERESIS_REG;
	uint8_t write_buffer[1] = {reg_addr};
	uint8_t write_length = sizeof(write_buffer);
	uint8_t read_buffer[2];
	uint8_t read_length = sizeof(read_buffer);

#ifdef DEBUG_PRINT
	xil_printf("Reg_addr; 0x%x write_length: %d read_length: %d\r\n", write_buffer[0], write_length, read_length);
#endif
	ret_code = i2c_write_read(I2CInstance, lm_address, write_buffer, write_length, read_buffer, read_length);

    if (ret_code) {
        xil_printf("Could not get the temperature from LM75 (0x%x) [%d]", lm_address, ret_code);
        return -1;
    }

#ifdef DEBUG_PRINT
    xil_printf("Read_buffer[0]: 0x%x, read_buffer[1]: 0x%x\r\n", read_buffer[0], read_buffer[1]);
#endif
    return 0;
}
