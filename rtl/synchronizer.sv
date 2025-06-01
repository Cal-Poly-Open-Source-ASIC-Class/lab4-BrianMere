`timescale 1ns/1ps
/**
    Variable-logic size two-clock synchronizer. 

    Handles buffering metastability by chaining ff's
    such that metastability has a multiplicative chance of
    happening. 

    Ex: if you have two ff's, and there's a 1% chance
    of metastability, then you're chance reduces to 
    (1%)^2 = .01%. 

    Will just use two ff's, but the parameter is there to
    add more where needed.  
*/
module synchronizer #(
    parameter LOGIC_SIZE = 8, // default to byte size
    parameter NUM_FFS    = 2 
) (
    input logic i_reset_n,    // active low reset, but can be async from the new_clk

    input logic [LOGIC_SIZE-1:0] i_input_data,  // from old clock domain
    input logic i_new_clk,                      // clock domain for the output port
    output logic [LOGIC_SIZE-1:0] o_output_data
);

    (* keep *) logic [LOGIC_SIZE-1:0] imm [NUM_FFS-1:0]; // intermediate wire value, need (* keep *) to not optimize the wire out. 

    always_comb begin : outputAssign
        o_output_data = imm[NUM_FFS-1]; // always assign the output as the output of the last FF
    end

    // Handle entering and exiting reset states (see https://zipcpu.com/blog/2017/10/20/cdc.html)
    // synchronous active low signal, converted from the async module. 
    // Handle stringing the ff's together here... 
    always_ff @( posedge i_new_clk or negedge i_reset_n ) begin : zero_thFlipFlop
        if(!i_reset_n) 
            imm[0] <= 0;
        else
            imm[0] <= i_input_data;
    end
    generate
        for(genvar i = 1; i < NUM_FFS; i++) begin 
            always_ff @( posedge i_new_clk or negedge i_reset_n ) begin : n_thFlipFlop
                if(!i_reset_n) 
                    imm[i] <= 0;
                else 
                    imm[i] <= imm[i-1];
            end
        end
    endgenerate
    
endmodule