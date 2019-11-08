library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all;

-- generates underrun indicator when data starvation occurs
entity dac_underrun_detector is
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    status    : out dac_underrun_detector_status_t;
    -- INPUT
    idata     : in  data_complex_t;
    imetadata : in  metadata_dac_t;
    ivld      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    odata     : out data_complex_t;
    ometadata : out metadata_dac_t;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end entity dac_underrun_detector;
architecture rtl of dac_underrun_detector is
  signal underrun                      : std_logic := '0';
  signal pending_xfer_underrun_error_r : std_logic := '0';
  signal xfer_underrun_error           : std_logic := '0';
begin

  status.underrun_error <= underrun;

  --underrun only generated when ctrl_tx_on_off = '1'
  underrun <= ordy and (not ivld) and imetadata.ctrl_tx_on_off;

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

  odata.i                        <= idata.i;
  odata.q                        <= idata.q;
  ometadata.underrun_error       <= xfer_underrun_error;
  ometadata.ctrl_tx_on_off       <= imetadata.ctrl_tx_on_off;
  ometadata.data_vld             <= ordy and ivld;
  ovld                           <= ordy and (ivld or xfer_underrun_error);
  irdy                           <= ordy;

end rtl;
