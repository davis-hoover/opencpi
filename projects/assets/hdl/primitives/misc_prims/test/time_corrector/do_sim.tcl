# motivation for these two lines: https://forums.xilinx.com/t5/Simulation-and-Verification/global-signal-logging/td-p/793979
add_wave [get_objects -r]
remove_wave [get_waves *]

add_wave_divider SUBTEST_0_DATA_SRC
add_wave {{/testbench/subtest_0/data_src}}
add_wave_divider SUBTEST_0_UUT
add_wave {{/testbench/subtest_0/uut}}
add_wave_divider SUBTEST_0_FILE_WRITER
add_wave {{/testbench/subtest_0/file_writer}}
add_wave_divider SUBTEST_1_DATA_SRC
add_wave {{/testbench/subtest_1/data_src}}
add_wave_divider SUBTEST_1_UUT
add_wave {{/testbench/subtest_1/uut}}
add_wave_divider SUBTEST_1_FILE_WRITER
add_wave {{/testbench/subtest_1/file_writer}}
add_wave_divider SUBTEST_2_DATA_SRC
add_wave {{/testbench/subtest_2/data_src}}
add_wave_divider SUBTEST_2_UUT
add_wave {{/testbench/subtest_2/uut}}
add_wave_divider SUBTEST_2_FILE_WRITER
add_wave {{/testbench/subtest_2/file_writer}}
add_wave_divider SUBTEST_3_DATA_SRC
add_wave {{/testbench/subtest_3/data_src}}
add_wave_divider SUBTEST_3_UUT
add_wave {{/testbench/subtest_3/uut}}
add_wave_divider SUBTEST_3_FILE_WRITER
add_wave {{/testbench/subtest_3/file_writer}}
add_wave_divider SUBTEST_4_DATA_SRC
add_wave {{/testbench/subtest_4/data_src}}
add_wave_divider SUBTEST_4_UUT
add_wave {{/testbench/subtest_4/uut}}
add_wave_divider SUBTEST_4_FILE_WRITER
add_wave {{/testbench/subtest_4/file_writer}}
add_wave_divider SUBTEST_5_DATA_SRC
add_wave {{/testbench/subtest_5/data_src}}
add_wave_divider SUBTEST_5_UUT
add_wave {{/testbench/subtest_5/uut}}
add_wave_divider SUBTEST_5_FILE_WRITER
add_wave {{/testbench/subtest_5/file_writer}}
add_wave_divider SUBTEST_6_DATA_SRC
add_wave {{/testbench/subtest_6/data_src}}
add_wave_divider SUBTEST_6_UUT
add_wave {{/testbench/subtest_6/uut}}
add_wave_divider SUBTEST_6_FILE_WRITER
add_wave {{/testbench/subtest_6/file_writer}}

run 1 us
