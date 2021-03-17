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

-- This module configures a zynq PS with axi adapters to SDP in a few different configurations
-- The control path simply selects which m_gp AXI port to use (0 or 1)
-- The data path has count (how many SDPs and AXIs) and SDP width
-- The data path also has the option of using the AXI ACP port rather than the AXI HP ports.
-- Note that using the AXI ACP port limits buffer count to 4 and node count to 2
-- (it could limit buffer count to 2 and node count to 4)

library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library ocpi; use ocpi.types.all;
library zynq; use zynq.zynq_pkg.all;
library unisim; use unisim.vcomponents.all;
library platform, sdp, axi, cdc;

entity zynq_sdp is
  generic (package_name : string  := "clg484";
           dq_width     : natural := 32;
           sdp_width    : natural := 2;
           sdp_count    : natural := 4;
           use_acp      : boolean := false;
           which_fclk   : natural := 0;
           which_gp     : natural := 0);
  port    (clk          : out std_logic;
           reset        : out std_logic;
           cp_in        : in platform.platform_pkg.occp_out_t;
           cp_out       : out platform.platform_pkg.occp_in_t;
           sdp_in       : in sdp.sdp.s2m_array_t(0 to sdp_count-1);
           sdp_in_data  : in sdp.sdp.data_array_t(0 to sdp_count-1, 0 to sdp_width-1);
           sdp_out      : out sdp.sdp.m2s_array_t(0 to sdp_count-1);
           sdp_out_data : out sdp.sdp.data_array_t(0 to sdp_count-1, 0 to sdp_width-1);
           axi_error    : out bool_array_t(0 to sdp_count-1);
           dbg_state    : out ulonglong_array_t(0 to sdp_count-1);
           dbg_state1   : out ulonglong_array_t(0 to sdp_count-1);
           dbg_state2   : out ulonglong_array_t(0 to sdp_count-1));
end entity zynq_sdp;

architecture rtl of zynq_sdp is
  type sdp_data_t is array(0 to sdp_count-1) of dword_array_t(0 to sdp_width-1);
  signal sdp_in_data_1d   : sdp_data_t;
  signal sdp_out_data_1d  : sdp_data_t;
  signal raw_rst_n        : std_logic; -- FCLKRESET_Ns need synchronization
  signal rst_n            : std_logic; -- the synchronized negative reset
  signal fclk             : std_logic_vector(3 downto 0);
  signal clk_out          : std_logic;
  signal reset_out        : std_logic;
  -- signals between the processor and the axi2sdp adapters
  signal ps_m_axi_gp_in   : axi.zynq_7000_m_gp.axi_s2m_array_t(0 to C_M_AXI_GP_COUNT-1); -- s2m
  signal ps_m_axi_gp_out  : axi.zynq_7000_m_gp.axi_m2s_array_t(0 to C_M_AXI_GP_COUNT-1); -- m2s
  signal ps_s_axi_hp_in   : axi.zynq_7000_s_hp.axi_m2s_array_t(0 to C_S_AXI_HP_COUNT-1); -- m2s
  signal ps_s_axi_hp_out  : axi.zynq_7000_s_hp.axi_s2m_array_t(0 to C_S_AXI_HP_COUNT-1); -- s2m
  signal ps_s_axi_acp_in  : axi.zynq_7000_s_hp.axi_m2s_t; -- s2m
  signal ps_s_axi_acp_out : axi.zynq_7000_s_hp.axi_s2m_t; -- m2s
begin
  -- convert 2d data paths into 1d (VHDL does not allow 1d slices of 2d)
  sd0 : for i in 0 to sdp_count-1 generate
    sd1: for j in 0 to sdp_width-1 generate
           sdp_in_data_1d(i)(j) <= sdp_in_data(i, j);
           sdp_out_data(i, j) <= sdp_out_data_1d(i)(j);
    end generate;
  end generate;
  -- Instantiate the processor system (i.e. the interface to it).
  ps : zynq_ps
    generic map (
	package_name 	   => package_name,
	dq_width 	   => dq_width
    )
    port map(
      -- Signals from the PS used in the PL
      ps_in.debug           => (31 => ocpi.util.slvn(which_gp,1)(0), others => '0'),
      ps_out.FCLK           => fclk,
      ps_out.FCLKRESET_N    => raw_rst_n,
      m_axi_gp_in           => ps_m_axi_gp_in,
      m_axi_gp_out          => ps_m_axi_gp_out,
      s_axi_hp_in           => ps_s_axi_hp_in,
      s_axi_hp_out          => ps_s_axi_hp_out,
      s_axi_acp_in          => ps_s_axi_acp_in,
      s_axi_acp_out         => ps_s_axi_acp_out);

  -- Use a global clock buffer for this clock used for both control and data
  clkbuf   : BUFG   port map(I => fclk(which_fclk),
                             O => clk_out);
  clk <= clk_out;
  -- The FCLKRESET signals from the PS are documented as asynchronous with the
  -- associated FCLK for whatever reason.  Here we make a synchronized reset from it.
  sr : cdc.cdc.reset
    generic map(SRC_RST_VALUE => '0',
		RST_DELAY => 17)
    port map   (src_rst   => raw_rst_n,
                dst_clk   => fclk(which_fclk),
                dst_rst   => reset_out,
	        dst_rst_n => open);

  -- Adapt the axi master from the PS to be a CP Master
  cp : axi.zynq_7000_m_gp.axi2cp_zynq_7000_m_gp
    port map(
      clk     => clk_out,
      reset   => reset_out,
      axi_in  => ps_m_axi_gp_out(which_gp),
      axi_out => ps_m_axi_gp_in(which_gp),
      cp_in   => cp_in,
      cp_out  => cp_out);

  -- Now configure the AXI connections to SDP (channels).
  -- We use one sdp2axi adapter foreach of the processor's S_AXI_HP channels
  g0 : if not use_acp generate
    g1 : for i in 0 to C_S_AXI_HP_COUNT-1 generate
      dp : axi.zynq_7000_s_hp.sdp2axi_zynq_7000_s_hp
        generic map(ocpi_debug => true,
                    sdp_width  => sdp_width)
        port map(   clk          => clk_out,
                    reset        => reset_out,
                    sdp_in       => sdp_in(i),
                    sdp_in_data  => sdp_in_data_1d(i),
                    sdp_out      => sdp_out(i),
                    sdp_out_data => sdp_out_data_1d(i),
                    axi_in       => ps_s_axi_hp_out(i),
                    axi_out      => ps_s_axi_hp_in(i),
                    axi_error    => axi_error(i),
                    dbg_state    => dbg_state(i),
                    dbg_state1   => dbg_state1(i),
                    dbg_state2   => dbg_state2(i));
    end generate;
    -- terminate the one we are not using
    n0 : axi.zynq_7000_s_hp.axinull_zynq_7000_s_hp
      port map(clk => clk_out,
               reset => reset_out,
               axi_in => ps_s_axi_acp_out,
               axi_out => ps_s_axi_acp_in);
  end generate;
  g2 : if use_acp generate
    dp : axi.zynq_7000_s_hp.sdp2axi_zynq_7000_s_hp
      generic map(ocpi_debug => true,
                  sdp_width  => sdp_width)
      port map(   clk          => clk_out,
                  reset        => reset_out,
                  sdp_in       => sdp_in(0),
                  sdp_in_data  => sdp_in_data_1d(0),
                  sdp_out      => sdp_out(0),
                  sdp_out_data => sdp_out_data_1d(0),
                  axi_in       => ps_s_axi_acp_out,
                  axi_out      => ps_s_axi_acp_in,
                  axi_error    => axi_error(0),
                  dbg_state    => dbg_state(0),
                  dbg_state1   => dbg_state1(0),
                  dbg_state2   => dbg_state2(0));
    n1 : for i in 0 to C_S_AXI_HP_COUNT-1 generate
      n2 : axi.zynq_7000_s_hp.axinull_zynq_7000_s_hp
        port map(clk => clk_out,
                 reset => reset_out,
                 axi_in => ps_s_axi_hp_out(i),
                 axi_out => ps_s_axi_hp_in(i));
    end generate;
  end generate;
end rtl;
