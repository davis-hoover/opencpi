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
library protocol; use protocol.iqstream.all;
architecture structural of worker is
  -- ctl clk domain
  signal ctl_0_demarshaller_to_ctl_tx_0_converter_pro : protocol_t
                                                      := PROTOCOL_ZERO;
  signal ctl_0_demarshaller_to_ctl_tx_0_converter_rdy : std_logic := '0';
  signal ctl_tx_0_converter_to_tx_0_cdc_tdata  : std_logic_vector(32-1 downto 0)
                                               := (others => '0');
  signal ctl_tx_0_converter_to_tx_0_cdc_tvalid        : std_logic := '0';
  signal ctl_tx_0_converter_to_tx_0_cdc_tready        : std_logic := '0';
  signal ctl_1_demarshaller_to_ctl_tx_1_converter_pro : protocol_t
                                                      := PROTOCOL_ZERO;
  signal ctl_1_demarshaller_to_ctl_tx_1_converter_rdy : std_logic := '0';
  signal ctl_tx_1_converter_to_tx_1_cdc_tdata  : std_logic_vector(32-1 downto 0)
                                               := (others => '0');
  signal ctl_tx_1_converter_to_tx_1_cdc_tvalid        : std_logic := '0';
  signal ctl_tx_1_converter_to_tx_1_cdc_tready        : std_logic := '0';
  signal ctl_0_cdc_to_ctl_rx_0_converter_tdata : std_logic_vector(32-1 downto 0)
                                               := (others => '0');
  signal ctl_0_cdc_to_ctl_rx_0_converter_tvalid       : std_logic := '0';
  signal ctl_0_cdc_to_ctl_rx_0_converter_tready       : std_logic := '0';
  signal ctl_rx_0_converter_to_ctl_0_marshaller_pro   : protocol_t
                                                      := PROTOCOL_ZERO;
  signal ctl_rx_0_converter_to_ctl_0_marshaller_rdy   : std_logic := '0';
  signal ctl_1_cdc_to_ctl_rx_1_converter_tdata : std_logic_vector(32-1 downto 0)
                                               := (others => '0');
  signal ctl_1_cdc_to_ctl_rx_1_converter_tvalid       : std_logic := '0';
  signal ctl_1_cdc_to_ctl_rx_1_converter_tready       : std_logic := '0';
  signal ctl_rx_1_converter_to_ctl_1_marshaller_pro   : protocol_t
                                                      := PROTOCOL_ZERO;
  signal ctl_rx_1_converter_to_ctl_1_marshaller_rdy   : std_logic := '0';
  -- rx_0 clk domain
  signal rx_0_clk                 : std_logic := '0';
  signal rx_0_reset               : std_logic := '0';
  signal rfdc_to_ctl_0_cdc_tdata  : std_logic_vector(32-1 downto 0)
                                  := (others => '0');
  signal rfdc_to_ctl_0_cdc_tvalid : std_logic := '0';
  signal rfdc_to_ctl_0_cdc_tready : std_logic := '0';
  -- rx_1 clk domain
  signal rx_1_clk                 : std_logic := '0';
  signal rx_1_reset               : std_logic := '0';
  signal rfdc_to_ctl_1_cdc_tdata  : std_logic_vector(32-1 downto 0)
                                  := (others => '0');
  signal rfdc_to_ctl_1_cdc_tvalid : std_logic := '0';
  signal rfdc_to_ctl_1_cdc_tready : std_logic := '0';
  -- tx_0 clk domain
  signal tx_0_clk                     : std_logic := '0';
  signal tx_0_reset                   : std_logic := '0';
  signal tx_0_cdc_to_rfdc_prim_tdata  : std_logic_vector(32-1 downto 0)
                                      := (others => '0');
  signal tx_0_cdc_to_rfdc_prim_tvalid : std_logic := '0';
  signal tx_0_cdc_to_rfdc_prim_tready : std_logic := '0';
  -- tx_1 clk domain
  signal tx_1_clk                     : std_logic := '0';
  signal tx_1_reset                   : std_logic := '0';
  signal tx_1_cdc_to_rfdc_prim_tdata  : std_logic_vector(32-1 downto 0)
                                      := (others => '0');
  signal tx_1_cdc_to_rfdc_prim_tvalid : std_logic := '0';
  signal tx_1_cdc_to_rfdc_prim_tready : std_logic := '0';
begin

  ctl_0_demarshaller : iqstream_demarshaller
    generic map(
      WSI_DATA_WIDTH => in0_in.data'length)
    port map(
      clk       => ctl_in.clk,
      rst       => ctl_in.reset,
      idata     => in0_in.data,
      ivalid    => in0_in.valid,
      iready    => in0_in.ready,
      isom      => in0_in.som,
      ieom      => in0_in.eom,
      ieof      => in0_in.eof,
      itake     => in0_out.take,
      oprotocol => ctl_0_demarshaller_to_ctl_tx_0_converter_pro,
      oeof      => open,
      ordy      => ctl_0_demarshaller_to_ctl_tx_0_converter_rdy);

  ctl_tx_0_converter : iqstream_to_axis_converter
    port map(
      iprotocol     => ctl_0_demarshaller_to_ctl_tx_0_converter_pro,
      irdy          => ctl_0_demarshaller_to_ctl_tx_0_converter_rdy,
      m_axis_tdata  => ctl_tx_0_converter_to_tx_0_cdc_tdata,
      m_axis_tvalid => ctl_tx_0_converter_to_tx_0_cdc_tvalid,
      m_axis_tready => ctl_tx_0_converter_to_tx_0_cdc_tready);

  tx_0_cdc : cdc.cdc.fifo
    generic map(
      WIDTH       => out0_out.data'length)
    port map(
      src_CLK     => ctl_in.clk,
      src_RST     => ctl_in.reset,
      src_ENQ     => ctl_tx_0_converter_to_tx_0_cdc_tvalid,
      src_in      => ctl_tx_0_converter_to_tx_0_cdc_tdata,
      src_FULL_N  => ctl_tx_0_converter_to_tx_0_cdc_tready,
      dst_CLK     => tx_0_clk,
      dst_DEQ     => tx_0_cdc_to_rfdc_prim_tready,
      dst_out     => tx_0_cdc_to_rfdc_prim_tdata,
      dst_EMPTY_N => tx_0_cdc_to_rfdc_prim_tvalid);

  ctl_1_demarshaller : iqstream_demarshaller
    generic map(
      WSI_DATA_WIDTH => in1_in.data'length)
    port map(
      clk       => ctl_in.clk,
      rst       => ctl_in.reset,
      idata     => in1_in.data,
      ivalid    => in1_in.valid,
      iready    => in1_in.ready,
      isom      => in1_in.som,
      ieom      => in1_in.eom,
      ieof      => in1_in.eof,
      itake     => in1_out.take,
      oprotocol => ctl_1_demarshaller_to_ctl_tx_1_converter_pro,
      oeof      => open,
      ordy      => ctl_1_demarshaller_to_ctl_tx_1_converter_rdy);

  ctl_tx_1_converter : iqstream_to_axis_converter
    port map(
      iprotocol     => ctl_1_demarshaller_to_ctl_tx_1_converter_pro,
      irdy          => ctl_1_demarshaller_to_ctl_tx_1_converter_rdy,
      m_axis_tdata  => ctl_tx_1_converter_to_tx_1_cdc_tdata,
      m_axis_tvalid => ctl_tx_1_converter_to_tx_1_cdc_tvalid,
      m_axis_tready => ctl_tx_1_converter_to_tx_1_cdc_tready);

  tx_1_cdc : cdc.cdc.fifo
    generic map(
      WIDTH       => out1_out.data'length)
    port map(
      src_CLK     => ctl_in.clk,
      src_RST     => ctl_in.reset,
      src_ENQ     => ctl_tx_1_converter_to_tx_1_cdc_tvalid,
      src_in      => ctl_tx_1_converter_to_tx_1_cdc_tdata,
      src_FULL_N  => ctl_tx_1_converter_to_tx_1_cdc_tready,
      dst_CLK     => tx_1_clk,
      dst_DEQ     => tx_1_cdc_to_rfdc_prim_tready,
      dst_out     => tx_1_cdc_to_rfdc_prim_tdata,
      dst_EMPTY_N => tx_1_cdc_to_rfdc_prim_tvalid);

  rfdc_prim : rfdc.rfdc_pkg.rfdc
    generic map(
      NUM_RX_CHANS        => to_integer(unsigned(NUM_RX_CHANS)),
      NUM_TX_CHANS        => to_integer(unsigned(NUM_TX_CHANS)),
      AXI_STREAM_LOOPBACK => PORT_LOOPBACK = '1')
    port map(
      raw_props_clk   => ctl_in.clk,
      raw_props_reset => ctl_in.reset,
      raw_props_in    => props_in.raw,
      raw_props_out   => props_out.raw,
      -- TODO comment back in worker signal connections
      rx_clks_p       => (others => '0'),--rx_clks_p,
      rx_clks_n       => (others => '0'),--rx_clks_n,
      tx_clks_p       => (others => '0'),--tx_clks_p,
      tx_clks_n       => (others => '0'),--tx_clks_n,
      sysref_p        => '0',--sysref_p,
      sysref_n        => '0',--sysref_n,
      rf_rx_p         => (others => '0'),--rf_rx_p,
      rf_rx_n         => (others => '0'),--rf_rx_n,
      rf_tx_p         => open,--rf_tx_p,
      rf_tx_n         => open,--rf_tx_n,
      s_axis_0_aclk   => tx_0_clk,
      s_axis_0_tdata  => tx_0_cdc_to_rfdc_prim_tdata,
      s_axis_0_tvalid => tx_0_cdc_to_rfdc_prim_tvalid,
      s_axis_0_tready => tx_0_cdc_to_rfdc_prim_tready,
      s_axis_1_aclk   => tx_1_clk,
      s_axis_1_tdata  => tx_1_cdc_to_rfdc_prim_tdata,
      s_axis_1_tvalid => tx_1_cdc_to_rfdc_prim_tvalid,
      s_axis_1_tready => tx_1_cdc_to_rfdc_prim_tready,
      m_axis_0_aclk   => rx_0_clk,
      m_axis_0_tdata  => rfdc_to_ctl_0_cdc_tdata,
      m_axis_0_tvalid => rfdc_to_ctl_0_cdc_tvalid,
      m_axis_0_tready => rfdc_to_ctl_0_cdc_tready,
      m_axis_1_aclk   => rx_1_clk,
      m_axis_1_tdata  => rfdc_to_ctl_1_cdc_tdata,
      m_axis_1_tvalid => rfdc_to_ctl_1_cdc_tvalid,
      m_axis_1_tready => rfdc_to_ctl_1_cdc_tready);

  ctl_0_cdc : cdc.cdc.fifo
    generic map(
      WIDTH       => out0_out.data'length)
    port map(
      src_CLK     => rx_0_clk,
      src_RST     => rx_0_reset,
      src_ENQ     => rfdc_to_ctl_0_cdc_tvalid,
      src_in      => rfdc_to_ctl_0_cdc_tdata,
      src_FULL_N  => rfdc_to_ctl_0_cdc_tready,
      dst_CLK     => ctl_in.clk,
      dst_DEQ     => ctl_0_cdc_to_ctl_rx_0_converter_tready,
      dst_out     => ctl_0_cdc_to_ctl_rx_0_converter_tdata,
      dst_EMPTY_N => ctl_0_cdc_to_ctl_rx_0_converter_tvalid);

  ctl_rx_0_converter : axis_to_iqstream_converter
    port map(
      s_axis_tdata  => ctl_0_cdc_to_ctl_rx_0_converter_tdata,
      s_axis_tvalid => ctl_0_cdc_to_ctl_rx_0_converter_tvalid,
      s_axis_tready => ctl_0_cdc_to_ctl_rx_0_converter_tready,
      oprotocol     => ctl_rx_0_converter_to_ctl_0_marshaller_pro,
      ordy          => ctl_rx_0_converter_to_ctl_0_marshaller_rdy);

  ctl_0_marshaller : iqstream_marshaller
    generic map(
      WSI_DATA_WIDTH    => out0_out.data'length,
      WSI_MBYTEEN_WIDTH => out0_out.byte_enable'length)
    port map(
      clk          => rx_0_clk,
      rst          => rx_0_reset,
      iprotocol    => ctl_rx_0_converter_to_ctl_0_marshaller_pro,
      ieof         => bfalse,
      irdy         => ctl_rx_0_converter_to_ctl_0_marshaller_rdy,
      odata        => out0_out.data,
      ovalid       => out0_out.valid,
      obyte_enable => out0_out.byte_enable,
      ogive        => out0_out.give,
      osom         => out0_out.som,
      oeom         => out0_out.eom,
      oeof         => out0_out.eof,
      oready       => out0_in.ready);

  ctl_1_cdc : cdc.cdc.fifo
    generic map(
      WIDTH       => out1_out.data'length)
    port map(
      src_CLK     => rx_1_clk,
      src_RST     => rx_1_reset,
      src_ENQ     => rfdc_to_ctl_1_cdc_tvalid,
      src_in      => rfdc_to_ctl_1_cdc_tdata,
      src_FULL_N  => rfdc_to_ctl_1_cdc_tready,
      dst_CLK     => ctl_in.clk,
      dst_DEQ     => ctl_1_cdc_to_ctl_rx_1_converter_tready,
      dst_out     => ctl_1_cdc_to_ctl_rx_1_converter_tdata,
      dst_EMPTY_N => ctl_1_cdc_to_ctl_rx_1_converter_tvalid);

  ctl_rx_1_converter : axis_to_iqstream_converter
    port map(
      s_axis_tdata  => ctl_1_cdc_to_ctl_rx_1_converter_tdata,
      s_axis_tvalid => ctl_1_cdc_to_ctl_rx_1_converter_tvalid,
      s_axis_tready => ctl_1_cdc_to_ctl_rx_1_converter_tready,
      oprotocol     => ctl_rx_1_converter_to_ctl_1_marshaller_pro,
      ordy          => ctl_rx_1_converter_to_ctl_1_marshaller_rdy);

  ctl_1_marshaller : iqstream_marshaller
    generic map(
      WSI_DATA_WIDTH    => out1_out.data'length,
      WSI_MBYTEEN_WIDTH => out1_out.byte_enable'length)
    port map(
      clk          => rx_1_clk,
      rst          => rx_1_reset,
      iprotocol    => ctl_rx_1_converter_to_ctl_1_marshaller_pro,
      ieof         => bfalse,
      irdy         => ctl_rx_1_converter_to_ctl_1_marshaller_rdy,
      odata        => out1_out.data,
      ovalid       => out1_out.valid,
      obyte_enable => out1_out.byte_enable,
      ogive        => out1_out.give,
      osom         => out1_out.som,
      oeom         => out1_out.eom,
      oeof         => out1_out.eof,
      oready       => out1_in.ready);

end structural;
