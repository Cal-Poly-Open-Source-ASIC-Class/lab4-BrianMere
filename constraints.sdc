puts "\[INFO\]: Creating Clocks"

create_clock [get_ports i_rclk] -name i_rclk -period 7
set_propagated_clock i_rclk
create_clock [get_ports i_wclk] -name i_wclk -period 7
set_propagated_clock i_wclk

set_clock_groups -asynchronous -group [get_clocks {i_rclk i_wclk}]


set r_period [get_property -object_type clock [get_clocks {i_rclk}] period]
set w_period [get_property -object_type clock [get_clocks {i_wclk}] period]
set min_period [expr {min(${r_period}, ${w_period})}]

puts "\[INFO\]: Setting Max Delay"

# Replace the '1' with NUM_FFS - 1 if that ever changes...
set_max_delay -from [get_pins ReadToWrite.imm\[0\]*df*/CLK] -to [get_pins ReadToWrite.imm\[1\]*df*/D] $min_period
set_max_delay -from [get_pins WriteToRead.imm\[0\]*df*/CLK] -to [get_pins WriteToRead.imm\[1\]*df*/D] $min_period

#openlane config.yaml --flow Classic -T openroad.staprepnr 
#to not run all stages


# puts "\[INFO\]: Setting inputs to synchronous"
# # set_input_delay 0 -clock clk {a_i b_i}
# # set_output_delay 0 -clock clk {z_o}

# set_multicycle_path -setup 17 -from [get_pins Comb.a_reg*/CLK ] -to  [get_pins  multicycle_out*df*/D]
# set_multicycle_path -hold  16 -from [get_pins Comb.a_reg*/CLK ] -to  [get_pins  multicycle_out*df*/D]

# set_multicycle_path -setup 17 -from [get_pins Comb.b_reg*/CLK ] -to  [get_pins  multicycle_out*df*/D]
# set_multicycle_path -hold  16 -from [get_pins Comb.b_reg*/CLK ] -to  [get_pins  multicycle_out*df*/D]

# puts [get_pins Div.a[*]*df*/Q ]
# puts [get_pins z_o*df*/D]