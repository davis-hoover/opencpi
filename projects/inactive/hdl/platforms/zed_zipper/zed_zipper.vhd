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
  timebase_out.clk      <= clk;
  timebase_out.PPS      <= '0';
  timebase_out.usingPPS <= '0'; -- When not using PPS, drive usingPPS low
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
  -- TODO / FIXME comment back in once volatile sequence properties are fixed in codegen, which
  -- SHOULD result in this property being changed from an array to a sequence
  --props_out.slotCardIsPresent_length <= nSlots;
  -- fmc_prsnt is active low, this coincides with index 0 of slotName property
  props_out.slotCardIsPresent <= (0 => not fmc_prsnt,
                                  others => '0');
  -- TODO / FIXME remove this line once volatile sequence properties are fixed in codegen, which
  -- SHOULD result in this property being changed from an array to a sequence)
  --  props_out.slotCardIsPresent(1 to 63) <= (others => '0');
  -- Settable properties - drive the leds that are not driven by hardware from the property
  -- led(6 downto 1)           <= std_logic_vector(props_in.leds(6 downto 1));
  -- led(led'left downto 8)    <= (others => '0');
  led(0) <= count(count'left);
  led(1) <= '0';
  led(2) <= '0';
  led(3) <= '0';
  led(4) <= '0';
  led(5) <= dbg_state(0)(0);
  led(6) <= dbg_state1(0)(0);
  led(7) <= dbg_state2(0)(0);
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
