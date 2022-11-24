/*
 * ad9117.c
 *
 *  Created on: Oct 6, 2022
 *      Author: Jakub Matyas
 */


#include "ad9117.h"
#include "config.h"


static u8 SpiRead [2];
static u8 SpiWrite[2];

#define DEBUG_PRINT

int config_main_dac_spi(XSpiPs *SPI_Instance, uint8_t slave_no) {
	/*
	 * slave_no - choose number of the slave select to use by the hardware SPI controller; 0,1 or 2
	 */
	int Status;
	int ss_no;
	Status = XSpiPs_SetOptions(SPI_Instance, XSPIPS_MASTER_OPTION | XSPIPS_CLK_PHASE_1_OPTION | XSPIPS_CLK_ACTIVE_LOW_OPTION );
	if (Status != XST_SUCCESS)
		print("Failed to set options SPI\r\n");

	Status = XSpiPs_SetClkPrescaler(SPI_Instance, XSPIPS_CLK_PRESCALE_128);
	if (Status != XST_SUCCESS)
		print("Failed to set prescaler SPI\r\n");

	XSpiPs_SetSlaveSelect(SPI_Instance, slave_no);

#ifdef DEBUG_PRINT
		ss_no = XSpiPs_GetSlaveSelect(SPI_Instance);
		xil_printf("Slave select readback: %d\r\n", ss_no);
#endif

	return Status;
}

void main_dac_init(XSpiPs *SPI_Instance, XGpioPs *GPIO_Instance) {

	XGpioPs_SetDirectionPin(GPIO_Instance, DAC_CH1_PDn, 1);
	XGpioPs_SetDirectionPin(GPIO_Instance, DAC_CH2_PDn, 1);

	XGpioPs_SetOutputEnablePin(GPIO_Instance, DAC_CH1_PDn, 1);
	XGpioPs_SetOutputEnablePin(GPIO_Instance, DAC_CH2_PDn, 1);


	// Pulse DAC RST pin to reset DAC SPI (minimum width of 50 ns)
	XGpioPs_SetDirectionPin(GPIO_Instance, DACRST, 1);
	XGpioPs_SetOutputEnablePin(GPIO_Instance, DACRST, 1);
	XGpioPs_WritePin(GPIO_Instance, DACRST, 0);
	usleep(5000);
	XGpioPs_WritePin(GPIO_Instance, DACRST, 1);
	usleep(100);
	XGpioPs_WritePin(GPIO_Instance, DACRST, 0);
	usleep(500);

	// Perform software reset - set RESET bit in SPI control reg and then clear it
	SpiWrite[0] = 0<<7 | 0x00;		// SPI Control REG
	SpiWrite[1] = 1<<4;				// Software Reset
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 2);

//	usleep(100);
	SpiWrite[0] = 0<<7 | 0x00;		// SPI Control REG
	SpiWrite[1] = 0x00;				// Release Software Reset
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 2);

#ifdef DEBUG_PRINT
	// Read back register
	SpiWrite[0] = 1<<7 | 0x00;		// SPI Control REG
	SpiWrite[1] = 0x00;				// Release Software Reset
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 2);
	xil_printf("Control reg SpiRead[0]: 0x%x\r\n", SpiRead[0]);
	xil_printf("Control reg SpiRead[1]: 0x%x\r\n", SpiRead[1]);
#endif


	// Enable on-chip IRset resistor
	SpiWrite[0] = 0<<7 | 0x04;		// IRSET register
	SpiWrite[1] = 1<<7;				// enable on-chip IRset
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 2);

#ifdef DEBUG_PRINT
	// Read the register back
	SpiWrite[0] = 1<<7 | 0x04;
	SpiWrite[1] = 0x00;
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 2);
	xil_printf("IRSet SpiRead[0]: 0x%x\r\n", SpiRead[0]);
	xil_printf("IRSet SpiRead[1]: 0x%x\r\n", SpiRead[1]);
#endif

	// Enable on-chip QRset resistor
	SpiWrite[0] = 0<<7 | 0x07;		// IRSET register
	SpiWrite[1] = 1<<7;				// enable on-chip IRset
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 2);

#ifdef DEBUG_PRINT
	// Read the register back
	SpiWrite[0] = 1<<7 | 0x07;
	SpiWrite[1] = 0x00;
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 2);
	xil_printf("QRSet SpiRead[0]: 0x%x\r\n", SpiRead[0]);
	xil_printf("QRSet SpiRead[1]: 0x%x\r\n", SpiRead[1]);
#endif

	XGpioPs_WritePin(GPIO_Instance, DAC_CH1_PDn, 1);
	XGpioPs_WritePin(GPIO_Instance, DAC_CH2_PDn, 1);


}

uint8_t main_dac_read_reg(XSpiPs *SPI_Instance, uint8_t reg_addr) {
	SpiWrite[0] = 1<<7 | reg_addr;
	SpiWrite[1] = 0x00;
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 2);

#ifdef DEBUG_PRINT
	xil_printf("Main DAC SpiRead[0] 0x%x\r\n", SpiRead[0]);
	xil_printf("Main DAC SpiRead[1] 0x%x\r\n", SpiRead[1]);
#endif

	return SpiRead[1];
}

