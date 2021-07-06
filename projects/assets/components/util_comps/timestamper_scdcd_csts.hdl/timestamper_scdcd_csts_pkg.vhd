library ieee;
use ieee.std_logic_1164.all;
USE IEEE.NUMERIC_STD.ALL;
USE IEEE.MATH_REAL.ALL;
USE IEEE.MATH_COMPLEX.ALL;
library timed_sample_prot, ocpi;
use ocpi.types.all;


package timestamper_scdcd_csts_pkg is

constant TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH : positive := 32;

type time_downsampler_ctrl_t is record
  bypass                         : bool_t; -- overrides others
  -- for timestamping
  time                           : timed_sample_prot.complex_short_timed_sample.op_time_t;
  time_vld                       : bool_t; -- indicates insertion
  samples_per_timestamp          : unsigned(TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH-1 downto 0); -- once if zero
  -- for interval insertion
  insert_interval_seconds        : bool_t; -- rising edge triggers insertion when possible
  insert_interval_fraction       : bool_t; -- rising edge triggers insertion when possible
  interval                       : timed_sample_prot.complex_short_timed_sample.op_sample_interval_t;
end record time_downsampler_ctrl_t;

type time_corrector_ctrl_t is record
  bypass              : std_logic;
  time_correction     : signed(
      timed_sample_prot.complex_short_timed_sample.OP_TIME_BIT_WIDTH-1 downto 0);
end record time_corrector_ctrl_t;

type time_corrector_status_t is record
  overflow : std_logic;
  --overflow_sticky : std_logic;
end record time_corrector_status_t;

component time_corrector is
  -- the DATA PIPE LATENCY CYCLES is currently 0
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    ctrl      : in  time_corrector_ctrl_t;
    status    : out time_corrector_status_t;
    -- INPUT
    iprotocol : in  timed_sample_prot.complex_short_timed_sample.protocol_t;
    ieof      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    oprotocol : out timed_sample_prot.complex_short_timed_sample.protocol_t;
    oeof      : out std_logic;
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
    iprotocol : in  timed_sample_prot.complex_short_timed_sample.protocol_t;
    ieof      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    oprotocol : out timed_sample_prot.complex_short_timed_sample.protocol_t;
    oeof      : out std_logic;
    ordy      : in  std_logic);
end component;


end package timestamper_scdcd_csts_pkg;
