library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library protocol, dac; use dac.dac.all;

-- generates underrun indicator when data starvation occurs
entity underrun_detector is
  port(
    -- CTRL
    clk           : in  std_logic;
    rst           : in  std_logic;
    status        : out underrun_detector_status_t;
    -- INPUT
    iprotocol     : in  protocol.complex_short_with_metadata.protocol_t;
    imetadata     : in  metadata_t;
    imetadata_vld : in  std_logic;
    irdy          : out std_logic;
    -- OUTPUT
    oprotocol     : out protocol.complex_short_with_metadata.protocol_t;
    ometadata     : out metadata_t;
    ometadata_vld : out std_logic;
    ordy          : in  std_logic);
end entity underrun_detector;
architecture rtl of underrun_detector is
  signal underrun                      : std_logic := '0';
  signal pending_xfer_underrun_error_r : std_logic := '0';
  signal xfer_underrun_error           : std_logic := '0';
begin

  status.underrun_error <= underrun;

  --underrun only generated when ctrl_tx_on_off = '1'
  underrun <= ordy and (not iprotocol.samples_vld) and imetadata.ctrl_tx_on_off;

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
