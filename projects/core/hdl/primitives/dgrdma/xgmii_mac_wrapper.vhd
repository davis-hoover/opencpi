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

entity xgmii_mac_wrapper is
  generic (
    DATA_WIDTH: natural := 64;
    KEEP_WIDTH: natural := 8;
    MAX_FRAME_SIZE : natural := 10240
  );
  port (
    -- Logic clock
    clk           : in  std_logic;
    reset         : in  std_logic;

    -- XGMII
    xgmii_rx_clk   : in  std_logic;
    xgmii_rx_reset : in  std_logic;
    xgmii_rxd      : in  std_logic_vector(63 downto 0);
    xgmii_rxc      : in  std_logic_vector(7 downto 0);
    xgmii_tx_clk   : in  std_logic;
    xgmii_tx_reset : in  std_logic;
    xgmii_txd      : out std_logic_vector(63 downto 0);
    xgmii_txc      : out std_logic_vector(7 downto 0);

    -- Receive Ethernet frame stream
    rx_eth_tdata  : out std_logic_vector(DATA_WIDTH - 1 downto 0);
    rx_eth_tkeep  : out std_logic_vector(KEEP_WIDTH - 1 downto 0);
    rx_eth_tvalid : out std_logic;
    rx_eth_tready : in  std_logic;
    rx_eth_tlast  : out std_logic;
    rx_eth_tuser  : out std_logic;

    -- Transmit Ethernet frame stream
    tx_eth_tdata  : in  std_logic_vector(DATA_WIDTH - 1 downto 0);
    tx_eth_tkeep  : in  std_logic_vector(KEEP_WIDTH - 1 downto 0);
    tx_eth_tvalid : in  std_logic;
    tx_eth_tready : out std_logic;
    tx_eth_tlast  : in  std_logic;
    tx_eth_tuser  : in  std_logic;

    -- Configuration & status
    ifg_delay     : in unsigned(7 downto 0)  -- inter-frame gap, in bytes (minimum: 12)
  );
end entity xgmii_mac_wrapper;

architecture rtl of xgmii_mac_wrapper is
begin

  -- Ethernet MAC with XGMII interface and FIFO
  --
  -- The FIFO is clock-domain-crossing, so logic_clk can be different from the
  -- 156.25 MHz transmit and receive clocks.
  --
  -- We leave the internal data width at the default value of 64 -- the other
  -- option being 32 -- and use the FIFOs to do a width conversion to the
  -- requested DATA_WIDTH.
  mac_inst : dgrdma.verilog_ethernet.eth_mac_10g_fifo
    generic map (
      AXIS_DATA_WIDTH        => DATA_WIDTH,
      AXIS_KEEP_ENABLE       => (DATA_WIDTH > 8),
      AXIS_KEEP_WIDTH        => KEEP_WIDTH,
      TX_FIFO_DEPTH          => MAX_FRAME_SIZE,
      RX_FIFO_DEPTH          => MAX_FRAME_SIZE
    )
    port map (
      rx_clk                 => xgmii_rx_clk,
      rx_rst                 => xgmii_rx_reset,
      tx_clk                 => xgmii_tx_clk,
      tx_rst                 => xgmii_tx_reset,
      logic_clk              => clk,
      logic_rst              => reset,
      ptp_sample_clk         => '0',

      -- AXI input
      tx_axis_tdata          => tx_eth_tdata,
      tx_axis_tkeep          => tx_eth_tkeep,
      tx_axis_tvalid         => tx_eth_tvalid,
      tx_axis_tready         => tx_eth_tready,
      tx_axis_tlast          => tx_eth_tlast,
      tx_axis_tuser          => tx_eth_tuser,

      -- Transmit timestamp tag input (unused as PTP is disabled)
      s_axis_tx_ptp_ts_tag   => (others => '0'),
      s_axis_tx_ptp_ts_valid => '0',
      s_axis_tx_ptp_ts_ready => open,

      -- Transmit timestamp output (unused as PTP is disabled)
      m_axis_tx_ptp_ts_96    => open,
      m_axis_tx_ptp_ts_tag   => open,
      m_axis_tx_ptp_ts_valid => open,
      m_axis_tx_ptp_ts_ready => '0',

      -- AXI output
      rx_axis_tdata          => rx_eth_tdata,
      rx_axis_tkeep          => rx_eth_tkeep,
      rx_axis_tvalid         => rx_eth_tvalid,
      rx_axis_tready         => rx_eth_tready,
      rx_axis_tlast          => rx_eth_tlast,
      rx_axis_tuser          => rx_eth_tuser,

      -- Receive timestamp output (unused as PTP is disabled)
      m_axis_rx_ptp_ts_96    => open,
      m_axis_rx_ptp_ts_valid => open,
      m_axis_rx_ptp_ts_ready => '0',

      -- XGMII interface
      xgmii_rxd              => xgmii_rxd,
      xgmii_rxc              => xgmii_rxc,
      xgmii_txd              => xgmii_txd,
      xgmii_txc              => xgmii_txc,

      -- Status
      tx_fifo_overflow       => open,
      tx_fifo_bad_frame      => open,
      tx_fifo_good_frame     => open,
      rx_error_bad_frame     => open,
      rx_error_bad_fcs       => open,
      rx_fifo_overflow       => open,
      rx_fifo_bad_frame      => open,
      rx_fifo_good_frame     => open,

      -- PTP clock (unused as PTP is disabled)
      ptp_ts_96              => (others => '0'),

      -- Configuration
      ifg_delay              => ifg_delay
    );

end rtl;
