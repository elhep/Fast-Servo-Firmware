/******************************************************************************
*
* Copyright (C) 2009 - 2014 Xilinx, Inc.  All rights reserved.
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in
* all copies or substantial portions of the Software.
*
* Use of the Software is limited solely to applications:
* (a) running on a Xilinx device, or
* (b) that interact with a Xilinx device through a bus or interconnect.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
* XILINX  BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
* WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF
* OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
* SOFTWARE.
*
* Except as contained in this notice, the name of the Xilinx shall not be used
* in advertising or otherwise to promote the sale, use or other dealings in
* this Software without prior written authorization from Xilinx.
*
******************************************************************************/

/*
 * fast_servo_main.c: simple test application
 *
 * This application configures UART 16550 to baud rate 9600.
 * PS7 UART (Zynq) is not initialized by this application, since
 * bootrom/bsp configures it to baud rate 115200
 *
 * ------------------------------------------------
 * | UART TYPE   BAUD RATE                        |
 * ------------------------------------------------
 *   uartns550   9600
 *   uartlite    Configurable only in HW design
 *   ps7_uart    115200 (configured by bootrom/bsp)
 */

#include <sleep.h>
#include <sys/_stdint.h>
#include <xgpiops.h>
#include <xiicps.h>
#include <xil_io.h>
#include <xil_printf.h>
#include <xil_types.h>
#include <xparameters.h>
#include <xspips.h>
#include <xstatus.h>

#include "aux.h"
#include "ltc2195.h"
#include "ad9117.h"
#include "config.h"
#include "platform.h"
#include "misc.h"


#define DEBUG_PRINT

static XGpioPs GPIO;

static XIicPs I2CInstance;
static XIicPs EEM_I2CInstance;

static XSpiPs ADCSpiInstance;
static XSpiPs DACSpiInstance;


uint8_t word_align(void) {
	uint8_t edge_detected = 0;
	uint8_t tap_delay = 0;
	uint8_t transition = 0;

	int current_frame = 0;
	int prev_frame = 0;
	int value = 0;
	value = Xil_In32(ADC_FRAME_READ_ADDR);
	current_frame = (value >> 16) & 0xFFFF;
	prev_frame = current_frame;

	for (int i=0; i < 32; i++)
	{
		tap_delay = i;
		Xil_Out32(ADC_IDELAY_WRITE_ADDR, tap_delay);

		if (edge_detected == 1) break;
		value = Xil_In32(ADC_FRAME_READ_ADDR);
		current_frame = value & 0xFF;
#ifdef DEBUG_PRINT
		xil_printf("Tap delay: %d\r\n", tap_delay);
		xil_printf("Value: 0x%x\r\n", value);
#endif
		if (current_frame == prev_frame) {
			tap_delay += 1;
		} else if (transition == 0) {
			tap_delay += 1;
			transition = 1;
		} else if (transition == 1) {
			tap_delay = i/2;
			edge_detected = 1;
		}
		prev_frame = current_frame;
		usleep(10000);

	}
	if (edge_detected == 0) {
		tap_delay = 24;
		Xil_Out32(ADC_IDELAY_WRITE_ADDR, tap_delay);
		xil_printf("No edge detected; setting IDELAY to: %d\r\n", tap_delay);
	}
	if (edge_detected == 1) {
		Xil_Out32(ADC_IDELAY_WRITE_ADDR, tap_delay + 2);
	}
	value = Xil_In32(ADC_DATA_READ_ADDR);

	xil_printf("ADC1: 0x%x\tADC0: 0x%x\r\n", (value>>16) & 0xFFFF, value & 0xFFFF);
	return tap_delay;

}


int main()
{
	init_platform();

	//	PS LED Config
	XGpioPs_Config *GPIO_Config;
	int Status;

	GPIO_Config = XGpioPs_LookupConfig(XPAR_PS7_GPIO_0_DEVICE_ID);
	Status = XGpioPs_CfgInitialize(&GPIO, GPIO_Config, GPIO_Config->BaseAddr);
	if(Status != XST_SUCCESS) {
		print("PS GPIO init failed!\n\r");
	} else {
		print("PS GPIO init successful\n\r");
	}

	// set nRST of Si5340 pin to 1
	XGpioPs_SetDirectionPin(&GPIO, nRSTSI, 1);
	XGpioPs_WritePin(&GPIO, nRSTSI, 0);

	usleep(450000);

	/*
	 * I2C to Si5340
	 */
	XIicPs_Config *I2C_ConfigPtr;

	I2C_ConfigPtr = XIicPs_LookupConfig(XPAR_PS7_I2C_0_DEVICE_ID);
	Status = XIicPs_CfgInitialize(&I2CInstance, I2C_ConfigPtr, I2C_ConfigPtr->BaseAddress);
	if(Status != XST_SUCCESS) {
		print("I2C init failed\n\r");
	} else {
		print("i2c init successful\r\n");
	}

	Status = XIicPs_SelfTest(&I2CInstance);
	if (Status != XST_SUCCESS) {
		print("I2C self test failed");
	}
	XIicPs_SetSClk(&I2CInstance, 50000);

	/*
	 * EEM I2C
	 */
	XIicPs_Config *EEM_I2C_ConfigPtr;

	EEM_I2C_ConfigPtr = XIicPs_LookupConfig(XPAR_PS7_I2C_1_DEVICE_ID);
	Status = XIicPs_CfgInitialize(&EEM_I2CInstance, EEM_I2C_ConfigPtr, EEM_I2C_ConfigPtr->BaseAddress);
	if(Status != XST_SUCCESS) {
		print("EEM I2C init failed\n\r");
	} else {
		print("EEM I2C init successful\r\n");
	}

	Status = XIicPs_SelfTest(&EEM_I2CInstance);
	if (Status != XST_SUCCESS) {
		print("EEM I2C self test failed");
	}
	XIicPs_SetSClk(&EEM_I2CInstance, 50000);

	/*
	 * SPI to ADCs and DACs
	 */
	XSpiPs_Config *ADCSpi_CnfigPtr;
	XSpiPs_Config *DACSpi_ConfigPtr;

	ADCSpi_CnfigPtr = XSpiPs_LookupConfig(XPAR_PS7_SPI_0_DEVICE_ID);
	Status = XSpiPs_CfgInitialize(&ADCSpiInstance, ADCSpi_CnfigPtr, ADCSpi_CnfigPtr->BaseAddress);
	if(Status != XST_SUCCESS) {
		print("ADCSPI init failed\n\r");
	} else {
		print("ADCSPI init successful\r\n");
	}

	Status = XSpiPs_SelfTest(&ADCSpiInstance);
	if (Status != XST_SUCCESS) {
		print("ADC SPI self test failed");
	}

	DACSpi_ConfigPtr = XSpiPs_LookupConfig(XPAR_PS7_SPI_1_DEVICE_ID);
	Status = XSpiPs_CfgInitialize(&DACSpiInstance, DACSpi_ConfigPtr, DACSpi_ConfigPtr->BaseAddress);

	if(Status != XST_SUCCESS) {
		print("DAC SPI init failed\n\r");
	} else {
		print("DAC SPI init successful\r\n");
	}

	Status = XSpiPs_SelfTest(&DACSpiInstance);
	if (Status != XST_SUCCESS) {
		print("DAC SPI self test failed");
	} else {
		print("DAC test successful\r\n");
	}


	si5340_config(&I2CInstance);

	XGpioPs_SetDirectionPin(&GPIO, PS_LED_PIN, 1);
	XGpioPs_WritePin(&GPIO, PS_LED_PIN, 1);

	XGpioPs_SetDirectionPin(&GPIO, ETH_LED1, 1);
	XGpioPs_SetOutputEnablePin(&GPIO, ETH_LED1, 1);
	XGpioPs_SetDirectionPin(&GPIO, ETH_LED2, 1);
	XGpioPs_SetOutputEnablePin(&GPIO, ETH_LED2, 1);


	/*
	 * END OF INIT;
	 * CODE
	 */


    print("Hello World\n\r");
    usleep(1000000);

    /*
     * ===== MAIN ADC =====
     */
    // Configure main ADC LTC2195 SPI and the IC itself
    config_main_adc_spi(&ADCSpiInstance, MAIN_ADC_CS);
	main_adc_config(&ADCSpiInstance, 1);
	main_adc_set_test_pattern(&ADCSpiInstance, 0x811f);
	word_align();

	/*
	 * ===== MAIN DAC =====
	 */
	print("====DAC START====\r\n");
	config_main_dac_spi(&DACSpiInstance, MAIN_DAC_CS);
	main_dac_init(&DACSpiInstance, &GPIO);
	usleep(500);
	print("====POWER_DOWN REG====\r\n");
	main_dac_read_reg(&DACSpiInstance, 0x01);
	print("====DATA_CONTROL REG====\r\n");
	main_dac_read_reg(&DACSpiInstance, 0x02);

	print("DAC_CH1_PDn=0, DAC_CH2_PDn=1\r\n");
	XGpioPs_WritePin(&GPIO,DAC_CH2_PDn, 1);
	XGpioPs_WritePin(&GPIO,DAC_CH1_PDn, 0);

	// Output a saw-shaped output signal
	for (int j=0; j<500; j++) {
		for (int i=0; i <65536; i=i+5) {
			Xil_Out32(DAC_SAMPLES_WRITE_ADDR, i | (i<<16));
			usleep(1);
		}
	}

	/*
	 * ==== AUX DAC =====
	 */
	config_dac_aux_spi(&DACSpiInstance, AUX_DAC_CS);
	aux_dac_config(&DACSpiInstance, &GPIO);

	XGpioPs_WritePin(&GPIO, AUX_DAC_nCLR, 1);
	usleep(100);

	// DAC is configured to Analog Output Range +10 V, which means that output ranges
	// having taken into consideration voltage refrence, from 0 to 4 V (2^16 - 1);
	aux_dac_set(&DACSpiInstance, &GPIO, 0, 32768 -1);			// 2 V
	aux_dac_set(&DACSpiInstance, &GPIO, 2, 32768/2 -1);		// 1 V

	/*
	 * ===== AUX ADC =====
	 */
	// ADC is configured in a way that maximum input voltage equals 2.5 V
	uint16_t adc_ret;
	config_adc_aux_spi(&ADCSpiInstance);
	adc_aux_config(&GPIO);

	adc_ret = adc_aux_read(&ADCSpiInstance, &GPIO, ADC_AUX_PORTA, 1, 3);
	xil_printf("ADC AUX port A read value: %d\r\n", adc_ret);
	adc_ret = adc_aux_read(&ADCSpiInstance, &GPIO, ADC_AUX_PORTB, 1, 3);
	xil_printf("ADC AUX port B read value: %d\r\n", adc_ret);


	/*
	 * GPIO AND LVDS HEADERS
	 * Connect first half of GPIOs to the second half
	 * and LVDS pins to their corresponding of the opposite polarity (i.e. LVDS0P to LVDS0N)
	 */
	printf("====GPIO HEADER====\r\n");
	xil_printf("First as output: 0x%x Second as output: 0x%x\r\n", test_gpio_header(&GPIO, gpio_header_pins, 1, sizeof(gpio_header_pins)), test_gpio_header(&GPIO, gpio_header_pins, 0, sizeof(gpio_header_pins)));
	printf("====LVDS HEADER====\r\n");
	xil_printf("First as output: 0x%x Second as output: 0x%x\r\n", test_gpio_header(&GPIO, lvds_header_pins, 1, sizeof(lvds_header_pins)), test_gpio_header(&GPIO, lvds_header_pins, 0, sizeof(lvds_header_pins)));

	int state = 0;
	while(1) {

		XGpioPs_WritePin(&GPIO,PS_LED_PIN,state);
		XGpioPs_WritePin(&GPIO, ETH_LED1, state);
		usleep(50000);
		if (state == 0) state = 1; else state = 0;
		XGpioPs_WritePin(&GPIO, ETH_LED2, state);
		usleep(50000);
	}

    cleanup_platform();
    return 0;
}


