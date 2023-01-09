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

-- This package contains component definitions for verilog-ethernet modules
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;

package verilog_ethernet is
  component eth_mac_1g_rgmii_fifo is
    generic (
      TARGET : string := "GENERIC";
      IODDR_STYLE : string := "IODDR2";
      CLOCK_INPUT_STYLE : string := "BUFIO2";
      USE_CLK90 : string := "TRUE";
      AXIS_DATA_WIDTH : natural := 8;
      AXIS_KEEP_ENABLE : boolean := false;
      AXIS_KEEP_WIDTH : natural := 1;
      ENABLE_PADDING : boolean := true;
      MIN_FRAME_LENGTH : natural := 64;
      TX_FIFO_DEPTH : natural := 4096;
      TX_FIFO_PIPELINE_OUTPUT : natural := 2;
      TX_FRAME_FIFO : boolean := true;
      TX_DROP_BAD_FRAME : boolean := true;
      TX_DROP_WHEN_FULL : boolean := false;
      RX_FIFO_DEPTH : natural := 4096;
      RX_FIFO_PIPELINE_OUTPUT : natural := 2;
      RX_FRAME_FIFO : boolean := true;
      RX_DROP_BAD_FRAME : boolean := true;
      RX_DROP_WHEN_FULL : boolean := true
    );
    port (
      gtx_clk : in std_logic;
      gtx_clk90 : in std_logic;
      gtx_rst : in std_logic;
      logic_clk : in std_logic;
      logic_rst : in std_logic;

      tx_axis_tdata : in std_logic_vector(AXIS_DATA_WIDTH - 1 downto 0);
      tx_axis_tkeep : in std_logic_vector(AXIS_KEEP_WIDTH - 1 downto 0);
      tx_axis_tvalid : in std_logic;
      tx_axis_tready : out std_logic;
      tx_axis_tlast : in std_logic;
      tx_axis_tuser : in std_logic;

      rx_axis_tdata : out std_logic_vector(AXIS_DATA_WIDTH - 1 downto 0);
      rx_axis_tkeep : out std_logic_vector(AXIS_KEEP_WIDTH - 1 downto 0);
      rx_axis_tvalid : out std_logic;
      rx_axis_tready : in std_logic;
      rx_axis_tlast : out std_logic;
      rx_axis_tuser : out std_logic;

      rgmii_rx_clk : in std_logic;
      rgmii_rxd : in std_logic_vector(3 downto 0);
      rgmii_rx_ctl : in std_logic;
      rgmii_tx_clk : out std_logic;
      rgmii_txd : out std_logic_vector(3 downto 0);
      rgmii_tx_ctl : out std_logic;

      tx_error_underflow : out std_logic;
      tx_fifo_overflow : out std_logic;
      tx_fifo_bad_frame : out std_logic;
      tx_fifo_good_frame : out std_logic;
      rx_error_bad_frame : out std_logic;
      rx_error_bad_fcs : out std_logic;
      rx_fifo_overflow : out std_logic;
      rx_fifo_bad_frame : out std_logic;
      rx_fifo_good_frame : out std_logic;
      speed : out std_logic_vector(1 downto 0);

      ifg_delay : in unsigned(7 downto 0)
    );
  end component eth_mac_1g_rgmii_fifo;

  component eth_axis_rx is
    generic(
      DATA_WIDTH : natural := 8;
      KEEP_ENABLE : boolean := false;
      KEEP_WIDTH : natural := 1
    );
    port (
      clk : in std_logic;
      rst : in std_logic;

      s_axis_tdata : in std_logic_vector(DATA_WIDTH - 1 downto 0);
      s_axis_tkeep : in std_logic_vector(KEEP_WIDTH - 1 downto 0);
      s_axis_tvalid : in std_logic;
      s_axis_tready : out std_logic;
      s_axis_tlast : in std_logic;
      s_axis_tuser : in std_logic;

      m_eth_dest_mac : out std_logic_vector(47 downto 0);
      m_eth_src_mac : out std_logic_vector(47 downto 0);
      m_eth_type : out std_logic_vector(15 downto 0);
      m_eth_hdr_valid : out std_logic;
      m_eth_hdr_ready : in std_logic;

      m_eth_payload_axis_tdata : out std_logic_vector(DATA_WIDTH - 1 downto 0);
      m_eth_payload_axis_tkeep : out std_logic_vector(KEEP_WIDTH - 1 downto 0);
      m_eth_payload_axis_tvalid : out std_logic;
      m_eth_payload_axis_tready : in std_logic;
      m_eth_payload_axis_tlast : out std_logic;
      m_eth_payload_axis_tuser : out std_logic;

      busy : out std_logic;
      error_header_early_termination: out std_logic
    );
  end component eth_axis_rx;

  component eth_axis_tx is
    generic(
      DATA_WIDTH : natural := 8;
      KEEP_ENABLE : boolean := false;
      KEEP_WIDTH : natural := 1
    );
    port (
      clk : in std_logic;
      rst : in std_logic;

      s_eth_dest_mac : in std_logic_vector(47 downto 0);
      s_eth_src_mac : in std_logic_vector(47 downto 0);
      s_eth_type : in std_logic_vector(15 downto 0);
      s_eth_hdr_valid : in std_logic;
      s_eth_hdr_ready : out std_logic;

      s_eth_payload_axis_tdata : in std_logic_vector(DATA_WIDTH - 1 downto 0);
      s_eth_payload_axis_tkeep : in std_logic_vector(KEEP_WIDTH - 1 downto 0);
      s_eth_payload_axis_tvalid : in std_logic;
      s_eth_payload_axis_tready : out std_logic;
      s_eth_payload_axis_tlast : in std_logic;
      s_eth_payload_axis_tuser : in std_logic;

      m_axis_tdata : out std_logic_vector(DATA_WIDTH - 1 downto 0);
      m_axis_tkeep : out std_logic_vector(KEEP_WIDTH - 1 downto 0);
      m_axis_tvalid : out std_logic;
      m_axis_tready : in std_logic;
      m_axis_tlast : out std_logic;
      m_axis_tuser : out std_logic;

      busy : out std_logic
    );
  end component eth_axis_tx;

  component eth_mac_10g_fifo is
    generic (
      DATA_WIDTH              : natural := 64;
      CTRL_WIDTH              : natural := 8;
      AXIS_DATA_WIDTH         : natural := 64;
      AXIS_KEEP_ENABLE        : boolean := true;
      AXIS_KEEP_WIDTH         : natural := 8;
      ENABLE_PADDING          : boolean := true;
      ENABLE_DIC              : boolean := true;
      MIN_FRAME_LENGTH        : natural := 64;
      TX_FIFO_DEPTH           : natural := 4096;
      TX_FIFO_PIPELINE_OUTPUT : natural := 2;
      TX_FRAME_FIFO           : boolean := true;
      TX_DROP_BAD_FRAME       : boolean := true;
      TX_DROP_WHEN_FULL       : boolean := false;
      RX_FIFO_DEPTH           : natural := 4096;
      RX_FIFO_PIPELINE_OUTPUT : natural := 2;
      RX_FRAME_FIFO           : boolean := true;
      RX_DROP_BAD_FRAME       : boolean := true;
      RX_DROP_WHEN_FULL       : boolean := true;
      LOGIC_PTP_PERIOD_NS     : natural := 6;
      LOGIC_PTP_PERIOD_FNS    : natural := 26216;
      PTP_PERIOD_NS           : natural := 6;
      PTP_PERIOD_FNS          : natural := 26216;
      PTP_USE_SAMPLE_CLOCK    : boolean := false;
      TX_PTP_TS_ENABLE        : boolean := false;
      RX_PTP_TS_ENABLE        : boolean := false;
      TX_PTP_TS_FIFO_DEPTH    : natural := 64;
      RX_PTP_TS_FIFO_DEPTH    : natural := 64;
      PTP_TS_WIDTH            : natural := 96;
      TX_PTP_TAG_ENABLE       : boolean := false;
      PTP_TAG_WIDTH           : natural := 16
    );
    port (
      rx_clk                 : in  std_logic;
      rx_rst                 : in  std_logic;
      tx_clk                 : in  std_logic;
      tx_rst                 : in  std_logic;
      logic_clk              : in  std_logic;
      logic_rst              : in  std_logic;
      ptp_sample_clk         : in  std_logic;

      -- AXI input
      tx_axis_tdata          : in  std_logic_vector(AXIS_DATA_WIDTH - 1 downto 0);
      tx_axis_tkeep          : in  std_logic_vector(AXIS_KEEP_WIDTH - 1 downto 0);
      tx_axis_tvalid         : in  std_logic;
      tx_axis_tready         : out std_logic;
      tx_axis_tlast          : in  std_logic;
      tx_axis_tuser          : in  std_logic;

      -- Transmit timestamp tag input
      s_axis_tx_ptp_ts_tag   : in  std_logic_vector(PTP_TAG_WIDTH - 1 downto 0);
      s_axis_tx_ptp_ts_valid : in  std_logic;
      s_axis_tx_ptp_ts_ready : out std_logic;

      -- Transmit timestamp output
      m_axis_tx_ptp_ts_96    : out std_logic_vector(PTP_TS_WIDTH - 1 downto 0);
      m_axis_tx_ptp_ts_tag   : out std_logic_vector(PTP_TAG_WIDTH - 1 downto 0);
      m_axis_tx_ptp_ts_valid : out std_logic;
      m_axis_tx_ptp_ts_ready : in  std_logic;

      -- AXI output
      rx_axis_tdata          : out std_logic_vector(AXIS_DATA_WIDTH - 1 downto 0);
      rx_axis_tkeep          : out std_logic_vector(AXIS_KEEP_WIDTH - 1 downto 0);
      rx_axis_tvalid         : out std_logic;
      rx_axis_tready         : in  std_logic;
      rx_axis_tlast          : out std_logic;
      rx_axis_tuser          : out std_logic;

      -- Receive timestamp output
      m_axis_rx_ptp_ts_96    : out std_logic_vector(PTP_TS_WIDTH - 1 downto 0);
      m_axis_rx_ptp_ts_valid : out std_logic;
      m_axis_rx_ptp_ts_ready : in  std_logic;

      -- XGMII interface
      xgmii_rxd              : in  std_logic_vector(DATA_WIDTH - 1 downto 0);
      xgmii_rxc              : in  std_logic_vector(CTRL_WIDTH - 1 downto 0);
      xgmii_txd              : out std_logic_vector(DATA_WIDTH - 1 downto 0);
      xgmii_txc              : out std_logic_vector(CTRL_WIDTH - 1 downto 0);

      -- Status
      tx_error_underflow     : out std_logic;
      tx_fifo_overflow       : out std_logic;
      tx_fifo_bad_frame      : out std_logic;
      tx_fifo_good_frame     : out std_logic;
      rx_error_bad_frame     : out std_logic;
      rx_error_bad_fcs       : out std_logic;
      rx_fifo_overflow       : out std_logic;
      rx_fifo_bad_frame      : out std_logic;
      rx_fifo_good_frame     : out std_logic;

      -- PTP clock
      ptp_ts_96              : in  std_logic_vector(PTP_TS_WIDTH - 1 downto 0);

      -- Configuration
      ifg_delay              : in  unsigned(7 downto 0)
    );
  end component eth_mac_10g_fifo;

end package verilog_ethernet;
