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

-- THIS FILE WAS ORIGINALLY GENERATED ON Tue Jun 23 17:57:52 2015 EDT
-- BASED ON THE FILE: time_server.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: time_server

--
-- This module is normalized the interface when the BSV was converted to VHDL
-- 
library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi, cdc, platform; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of time_server_worker is
  signal ppsIn               : std_logic;
  signal ctl2timebase_reset  : std_logic;
  signal timeControl         : ulong_t;
  signal timeControl_written : bool_t;
  signal timeStatus          : ulong_t;
begin

  -- Map properties to control/status register bits
  timeControl(31)         <= props_in.clr_status_sticky_bits;
  timeControl(6)          <= props_in.force_time_now_invalid;
  timeControl(5)          <= props_in.force_time_now_valid;
  timeControl(4)          <= props_in.force_time_now_to_free_running;
  timeControl(3)          <= not props_in.valid_requires_write_to_time_now; --formerly disableGPS
  timeControl(2)          <= not props_in.enable_time_now_updates_from_PPS; --formerly disablePPS
  timeControl(1 downto 0) <= "00" when props_in.PPS_out_source = derived_from_input_clk_e else
                             "01" when props_in.PPS_out_source = copy_of_input_pps_e else
                             "10" when props_in.PPS_out_source = local_refclk_div_2_e else
                             "11"; --disabled

  timeControl_written     <= props_in.clr_status_sticky_bits_written or
                             props_in.force_time_now_to_free_running_written or
                             props_in.valid_requires_write_to_time_now_written or
                             props_in.enable_time_now_updates_from_PPS_written or
                             props_in.PPS_out_source_written;
  
  props_out.PPS_lost_sticky_error          <= timeStatus(31);
  props_out.time_now_set_sticky            <= timeStatus(30); --formerly gpsIn
  props_out.time_now_updated_by_PPS_sticky <= timeStatus(29); --formerly ppsIn
  props_out.time_now_set_sticky            <= timeStatus(28);
  props_out.PPS_ok                         <= timeStatus(27);
  props_out.PPS_lost_last_second_error     <= timeStatus(26);
  props_out.PPS_count                      <= timeStatus(7 downto 0);
  
  ctl2timebase_rst : component cdc.cdc.reset
    port map   (src_rst => ctl_in.reset,
                dst_clk => timebase_in.clk,
                dst_rst => ctl2timebase_reset);

  ts : entity work.time_service
    generic map(
      g_TIMECLK_FREQ      => from_float(frequency),
      g_PPS_tolerance_PPM => to_integer(PPS_tolerance_PPM))
    port map(
      CLK                 => ctl_in.clk,
      RST                 => ctl_in.reset,
      timeCLK             => timebase_in.clk,
      timeRST             => ctl2timebase_reset,
      ppsIn               => ppsIn,
      timeControl         => timeControl,
      timeControl_written => timeControl_written,
      timeStatus          => timeStatus,
      timeNowIn           => props_in.time_now,
      timeNow_written     => props_in.time_now_written,
      timeNowOut          => props_out.time_now,
      timeDeltaIn         => props_in.delta,
      timeDelta_written   => props_in.delta_written,
      timeDeltaOut        => props_out.delta,
      ticksPerSecond      => props_out.ticks_per_second,
      ppsOut              => timebase_out.PPS,
      time_service        => time_out);

  no_pps_gen: if its(not pps_sim_test) generate
    ppsIn <= timebase_in.PPS;
  end generate;
  
  pps_gen: if its(pps_sim_test) generate
    -- To accelerate the speed of the time_server_test_app, clock the time server
    -- at 100 MHz, but declare frequency at 1 MHz and generate "PPS" at 10 ms. 
    constant c_clk_period     : time := 10 ns;
    constant c_pulse_period   : time := 10 ms;
    constant c_pulse_width    : positive := 16;
  begin
    pps : component platform.platform_pkg.sim_pulse_gen
      generic map(g_clk_period =>   c_clk_period,
                  g_pulse_period => c_pulse_period,
                  g_pulse_width  => c_pulse_width)
      port map(i_reset => ctl2timebase_reset,
               o_pulse => ppsIn);
  end generate;

end rtl;
