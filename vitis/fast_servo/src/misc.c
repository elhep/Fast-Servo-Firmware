/*
 * misc.c
 *
 *  Created on: Oct 5, 2022
 *      Author: Jakub Matyas
 */

#include "misc.h"

#define DEBUG_PRINT

void set_dio(XGpioPs *GPIO_Instance, uint8_t pin, uint8_t state) {
	uint8_t oen_pin;
	if (pin == 66) oen_pin = 67; else oen_pin = 70;

	XGpioPs_SetDirectionPin(GPIO_Instance, pin, 1);			// pin as output
	XGpioPs_SetDirectionPin(GPIO_Instance, oen_pin, 1);		// OE pin as output
	XGpioPs_SetOutputEnablePin(GPIO_Instance, pin, 1);
	XGpioPs_SetOutputEnablePin(GPIO_Instance, oen_pin, 1);

	XGpioPs_WritePin(GPIO_Instance, oen_pin, 0);		// active low
	XGpioPs_WritePin(GPIO_Instance, pin, state);
}

uint32_t get_dio (XGpioPs *GPIO_Instance, uint8_t pin) {
	uint8_t oen_pin;
	if (pin == 65) oen_pin = 67; else oen_pin = 70;

	XGpioPs_SetDirectionPin(GPIO_Instance, pin, 0);			// pin as input
	XGpioPs_SetDirectionPin(GPIO_Instance, oen_pin, 1);		// OE pin as output

	XGpioPs_SetOutputEnablePin(GPIO_Instance, pin, 0);
	XGpioPs_SetOutputEnablePin(GPIO_Instance, oen_pin, 1);


	XGpioPs_WritePin(GPIO_Instance, oen_pin, 1);
	return XGpioPs_ReadPin(GPIO_Instance, pin);
}


void si5340_config(XIicPs *I2CInstance) {
	u8 read_buffer[2] = {0, 0};

//	Change to page 1 for output settings
	i2c_write(I2CInstance, SI5340_ADDR, 1, 0x1);

#ifdef DEBUG_PRINT
	i2c_read(I2CInstance, read_buffer, 1, SI5340_ADDR);
	xil_printf("Si5340 initial page readout: 0x%x\r\n", read_buffer[0]);
#endif

	u8 clk_out_addr[4] = {0x15, 0x1A, 0x29, 0x1E};
	for (int i=0; i < 4; i++){
		i2c_write(I2CInstance, SI5340_ADDR, clk_out_addr[i], 1);
#ifdef DEBUG_PRINT
		i2c_read(I2CInstance, read_buffer, clk_out_addr[i], SI5340_ADDR);
		xil_printf("Si5340 CLK_OUT%d config: 0x%x\r\n", i, read_buffer[0]);
#endif
	}

	i2c_write(I2CInstance, SI5340_ADDR, 0x28, 13);
#ifdef DEBUG_PRINT
	i2c_read(I2CInstance, read_buffer, 0x28, SI5340_ADDR);
	xil_printf("Si5340 OUTx_CM CLK2: 0x%x\r\n",read_buffer[0]);
#endif

	i2c_write(I2CInstance, SI5340_ADDR, 0x28, 0x6B);		// setting OUT2 to LVDS25

	i2c_write(I2CInstance, SI5340_ADDR, 0x2C, 0xCC);		// SETTING out3 to LVCMOS 18
	i2c_write(I2CInstance, SI5340_ADDR, 0x2E, 0x09);		// SETTING out3 to LVCMOS 33

	i2c_read(I2CInstance, read_buffer, 0x2B, SI5340_ADDR);
	xil_printf("Si5340 OUTx_PDN CLK3: 0x%x\r\n",read_buffer[0]);

	i2c_read(I2CInstance, read_buffer, 0x2C, SI5340_ADDR);
	xil_printf("Si5340 OUTx_FORMAT CLK3: 0x%x\r\n",read_buffer[0]);

	i2c_read(I2CInstance, read_buffer, 0x2D, SI5340_ADDR);
	xil_printf("Si5340 OUTx_AMPL CLK3: 0x%x\r\n",read_buffer[0]);


	i2c_read(I2CInstance, read_buffer, 0x2E, SI5340_ADDR);
	xil_printf("Si5340 OUTx_CM CLK3: 0x%x\r\n",read_buffer[0]);

	i2c_write(I2CInstance, SI5340_ADDR, 1, 0x3);		// setting page to 3 to change dividers values
#ifdef DEBUG_PRINT
	i2c_read(I2CInstance, read_buffer, 1, SI5340_ADDR);
	xil_printf("Si5340 after setup page readout: 0x%x\r\n", read_buffer[0]);
#endif

	// Numerator (100 MHz): 0x00_22_60_00_00_00
	// Numerator (10 MHz): 0x1_57_C0_00_00_00
	// Default denominator: 0x80000000
	// Numerator/Denominator = 68.75 (decimal)
	// OSC_freq = 48 MHz
	// Default M = 286.46
	// OSC_freq * M / N / 2 = freq_out
	//
	// 48 MHz * 286.46 / 68.75 / 2 = 100 MHz


	u8 n1_numerator[6] = {0x0, 0x0, 0x0, 0x60, 0x22, 0x0};
	u8 n1_numerator_10M[6] = {0x0, 0x0, 0x0, 0xC0, 0x57, 0x1};
	u8 n1_num_addr[6] = {0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12};
	u8 n1_denom_addr[4] = {0x13, 0x14, 0x15, 0x16};
	for (int i=0; i<6; i++) {
		i2c_write(I2CInstance, SI5340_ADDR, n1_num_addr[i], n1_numerator[i]);
	}

	i2c_write(I2CInstance, SI5340_ADDR, 0x17, 1);

#ifdef DEBUG_PRINT
	for (int i=0; i < 6; i++) {
		i2c_read(I2CInstance, read_buffer, n1_num_addr[i], SI5340_ADDR);
		xil_printf("Numerator buffer: %x\r\n", read_buffer[0]);
	}
	for (int i=0; i < 4; i++) {
		i2c_read(I2CInstance, read_buffer, n1_denom_addr[i], SI5340_ADDR);
		xil_printf("Denominator buffer: %x\r\n", read_buffer[0]);
	}
#endif
	i2c_write(I2CInstance, SI5340_ADDR, 1, 0x0);		// setting page to 0

}

void config_gpio_header(XGpioPs *GPIO_Instance, uint8_t *pins, uint8_t mode_first_half, uint8_t mode_second_half, uint8_t header_length) {
	// mode - 1 configures the pins from the half to output, whereas 0 configures them as input
	uint8_t half_size = header_length/2;
	uint8_t mode;

	for (uint8_t i=0; i < header_length; i++)
	{
		if (i < half_size)
			mode = (mode_first_half == 0) ? 0 : 1;
		else
			mode = (mode_second_half == 0) ? 0 : 1;

		usleep(500);
		XGpioPs_SetDirectionPin(GPIO_Instance, pins[i], mode);
		XGpioPs_SetOutputEnablePin(GPIO_Instance, pins[i], mode);
	}
}

uint16_t test_gpio_header(XGpioPs *GPIO_Instance, uint8_t *pins, uint8_t first_half_as_output, uint8_t header_length){
	uint8_t mode_first_half, mode_second_half;
	uint8_t half_size = header_length/2;
	uint16_t read_value = 0;
	uint8_t temp=0;

	if(first_half_as_output == 1) {
		mode_first_half = 1;
		mode_second_half = 0;
	} else {
		mode_first_half = 0;
		mode_second_half = 1;
	}
	config_gpio_header(GPIO_Instance, pins, mode_first_half, mode_second_half, header_length);

	if (first_half_as_output == 1) {
		for(uint8_t i=0; i < half_size; i++) {
			XGpioPs_WritePin(GPIO_Instance, pins[i], 1);
		}
		for (uint8_t j=half_size; j < header_length; j++) {
			temp = XGpioPs_ReadPin(GPIO_Instance, pins[j]);
			read_value |= (temp & 0b1) << (j - half_size);
#ifdef DEBUG_PRINT
			xil_printf("pin: %d\tFirst Output TEMP: %d\tREAD_VALUE: 0x%x\r\n", pins[j], temp, read_value);
#endif

		}
	} else {
		for(uint8_t i=half_size; i < header_length; i++) {
			XGpioPs_WritePin(GPIO_Instance, pins[i], 1);
		}
		for (uint8_t j=0; j < half_size; j++) {
			temp = XGpioPs_ReadPin(GPIO_Instance, pins[j]);
			read_value |= (temp & 0b1) << j;
#ifdef DEBUG_PRINT
			xil_printf("pin: %d\tSecond Output TEMP: %d\tREAD_VALUE: 0x%x\r\n", pins[j], temp, read_value);
#endif
		}
	}

	return read_value;
}
