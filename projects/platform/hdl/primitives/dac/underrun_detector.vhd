library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library timed_sample_prot, dac; use dac.dac.all;

-- generates underrun indicator when data starvation occurs
entity underrun_detector is
  port(
    -- CTRL
    clk           : in  std_logic;
    rst           : in  std_logic;
    status        : out underrun_detector_status_t;
    -- INPUT
    iprotocol     : in  timed_sample_prot.complex_short_timed_sample.protocol_t;
    imetadata     : in  metadata_t;
    imetadata_vld : in  std_logic;
    irdy          : out std_logic;
    -- OUTPUT
    oprotocol     : out timed_sample_prot.complex_short_timed_sample.protocol_t;
    ometadata     : out metadata_t;
    ometadata_vld : out std_logic;
    ordy          : in  std_logic);
end entity underrun_detector;
architecture rtl of underrun_detector is
  constant samp_count_max_value           : unsigned  := x"FFFF_FFFF"; -- (2^SAMP_COUNT_BIT_WIDTH)-1
  constant num_underruns_count_max_value  : unsigned  := x"FFFF_FFFF"; -- (2^NUM_UNDERRUNS_BIT_WIDTH)-1
  signal underrun                      : std_logic := '0';
  signal pending_xfer_underrun_error_r : std_logic := '0';
  signal xfer_underrun_error           : std_logic := '0';
  signal samp_count_before_first_underrun  : unsigned(SAMP_COUNT_BIT_WIDTH-1 downto 0);
  signal num_underruns                     : unsigned(NUM_UNDERRUNS_BIT_WIDTH-1 downto 0);
  signal first_underrun_detected_sticky    : std_logic;
begin

  status.underrun_error <= underrun;
  status.samp_count_before_first_underrun <= std_logic_vector(samp_count_before_first_underrun);
  status.num_underruns <= std_logic_vector(num_underruns);

  --underrun only generated when ctrl_tx_on_off = '1'
  underrun <= ordy and (not iprotocol.sample_vld) and imetadata.ctrl_tx_on_off;
  
  first_underrun_detected_sticky_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        first_underrun_detected_sticky <= '0';
      elsif(xfer_underrun_error = '1') then
        first_underrun_detected_sticky <= '1';
      end if;
    end if;
  end process;

  samp_count_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        samp_count_before_first_underrun <= (others=>'0');
      elsif(first_underrun_detected_sticky = '0' and samp_count_before_first_underrun < samp_count_max_value) then
          if (iprotocol.sample_vld = '1' and ordy = '1' and imetadata.ctrl_tx_on_off = '1') then
            samp_count_before_first_underrun <= samp_count_before_first_underrun + 1;
          end if;
      end if;
    end if;
  end process;

  num_underruns_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        num_underruns <= (others=>'0');
      elsif (xfer_underrun_error = '1' and num_underruns < num_underruns_count_max_value) then
        num_underruns <= num_underruns + 1;
      end if;
    end if;
  end process;

  pending_underrun_error_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        pending_xfer_underrun_error_r <= '0';
      else
        pending_xfer_underrun_error_r <= underrun;
      end if;
    end if;
  end process;

  xfer_underrun_error <= ordy and pending_xfer_underrun_error_r;

  oprotocol                <= iprotocol;
  ometadata.underrun_error <= xfer_underrun_error;
  ometadata.ctrl_tx_on_off <= imetadata.ctrl_tx_on_off;
  ometadata_vld            <= ordy and ((imetadata_vld and
                              imetadata.ctrl_tx_on_off) or xfer_underrun_error);
  irdy                     <= ordy;

end rtl;
