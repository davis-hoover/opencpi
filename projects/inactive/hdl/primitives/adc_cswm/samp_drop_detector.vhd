-- This file is protected by Copyright. Please refer to the COPYRIGHT file
-- distributed with this source distribution.
--
-- This file is part of OpenCPI <http://www.opencpi.org>
--
-- OpenCPI is free software: you can redistribute it and/or modify it under the
-- terms of the GNU Lesser General Public License as published by the Free
-- Software Foundation, either version 3 of the License, or (at your option) any
-- later version.
--
-- OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
-- WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
-- A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
-- details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library adc_cswm; use adc_cswm.adc_cswm.all;

-- generates samp drop indicator when backpressure is received
entity samp_drop_detector is
  -- the DATA PIPE LATENCY CYCLES is currently 0
  port(
    -- CTRL
    clk        : in  std_logic;
    rst        : in  std_logic;
    status     : out samp_drop_detector_status_t;
    -- INPUT
    idata      : in  data_complex_t;
    ivld       : in  std_logic;
    -- OUTPUT
    odata      : out data_complex_t;
    osamp_drop : out std_logic;
    ovld       : out std_logic;
    ordy       : in  std_logic);
end entity samp_drop_detector;
architecture rtl of samp_drop_detector is
  constant samp_count_max_value               : unsigned  := x"FFFF_FFFF"; -- (2^SAMP_COUNT_BIT_WIDTH)-1
  constant num_dropped_samps_count_max_value  : unsigned  := x"FFFF_FFFF"; -- (2^DROPPED_SAMPS_BIT_WIDTH)-1
  signal samp_drop                            : std_logic := '0';
  signal pending_xfer_error_samp_drop_r       : std_logic := '0';
  signal xfer_error_samp_drop                 : std_logic := '0';
  signal samp_count_before_first_samp_drop    : unsigned(SAMP_COUNT_BIT_WIDTH-1 downto 0);
  signal num_dropped_samps                    : unsigned(DROPPED_SAMPS_BIT_WIDTH-1 downto 0);
  signal first_samp_drop_detected_sticky      : std_logic := '0';
begin

  status.error_samp_drop <= samp_drop;
  status.samp_count_before_first_samp_drop <= std_logic_vector(samp_count_before_first_samp_drop);
  status.num_dropped_samps <= std_logic_vector(num_dropped_samps);

  samp_drop <= ivld and (not ordy);

  first_samp_drop_detected_sticky_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        first_samp_drop_detected_sticky <= '0';
      elsif(xfer_error_samp_drop = '1') then
        first_samp_drop_detected_sticky <= '1';
      end if;
    end if;
  end process;

  samp_count_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        samp_count_before_first_samp_drop <= (others=>'0');
      elsif(first_samp_drop_detected_sticky = '0' and samp_count_before_first_samp_drop < samp_count_max_value) then
          if (ivld = '1' and ordy = '1') then
            samp_count_before_first_samp_drop <= samp_count_before_first_samp_drop + 1;
          end if;
      end if;
    end if;
  end process;

  num_samps_dropped_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        num_dropped_samps <= (others=>'0');
      elsif (xfer_error_samp_drop = '1' and num_dropped_samps < num_dropped_samps_count_max_value) then
        num_dropped_samps <= num_dropped_samps + 1;
      end if;
    end if;
  end process;


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

  ovld <= ordy and ivld;
  -- end the DATA PIPE LATENCY CYCLES is currently 0

end rtl;
