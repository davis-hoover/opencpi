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
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library platform; use platform.platform_pkg.all;
library zynq_ultra; use zynq_ultra.zynq_ultra_pkg.all;
library axi; use axi.axi_pkg.all;
library unisim; use unisim.vcomponents.all;
library bsv;
library sdp; use sdp.sdp.all;
architecture rtl of zcu104_worker is
  -- Note: useGP1/whichGP are used in Zynq platforms but require PS/SW to detect this property's value.
  --       This is not yet supported on ZynqMP/UltraScale+, so it is tied to '0' to use GP0.
  --constant whichGP : natural := to_integer(unsigned(from_bool(useGP1)));
  constant whichGP : natural := to_integer(unsigned(from_bool('0')));
  signal ps_m_axi_gp_in   : axi.zynq_ultra_m_hp.axi_s2m_array_t(0 to C_M_AXI_HP_COUNT-1); -- s2m
  signal ps_m_axi_gp_out  : axi.zynq_ultra_m_hp.axi_m2s_array_t(0 to C_M_AXI_HP_COUNT-1); -- m2s
  signal ps_s_axi_hp_in   : axi.zynq_ultra_s_hp.axi_m2s_array_t(0 to C_S_AXI_HP_COUNT-1); -- m2s
  signal ps_s_axi_hp_out  : axi.zynq_ultra_s_hp.axi_s2m_array_t(0 to C_S_AXI_HP_COUNT-1); -- s2m
  signal fclk             : std_logic_vector(3 downto 0);
  signal clk              : std_logic;
  signal raw_rst_n        : std_logic;     -- FCLKRESET_Ns need synchronization
  signal rst_n            : std_logic;     -- the synchronized negative reset
  signal reset            : std_logic; -- our positive reset
  signal count            : unsigned(25 downto 0);
  signal my_sdp_out       : zynq_ultra_out_array_t;
  signal my_sdp_out_data  : zynq_ultra_out_data_array_t;
  signal dbg_state        : ulonglong_array_t(0 to 3);
  signal dbg_state1       : ulonglong_array_t(0 to 3);
  signal dbg_state2       : ulonglong_array_t(0 to 3);
  signal ledbuf           : std_logic_vector(2 downto 0) := (others => '0');
  signal cnt_t            : STD_LOGIC_VECTOR(31 DOWNTO 0) := x"0000_0000";
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
  clkbuf : BUFG port map(I => fclk(0),
                         O => clk);
  -- The FCLKRESET signals from the PS are documented as asynchronous with the
  -- associated FCLK for whatever reason.  Here we make a synchronized reset from it.
  -- cdc.cdc reset allows one to take in active low reset and output an active high or low reset
  sr : cdc.cdc.reset
    generic map(SRC_RST_VALUE => '0',
                RST_DELAY => 17)
    port map   (src_rst => raw_rst_n,
                dst_clk => clk,
                dst_rst => reset,
                dst_rst_n => open);
  -- Instantiate the processor system (i.e. the interface to it).
  ps : zynq_ultra_ps
    port map(
      -- Signals from the PS used in the PL
      --   Note: useGP1 is used on Zynq platforms but requires the PS/SW to detect this property's value.
      --         This is not yet suppported on ZynqMP/UltraScale, so it is tied to '0' to use GP0.
      --     ps_in.debug           => (31 => useGP1, others => '0'),
      ps_in.debug           => (31 => useGP1, others => '0'),
      ps_out.FCLK           => fclk,
      ps_out.FCLKRESET_N    => raw_rst_n,
      m_axi_hp_in           => ps_m_axi_gp_in,
      m_axi_hp_out          => ps_m_axi_gp_out,
      s_axi_hp_in           => ps_s_axi_hp_in,
      s_axi_hp_out          => ps_s_axi_hp_out);

  -- Adapt the axi master from the PS to be a CP Master
  cp : axi.zynq_ultra_m_hp.axi2cp_zynq_ultra_m_hp
    port map(
      clk     => clk,
      reset   => reset,
      axi_in  => ps_m_axi_gp_out(whichGP),
      axi_out => ps_m_axi_gp_in(whichGP),
      cp_in   => cp_in,
      cp_out  => cp_out);
  zynq_ultra_out               <= my_sdp_out;
  zynq_ultra_out_data          <= my_sdp_out_data;
  props_out.sdpDropCount <= zynq_ultra_in(0).dropCount;
  -- We use one sdp2axi adapter foreach of the processor's S_AXI_HP channels
  g : for i in 0 to C_S_AXI_HP_COUNT-1 generate
    dp : axi.zynq_ultra_s_hp.sdp2axi_zynq_ultra_s_hp
      generic map(ocpi_debug => true,
                  sdp_width  => to_integer(sdp_width))
      port map(   clk          => clk,
                  reset        => reset,
                  sdp_in       => zynq_ultra_in(i),
                  sdp_in_data  => zynq_ultra_in_data(i),
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
  props_out.memories_length <= to_ulong(1);
  props_out.memories        <= (others => to_ulong(0));
  props_out.UUID            <= metadata_in.UUID;
  props_out.romData         <= metadata_in.romData;
  props_out.switches        <= resize(unsigned(switches), props_out.switches'length);
  leds <= std_logic_vector(props_in.leds(leds'range));
  -- The process below toggles LEDs 0-2 at rates of 0.5, 1 and 2 seconds respectively
  -- This allows for experimental verification that 'clk' is running at roughly 100MHz
  process (clk) is
  begin
    if rising_edge(clk)  then
        if (reset ='1') then
          cnt_t <= x"0000_0000";
          ledbuf(0) <= '0';
          ledbuf(1) <= '0';
          ledbuf(2) <= '0';
        elsif (cnt_t = x"02FA_F080") then -- 0.5 second
            cnt_t <= std_logic_vector(unsigned(cnt_t) + 1);
            ledbuf(0) <= not ledbuf(0);
        elsif (cnt_t = x"05F5_E100") then --   1 second
            cnt_t <= std_logic_vector(unsigned(cnt_t) + 1);
            ledbuf(0) <= not ledbuf(0);
            ledbuf(1) <= not ledbuf(1);
        elsif (cnt_t = x"08F0_D180") then -- 1.5 seconds
            cnt_t <= std_logic_vector(unsigned(cnt_t) + 1);
            ledbuf(0) <= not ledbuf(0);
        elsif (cnt_t = x"0BEB_C200") then --   2 seconds
            cnt_t <= x"0000_0000";
            ledbuf(0) <= not ledbuf(0);
            ledbuf(1) <= not ledbuf(1);
            ledbuf(2) <= not ledbuf(2);
        else
            cnt_t <= std_logic_vector(unsigned(cnt_t) + 1);
        end if;
    end if;
  end process;

  -- -- Some LED logic which is unecessary but may be useful for debugging
  -- led(3) <= reset;
  -- -- This pattern of LEDs makes it easy to experimentally determine which LED is index 0 vs 7 on the board
  -- led(4) <= '1';
  -- led(5) <= '0';
  -- led(6) <= '1';
  -- led(7) <= '1';

  -- work : process(clk)
  -- begin
  --   if rising_edge(clk) then
  --     if reset = '0' then
  --       dbg_state_r <= dbg_state;
  --       dbg_state1_r <= dbg_state1;
  --       dbg_state2_r <= dbg_state2;
  --     end if;
  --   end if;
  -- end process;
end rtl;
