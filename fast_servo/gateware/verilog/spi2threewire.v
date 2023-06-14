`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company:  WUT
// Engineer: Jakub Matyas
// 
// Create Date: 03/02/2023 01:39:08 PM
// Design Name: 
// Module Name: spi2threewire
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

module spi2threewire (
    output ps_sclk_i,
    input ps_sclk_o,
    input ps_sclk_t,
    
    output ps_mosi_i,
    input ps_mosi_o,
    input ps_mosi_t,
    
    output ps_miso_i,
    input ps_miso_o,
    input ps_miso_t,
    
    output ps_ss_i,
    input [2:0] ps_ss,
    input ps_ss_t,
    
    output o_ss,
    output o_sclk,
    inout sdio

);

assign ps_sclk_i = 1'b0;
assign ps_mosi_i = 1'b0;
assign ps_ss_i = 1'b1;


reg [3:0]   bit_count = 'd0;

// rd_wr_n - whether it will be READ transaction or WRITE
//           first bit of the command
reg         rd_wr_n = 'd0;          
reg         sdio_buffer_direction = 'd0;

wire        s_sclk;
wire        s_csn;
wire        s_sdio_buffer_direction;

assign s_sclk = ps_sclk_o;
assign s_csn = ps_ss[0];
assign o_ss = s_csn;

// 1 if there is a SPI tranmsission going on (CS_N is LOW)
//      AND transmission is of READ type
// 0 otherwise
assign s_sdio_buffer_direction = sdio_buffer_direction & ~s_csn;

always @(posedge s_sclk or posedge s_csn) begin
    if (s_csn == 1'b1) begin
        // after the transmission, fill bit counter with ZEROS
        // and zero transmission type (rd_wr_n)
        bit_count <= 4'd0;
        rd_wr_n <= 1'b0;
    end else begin 
        // on every rising edge increment bit counter
        // sample first bit to get the knowledge of the transmission type
        bit_count <= (bit_count < 4'd15) ? bit_count + 1'b1 : bit_count;
        if (bit_count == 4'b0) 
            rd_wr_n <= ps_mosi_o;
    end
end

always @(negedge s_sclk or posedge s_csn) begin
    if (s_csn == 1'b1)
        sdio_buffer_direction <= 1'b0;
    else begin
        if (bit_count == 4'd8)
            // after the 8th bit, on falling edge,
            // set the SDIO buffer direction 
            // accordingly to the transmission type
            sdio_buffer_direction <= rd_wr_n;
    end
end


IOBUF IOBUF_inst (
    .O(ps_miso_i),
    .IO(sdio),
    .I(ps_mosi_o),
    .T(s_sdio_buffer_direction)      // 3-state enable input, high=input (from ext), low=output
);

OBUFT sclk_buf (
    .O(o_sclk),
    .I(ps_sclk_o),
    .T('b0)
);

endmodule