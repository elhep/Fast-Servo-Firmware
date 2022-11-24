/*
 * aux.c
 *
 *  Created on: Sep 27, 2022
 *      Author: Jakub Matyas
 */


#include "aux.h"
#include "config.h"

static u8 SpiRead [3];
static u8 SpiWrite[3];

#define DEBUG_PRINT

uint32_t aux_dac_read_reg(XSpiPs *SPI_Instance, uint8_t reg, uint8_t addr) {
	uint32_t val;
	uint8_t ctrl_reg;
	ctrl_reg = ((1 << 7) | ((reg & 0b111) << 3) | (addr & 0b111));		// R | 0 | REG[2:0] | ADDR[2:0]
	SpiWrite[0] = ctrl_reg;
	SpiWrite[1] = 0;
	SpiWrite[2] = 0;
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, NULL, 3);

	ctrl_reg = 0x18;		// NOP operation for readback
	SpiWrite[0] = ctrl_reg;

	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 3);
#ifdef DEBUG_PRINT
	xil_printf("SpiRead[0] %x\r\n", SpiRead[0]);
	xil_printf("SpiRead[1] %x\r\n", SpiRead[1]);
	xil_printf("SpiRead[2] %x\r\n", SpiRead[2]);
#endif

	val = (SpiRead[0] << 15) | (SpiRead[1] << 7) | SpiRead[2];
	return val;
}


void aux_dac_config(XSpiPs *SPI_Instance, XGpioPs *GPIO_Instance) {
	uint32_t readback;
	uint8_t ctrl_reg;

	/*
	 * OUTPUT RANGE SELECT REGISTER => !W | 0 | OUTPUT_RANGE_REG[2:0] | BOTH_DACs [2:0]
	 * | 0b0|	0b0	|	0b001		|	0b100		|			...			|	0b001	|
	 * | !W	|	0	|	REG ADDR	|	Both DACs	|	DON'T CARE [15:13]	|	+10V	|
	 */
	ctrl_reg = 0 << 7 | 0 << 6 | 1 << 3 |  0b100;

	SpiWrite[0] = ctrl_reg;
	SpiWrite[1] = 0;
	SpiWrite[2] = 0b001;	// Set output range  to +10 V

	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, NULL, 3);
#ifdef DEBUG_PRINT
	readback = aux_dac_read_reg(SPI_Instance, 0b001, 000);
	xil_printf("Readback Output Range Reg: 0x%x\r\n", readback);
#endif

	/*
	 * CONTROL REGISTER	=>	!W | 0 | CONTROL_REG[2:0] | FUNCTION[2:0]
	 * | 0b0|	0b0	|	0b011		|	0b001	|			...			|	0b010		|
	 * | !W	|	0	|	REG ADDR	|	OPTION	|	DON'T CARE [15:13]	|	CLR output	|
	 * 																	|	Unipolar Midscale
	 * 																	|	Bipolar Negative Full-Scale
	 */

	ctrl_reg = 0 << 7 | 0 << 6 | 0b011 << 3 | 0b001;
	SpiWrite[0] = ctrl_reg;
	SpiWrite[1] = 0;
	SpiWrite[2] = 0b10;		//	CLR Select
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, NULL, 3);

#ifdef DEBUG_PRINT
	readback = aux_dac_read_reg(SPI_Instance, 0b011, 000);
	xil_printf("Readback Control Reg: 0x%x\r\n", readback);
#endif

	/*
	 * POWER CONTROL REGISTER => !W | 0 | PWR_CTRL_REG [2:0] | 0 | 0 | 0
	 * | 0b0|	0b0	|	0b010		|	0b000	|			...			|		0b101			|
	 * | !W	|	0	|	REG ADDR	|			|	DON'T CARE [15:13]	|	Power Up Both DACs	|
	 */
	ctrl_reg = 0 << 7 | 0 << 6 | 0b010 << 3 | 0b000;
	SpiWrite[0] = ctrl_reg;
	SpiWrite[1] = 0;
	SpiWrite[2] = 0b101;		// Power Up DAC A and DAC B
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, NULL, 3);

#ifdef DEBUG_PRINT
	readback = aux_dac_read_reg(SPI_Instance, 0b010, 000);
	xil_printf("Readback Power Reg: 0x%x\r\n", readback);
#endif

	usleep(100);

	// set pins below as outputs
	XGpioPs_SetDirectionPin(GPIO_Instance, AUX_DAC_BIN, 1);			// pin as output
	XGpioPs_SetDirectionPin(GPIO_Instance, AUX_DAC_nCLR, 1);
	XGpioPs_SetDirectionPin(GPIO_Instance, AUX_DAC_nLDAC, 1);

	// set output enable for those pins
	XGpioPs_SetOutputEnablePin(GPIO_Instance, AUX_DAC_BIN, 1);
	XGpioPs_SetOutputEnablePin(GPIO_Instance, AUX_DAC_nCLR, 1);
	XGpioPs_SetOutputEnablePin(GPIO_Instance, AUX_DAC_nLDAC, 1);

	// set pins to 1
	XGpioPs_WritePin(GPIO_Instance, AUX_DAC_nLDAC, 1);
	XGpioPs_WritePin(GPIO_Instance, AUX_DAC_nCLR, 1);
}


void aux_dac_set(XSpiPs *SPI_Instance, XGpioPs *GPIO_Instance, uint8_t dac_no, uint16_t value) {
	/*
	 * dac_no:
	 * 		0b000 - DAC A
	 * 		0b010 - DAC B
	 * 		0b100 - Both
	 */
	uint32_t readback;
	uint8_t ctrl_reg;
	ctrl_reg = 0 << 7 | 0 << 6 | 0 << 3 |  (dac_no & 0b111);	// !W | 0 | DAC_REG[2:0] | DAC_NO [2:0]
	SpiWrite[0] = ctrl_reg;
	SpiWrite[1] = (value >> 8) & 0xFF;
	SpiWrite[2] = value & 0xFF;
	XGpioPs_WritePin(GPIO_Instance, AUX_DAC_nLDAC, 0);			// keep LDAC low for the whole duration of the SPI transmission (individual DAC updating)
	usleep(10);		// just in case

	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, NULL, 3);
#ifdef DEBUG_PRINT
	readback = aux_dac_read_reg(SPI_Instance, 0b000, dac_no & 0b111);
	xil_printf("Readback DAC contents on DAC_NO: %d\t: 0x%x\r\n", dac_no, readback);
#endif

	usleep(10);		// just in case
	XGpioPs_WritePin(GPIO_Instance, AUX_DAC_nLDAC, 1);

}

void adc_aux_config(XGpioPs *GPIO_Instance) {

	// Set pins as outputs
	XGpioPs_SetDirectionPin(GPIO_Instance, AUX_ADC_DIFFn, 1);
	XGpioPs_SetDirectionPin(GPIO_Instance, AUX_ADC_A0, 1);
	XGpioPs_SetDirectionPin(GPIO_Instance, AUX_ADC_A1, 1);
	XGpioPs_SetDirectionPin(GPIO_Instance, AUX_ADC_A2, 1);
	XGpioPs_SetDirectionPin(GPIO_Instance, AUX_ADC_RANGE, 1);

	// Set output enables
	XGpioPs_SetOutputEnablePin(GPIO_Instance, AUX_ADC_DIFFn, 1);
	XGpioPs_SetOutputEnablePin(GPIO_Instance, AUX_ADC_RANGE, 1);
	XGpioPs_SetOutputEnablePin(GPIO_Instance, AUX_ADC_A0, 1);
	XGpioPs_SetOutputEnablePin(GPIO_Instance, AUX_ADC_A1, 1);
	XGpioPs_SetOutputEnablePin(GPIO_Instance, AUX_ADC_A2, 1);

	XGpioPs_WritePin(GPIO_Instance, AUX_ADC_DIFFn, 1);		// Single-ended
	XGpioPs_WritePin(GPIO_Instance, AUX_ADC_RANGE, 0);		// 0 - 2.5 V ref
	XGpioPs_WritePin(GPIO_Instance, AUX_ADC_A0, 0);
	XGpioPs_WritePin(GPIO_Instance, AUX_ADC_A1, 0);
	XGpioPs_WritePin(GPIO_Instance, AUX_ADC_A2, 0);
}

uint16_t adc_aux_read(XSpiPs *SPI_Instance, XGpioPs *GPIO_Instance, uint8_t port, uint8_t type, uint8_t pin) {
	/*
	 * port - sets Zynq's corresponding chip select to read data from a port
	 * 		(mux implemented in PL)
	 * 		1 - port A
	 * 		2 - port B
	 * type:
	 * 		0 	- differential
	 * 		1	- single-ended
	 * 	pin:
	 * 		0b000	- VA1/VB1
	 * 		0b001	- VA2/VB2
	 * 		0b010	- VA3/VB3
	 * 		0b011	- VA4/VB4
	 */

	uint8_t write_buff[2] = {0, 0};
	uint8_t read_buff[2] = {0, 0};
	uint16_t ret_value;

	if (type == 0) // DIFFERENTIAL
		XGpioPs_WritePin(GPIO_Instance, AUX_ADC_DIFFn, 0);
	else	// SINGLE-ENDED
		XGpioPs_WritePin(GPIO_Instance, AUX_ADC_DIFFn, 1);


	XGpioPs_WritePin(GPIO_Instance, AUX_ADC_A0, pin & 0b1);
	XGpioPs_WritePin(GPIO_Instance, AUX_ADC_A1, (pin >> 1) & 0b1);
	XGpioPs_WritePin(GPIO_Instance, AUX_ADC_A2, (pin >> 2) & 0b1);

	XSpiPs_SetSlaveSelect(SPI_Instance, port);
	XSpiPs_PolledTransfer(SPI_Instance, write_buff , read_buff, 2);
#ifdef DEBUG_PRINT
	xil_printf("AUX_ADC_READ[0]: 0x%x\r\n", read_buff[0]);
	xil_printf("AUX_ADC_READ[1]: 0x%x\r\n", read_buff[1]);
#endif

	ret_value = ((read_buff[0] << 8) | read_buff[1]) >> 2;
	return ret_value;
}

int config_adc_aux_spi(XSpiPs *SPI_Instance) {
	int Status;
	Status = XSpiPs_SetOptions(SPI_Instance, XSPIPS_MASTER_OPTION | XSPIPS_CLK_PHASE_1_OPTION);
	if (Status != XST_SUCCESS)
		print("Failed to set options SPI\r\n");

	Status = XSpiPs_SetClkPrescaler(SPI_Instance, XSPIPS_CLK_PRESCALE_128);
	if (Status != XST_SUCCESS)
			print("Failed to set prescaler SPI\r\n");
}

int config_dac_aux_spi(XSpiPs *SPI_Instance, uint8_t slave_no){
	int Status;
	Status = XSpiPs_SetOptions(SPI_Instance, XSPIPS_MASTER_OPTION |  XSPIPS_CLK_PHASE_1_OPTION );
	if (Status != XST_SUCCESS)
		print("Failed to set options SPI\r\n");

	Status = XSpiPs_SetClkPrescaler(SPI_Instance, XSPIPS_CLK_PRESCALE_128);
	if (Status != XST_SUCCESS)
			print("Failed to set prescaler SPI\r\n");

	XSpiPs_SetSlaveSelect(SPI_Instance, slave_no);

}


