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
library zynq; use zynq.zynq_pkg.all;

architecture rtl of worker is
  constant sdp_width_c : natural := to_integer(sdp_width);
  constant sdp_count_c : natural := to_integer(sdp_channels);
  signal clk           : std_logic;
  signal reset         : std_logic; -- our positive reset
  signal count         : unsigned(25 downto 0);
  signal sdp_in_data   : sdp.sdp.data_array_t(0 to sdp_count_c-1, 0 to sdp_width_c-1);
  signal sdp_out_data  : sdp.sdp.data_array_t(0 to sdp_count_c-1, 0 to sdp_width_c-1);
  signal dbg_state     : ulonglong_array_t(0 to sdp_count_c-1);
  signal dbg_state1    : ulonglong_array_t(0 to sdp_count_c-1);
  signal dbg_state2    : ulonglong_array_t(0 to sdp_count_c-1);
begin
  -- Drive metadata interface - boiler plate
  metadata_out.clk     <= clk;
  metadata_out.romAddr <= props_in.romAddr;
  metadata_out.romEn   <= props_in.romData_read;
  -- Drive timekeepping interface - depends on which clock, and whether there is a PPS input
  timebase_out.clk     <= clk;
  timebase_out.reset   <= reset;
  timebase_out.pps     <= GPS_1PPS_IN;
  EXT_1PPS_OUT         <= timebase_in.pps;
  -- convert between 2d array and array of arrays (VHDL does not allow 1d slices of 2d)
   sd0 : for i in 0 to sdp_count_c-1 generate
     sd1: for j in 0 to sdp_width_c-1 generate
            sdp_in_data(i,j) <= zynq_in_data(i)(j);
            zynq_out_data(i)(j) <= sdp_out_data(i,j);
        end generate;
     end generate;
  -- Instantiate the processor system and the converters to control plane and sdp
  ps : zynq_sdp
    generic map(sdp_width => sdp_width_c,
                sdp_count => sdp_count_c,
                use_acp   => its(use_acp),
                which_gp => to_integer(unsigned(from_bool(useGp1))))
    port map(clk => clk,
             reset => reset,
             cp_in => cp_in,
             cp_out => cp_out,
             sdp_in => sdp.sdp.s2m_array_t(zynq_in),
             sdp_in_data => sdp_in_data,
             zynq_out_array_t(sdp_out) => zynq_out,
             sdp_out_data => sdp_out_data,
             axi_error => props_out.axi_error,
             dbg_state => dbg_state,
             dbg_state1 => dbg_state1,
             dbg_state2 => dbg_state2);

  -- Output/readable properties
  props_out.sdpDropCount    <= zynq_in(0).dropCount;
  props_out.dna             <= (others => '0');
  props_out.nSwitches       <= (others => '0');
  props_out.switches        <= (others => '0');
  props_out.memories_length <= to_ulong(1);
  props_out.memories        <= (others => to_ulong(0));
  props_out.nLEDs           <= to_ulong(0); --led'length);
  props_out.UUID            <= metadata_in.UUID;
  props_out.romData         <= metadata_in.romData;

  -- Matchstiq-Z1 clocking
  -- Clock output 1 of the Si5338 comes into the FPGA differentially and is
  -- converted to single ended. The result is sent to the Lime RX_CLK pin
  IBUFGDS_inst : IBUFGDS
    generic map (
      DIFF_TERM => true)
    port map (
      O  => LIME_RX_CLK,
      I  => SI5338_CLK0A,
      IB => SI5338_CLK0B);

  ATLAS_LEDS(2) <= not gps_fix_ind;
  ATLAS_LEDS(1) <= gps_fix_ind;
  ATLAS_LEDS(0) <= not gps_fix_ind;
end rtl;
