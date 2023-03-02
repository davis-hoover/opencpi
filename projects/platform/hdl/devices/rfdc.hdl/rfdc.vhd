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

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library rfdc;
library protocol;
architecture structural of worker is
  -- rx_0 clk domain
  signal rx_0_clk                            : std_logic := '0';
  signal rx_0_rst                            : std_logic := '0';
  signal rx_0_protocol                       : protocol.iqstream.protocol_t
                                             := protocol.iqstream.PROTOCOL_ZERO;
  signal rfdc_to_rx_0_marshaller_tdata       : std_logic_vector(32-1 downto 0)
                                             := (others => '0');
  signal rfdc_to_rx_0_marshaller_tvalid      : std_logic := '0';
  signal rfdc_to_rx_0_marshaller_tready      : std_logic := '0';
  -- rx_1 clk domain
  signal rx_1_clk                            : std_logic := '0';
  signal rx_1_rst                            : std_logic := '0';
  signal rx_1_protocol                       : protocol.iqstream.protocol_t
                                             := protocol.iqstream.PROTOCOL_ZERO;
  signal rfdc_to_rx_1_marshaller_tdata       : std_logic_vector(32-1 downto 0)
                                             := (others => '0');
  signal rfdc_to_rx_1_marshaller_tvalid      : std_logic := '0';
  signal rfdc_to_rx_1_marshaller_tready      : std_logic := '0';
  -- tx_0 clk domain
  signal tx_0_clk                            : std_logic := '0';
  signal tx_0_rst                            : std_logic := '0';
  signal tx_0_protocol                       : protocol.iqstream.protocol_t
                                             := protocol.iqstream.PROTOCOL_ZERO;
  signal tx_0_demarshaller_to_rfdc_ip_tdata  : std_logic_vector(32-1 downto 0)
                                             := (others => '0');
  signal tx_0_demarshaller_to_rfdc_ip_tvalid : std_logic := '0';
  signal tx_0_demarshaller_to_rfdc_ip_tready : std_logic := '0';
  -- tx_1 clk domain
  signal tx_1_clk                            : std_logic := '0';
  signal tx_1_rst                            : std_logic := '0';
  signal tx_1_protocol                       : protocol.iqstream.protocol_t
                                             := protocol.iqstream.PROTOCOL_ZERO;
  signal tx_1_demarshaller_to_rfdc_ip_tdata  : std_logic_vector(32-1 downto 0)
                                             := (others => '0');
  signal tx_1_demarshaller_to_rfdc_ip_tvalid : std_logic := '0';
  signal tx_1_demarshaller_to_rfdc_ip_tready : std_logic := '0';
begin

  tx_0_demarshaller : protocol.iqstream.iqstream_demarshaller
    generic map(
      WSI_DATA_WIDTH => in0_in.data'length)
    port map(
      clk       => rx_0_clk,
      rst       => rx_0_rst,
      idata     => in0_in.data,
      ivalid    => in0_in.valid,
      iready    => in0_in.ready,
      isom      => in0_in.som,
      ieom      => in0_in.eom,
      ieof      => in0_in.eof,
      itake     => in0_out.take,
      oprotocol => tx_0_protocol,
      oeof      => open,
      ordy      => tx_0_demarshaller_to_rfdc_ip_tready);

  in0_out.clk <= tx_0_clk;
  tx_0_demarshaller_to_rfdc_ip_tdata <=
      tx_0_protocol.iq.data.q &
      tx_0_protocol.iq.data.i;

  tx_1_demarshaller : protocol.iqstream.iqstream_demarshaller
    generic map(
      WSI_DATA_WIDTH => in1_in.data'length)
    port map(
      clk       => rx_1_clk,
      rst       => rx_1_rst,
      idata     => in1_in.data,
      ivalid    => in1_in.valid,
      iready    => in1_in.ready,
      isom      => in1_in.som,
      ieom      => in1_in.eom,
      ieof      => in1_in.eof,
      itake     => in1_out.take,
      oprotocol => tx_1_protocol,
      oeof      => open,
      ordy      => tx_1_demarshaller_to_rfdc_ip_tready);

  in1_out.clk <= tx_1_clk;
  tx_1_demarshaller_to_rfdc_ip_tdata <=
      tx_1_protocol.iq.data.q &
      tx_1_protocol.iq.data.i;

  rfdc_ip : rfdc.rfdc_pkg.rfdc
    generic map(
      NUM_RX_CHANS        => to_integer(unsigned(NUM_RX_CHANS)),
      NUM_TX_CHANS        => to_integer(unsigned(NUM_TX_CHANS)),
      AXI_STREAM_LOOPBACK => PORT_LOOPBACK = '1')
    port map(
      raw_clk         => ctl_in.clk,
      raw_reset       => ctl_in.reset,
      raw_in          => props_in.raw,
      raw_out         => props_out.raw,
      rx_clks_p       => rx_clks_p,
      rx_clks_n       => rx_clks_n,
      tx_clks_p       => tx_clks_p,
      tx_clks_n       => tx_clks_n,
      sysref_p        => sysref_p,
      sysref_n        => sysref_n,
      rf_rx_p         => rf_rx_p,
      rf_rx_n         => rf_rx_n,
      rf_tx_p         => rf_tx_p,
      rf_tx_n         => rf_tx_n,
      s_axis_0_aclk   => tx_0_clk,
      s_axis_0_tdata  => tx_0_demarshaller_to_rfdc_ip_tdata,
      s_axis_0_tvalid => tx_0_demarshaller_to_rfdc_ip_tvalid,
      s_axis_0_tready => tx_0_demarshaller_to_rfdc_ip_tready,
      s_axis_1_aclk   => tx_1_clk,
      s_axis_1_tdata  => tx_1_demarshaller_to_rfdc_ip_tdata,
      s_axis_1_tvalid => tx_1_demarshaller_to_rfdc_ip_tvalid,
      s_axis_1_tready => tx_1_demarshaller_to_rfdc_ip_tready,
      m_axis_0_aclk   => rx_0_clk,
      m_axis_0_tdata  => rfdc_to_rx_0_marshaller_tdata,
      m_axis_0_tvalid => rfdc_to_rx_0_marshaller_tvalid,
      m_axis_0_tready => rfdc_to_rx_0_marshaller_tready,
      m_axis_1_aclk   => rx_1_clk,
      m_axis_1_tdata  => rfdc_to_rx_1_marshaller_tdata,
      m_axis_1_tvalid => rfdc_to_rx_1_marshaller_tvalid,
      m_axis_1_tready => rfdc_to_rx_1_marshaller_tready);

  rx_0_protocol.iq.data.i <= rfdc_to_rx_0_marshaller_tdata(32-1 downto 16);
  rx_0_protocol.iq.data.q <= rfdc_to_rx_0_marshaller_tdata(16-1 downto 0);

  rx_0_marshaller : protocol.iqstream.iqstream_marshaller
    generic map(
      WSI_DATA_WIDTH    => out0_out.data'length,
      WSI_MBYTEEN_WIDTH => out0_out.byte_enable'length)
    port map(
      clk          => rx_0_clk,
      rst          => rx_0_rst,
      iprotocol    => rx_0_protocol,
      ieof         => bfalse,
      irdy         => rfdc_to_rx_0_marshaller_tready,
      odata        => out0_out.data,
      ovalid       => out0_out.valid,
      obyte_enable => out0_out.byte_enable,
      ogive        => out0_out.give,
      osom         => out0_out.som,
      oeom         => out0_out.eom,
      oeof         => out0_out.eof,
      oready       => out0_in.ready);

  rx_1_protocol.iq.data.i <= rfdc_to_rx_1_marshaller_tdata(32-1 downto 16);
  rx_1_protocol.iq.data.q <= rfdc_to_rx_1_marshaller_tdata(16-1 downto 0);

  rx_1_marshaller : protocol.iqstream.iqstream_marshaller
    generic map(
      WSI_DATA_WIDTH    => out1_out.data'length,
      WSI_MBYTEEN_WIDTH => out1_out.byte_enable'length)
    port map(
      clk          => tx_1_clk,
      rst          => tx_1_rst,
      iprotocol    => rx_1_protocol,
      ieof         => bfalse,
      irdy         => rfdc_to_rx_1_marshaller_tready,
      odata        => out1_out.data,
      ovalid       => out1_out.valid,
      obyte_enable => out1_out.byte_enable,
      ogive        => out1_out.give,
      osom         => out1_out.som,
      oeom         => out1_out.eom,
      oeof         => out1_out.eof,
      oready       => out1_in.ready);

end structural;
