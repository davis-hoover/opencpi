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
library axi;
library cdc;
LIBRARY altera; use altera.altera_primitives_components.all;
architecture rtl of worker is
  signal hps_m_h2f_axi_in   : axi.cyclone5_m.axi_s2m_array_t(0 to C_M_AXI_COUNT-1); -- s2m
  signal hps_m_h2f_axi_out  : axi.cyclone5_m.axi_m2s_array_t(0 to C_M_AXI_COUNT-1); -- m2s
  signal hps_s_f2h_axi_in   : axi.cyclone5_s.axi_m2s_array_t(0 to C_S_AXI_COUNT-1); -- m2s
  signal hps_s_f2h_axi_out  : axi.cyclone5_s.axi_s2m_array_t(0 to C_S_AXI_COUNT-1); -- s2m
  signal clk              : std_logic;
  signal raw_rst_n        : std_logic; -- FCLKRESET_Ns need synchronization
  signal rst_n            : std_logic; -- the synchronized negative reset
  signal reset            : std_logic; -- our positive reset
  signal count            : unsigned(25 downto 0);
  signal my_sdp_out       : cyclone5_sockit_out_array_t;      -- so we can observe the SDP outputs for debug
  signal my_sdp_out_data  : cyclone5_sockit_out_data_array_t; -- ditto
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

  clkbuf   : global   port map(a_in=> fpga_clk_50,
                               a_out => clk);
  -- The FCLKRESET signals from the PS are documented as asynchronous with the
  -- associated FCLK for whatever reason.  Here we make a synchronized reset from it.
  sr : cdc.cdc.reset
    generic map(
            SRC_RST_VALUE => '0',
            RST_DELAY => 17)
    port map(src_rst => raw_rst_n,
            dst_clk => clk,
            dst_rst => reset);
  -- reset <= not rst_n;

  -- Instantiate the hard processor system (i.e. the interface to it).
  hps : cyclone5_hps
    port map(
      -- Signals from the PS used in the PL
      hps_in.CLK             => fpga_clk_50,
      hps_in.oct_rzqin       => oct_rzqin(0),
      hps_out.RESET_N        => raw_rst_n,
      hps_inout.hps_io_emac1_inst_MDIO   => hps_io_emac1_inst_MDIO(0),
      hps_inout.hps_io_qspi_inst_IO      => hps_io_qspi_inst_IO,
      -- hps_inout.hps_io_qspi_inst_IO1     => hps_io_qspi_inst_IO(0),
      -- hps_inout.hps_io_qspi_inst_IO2     => hps_io_qspi_inst_IO(0),
      -- hps_inout.hps_io_qspi_inst_IO3     => hps_io_qspi_inst_IO(0),
      hps_inout.hps_io_sdio_inst_CMD     => hps_io_sdio_inst_CMD(0),
      hps_inout.hps_io_sdio_inst_D       => hps_io_sdio_inst_D,
      -- hps_inout.hps_io_sdio_inst_D1      => hps_io_sdio_inst_D1(0),
      -- hps_inout.hps_io_sdio_inst_D2      => hps_io_sdio_inst_D2(0),
      -- hps_inout.hps_io_sdio_inst_D3      => hps_io_sdio_inst_D3(0),
      hps_inout.hps_io_usb1_inst_D       => hps_io_usb1_inst_D,
      -- hps_inout.hps_io_usb1_inst_D1      => hps_io_usb1_inst_D1(0),
      -- hps_inout.hps_io_usb1_inst_D2      => hps_io_usb1_inst_D2(0),
      -- hps_inout.hps_io_usb1_inst_D3      => hps_io_usb1_inst_D3(0),
      -- hps_inout.hps_io_usb1_inst_D4      => hps_io_usb1_inst_D4(0),
      -- hps_inout.hps_io_usb1_inst_D5      => hps_io_usb1_inst_D5(0),
      -- hps_inout.hps_io_usb1_inst_D6      => hps_io_usb1_inst_D6(0),
      -- hps_inout.hps_io_usb1_inst_D7      => hps_io_usb1_inst_D7(0),
      hps_out.ddr3_hps_a            => ddr3_hps_a,
      hps_out.ddr3_hps_ba           => ddr3_hps_ba,
      hps_out.ddr3_hps_dm           => ddr3_hps_dm,
      hps_out.ddr3_hps_casn         => ddr3_hps_casn(0),
      hps_out.ddr3_hps_cke          => ddr3_hps_cke(0),
      hps_out.ddr3_hps_clk_n        => ddr3_hps_clk_n(0),
      hps_out.ddr3_hps_clk_p        => ddr3_hps_clk_p(0),
      hps_out.ddr3_hps_csn          => ddr3_hps_csn(0),
      hps_out.ddr3_hps_odt          => ddr3_hps_odt(0),
      hps_out.ddr3_hps_rasn         => ddr3_hps_rasn(0),
      hps_out.ddr3_hps_resetn       => ddr3_hps_resetn(0),
      hps_out.ddr3_hps_wen          => ddr3_hps_wen(0),
      hps_inout.ddr3_hps_dq              => ddr3_hps_dq,
      hps_inout.ddr3_hps_dqs_n           => ddr3_hps_dqs_n,
      hps_inout.ddr3_hps_dqs_p           => ddr3_hps_dqs_p,
      hps_out.enet_hps_gtx_clk => enet_hps_gtx_clk(0),
      hps_out.enet_hps_txd     => enet_hps_txd,
      hps_in.enet_hps_rxd      => enet_hps_rxd,
      hps_out.enet_hps_mdc     => enet_hps_mdc(0),
      hps_in.enet_hps_rx_dv    => enet_hps_rx_dv(0),
      hps_out.enet_hps_tx_en   => enet_hps_tx_en(0),
      hps_in.enet_hps_rx_clk   => enet_hps_rx_clk(0),
      hps_in.usb_clk  => usb_clk(0),
      hps_in.usb_nxt  => usb_nxt(0),
      hps_in.usb_dir  => usb_dir(0),
      hps_out.usb_stp => usb_stp(0),
      hps_out.spi_sck    => spi_sck(0),
      hps_out.spi_mosi   => spi_mosi(0),
      hps_in.spi_miso   => spi_miso(0),
      hps_out.spi_csn    => spi_csn(0),
      hps_in.hps_io_uart0_inst_RX     => hps_io_uart0_inst_RX(0),
      hps_out.hps_io_uart0_inst_TX     => hps_io_uart0_inst_TX(0),
      hps_inout.hps_io_i2c0_inst_SCL  => hps_io_i2c0_inst_SCL(0),
      hps_inout.hps_io_i2c0_inst_SDA  => hps_io_i2c0_inst_SDA(0),
      hps_in.can_0_rx  => can_0_rx(0),
      hps_out.can_0_tx => can_0_tx(0),
      hps_inout.hps_io_gpio_inst_GPIO09  => hps_io_gpio_inst_GPIO09(0),
      hps_inout.hps_io_gpio_inst_GPIO35  => hps_io_gpio_inst_GPIO35(0),
      hps_inout.hps_io_gpio_inst_GPIO41  => hps_io_gpio_inst_GPIO41(0),
      hps_inout.hps_io_gpio_inst_GPIO42  => hps_io_gpio_inst_GPIO42(0),
      hps_inout.hps_io_gpio_inst_GPIO43  => hps_io_gpio_inst_GPIO43(0),
      hps_inout.hps_io_gpio_inst_GPIO44  => hps_io_gpio_inst_GPIO44(0),
      m_h2f_axi_in           => hps_m_h2f_axi_in,
      m_h2f_axi_out          => hps_m_h2f_axi_out,
      s_f2h_axi_in           => hps_s_f2h_axi_in,
      s_f2h_axi_out          => hps_s_f2h_axi_out);

  -- Adapt the axi master from the HPS to be a CP Master
  cp : axi.cyclone5_m.axi2cp_cyclone5_m
    port map(
      clk     => clk,
      reset   => reset,
      axi_in  => hps_m_h2f_axi_out(0),
      axi_out => hps_m_h2f_axi_in(0),
      cp_in   => cp_in,
      cp_out  => cp_out
      );
  cyclone5_sockit_out               <= my_sdp_out;
  cyclone5_sockit_out_data          <= my_sdp_out_data;
  props_out.sdpDropCount <= cyclone5_sockit_in(0).dropCount;
  -- We use one sdp2axi adapter foreach of the processor's S_AXI channels
  g : for i in 0 to C_S_AXI_COUNT-1 generate
    dp : axi.cyclone5_s.sdp2axi_cyclone5_s
      generic map(ocpi_debug => true,
                  sdp_width  => to_integer(sdp_width))
      port map(   clk          => clk,
                  reset        => reset,
                  sdp_in       => cyclone5_sockit_in(i),
                  sdp_in_data  => cyclone5_sockit_in_data(i),
                  sdp_out      => my_sdp_out(i),
                  sdp_out_data => my_sdp_out_data(i),
                  axi_in       => hps_s_f2h_axi_out(i),
                  axi_out      => hps_s_f2h_axi_in(i),
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
  -- props_out.slotCardIsPresent <= (0 => not fmc_prsnt,
  --                                 others => '0');
  -- TODO / FIXME remove this line once volatile sequence properties are fixed in codegen, which
  -- SHOULD result in this property being changed from an array to a sequence)
  --  props_out.slotCardIsPresent(1 to 63) <= (others => '0');
  -- Settable properties - drive the leds that are not driven by hardware from the property
  -- led(6 downto 1)           <= std_logic_vector(props_in.leds(6 downto 1));
  -- led(led'left downto 8)    <= (others => '0');
  -- led(0) <= count(count'left);
  -- led(1) <= ps_m_axi_gp_out(whichGP).AR.VALID;
  -- led(2) <= '0';
  -- led(3) <= cp_in.take;
  -- led(4) <= cp_in.valid;
  -- led(5) <= ps_m_axi_gp_in(whichGP).AR.READY;
  -- led(6) <= ps_m_axi_gp_in(whichGP).R.VALID;
  -- led(7) <= ps_m_axi_gp_out(whichGP).R.READY;
  -- Counter for blinking LED and debug
  -- work : process(clk)
  -- begin
  --   if rising_edge(clk) then
  --     if reset = '1' then
  --       count <= (others => '0');
  --     else
  --       count <= count + 1;
  --     end if;
  --   end if;
  -- end process;
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
