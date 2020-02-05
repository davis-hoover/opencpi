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

-------------------------------------------------------------------------------
-- Signal Time Tagger
-------------------------------------------------------------------------------
--
-- Description:
-- The worker detects rising edges of input signal "signal_to_time_tag" and
-- records the time from its time interface in the time_tags_collected property
--
-------------------------------------------------------------------------------
library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi,cdc,misc_prims; use ocpi.types.all, ocpi.util.all; -- remove this to avoid all ocpi name collisions
architecture rtl of signal_time_tagger_worker is
  signal time_tag_cnt             : unsigned(width_for_max(to_integer(MAX_NUM_TIME_TAGS_TO_COLLECT))-1 downto 0);
  signal ctl2time_reset           : std_logic;
  signal time_is_operating        : std_logic;
  signal signal_to_time_tag_redge : std_logic;
  signal time_64bit               : ulonglong_t;
  signal time_64bit_corrected     : ulonglong_t;
begin

  ctl2time_rst : component cdc.cdc.reset
    port map (src_rst => ctl_in.reset,
              dst_clk => time_in.clk,
              dst_rst => ctl2time_reset);

  is_op : component cdc.cdc.single_bit
    port map   (src_clk => ctl_in.clk,
                src_rst => ctl_in.reset,
                src_in  => ctl_in.is_operating,
                src_en  => '1',
                dst_clk => time_in.clk,
                dst_rst => '0',
                dst_out => time_is_operating);
  
  redge_detect : component misc_prims.misc_prims.edge_detector
    port map (clk           => time_in.clk,
              reset         => ctl2time_reset,
              din           => signal_to_time_tag,
              rising_pulse  => signal_to_time_tag_redge,
              falling_pulse => open);

  time_64bit           <= time_in.seconds & time_in.fraction;
  time_64bit_corrected <= ulonglong_t(signed(time_64bit) - props_in.calibration_value);
  
  process(time_in.clk)
  begin
    if rising_edge(time_in.clk) then
      if its(ctl2time_reset) then
        time_tag_cnt <= (others => '0');
        props_out.collected_time_tags <= (others => (others => '0'));
      elsif its(time_is_operating) then
        if its(signal_to_time_tag_redge) and time_tag_cnt < props_in.num_time_tags_to_collect then
          time_tag_cnt <= time_tag_cnt + 1;
          props_out.collected_time_tags(to_integer(time_tag_cnt)) <= time_64bit_corrected;
        end if;
      end if;
    end if;
  end process;

  ctl_out.finished <= to_bool(time_tag_cnt = props_in.num_time_tags_to_collect);
  
end rtl;
