library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.all; use misc_prims.misc_prims.all;

-- generates samp drop indicator when backpressure is received
entity adc_samp_drop_detector is
  -- the DATA PIPE LATENCY CYCLES is currently 0
  port(
    -- CTRL
    clk        : in  std_logic;
    rst        : in  std_logic;
    status     : out adc_samp_drop_detector_status_t;
    -- INPUT
    idata      : in  data_complex_adc_t;
    ivld       : in  std_logic;
    -- OUTPUT
    odata      : out data_complex_adc_t;
    osamp_drop : out std_logic;
    ovld       : out std_logic;
    ordy       : in  std_logic);
end entity adc_samp_drop_detector;
architecture rtl of adc_samp_drop_detector is
  signal samp_drop                      : std_logic := '0';
  signal pending_xfer_error_samp_drop_r : std_logic := '0';
  signal xfer_error_samp_drop           : std_logic := '0';
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

  -- start the DATA PIPE LATENCY CYCLES is currently 0
  odata      <= idata;
  osamp_drop <= xfer_error_samp_drop;

  ovld <= ordy and (ivld or xfer_error_samp_drop);
  -- end the DATA PIPE LATENCY CYCLES is currently 0

end rtl;
