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
library protocol;

package misc_prims is

constant TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH : positive := 32;
constant DATA_ADC_BIT_WIDTH                  : positive := 12;
constant DATA_DAC_BIT_WIDTH                  : positive := 12;
type file_writer_backpressure_select_t is (NO_BP, LFSR_BP);

type data_complex_adc_t is record
  i : std_logic_vector(DATA_ADC_BIT_WIDTH-1 downto 0);
  q : std_logic_vector(DATA_ADC_BIT_WIDTH-1 downto 0);
end record data_complex_adc_t;

type data_complex_dac_t is record
  i : std_logic_vector(DATA_DAC_BIT_WIDTH-1 downto 0);
  q : std_logic_vector(DATA_DAC_BIT_WIDTH-1 downto 0);
end record data_complex_dac_t;

-- provides info in additional to ComplexShortWithMetadata protocol
type metadata_dac_t is record
  underrun_error : std_logic; -- samples were not available for one or
                              -- more dac clock cycles
  ctrl_tx_on_off : std_logic; -- high when transmitter should be powered on
                              -- low when transmitter should be powered off
end record metadata_dac_t;

function calc_cdc_bit_dst_fifo_depth (constant src_dst_ratio : in real; constant num_input_samples : in natural) return natural;
function calc_cdc_fifo_depth (constant src_dst_ratio : in real) return natural;
function calc_cdc_pulse_dst_fifo_depth (constant src_dst_ratio : in real; constant num_input_samples : in natural) return natural;
function calc_cdc_count_up_dst_fifo_depth (constant src_dst_ratio : in real; constant num_input_samples : in natural) return natural;

type adc_samp_drop_detector_status_t is record
  error_samp_drop : std_logic;
end record adc_samp_drop_detector_status_t;

type dac_underrun_detector_status_t is record
  underrun_error : std_logic;
end record dac_underrun_detector_status_t;

type time_downsampler_ctrl_t is record
  bypass                : std_logic;
  min_num_data_per_time : unsigned(TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH-1
                          downto 0);
end record time_downsampler_ctrl_t;

type time_corrector_ctrl_t is record
  bypass              : std_logic;
  time_correction     : signed(
      protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH-1 downto 0);
end record time_corrector_ctrl_t;

type time_corrector_status_t is record
  overflow : std_logic;
  --overflow_sticky : std_logic;
end record time_corrector_status_t;

component round_conv
  generic (
    DIN_WIDTH  : positive;
    DOUT_WIDTH : positive);
  port (
    CLK      : in  std_logic;
    RST      : in  std_logic;
    DIN      : in  std_logic_vector(DIN_WIDTH-1 downto 0);
    DIN_VLD  : in  std_logic;
    DOUT     : out std_logic_vector(DOUT_WIDTH-1 downto 0);
    DOUT_VLD : out std_logic);
end component;

component lfsr
  generic (
    POLYNOMIAL : std_logic_vector;
    SEED       : std_logic_vector); -- must never be all zeros
  port (
    CLK      : in std_logic; -- rising edge clock
    RST      : in std_logic; -- synchronous, active high
    EN       : in std_logic; -- synchronous, active high
    REG      : out std_logic_vector(POLYNOMIAL'length-1 downto 0));
end component;

component event_in_to_txen
  port (
    EVENT_IN_CLK           : in  std_logic;
    EVENT_IN_RESET         : in  std_logic;
    CTL_IN_IS_OPERATING    : in  std_logic;
    EVENT_IN_IN_RESET      : in  std_logic;
    EVENT_IN_IN_SOM        : in  std_logic;
    EVENT_IN_IN_VALID      : in  std_logic;
    EVENT_IN_IN_EOM        : in  std_logic;
    EVENT_IN_IN_READY      : in  std_logic;
    EVENT_IN_OUT_TAKE      : in  std_logic;
    -- '1'/'0' corresponds to on opcode/off opcode
    EVENT_IN_OPCODE_ON_OFF : in  std_logic;
    -- use case 1: use tx enable to directly drive pin
    TXEN                   : out std_logic;
    -- use case 2: use intermediate signals to drive other logic which
    -- drives pin (useful when there are multiple channels/event ports)
    TXON_PULSE             : out std_logic;
    TXOFF_PULSE            : out std_logic;
    EVENT_IN_CONNECTED     : out std_logic;
    IS_OPERATING           : out std_logic);
end component;

component edge_detector
  port(
    clk               : in  std_logic;
    reset             : in  std_logic;
    din               : in  std_logic;
    rising_pulse      : out std_logic;
    falling_pulse     : out std_logic);
end component;

component debounce
  generic (
    COUNTER_WIDTH : positive);
  port(
    CLK    : in  std_logic;
    RST    : in  std_logic;
    BUTTON : in  std_logic;
    RESULT : out std_logic);
end component;

component adc_maximal_lfsr_data_src is
  port(
    -- CTRL
    clk                : in  std_logic;
    rst                : in  std_logic;
    stop_on_period_cnt : in  std_logic;
    stopped            : out std_logic;
    -- OUTPUT
    odata              : out data_complex_adc_t;
    ovld               : out std_logic;
    ordy               : in  std_logic);
end component;

component maximal_lfsr_data_src is
  port(
    -- CTRL
    clk                : in  std_logic;
    rst                : in  std_logic;
    stop_on_period_cnt : in  std_logic;
    stopped            : out std_logic;
    -- OUTPUT
    odata              : out
        protocol.complex_short_with_metadata.op_samples_arg_iq_t;
    ovld               : out std_logic;
    ordy               : in  std_logic);
end component;

component adc_samp_drop_detector is
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    status    : out adc_samp_drop_detector_status_t;
    -- INPUT
    idata     : in  data_complex_adc_t;
    ivld      : in  std_logic;
    -- OUTPUT
    odata     : out data_complex_adc_t;
    osamp_drop: out std_logic;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end component;

component data_widener is
  generic(
    BITS_PACKED_INTO_MSBS : boolean := true);
  port(
    -- CTRL
    clk        : in  std_logic;
    rst        : in  std_logic;
    -- INPUT
    idata      : in  data_complex_adc_t;
    isamp_drop : in  std_logic;
    ivld       : in  std_logic;
    irdy       : out std_logic;
    -- OUTPUT
    oprotocol  : out protocol.complex_short_with_metadata.protocol_t;
    ordy       : in  std_logic);
end component;

component data_narrower is
  generic(
    BITS_PACKED_INTO_LSBS : boolean := false);
  port(
    -- CTRL
    clk           : in  std_logic;
    rst           : in  std_logic;
    -- INPUT
    iprotocol     : in  protocol.complex_short_with_metadata.protocol_t;
    imetadata     : in  metadata_dac_t;
    imetadata_vld : in  std_logic;
    irdy          : out std_logic;
    -- OUTPUT
    odata         : out data_complex_dac_t;
    odata_vld     : out std_logic;
    ometadata     : out metadata_dac_t;
    ometadata_vld : out std_logic;
    ordy          : in  std_logic);
end component;

component dac_underrun_detector is
  port(
    -- CTRL
    clk           : in  std_logic;
    rst           : in  std_logic;
    status        : out dac_underrun_detector_status_t;
    -- INPUT
    iprotocol     : in  protocol.complex_short_with_metadata.protocol_t;
    imetadata     : in  metadata_dac_t;
    imetadata_vld : in  std_logic;
    irdy          : out std_logic;
    -- OUTPUT
    -- if ometadata.underrun_error and protocol.samples_vld are both 1, error is
    -- assumed to have happened before the current valid sample
    oprotocol     : out protocol.complex_short_with_metadata.protocol_t;
    ometadata     : out metadata_dac_t;
    ometadata_vld : out std_logic;
    ordy          : in  std_logic);
end component;

component time_corrector is
  -- the DATA PIPE LATENCY CYCLES is currently 0
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    ctrl      : in  time_corrector_ctrl_t;
    status    : out time_corrector_status_t;
    -- INPUT
    iprotocol : in  protocol.complex_short_with_metadata.protocol_t;
    irdy      : out std_logic;
    -- OUTPUT
    oprotocol : out protocol.complex_short_with_metadata.protocol_t;
    ordy      : in  std_logic);
end component;

component time_downsampler is
  generic(
    DATA_COUNTER_BIT_WIDTH : positive := 32);
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    ctrl      : in  time_downsampler_ctrl_t;
    -- INPUT
    iprotocol : in  protocol.complex_short_with_metadata.protocol_t;
    irdy      : out std_logic;
    -- OUTPUT
    oprotocol : out protocol.complex_short_with_metadata.protocol_t;
    ordy      : in  std_logic);
end component;

component level_to_pulse_converter is
  port(
    clk   : in  std_logic;
    rst   : in  std_logic;
    level : in  std_logic;
    pulse : out std_logic);
end component;

component gen_reset_sync
generic (src_clk_hz : real := 100000000.0;
         dst_clk_hz : real := 100000000.0);
  port(
    src_clk                   : in  std_logic;
    src_rst                   : in  std_logic;
    dst_clk                   : in  std_logic;
    dst_rst                   : in  std_logic;
    synced_dst_to_scr_rst     : out std_logic;
    synced_src_to_dst_rst     : out std_logic);
end component;

component four_bit_lfsr
generic (SEED : std_logic_vector := "1000");
  port(
    clk     : in std_logic;
    rst     : in std_logic;
    en      : in std_logic;
    dout    : out std_logic_vector);
end component;

component one_shot_fifo
generic (data_width : natural := 1;
         fifo_depth : natural := 2;
         num_output_samples : natural := 1);
  port(
    clk      : in std_logic;
    rst      : in std_logic;
    din      : in std_logic_vector;
    en       : in std_logic;
    rdy      : in std_logic;
    data_vld : out std_logic;
    done     : out std_logic;
    dout     : out std_logic_vector);
end component;

component advance_counter
generic (hold_width : natural := 1);
  port(
    clk       : in std_logic;
    rst       : in std_logic;
    en        : in std_logic;
    advance   : out std_logic);
end component;

end package misc_prims;
