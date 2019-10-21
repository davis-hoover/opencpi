library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

-- for metadata, registers time every data_count_between_time I/Q values,
-- effectively downsampling time
entity time_downsampler is
  generic(
    DATA_PIPE_LATENCY_CYCLES : natural  := 0;
    DATA_COUNTER_BIT_WIDTH   : positive := 32);
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    ctrl      : in  time_downsampler_ctrl_t;
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
end entity time_downsampler;
architecture rtl of time_downsampler is
  signal latest_time                      : unsigned(METADATA_TIME_BIT_WIDTH-1
                                            downto 0) := (others => '0');
  signal latest_time_vld                  : std_logic := '0';
  signal latest_min_num_data_per_time : unsigned(
                                            DATA_COUNTER_BIT_WIDTH-1 downto 0)
                                            := (others => '0');
  signal latest_min_num_data_per_time_vld : std_logic := '0';

  signal data_counter_rst  : std_logic := '0';
  signal data_counter_en   : std_logic := '0';
  signal data_counter_cnt  : unsigned(DATA_COUNTER_BIT_WIDTH-1 downto 0) :=
                             (others => '0');
  signal allow_time_xfer   : std_logic := '0';

  signal imetadata_slv     : std_logic_vector(METADATA_BIT_WIDTH-1 downto 0) :=
                             (others => '0');
  signal metadata          : std_logic_vector(METADATA_BIT_WIDTH-1 downto 0) :=
                             (others => '0');
  signal pending_time_xfer : std_logic := '0';
 
begin
  ------------------------------------------------------------------------------
  -- latest time/valid register to account for when valid time arrives only
  -- in the middle of counting over min_num_data_per_time
  ------------------------------------------------------------------------------

  latest_time_regs : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        latest_time     <= (others => '0');
        latest_time_vld <= '0';
      elsif((ordy = '1') and (imetadata.time_vld = '1')) then
        latest_time     <= imetadata.time;
        latest_time_vld <= '1';
      end if;
    end if;
  end process latest_time_regs;

  ------------------------------------------------------------------------------
  -- latest data_cnt_between_time register
  ------------------------------------------------------------------------------

  latest_min_num_data_per_time_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        latest_min_num_data_per_time <= (others => '0');
        latest_min_num_data_per_time_vld <= '0';
      elsif((ordy = '1') and (ctrl.min_num_data_per_time_vld = '1')) then
        latest_min_num_data_per_time     <= ctrl.min_num_data_per_time;
        latest_min_num_data_per_time_vld <= ctrl.min_num_data_per_time_vld;
      end if;
    end if;
  end process latest_min_num_data_per_time_reg;

  ------------------------------------------------------------------------------
  -- counter to initiate time selection for downsampling
  ------------------------------------------------------------------------------

  allow_time_xfer <= '1' when ((latest_min_num_data_per_time_vld = '1') and
                     (data_counter_en = '1') and
                     ((data_counter_cnt = 0) or
                     (latest_min_num_data_per_time = 0)))
                     else '0';

  data_counter_rst <= '1' when (rst = '1') or
                      ((latest_min_num_data_per_time_vld = '1') and
                      (data_counter_en = '1') and
                      ((data_counter_cnt = (latest_min_num_data_per_time-1)) or
                      (latest_min_num_data_per_time = 0)))
                      else '0';
  data_counter_en  <= ordy and ivld and latest_min_num_data_per_time_vld;

  data_counter : counter
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

  data_pipe_latency_cycles_0 : if(DATA_PIPE_LATENCY_CYCLES = 0) generate
    odata.i <= idata.i;
    odata.q <= idata.q;

    imetadata_slv <= to_slv(imetadata);

    metadata_gen : process(imetadata, latest_time, latest_time_vld,
                           allow_time_xfer, imetadata_slv)
    begin
      for idx in metadata'range loop
        if((idx <= METADATA_IDX_TIME_L) and (idx >= METADATA_IDX_TIME_R)) then
          if(pending_time_xfer = '1') then
            metadata(idx) <= latest_time(idx-METADATA_IDX_TIME_R);
          else
            metadata(idx) <= imetadata.time(idx-METADATA_IDX_TIME_R);
          end if;
        elsif(idx = METADATA_IDX_TIME_VLD) then
          metadata(idx) <= allow_time_xfer and
                           (imetadata.time_vld or latest_time_vld);
        else
          metadata(idx) <= imetadata_slv(idx);
        end if;
      end loop;
    end process metadata_gen;

    ometadata <= imetadata when (ctrl.bypass = '1') else from_slv(metadata);

    ovld <= ivld;
    irdy <= ordy;
  end generate;

end rtl;
