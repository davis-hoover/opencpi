library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

entity data_src is
  generic(
    DATA_BIT_WIDTH : positive); -- width of each of I/Q
    --INCLUDE_ERROR_SAMP_DROP : boolean);
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    -- OUTPUT
    odata     : out data_complex_t;
    ometadata : out metadata_t;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end entity data_src;
architecture rtl of data_src is
  signal rst_r                       : std_logic := '0';
  signal vld_rst                     : std_logic := '0';
  signal maximal_lfsr_data_src_ovld  : std_logic := '0';
  signal maximal_lfsr_data_src_odata : data_complex_t;

  signal time_time : unsigned(METADATA_TIME_BIT_WIDTH-1 downto 0) :=
                     (others => '0');
  signal metadata : std_logic_vector(METADATA_BIT_WIDTH-1 downto 0) :=
                    (others => '0');
begin

  -- trying to obey axi4streaming TVALID rules
  rst_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      rst_r <= rst;
    end if;
  end process;
  vld_rst <= rst or rst_r;

  maximal_lfsr_data_src : misc_prims.misc_prims.maximal_lfsr_data_src
    port map(
      -- CTRL
      clk                => clk,
      rst                => rst,
      stop_on_period_cnt => '0',
      stopped            => open,
      -- OUTPUT
      odata              => maximal_lfsr_data_src_odata,
      ovld               => maximal_lfsr_data_src_ovld,
      ordy               => ordy);

  time_gen : counter
    generic map(
      BIT_WIDTH => METADATA_TIME_BIT_WIDTH)
    port map(
      clk => clk,
      rst => rst,
      en  => '1',
      cnt => time_time);

  odata <= maximal_lfsr_data_src_odata;
  ovld  <= maximal_lfsr_data_src_ovld;

  metadata_gen : process(ordy, maximal_lfsr_data_src_odata,
                         maximal_lfsr_data_src_ovld)
  begin
    for idx in metadata'range loop
      if((idx <= METADATA_IDX_TIME_L) and (idx >= METADATA_IDX_TIME_R)) then
        metadata(idx) <= time_time(idx-METADATA_IDX_TIME_R);
      elsif(idx = METADATA_IDX_TIME_VLD) then
        metadata(idx) <= ordy and (not vld_rst);
      elsif(idx = METADATA_IDX_ERROR_SAMP_DROP) then
        metadata(idx) <= maximal_lfsr_data_src_odata.i(0);
      elsif(idx = METADATA_IDX_DATA_VLD) then
        metadata(idx) <= maximal_lfsr_data_src_ovld and (not vld_rst);
      else
        metadata(idx) <= '0';
      end if;
    end loop;
  end process metadata_gen;

  ometadata <= from_slv(metadata);

end rtl;
