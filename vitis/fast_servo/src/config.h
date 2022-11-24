#ifndef _CONFIG
#define _CONFIG

#include <xparameters.h>

#define DAC_SAMPLES_WRITE_ADDR	 XPAR_AXI_BRAM_CTRL_0_S_AXI_BASEADDR + 0x4
#define ADC_IDELAY_WRITE_ADDR	 XPAR_AXI_BRAM_CTRL_0_S_AXI_BASEADDR
#define ADC_DATA_READ_ADDR		 XPAR_AXI_BRAM_CTRL_0_S_AXI_BASEADDR
#define ADC_FRAME_READ_ADDR		 XPAR_AXI_BRAM_CTRL_0_S_AXI_BASEADDR + 0x4


#define ETH_LED1 54
#define ETH_LED2 55
#define LED1	 56
#define LED2	 57
#define LED3	 58

#define AFE_CH1_GAIN	59
#define nSHDN_CH1		60
#define AFE_CH2_GAIN	61
#define nSHDN_CH2		62

#define nRSTSI			63
#define DACRST			64

#define DI0				65
#define DO0				66
#define DO0_OEn			67
#define DI1				68
#define DO1				69
#define DO1_OEn			70

#define AUX_DAC_nCLR	71
#define AUX_DAC_BIN		72
#define AUX_DAC_nLDAC	73

#define AUX_ADC_DIFFn	74
#define AUX_ADC_A0		75
#define AUX_ADC_A1		76
#define AUX_ADC_A2		77
#define AUX_ADC_RANGE	78

#define DAC_CH1_PDn		79
#define DAC_CH2_PDn		80

#define SI5340_ADDR		0x74

#define PS_LED_PIN 7

// Number of slave to select with SPI' chip select
#define MAIN_ADC_CS	  0
#define ADC_AUX_PORTA 1
#define ADC_AUX_PORTB 2

#define MAIN_DAC_CS	  0
#define AUX_DAC_CS	  1

// GPIO HEADER
#define QSPI_IO3	  	81
#define QSPI_IO2	  	82
#define QSPI_IO1	  	83
#define QSPI_IO0	  	84
#define QSPI_CLK		85
#define QSPI_NCS		86
#define HRTIM_CHE1		87
#define HRTIM_CHE2		88
#define HRTIM_CHA1		89
#define HRTIM_CHA2		90
#define LPTIM2_OUT		91
#define UART4_TX		92
#define SPI1_MOSI		93
#define SPI1_MISO		94
#define SPI1_NSS		95
#define SPI1_SCK		96
#define I2C1_SDA		97
#define I2C1_SCL		98

// LVDS HEADER
#define LVDS0_P			99
#define LVDS1_P			100
#define LVDS2_P			101
#define LVDS3_P			102
#define LVDS4_P			103
#define LVDS5_P			104
#define LVDS6_P			105
#define LVDS7_P			106

#define LVDS0_N			107
#define LVDS1_N			108
#define LVDS2_N			109
#define LVDS3_N			110
#define LVDS4_N			111
#define LVDS5_N			112
#define LVDS6_N			113
#define LVDS7_N			114

#endif
