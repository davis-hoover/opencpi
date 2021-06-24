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

library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library ocpi; use ocpi.types.all;
library platform;
library cyclone5; use cyclone5.cyclone5_pkg.all;
library axi, sdp, cdc;
library altera; use altera.altera_primitives_components.all;

architecture rtl of worker is
  signal hps_h2f_axi_in   : axi.cyclone5_h2f.axi_s2m_array_t(0 to C_H2F_AXI_COUNT-1); -- s2m
  signal hps_h2f_axi_out  : axi.cyclone5_h2f.axi_m2s_array_t(0 to C_H2F_AXI_COUNT-1); -- m2s
  signal hps_f2h_axi_in   : axi.cyclone5_f2h.axi_m2s_array_t(0 to C_F2H_AXI_COUNT-1); -- m2s
  signal hps_f2h_axi_out  : axi.cyclone5_f2h.axi_s2m_array_t(0 to C_F2H_AXI_COUNT-1); -- s2m
  signal h2f_user0_clk    : std_logic;
  signal clk              : std_logic;
  signal raw_rst_n        : std_logic; -- h2f_rst_n need synchronization
  signal reset            : std_logic; -- our positive reset
  signal count            : unsigned(25 downto 0);
  signal my_sdp_out       : cyclone5_sockit_out_array_t;      -- so we can observe the SDP outputs for debug
  signal my_sdp_out_data  : cyclone5_sockit_out_data_array_t; -- ditto
  signal dbg_state        : ulonglong_array_t(0 to 3);
  signal dbg_state1       : ulonglong_array_t(0 to 3);
  signal dbg_state2       : ulonglong_array_t(0 to 3);
  signal h2f_cold_rst_n   : std_logic; -- Cold-only reset to FPGA fabric
begin
  -- Drive metadata interface - boiler plate
  metadata_out.clk     <= clk;
  metadata_out.romAddr <= props_in.romAddr;
  metadata_out.romEn   <= props_in.romData_read;
  -- Drive timekeepping interface - depends on which clock, and whether there is a PPS input
  timebase_out.clk      <= clk;
  timebase_out.PPS      <= '0';
  timebase_out.usingPPS <= '0'; -- When not using PPS, drive usingPPS low
  
  -- Use a global clock buffer for this clock used for both control and data
  clkbuf : global   port map(a_in  => h2f_user0_clk,
                             a_out => clk);

  -- The FCLKRESET signals from the PS are documented as asynchronous with the
  -- associated FCLK for whatever reason.  Here we make a synchronized reset from it.
  sr : cdc.cdc.reset
  generic map (
    SRC_RST_VALUE => '0',
    RST_DELAY => 17)
  port map (
    src_rst   => raw_rst_n,
    dst_clk   => clk,
    dst_rst   => reset,
    dst_rst_n => open);

  -- Instantiate the hard processor system (i.e. the interface to it).
  hps : cyclone5_hps
    port map(
      -- Signals from the PS used in the PL
      hps_out.h2f_rst_n       => raw_rst_n,
      hps_out.h2f_user0_clk   => h2f_user0_clk,
      hps_out.h2f_cold_rst_n  => h2f_cold_rst_n,
      h2f_axi_in              => hps_h2f_axi_in,
      h2f_axi_out             => hps_h2f_axi_out,
      f2h_axi_in              => hps_f2h_axi_in,
      f2h_axi_out             => hps_f2h_axi_out);

  -- Adapt the axi master from the HPS to be a CP Master
  cp : axi.cyclone5_h2f.axi2cp_cyclone5_h2f
    port map (
      clk     => clk,
      reset   => reset,
      axi_in  => hps_h2f_axi_out(0),
      axi_out => hps_h2f_axi_in(0),
      cp_in   => cp_in,
      cp_out  => cp_out);

  cyclone5_sockit_out <= my_sdp_out;
  cyclone5_sockit_out_data <= my_sdp_out_data;
  props_out.sdpDropCount <= cyclone5_sockit_in(0).dropCount;
  -- We use one sdp2axi adapter foreach of the processor's S_AXI channels
  g : for i in 0 to C_F2H_AXI_COUNT-1 generate
    dp : axi.cyclone5_f2h.sdp2axi_cyclone5_f2h
      generic map(ocpi_debug => true,
                  sdp_width  => to_integer(sdp_width))
      port map(   clk          => clk,
                  reset        => reset,
                  sdp_in       => cyclone5_sockit_in(i),
                  sdp_in_data  => cyclone5_sockit_in_data(i),
                  sdp_out      => my_sdp_out(i),
                  sdp_out_data => my_sdp_out_data(i),
                  axi_in       => hps_f2h_axi_out(i),
                  axi_out      => hps_f2h_axi_in(i),
                  axi_error    => props_out.axi_error(i),
                  dbg_state    => dbg_state(i),
                  dbg_state1   => dbg_state1(i),
                  dbg_state2   => dbg_state2(i));
  end generate;
  
  -- Output/readable properties
  props_out.dna             <= (others => '0');
  props_out.nSwitches       <= (others => '0');
  props_out.switches        <= (others => '0');
  props_out.memories_length <= to_ulong(1);
  props_out.memories        <= (others => to_ulong(0));
  props_out.nLEDs           <= to_ulong(0); --led'length);
  props_out.UUID            <= metadata_in.UUID;
  props_out.romData         <= metadata_in.romData;

  fpga_led_pio(0) <= count(count'left);
  fpga_led_pio(1) <= dbg_state(0)(0);
  fpga_led_pio(2) <= dbg_state1(0)(0);
  fpga_led_pio(3) <= dbg_state2(0)(0);
  -- Counter for blinking LED and debug
  work : process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        count <= (others => '0');
      else
        count <= count + 1;
      end if;
    end if;
  end process;
 
end rtl;
