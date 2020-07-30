library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library util;
library protocol;
library misc_prims; use misc_prims.misc_prims.all;

-- for metadata, registers time every data_count_between_time I/Q values,
-- effectively downsampling time
entity time_downsampler is
  generic(
    -- the DATA PIPE LATENCY CYCLES is currently 1
    DATA_COUNTER_BIT_WIDTH : positive := 32);
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    ctrl      : in  time_downsampler_ctrl_t;
    -- INPUT
    iprotocol : in  protocol.complex_short_with_metadata.protocol_t;
    ieof      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    oprotocol : out protocol.complex_short_with_metadata.protocol_t;
    oeof      : out std_logic;
    ordy      : in  std_logic);
end entity time_downsampler;
architecture rtl of time_downsampler is
  signal protocol_r        : protocol.complex_short_with_metadata.protocol_t :=
                             protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal data_counter_rst  : std_logic := '0';
  signal data_counter_en   : std_logic := '0';
  signal data_counter_cnt  : unsigned(DATA_COUNTER_BIT_WIDTH-1 downto 0) :=
                             (others => '0');
  signal allow_time_xfer   : std_logic := '0';
begin

  pipeline : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        protocol_r <= protocol.complex_short_with_metadata.PROTOCOL_ZERO;
        oeof       <= '0';
      elsif(ordy = '1') then
        protocol_r.samples        <= iprotocol.samples;
        protocol_r.samples_vld    <= iprotocol.samples_vld;
        protocol_r.time           <= iprotocol.time;
        protocol_r.time_vld       <= iprotocol.time_vld and
                                     (allow_time_xfer or ctrl.bypass);
        protocol_r.interval       <= iprotocol.interval;
        protocol_r.interval_vld   <= iprotocol.interval_vld;
        protocol_r.flush          <= iprotocol.flush;
        protocol_r.sync           <= iprotocol.sync;
        protocol_r.end_of_samples <= iprotocol.end_of_samples;
        oeof                      <= ieof;
      end if;
    end if;
  end process pipeline;

  ------------------------------------------------------------------------------
  -- counter to initiate time selection for downsampling
  ------------------------------------------------------------------------------

  allow_time_xfer <= '1' when (
                     (data_counter_en = '1') and
                     ((data_counter_cnt = 0) or
                     (ctrl.min_num_data_per_time = 0)))
                     else '0';

  data_counter_rst <= '1' when (rst = '1') or (
                      (data_counter_en = '1') and
                      ((data_counter_cnt = (ctrl.min_num_data_per_time-1)) or
                      (ctrl.min_num_data_per_time = 0)))
                      else '0';
  data_counter_en  <= ordy and iprotocol.samples_vld;

  data_counter : util.util.counter
    generic map(
      BIT_WIDTH => DATA_COUNTER_BIT_WIDTH)
    port map(
      clk => clk,
      rst => data_counter_rst,
      en  => data_counter_en,
      cnt => data_counter_cnt);

  ------------------------------------------------------------------------------
  -- output data/metadata generation
  ------------------------------------------------------------------------------

  oprotocol <= protocol_r;
  irdy      <= ordy;

end rtl;
