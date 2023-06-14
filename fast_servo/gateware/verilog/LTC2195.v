///////////////////////////////////////////////////////////////////////////////
// LTC2195.v
//
// 8/03/21
// Jakub Matyas
//
//	LTC2195 controller.
//
// 
///////////////////////////////////////////////////////////////////////////////

// `include "timescale.v"
`timescale 1ns/1ps // this was in the SelectIO design

module LTC2195(
	input	 						   rst_in,
	input clk200,
	input  DCO,
	input  DCO_2D,
	input  		 					FR_in_p,
	input  							FR_in_n,
	input  		 			[3:0]	D0_in_p,
	input  		 			[3:0]	D0_in_n,
	input  		 			[3:0]	D1_in_p,
	input  		 			[3:0]	D1_in_n,
	input  bitslip,
	input [4:0] delay_val,
	
	output reg	  [15:0] ADC0_out,
	output reg    [15:0] ADC1_out,
	output reg					[3:0] FR_out,
	output wire [8:0] o_data_from_pins,
	output idelay_rdy
);

// ///////////////////////////////////////////////////////////////////////////////
// // LVDS inputs

localparam N_BITS = 4;
localparam  N_LANES = 9;	// for each channel 4 lanes + 1 lane for FRAME
wire [N_LANES-1:0] data_in_p, data_in_n, data_in_from_pins, data_in_from_pins_delay;
assign data_in_p = {FR_in_p, D1_in_p, D0_in_p};
assign data_in_n = {FR_in_n, D1_in_n, D0_in_n};
assign o_data_from_pins = data_in_from_pins_delay;


wire [N_LANES*4 -1:0] data_out;
wire [35:0 ]data_out_mod;


assign data_out_mod = {~data_out[35:24], data_out[23:20], ~data_out[19:16], data_out[15:0]};


always @(posedge DCO_2D) begin
    ADC0_out <= {
		data_out_mod[0], data_out_mod[4], data_out_mod[1], data_out_mod[5],
        data_out_mod[2], data_out_mod[6], data_out_mod[3], data_out_mod[7],
        data_out_mod[8], data_out_mod[12], data_out_mod[9], data_out_mod[13],
        data_out_mod[10], data_out_mod[14], data_out_mod[11], data_out_mod[15]
    };

    ADC1_out <= {
		data_out_mod[16 + 0], data_out_mod[16 + 4], data_out_mod[16 + 1], data_out_mod[16 + 5],
        data_out_mod[16 + 2], data_out_mod[16 + 6], data_out_mod[16 + 3], data_out_mod[16 + 7],
        data_out_mod[16 + 8], data_out_mod[16 + 12], data_out_mod[16 + 9], data_out_mod[16 + 13],
        data_out_mod[16 + 10], data_out_mod[16 + 14], data_out_mod[16 + 11], data_out_mod[16 + 15]
    };
	FR_out <= {data_out_mod[32], data_out_mod[33], data_out_mod[34], data_out_mod[35]};		// value that arrived first is LSB, therefore reversing order
end

wire s_idelay_rdy;
IDELAYCTRL IDELAYCTRL_inst (
	.RDY(s_idelay_rdy),       // 1-bit output: Ready output
	.REFCLK(clk200), // 1-bit input: Reference clock input
	.RST(s_rst)        // 1-bit input: Active high reset input
);

assign idelay_rdy = s_idelay_rdy;


reg s_rst;
reg [5:0] rst_cnt;
wire serdes_o;

always @(posedge DCO_2D) begin
    if (rst_in) begin
        s_rst <= 1'b1;
        rst_cnt <= 'b0;
    end else begin
        if (rst_cnt == 22) 
            s_rst <= 'b0;
        else
            rst_cnt <= rst_cnt + 1;
    end
end

genvar lane;
generate for (lane=0; lane<N_LANES; lane=lane+1) begin
	IBUFDS #(
		.DIFF_TERM("TRUE")
	)
	ibufds_inst (
		.I(data_in_p[lane]),
		.IB(data_in_n[lane]),
		.O(data_in_from_pins[lane])
	);
    IDELAYE2 #(
        .CINVCTRL_SEL("FALSE"),          // Enable dynamic clock inversion (FALSE, TRUE)
        .DELAY_SRC("IDATAIN"),           // Delay input (IDATAIN, DATAIN)
        .HIGH_PERFORMANCE_MODE("TRUE"), // Reduced jitter ("TRUE"), Reduced power ("FALSE")
        .IDELAY_TYPE("VAR_LOAD"),           // FIXED, VARIABLE, VAR_LOAD, VAR_LOAD_PIPE
        .IDELAY_VALUE(0),                // Input delay tap setting (0-31)
        .PIPE_SEL("FALSE"),              // Select pipelined mode, FALSE, TRUE
        .REFCLK_FREQUENCY(200.0),        // IDELAYCTRL clock input frequency in MHz (190.0-210.0, 290.0-310.0).
        .SIGNAL_PATTERN("DATA")          // DATA, CLOCK input signal
    )
	IDELAYE2_inst (
	   .C(clk200),
	   .CE('b0),
	   .CNTVALUEIN(delay_val),
	   .LD(1'b1),
		.DATAOUT(data_in_from_pins_delay[lane]),         // 1-bit output: Delayed data output
		.IDATAIN(data_in_from_pins[lane]),         // 1-bit input: Data input from the I/O
		.LDPIPEEN		(1'b0),
	   .REGRST			(1'b0),
	   .CINVCTRL		(1'b0)
	);

	ISERDESE2 #(
		.DATA_RATE("DDR"),
		.DATA_WIDTH(3'd4),
		.INTERFACE_TYPE("NETWORKING"),
		.IOBDELAY("BOTH"),
		.SERDES_MODE("MASTER"),
		.NUM_CE(2'd2)
	)
	iserdes_inst (
		.CE1(1'd1),
		.CE2(1'd1),
		.DYNCLKDIVSEL('b0),
		.DYNCLKSEL('b0),
		.CLK(DCO),
		.CLKB(!DCO),
		.CLKDIV(DCO_2D),
//		.D(data_in_from_pins[lane]),
		.DDLY(data_in_from_pins_delay[lane]),
		.RST(s_rst),
		.BITSLIP(bitslip),
		// DATA is MSB first and OUTA is LANE0, so in case of OUTA:
		// Q1 = D9
		// Q2 = D11
		// Q3 = D13
		// Q4 = D15
		.Q1(data_out[lane*N_BITS + 3]),       
		.Q2(data_out[lane*N_BITS + 2]),
		.Q3(data_out[lane*N_BITS + 1]),
		.Q4(data_out[lane*N_BITS + 0]) 
	);
end
endgenerate

endmodule
