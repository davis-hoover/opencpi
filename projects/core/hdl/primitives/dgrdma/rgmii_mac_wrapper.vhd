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

library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library dgrdma;

entity rgmii_mac_wrapper is
  generic (
    DATA_WIDTH: natural := 64;
    KEEP_WIDTH: natural := 8;
    MAX_FRAME_SIZE : natural := 10240
  );
  port (
    clk : in std_logic;
    clk_125mhz : in std_logic;
    clk_125mhz_90 : in std_logic;
    reset : in std_logic;
    reset_125mhz : in std_logic;

    -- PHY interface
    phy_rx_clk : in std_logic;
    phy_rxd : in std_logic_vector(3 downto 0);
    phy_rx_ctl : in std_logic;
    phy_tx_clk : out std_logic;
    phy_txd : out std_logic_vector(3 downto 0);
    phy_tx_ctl : out std_logic;
    phy_reset_n : out std_logic;
    phy_int_n : in std_logic;

    -- Ethernet frame interface
    rx_eth_tdata : out std_logic_vector(DATA_WIDTH - 1 downto 0);
    rx_eth_tkeep : out std_logic_vector(KEEP_WIDTH - 1 downto 0);
    rx_eth_tvalid : out std_logic;
    rx_eth_tready : in std_logic;
    rx_eth_tlast : out std_logic;
    rx_eth_tuser : out std_logic;

    tx_eth_tdata : in std_logic_vector(DATA_WIDTH - 1 downto 0);
    tx_eth_tkeep : in std_logic_vector(KEEP_WIDTH - 1 downto 0);
    tx_eth_tvalid : in std_logic;
    tx_eth_tready : buffer std_logic;
    tx_eth_tlast : in std_logic;
    tx_eth_tuser : in std_logic;

    -- Configuration & status
    ifg_delay : in unsigned(7 downto 0);  -- inter-frame gap, in bytes (minimum: 12)
    eth_speed : out std_logic_vector(1 downto 0)
  );
end entity rgmii_mac_wrapper;

architecture rtl of rgmii_mac_wrapper is
begin
  phy_reset_n <= not reset;

  -- Ethernet MAC with RGMII interface and FIFO
  -- This contains a width conversion from the 8-bit native width to DATA_WIDTH
  -- (usually 64 bits). The FIFO is clock-domain-crossing, so logic_clk can be
  -- different from the 125MHz MAC byte clock
  mac_inst : dgrdma.verilog_ethernet.eth_mac_1g_rgmii_fifo
    generic map (
      TARGET => "XILINX",
      IODDR_STYLE => "IODDR", -- IODDR for 7 series, Ultrascale
      CLOCK_INPUT_STYLE => "BUFR", -- BUFR for Virtex-5, Virtex-6, 7-series
      AXIS_DATA_WIDTH => DATA_WIDTH,
      AXIS_KEEP_ENABLE => (DATA_WIDTH > 8),
      AXIS_KEEP_WIDTH => KEEP_WIDTH,
      TX_FIFO_DEPTH => MAX_FRAME_SIZE,
      RX_FIFO_DEPTH => MAX_FRAME_SIZE
    )
    port map (
      gtx_clk => clk_125mhz,
      gtx_clk90 => clk_125mhz_90,
      gtx_rst => reset_125mhz,

      logic_clk => clk,
      logic_rst => reset,

      tx_axis_tdata => tx_eth_tdata,
      tx_axis_tkeep => tx_eth_tkeep,
      tx_axis_tvalid => tx_eth_tvalid,
      tx_axis_tready => tx_eth_tready,
      tx_axis_tlast => tx_eth_tlast,
      tx_axis_tuser => tx_eth_tuser,

      rx_axis_tdata => rx_eth_tdata,
      rx_axis_tkeep => rx_eth_tkeep,
      rx_axis_tvalid => rx_eth_tvalid,
      rx_axis_tready => rx_eth_tready,
      rx_axis_tlast => rx_eth_tlast,
      rx_axis_tuser => rx_eth_tuser,

      rgmii_rx_clk => phy_rx_clk,
      rgmii_rxd => phy_rxd,
      rgmii_rx_ctl => phy_rx_ctl,
      rgmii_tx_clk => phy_tx_clk,
      rgmii_txd => phy_txd,
      rgmii_tx_ctl => phy_tx_ctl,

      -- TODO: Error / status outputs
      tx_error_underflow => open,
      tx_fifo_overflow => open,
      tx_fifo_bad_frame => open,
      tx_fifo_good_frame => open,
      rx_error_bad_frame => open,
      rx_error_bad_fcs => open,
      rx_fifo_overflow => open,
      rx_fifo_bad_frame => open,
      rx_fifo_good_frame => open,
      speed => eth_speed,

      ifg_delay => ifg_delay
    );
end rtl;
