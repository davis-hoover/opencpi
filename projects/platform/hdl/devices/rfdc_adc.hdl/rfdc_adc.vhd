-- THIS FILE WAS ORIGINALLY GENERATED ON Tue Mar 21 15:16:55 2023 EDT
-- BASED ON THE FILE: rfdc_adc-hdl.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: rfdc_adc
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
library protocol; use protocol.iqstream.all;
architecture structural of worker is
  -- ctl clk domain
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
begin

  axi_converter : axi.lite32.raw2axi_lite32
    port map(
      clk     => ctl_in.clk,
      reset   => ctl_in.reset,
      raw_in  => props_in.raw,
      raw_out => props_out.raw,
      axi_in  => axi_in,
      axi_out => axi_out);

  rfdc.axi_a_clk    <= axi_out.a.clk;
  rfdc.axi_a_resetn <= axi_out.a.resetn;
  rfdc.axi_aw_addr  <= axi_out.aw.addr;
  rfdc.axi_aw_valid <= axi_out.aw.valid;
  rfdc.axi_aw_prot  <= axi_out.aw.prot;
  rfdc.axi_aw_ready <= axi_in.aw.ready;
  rfdc.axi_ar_addr  <= axi_out.aw.addr;
  rfdc.axi_ar_valid <= axi_out.aw.valid;
  rfdc.axi_ar_prot  <= axi_out.aw.prot;
  rfdc.axi_ar_ready <= axi_in.ar.ready;
  rfdc.axi_w_data   <= axi_out.w.data;
  rfdc.axi_w_strb   <= axi_out.w.strb;
  rfdc.axi_w_valid  <= axi_out.w.valid;
  rfdc.axi_w_ready  <= axi_in.w.ready;
  rfdc.axi_r_data   <= axi_in.r.data;
  rfdc.axi_r_resp   <= axi_in.r.resp;
  rfdc.axi_r_valid  <= axi_in.r.valid;
  rfdc.axi_r_ready  <= axi_out.r.ready;
  rfdc.axi_b_resp   <= axi_in.b.resp;
  rfdc.axi_b_valid  <= axi_in.b.valid;
  rfdc.axi_b_ready  <= axi_out.b.ready;

  ctl_0_cdc : cdc.cdc.fifo
    generic map(
      WIDTH       => out0_out.data'length)
    port map(
      src_CLK     => rfdc.rx_aclks(0),
      src_RST     => rfdc.rx_aresets(0),
      src_ENQ     => rfdc.m_axis_0_tvalid,
      src_in      => rfdc.m_axis_0_tdata,
      src_FULL_N  => rfdc.m_axis_0_tready,
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
      clk          => rfdc.rx_aclks(0),
      rst          => rfdc.rx_aresets(0),
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
      src_CLK     => rfdc.rx_aclks(1),
      src_RST     => rfdc.rx_aresets(1),
      src_ENQ     => rfdc.m_axis_1_tvalid,
      src_in      => rfdc.m_axis_1_tdata,
      src_FULL_N  => rfdc.m_axis_1_tready,
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
      clk          => rfdc.rx_aclks(1),
      rst          => rfdc.rx_aresets(1),
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
