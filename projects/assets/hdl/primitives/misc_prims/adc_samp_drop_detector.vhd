library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.all; use misc_prims.misc_prims.all;

-- generates samp drop indicator when backpressure is received
entity adc_samp_drop_detector is
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
end entity adc_samp_drop_detector;
architecture rtl of adc_samp_drop_detector is
  signal samp_drop                      : std_logic := '0';
  signal pending_xfer_error_samp_drop_r : std_logic := '0';
  signal xfer_error_samp_drop           : std_logic := '0';

  signal metadata      : std_logic_vector(METADATA_BIT_WIDTH-1 downto 0) :=
                         (others => '0');
begin

  status.error_samp_drop <= samp_drop;

  samp_drop <= ivld and (not ordy);

  pending_terror_samp_drop_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        pending_xfer_error_samp_drop_r <= '0';
      elsif(samp_drop = '1') then
        pending_xfer_error_samp_drop_r <= '1';
      elsif(xfer_error_samp_drop = '1') then
        pending_xfer_error_samp_drop_r <= '0';
      end if;
    end if;
  end process;

  xfer_error_samp_drop <= ordy and pending_xfer_error_samp_drop_r;

  data_pipe_latency_cycles_0 : if(DATA_PIPE_LATENCY_CYCLES = 0) generate
    odata.i                   <= idata.i;
    odata.q                   <= idata.q;

    metadata_gen : process(xfer_error_samp_drop, ordy, ivld)
    begin
      for idx in metadata'range loop
        if(idx = METADATA_IDX_ERROR_SAMP_DROP) then
          metadata(idx) <= xfer_error_samp_drop;
        elsif(idx = METADATA_IDX_DATA_VLD) then
          metadata(idx) <= ordy and ivld;
        else
          metadata(idx) <= '0';
        end if;
      end loop;
    end process metadata_gen;

    ometadata <= from_slv(metadata);

    ovld <= ordy and (ivld or xfer_error_samp_drop);
  end generate;

end rtl;
