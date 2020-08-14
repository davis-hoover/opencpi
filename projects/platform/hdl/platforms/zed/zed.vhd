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
library zynq; use zynq.zynq_pkg.all;
library axi;
library unisim; use unisim.vcomponents.all;
library ocpi_core_bsv; use ocpi_core_bsv.all;
architecture rtl of worker is
  constant whichGP : natural := to_integer(unsigned(from_bool(useGP1)));
  signal ps_m_axi_gp_in   : axi.zynq_7000_m_gp.axi_s2m_array_t(0 to C_M_AXI_GP_COUNT-1); -- s2m
  signal ps_m_axi_gp_out  : axi.zynq_7000_m_gp.axi_m2s_array_t(0 to C_M_AXI_GP_COUNT-1); -- m2s
  signal ps_s_axi_hp_in   : axi.zynq_7000_s_hp.axi_m2s_array_t(0 to C_S_AXI_HP_COUNT-1); -- m2s
  signal ps_s_axi_hp_out  : axi.zynq_7000_s_hp.axi_s2m_array_t(0 to C_S_AXI_HP_COUNT-1); -- s2m
  signal fclk             : std_logic_vector(3 downto 0);
  signal clk              : std_logic;
  signal raw_rst_n        : std_logic; -- FCLKRESET_Ns need synchronization
  signal rst_n            : std_logic; -- the synchronized negative reset
  signal reset            : std_logic; -- our positive reset
  signal count            : unsigned(25 downto 0);
  signal my_sdp_out       : zynq_out_array_t;      -- so we can observe the SDP outputs for debug
  signal my_sdp_out_data  : zynq_out_data_array_t; -- ditto
  signal dbg_state        : ulonglong_array_t(0 to 3);
  signal dbg_state1       : ulonglong_array_t(0 to 3);
  signal dbg_state2       : ulonglong_array_t(0 to 3);
begin
  -- Drive metadata interface - boiler plate
  metadata_out.clk     <= clk;
  metadata_out.romAddr <= props_in.romAddr;
  metadata_out.romEn   <= props_in.romData_read;
  -- Drive timekeepping interface - depends on which clock, and whether there is a PPS input
  timebase_out.clk     <= clk;
  timebase_out.reset   <= reset;
  timebase_out.pps     <= '0';
  -- Use a global clock buffer for this clock used for both control and data
  clkbuf   : BUFG   port map(I => fclk(0),
                             O => clk);
  -- The FCLKRESET signals from the PS are documented as asynchronous with the
  -- associated FCLK for whatever reason.  Here we make a synchronized reset from it.
  sr : bsv_pkg.SyncResetA
    generic map(RSTDELAY => 17)
    port map   (IN_RST  => raw_rst_n,
                CLK     => clk,
                OUT_RST => rst_n);
  reset <= not rst_n;
  -- Instantiate the processor system (i.e. the interface to it).
  ps : zynq_ps
    port map(
      -- Signals from the PS used in the PL
      ps_in.debug           => (31 => useGP1, others => '0'),
      ps_out.FCLK           => fclk,
      ps_out.FCLKRESET_N    => raw_rst_n,
      m_axi_gp_in           => ps_m_axi_gp_in,
      m_axi_gp_out          => ps_m_axi_gp_out,
      s_axi_hp_in           => ps_s_axi_hp_in,
      s_axi_hp_out          => ps_s_axi_hp_out);

  -- Adapt the axi master from the PS to be a CP Master
  cp : axi.zynq_7000_m_gp.axi2cp_zynq_7000_m_gp
    port map(
      clk     => clk,
      reset   => reset,
      axi_in  => ps_m_axi_gp_out(whichGP),
      axi_out => ps_m_axi_gp_in(whichGP),
      cp_in   => cp_in,
      cp_out  => cp_out
      );
  zynq_out               <= my_sdp_out;
  zynq_out_data          <= my_sdp_out_data;
  props_out.sdpDropCount <= zynq_in(0).dropCount;
  -- We use one sdp2axi adapter foreach of the processor's S_AXI_HP channels
  g : for i in 0 to C_S_AXI_HP_COUNT-1 generate
    dp : axi.zynq_7000_s_hp.sdp2axi_zynq_7000_s_hp
      generic map(ocpi_debug => true,
                  sdp_width  => to_integer(sdp_width))
      port map(   clk          => clk,
                  reset        => reset,
                  sdp_in       => zynq_in(i),
                  sdp_in_data  => zynq_in_data(i),
                  sdp_out      => my_sdp_out(i),
                  sdp_out_data => my_sdp_out_data(i),
                  axi_in       => ps_s_axi_hp_out(i),
                  axi_out      => ps_s_axi_hp_in(i),
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
  led(1) <= ps_m_axi_gp_out(whichGP).AR.VALID;
  led(2) <= '0';
  led(3) <= cp_in.take;
  led(4) <= cp_in.valid;
  led(5) <= ps_m_axi_gp_in(whichGP).AR.READY;
  led(6) <= ps_m_axi_gp_in(whichGP).R.VALID;
  led(7) <= ps_m_axi_gp_out(whichGP).R.READY;
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
  -- g0: if its(ocpi_debug) generate
  --   debug: entity work.zed_debug 
  --     generic map(maxtrace        => maxtrace,
  --                 whichGP         => whichGP)
  --     port map   (clk             => clk,
  --                 reset           => reset,
  --                 props_in        => props_in,
  --                 props_out       => props_out,
  --                 sdp_in          => zynq_in,
  --                 sdp_in_data     => zynq_in_data,
  --                 sdp_out         => my_sdp_out,
  --                 sdp_out_data    => my_sdp_out_data,
  --                 ps_m_axi_gp_in  => ps_m_axi_gp_in,
  --                 ps_m_axi_gp_out => ps_m_axi_gp_out,
  --                 ps_s_axi_hp_in  => ps_s_axi_hp_in,
  --                 ps_s_axi_hp_out => ps_s_axi_hp_out,
  --                 count           => count,
  --                 dbg_state       => dbg_state,
  --                 dbg_state1      => dbg_state1,
  --                 dbg_state2      => dbg_state2);
  -- end generate g0;
end rtl;
