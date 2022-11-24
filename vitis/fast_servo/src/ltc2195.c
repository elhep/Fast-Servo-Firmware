#include "ltc2195.h"
#include "config.h"

#define DEBUG_PRINT

static u8 SpiRead [2];
static u8 SpiWrite[2];

int config_main_adc_spi(XSpiPs *SPI_Instance, uint8_t slave_no) {
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

void main_adc_config(XSpiPs *SPI_Instance, uint8_t test_mode) {
	// LTC2195 software reset
	SpiWrite[0] = 0<<7 | 0;			// !W | REG_ADDR
	SpiWrite[1] = 0b10000000;
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, NULL, 2);

	// Set register 2 of LTC2195 to default LVDS output, set 4 data Lanes and turn on the test pattern if test_mode==1
	SpiWrite[0] = 0<<7 | 2;
	SpiWrite[1] = 0b00010001;
	if (test_mode == 1)
		SpiWrite[1] = SpiWrite[1] | 1<<2;
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, NULL, 2);

#ifdef DEBUG_PRINT
	// Read the register back
	SpiWrite[0] = 1<<7 | 2;
	SpiWrite[1] = 0b0;
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 2);
	xil_printf("SpiRead[0]: 0x%x\r\n", SpiRead[0]);
	xil_printf("SpiRead[1]: 0x%x\r\n", SpiRead[1]);
#endif

#ifdef DEBUG_PRINT
	// Read the FORMAT and POWER-DOWN register
	SpiWrite[0] = 1<<7 | 1;
	SpiWrite[1] = 0x00;
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 2);
	xil_printf("Format reg: 0x%x\r\n", SpiRead[1]);
#endif
}


uint16_t main_adc_set_test_pattern(XSpiPs *SPI_Instance, uint16_t pattern) {
	uint16_t ret_pattern;
	// Set the  MSB test pattern register (0x03)
	SpiWrite[0] = 0<<7 | 3;
	SpiWrite[1] = (pattern >> 8) & 0xFF;	//0x81;
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, NULL, 2);

	// Set the test pattern register (0x04)
	SpiWrite[0] = 0<<7 | 4;
	SpiWrite[1] = pattern & 0xFF;	//0x1F;
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, NULL, 2);


	// Read the test pattern register (0x03)
	SpiWrite[0] = 1<<7 | 3;
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 2);
#ifdef DEBUG_PRINT
	xil_printf("Test pattern reg (0x03): SpiRead[0]: %x\r\n", SpiRead[0]);
	xil_printf("Test pattern reg (0x03): SpiRead[1]: %x\r\n", SpiRead[1]);
#endif
	ret_pattern = SpiRead[1] << 8;

	// Read the test patern register (0x04)
	SpiWrite[0] = 1<<7 | 4;
	XSpiPs_PolledTransfer(SPI_Instance, SpiWrite, SpiRead, 2);
#ifdef DEBUG_PRINT
	xil_printf("Test pattern reg (0x04): SpiRead[0]: %x\r\n", SpiRead[0]);
	xil_printf("Test pattern reg (0x04): SpiRead[1]: %x\r\n", SpiRead[1]);
#endif

	ret_pattern = ret_pattern | (SpiRead[1] & 0xFF);

	return ret_pattern;

}

