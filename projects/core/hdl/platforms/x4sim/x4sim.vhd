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

-- THIS FILE WAS ORIGINALLY GENERATED ON Thu Sep 26 15:32:12 2013 EDT
-- BASED ON THE FILE: modelsim.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: xsim4

library IEEE, ocpi, platform, sdp, util;
use IEEE.std_logic_1164.all, ieee.numeric_std.all, ocpi.types.all, platform.platform_pkg.all, sdp.all;

architecture rtl of worker is
  signal ctl_clk          : std_logic;
  signal ctl_reset        : std_logic := '0';
  signal ctl_reset_n      : std_logic;
  signal sdp_clk          : std_logic;
  signal sdp_reset        : std_logic := '0';
  -- between the sim_sdp and sdp_node for control plane
  signal sdp_sim_in       : sdp.sdp.s2m_t;
  signal sdp_sim_out      : sdp.sdp.m2s_t;
  signal sdp_sim_in_data  : dword_array_t(0 to to_integer(sdp_width)-1);
  signal sdp_sim_out_data : dword_array_t(0 to to_integer(sdp_width)-1);
  -- between sdp_node and sdp2cp_clk
  signal sdp_cp_in        : sdp.sdp.s2m_t;
  signal sdp_cp_out       : sdp.sdp.m2s_t;
  signal sdp_cp_in_data   : dword_array_t(0 to to_integer(sdp_width)-1);
  signal sdp_cp_out_data  : dword_array_t(0 to to_integer(sdp_width)-1);
  -- internal version of sdp_out so we can inject the clock and reset
  signal my_sdp_out       : sdp.sdp.m2s_t;
begin
  ctl_reset_n           <= not ctl_reset;
  timebase_out.clk      <= ctl_clk;
  timebase_out.PPS      <= '0';
  timebase_out.usingPPS <= '0'; -- When not using PPS, drive usingPPS low

  -- generate clocks
  control_clock : sim_clk
    generic map(frequency => 100000000.0, offset => 0)
    port map(clk => ctl_clk, reset => ctl_reset);
  sdp_clock : sim_clk
    generic map(frequency => 120000000.0, offset => 3)
    port map(clk => sdp_clk, reset => sdp_reset);


  sdp_sim_i : sdp.sdp.sdp_sim
    generic map(ocpi_debug => ocpi_debug,
                sdp_width  => sdp_width)
    port map(clk => sdp_clk,
             reset => sdp_reset,
             sdp_in => sdp_sim_in,
             sdp_out => sdp_sim_out,
             sdp_in_data => sdp_sim_in_data,
             sdp_out_data => sdp_sim_out_data);

  sdp_node_i : component sdp.sdp.sdp_node_rv
    generic map(sdp_width  => sdp_width)
    port map( wci_Clk => ctl_clk,
              wci_Reset_n => ctl_reset_n,
              sdp_Clk => sdp_clk,
              sdp_Reset => sdp_reset,
              up_in => sdp_sim_out,
              up_in_data => sdp_sim_out_data,
              up_out => sdp_sim_in,
              up_out_data => sdp_sim_in_data,
              client_in => sdp_cp_in,
              client_in_data => sdp_cp_in_data,
              client_out => sdp_cp_out,
              client_out_data => sdp_cp_out_data,
              down_in => sdp_in,
              down_in_data => sdp_in_data,
              down_out => my_sdp_out,
              down_out_data => sdp_out_data);

  sdp2cp_clk_i : component sdp.sdp.sdp2cp_clk_rv
    generic map(sdp_width  => sdp_width)
    port map( wci_Clk => ctl_clk,
              wci_Reset_n => ctl_reset_n,
              sdp_Clk => sdp_clk,
              sdp_Reset => sdp_reset,
              cp_in => cp_in,
              cp_out => cp_out,
              sdp_in => sdp_cp_out,
              sdp_in_data => sdp_cp_out_data,
              sdp_out => sdp_cp_in,
              sdp_out_data => sdp_cp_in_data);

  in2out_sdp_clk: util.util.in2out port map(in_port => sdp_clk, out_port => sdp_out.clk);
  --  sdp_out.clk   <= sdp_clk;
  sdp_out.reset <= sdp_reset;
  sdp_out.id    <= my_sdp_out.id;
  sdp_out.sdp   <= my_sdp_out.sdp;
  props_out.dna               <= (others => '0');
  props_out.nSwitches         <= (others => '0');
  props_out.switches          <= (others => '0');
  props_out.memories_length   <= to_ulong(1);
  props_out.memories          <= (others => to_ulong(0));
  props_out.nLEDs             <= (others => '0');
  props_out.UUID              <= metadata_in.UUID;
  props_out.romData           <= metadata_in.romData;
  props_out.sdpDropCount      <= sdp_in.dropCount;
  props_out.slotCardIsPresent <= (others => '0');
  metadata_out.clk            <= ctl_clk;
  metadata_out.romAddr        <= props_in.romAddr;
  metadata_out.romEn          <= props_in.romData_read;
end rtl;
