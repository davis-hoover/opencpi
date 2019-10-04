-- This file is protected by Copyright. Please refer to the COPYRIGHT file
-- distributed with this source distribution.
--
-- This file is part of OpenCPI <http://www.opencpi.org>
--
-- OpenCPI is free software: you can redistribute it and/or modify it under the
-- terms of the GNU Lesser General Public License as published by the Free
-- Software Foundation, either version 3 of the License, or (at your option) any
-- later version.
--
-- OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
-- WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
-- A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
-- details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.

library ieee;
use ieee.std_logic_1164.all;
USE IEEE.NUMERIC_STD.ALL;
USE IEEE.MATH_REAL.ALL;
USE IEEE.MATH_COMPLEX.ALL;
library ocpi; use ocpi.types.all; -- ULong_t

package ocpi is

type complex_short_with_metadata_opcode_t is (
  SAMPLES, TIME, INTERVAL, FLUSH, SYNC, END_OF_SAMPLES, USER);

component wsi_message_sizer is
  generic(
    SIZE_BIT_WIDTH : positive);
  port(
    clk                    : in  std_logic;
    rst                    : in  std_logic;
    give                   : in  std_logic;
    message_size_num_gives : in  unsigned(SIZE_BIT_WIDTH-1 downto 0);
    som                    : out std_logic;
    eom                    : out std_logic);
end component;

component data_src_adc_scdcd is
  generic(
    DATA_PIPE_LATENCY_CYCLES : ULong_t;
    OUT_PORT_DATA_WIDTH      : ULong_t;
    BITS_PACKED_INTO_MSBS    : Bool_t;
    GP_CTRL_ARRAY_LENGTH     : UShort_t;
    GP_STATUS_ARRAY_LENGTH   : UShort_t;
    OUT_PORT_MBYTEEN_WIDTH   : positive);
  port(
    -- CTRL
    ctrl_clk               : in  std_logic;
    ctrl_rst               : in  Bool_t;
    ctrl_is_operating      : in  Bool_t;
    ctrl_msg_size_samps    : in  UShort_t;
    ctrl_msg_size_samps_wr : in  Bool_t;
    ctrl_clr_samp_drop     : in  Bool_t;
    ctrl_clr_samp_drop_wr  : in  Bool_t;
    ctrl_clr_write_fail    : in  Bool_t;
    ctrl_clr_write_fail_wr : in  Bool_t;
    ctrl_samp_drop_sticky  : out Bool_t;
    ctrl_write_fail        : out Bool_t;
    ctrl_gp_ctrl           : in  ULongLong_array_t(0 to to_integer(unsigned(
                                                   GP_CTRL_ARRAY_LENGTH))-1);
    ctrl_gp_status         : out ULongLong_array_t(0 to to_integer(unsigned(
                                                   GP_STATUS_ARRAY_LENGTH))-1);
    -- INPUT
    adc_dev_clk            : in  std_logic;
    adc_dev_data_i         : in  std_logic_vector(16-1 downto 0);
    adc_dev_data_q         : in  std_logic_vector(16-1 downto 0);
    adc_dev_tvalid         : in  std_logic;
    adc_dev_present        : out std_logic;
    -- OUTPUT
    adc_out_clk            : out std_logic;
    adc_out_give           : out Bool_t;
    adc_out_data           : out std_logic_vector(to_integer(unsigned(OUT_PORT_DATA_WIDTH))-1 downto 0);
    adc_out_byte_enable    : out std_logic_vector(OUT_PORT_MBYTEEN_WIDTH-1 downto 0);
    adc_out_opcode         : out complex_short_with_metadata_opcode_t;
    adc_out_som            : out Bool_t;
    adc_out_eom            : out Bool_t;
    adc_out_valid          : out Bool_t;
    adc_out_ready          : in  Bool_t);
end component;

component ocpi_data_sink_dac is
  generic(
    DAC_WIDTH_BITS                         : UChar_t;
    DATA_PIPE_LATENCY_CYCLES               : ULong_t;
    IN_PORT_DATA_WIDTH                     : ULong_t;
    DAC_OUTPUT_IS_LSB_OF_IN_PORT           : Bool_t;
    IN_PORT_MBYTEEN_WIDTH                  : positive);
  port(
    -- CTRL
    ctrl_clk                               : in  std_logic;
    ctrl_rst                               : in  bool_t;
    ctrl_underrun_sticky_error             : out bool_t;
    ctrl_clr_underrun_sticky_error         : in bool_t;
    ctrl_unused_opcode_detected_sticky     : out bool_t;
    ctrl_clr_unused_opcode_detected_sticky : in bool_t;
    ctrl_finished                          : out bool_t;
    -- INPUT
    dac_in_clk                             : out std_logic;
    dac_in_take                            : out bool_t;
    dac_in_data                            : in  std_logic_vector(to_integer(unsigned(
                                                                  IN_PORT_DATA_WIDTH))-1 downto 0);
    dac_in_opcode                          : in  complex_short_with_metadata_opcode_t;
    dac_in_ready                           : in  bool_t;
    dac_in_valid                           : in  bool_t;
    dac_in_eof                             : in  bool_t;
    -- ON/OFF OUTPUT
    on_off_out_reset                       : in  bool_t;
    on_off_out_ready                       : in  bool_t;
    on_off_out_opcode                      : out bool_t;
    on_off_out_give                        : out bool_t;
    -- DEV SIGNAL OUTPUT (Matches dac-16-signals bundle)
    dac_dev_clk                            : in  std_logic;
    dac_dev_data_i                         : out std_logic_vector(15 downto 0);
    dac_dev_data_q                         : out std_logic_vector(15 downto 0);
    dac_dev_valid                          : out std_logic;
    dac_dev_take                           : in  std_logic;
    dac_dev_present                        : out std_logic);
end component;

end package ocpi;
