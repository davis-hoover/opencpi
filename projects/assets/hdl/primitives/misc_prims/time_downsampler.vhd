library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library timestamped_adc_ingestor;
use timestamped_adc_ingestor.timestamped_adc_ingestor.all;

-- for metadata, registers time every data_count_between_time I/Q values,
-- effectively downsampling time
entity time_downsampler is
  generic(
    PIPELINE_LATENCY_CYCLES : natural := 0);
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    ctrl      : in  time_downsampler_ctrl_t;
    -- INPUT
    idata     : in  data_complex_t;
    imetadata : in  metadata_samp_drop_t;
    ivld      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    odata     : out data_complex_t;
    ometadata : out metadata_samp_drop_time_t;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end entity time_downsampler;
architecture rtl of time_downsampler is
  signal do_reg                       : std_logic := '0';
  signal latest_time                  : unsigned(METADATA_TIME_BIT_WIDTH-1
                                        downto 0) := (others => '0');
  signal latest_time_vld              : std_logic := '0';
  signal latest_data_cnt_between_time : unsigned(
                                        CTRL_TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH
                                        -1 downto 0) := (others => '0');
  signal latest_data_cnt_between_time_vld : std_logic := '0';

  signal data_vld        : std_logic := '0';
  signal data_count_done : std_logic := '0';
  signal data_count_en   : std_logic := '0';
  signal data_count      : unsigned(CTRL_TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH
                                    -1 downto 0) := (others => '0');
  signal time_out_en     : std_logic := '0';
  
begin

  ------------------------------------------------------------------------------
  -- latest time/valid registers which effectively downsample
  ------------------------------------------------------------------------------

  do_reg <= ordy and imetadata.time_vld;

  latest_time_regs : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        latest_time     <= (others => '0');
        latest_time_vld <= '0';
      elsif((ordy = '1') and (imetadata.time_vld = '1')) then
        latest_time     <= imetadata.meta_time;
        latest_time_vld <= '1';
      end if;
    end if;
  end process latest_time_regs;

  ------------------------------------------------------------------------------
  -- latest data_cnt_between_time register
  ------------------------------------------------------------------------------

  latest_data_cnt_between_time_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        latest_data_cnt_between_time     <= (others => '0');
        latest_data_cnt_between_time_vld <= '0';
      elsif((ordy = '1') and (ctrl.data_cnt_between_time_vld = '1')) then
        latest_data_cnt_between_time     <= ctrl.data_cnt_between_time;
        latest_data_cnt_between_time_vld <= ctrl.data_cnt_between_time_vld;
      end if;
    end if;
  end process latest_data_cnt_between_time_reg;

  ------------------------------------------------------------------------------
  -- counter to initiate time selection for downsampling
  ------------------------------------------------------------------------------

  data_vld        <= ivld and (not imetadata.overrun);
  data_count_done <= '1' when ((latest_data_cnt_between_time_vld = '1') and
                      (data_count = latest_data_cnt_between_time - 1)) else '0';
  data_count_en   <= ordy and ivld;

  data_counter : process(clk)
  begin
    if(rising_edge(clk)) then
      if((rst = '1') or (data_count_done = '1')) then
        data_count <= (others => '0');
      elsif(data_count_en = '1') then
        data_count <= data_count + 1;
      end if;
    end if;
  end process;

  time_out_en <= data_count_done;

  ------------------------------------------------------------------------------
  -- output data/metadata generation
  ------------------------------------------------------------------------------

  pipeline_latency_cycles_0 : if(PIPELINE_LATENCY_CYCLES = 0) generate

    odata.i                 <= idata.i;
    odata.q                 <= idata.q;
    ometadata.overrun       <= imetadata.overrun;
    ometadata.meta_time     <= latest_time;
    ometadata.time_vld      <= latest_time_vld;
    ovld                    <= ivld;
    irdy                    <= ordy;

  end generate;

end rtl;
