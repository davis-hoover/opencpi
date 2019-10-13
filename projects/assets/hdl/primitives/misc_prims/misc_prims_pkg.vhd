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

package misc_prims is

constant DATA_ADC_BIT_WIDTH             : positive := 12;
constant DATA_BIT_WIDTH                 : positive := 16;
constant METADATA_TIME_BIT_WIDTH        : positive := 64;
constant METADATA_SAMP_PERIOD_BIT_WIDTH : positive := 64;

type file_writer_backpressure_select_t is (NO_BP, LFSR_BP);

type data_complex_adc_t is record
  i : std_logic_vector(DATA_ADC_BIT_WIDTH-1 downto 0);
  q : std_logic_vector(DATA_ADC_BIT_WIDTH-1 downto 0);
end record data_complex_adc_t;

type data_complex_t is record
  i : std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
  q : std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
end record data_complex_t;

type metadata_t is record
  flush             : std_logic; -- one or more samples have been dropped
  error_samp_drop   : std_logic; -- one or more samples have been dropped
  data_vld          : std_logic; -- allows for option of sending valid metadata
                                 -- in parallel with invalid data to output

  -- if error_samp_drop and data_vld are both 1, samp drop is assumed to have
  -- happened before the current valid data

  -- if data_vld=1 and time_vld=1 time of corresponding to current data value
  -- if data_vld=0 and time_vld=1 time of next valid data value
  time              : unsigned(METADATA_TIME_BIT_WIDTH-1 downto 0);

  time_vld          : std_logic;
  samp_period       : unsigned(METADATA_SAMP_PERIOD_BIT_WIDTH-1 downto 0);
  samp_period_vld   : std_logic;
end record metadata_t;

type info_t is record
  data     : data_complex_t;
  metadata : metadata_t;
end record info_t;

constant METADATA_IDX_SAMP_PERIOD_VLD : natural := 0;
constant METADATA_IDX_SAMP_PERIOD_R   : natural := 1;
constant METADATA_IDX_SAMP_PERIOD_L   : natural :=
                                        METADATA_IDX_SAMP_PERIOD_R+
                                        METADATA_SAMP_PERIOD_BIT_WIDTH-1;
constant METADATA_IDX_TIME_VLD        : natural :=
                                        METADATA_IDX_SAMP_PERIOD_L+1;
constant METADATA_IDX_TIME_R          : natural := METADATA_IDX_TIME_VLD+1;
constant METADATA_IDX_TIME_L          : natural := METADATA_IDX_TIME_R+
                                                   METADATA_TIME_BIT_WIDTH-1;
constant METADATA_IDX_DATA_VLD        : natural := METADATA_IDX_TIME_L+1;
constant METADATA_IDX_ERROR_SAMP_DROP : natural := METADATA_IDX_DATA_VLD+1;
constant METADATA_IDX_FLUSH           : natural := METADATA_IDX_ERROR_SAMP_DROP
                                                   +1;
constant METADATA_BIT_WIDTH : positive := METADATA_IDX_FLUSH+1;

constant INFO_BIT_WIDTH : positive := (2*DATA_BIT_WIDTH)+METADATA_BIT_WIDTH;

function to_slv(data     : in data_complex_t) return std_logic_vector;
function from_slv(slv    : in std_logic_vector) return data_complex_t;
function to_slv(metadata : in metadata_t)     return std_logic_vector;
function from_slv(slv    : in std_logic_vector) return metadata_t;
function to_slv(info     : in info_t)         return std_logic_vector;
function from_slv(slv    : in std_logic_vector) return info_t;

type adc_samp_drop_detector_status_t is record
  error_samp_drop : std_logic;
end record adc_samp_drop_detector_status_t;

type time_corrector_ctrl_t is record
  time_correction     : signed(METADATA_TIME_BIT_WIDTH-1 downto 0);
  time_correction_vld : std_logic;
end record time_corrector_ctrl_t;

type time_corrector_status_t is record
  overflow : std_logic;
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

component counter is
  generic(
    BIT_WIDTH : positive);
  port(
    clk : in  std_logic;
    rst : in  std_logic;
    en  : in  std_logic;
    cnt : out unsigned(BIT_WIDTH-1 downto 0));
end component;

component latest_reg is
  generic(
    BIT_WIDTH : positive);
  port(
    clk      : in  std_logic;
    rst      : in  std_logic;
    din      : in  std_logic;
    din_vld  : in  std_logic;
    dout     : out std_logic;
    dout_vld : out std_logic);
end component;

component latest_reg_slv is
  generic(
    BIT_WIDTH : positive);
  port(
    clk      : in  std_logic;
    rst      : in  std_logic;
    din      : in  std_logic_vector(BIT_WIDTH-1 downto 0);
    din_vld  : in  std_logic;
    dout     : out std_logic_vector(BIT_WIDTH-1 downto 0);
    dout_vld : out std_logic);
end component;

component latest_reg_signed is
  generic(
    BIT_WIDTH : positive);
  port(
    clk      : in  std_logic;
    rst      : in  std_logic;
    din      : in  signed(BIT_WIDTH-1 downto 0);
    din_vld  : in  std_logic;
    dout     : out signed(BIT_WIDTH-1 downto 0);
    dout_vld : out std_logic);
end component;

component adc_maximal_lfsr_data_src is
  generic(
    DATA_BIT_WIDTH : positive); -- width of each of I/Q
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
    odata              : out data_complex_t;
    ovld               : out std_logic;
    ordy               : in  std_logic);
end component;

component adc_samp_drop_detector is
  generic(
    DATA_PIPE_LATENCY_CYCLES : natural := 0);
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
    ometadata : out metadata_t;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end component;

component data_widener is
  generic(
    DATA_PIPE_LATENCY_CYCLES : natural := 0;
    BITS_PACKED_INTO_MSBS    : boolean := true);
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    -- INPUT
    idata     : in  data_complex_adc_t;
    imetadata : in  metadata_t;
    ivld      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    odata     : out data_complex_t;
    ometadata : out metadata_t;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end component;

component set_clr
  port(
    clk : in  std_logic;
    rst : in  std_logic;
    set : in  std_logic;
    clr : in  std_logic;
    q   : out std_logic;
    q_r : out std_logic);
end component set_clr;

component clk_src is
  generic(
    CLK_PERIOD : time);
  port(
    clk : out std_logic);
end component;

component time_corrector is
  generic(
    DATA_PIPE_LATENCY_CYCLES : natural := 0);
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    ctrl      : in  time_corrector_ctrl_t;
    status    : out time_corrector_status_t;
    -- INPUT
    idata     : in  data_complex_t;
    imetadata : in  metadata_t;
    ivld      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    odata     : out data_complex_t;
    ometadata : out metadata_t;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end component;

end package misc_prims;
