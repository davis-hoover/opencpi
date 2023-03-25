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
library axi, protocol; use protocol.iqstream.all;
architecture structural of worker is
  -- ctl clk domain
  signal ctl_axi_converter_to_rfdc_in : axi.lite32.axi_m2s_t := (
      a => (CLK => '0', RESETn => '0'),
      aw => (ADDR => (others => '0'), VALID => '0', PROT => (others => '0')),
      ar => (ADDR => (others => '0'), VALID => '0', PROT => (others => '0')),
      w => (DATA => (others => '0'), STRB => (others => '0'), VALID => '0'),
      r => (READY => '0'),
      b => (READY => '0'));
  signal ctl_axi_converter_to_rfdc_out : axi.lite32.axi_s2m_t := (
      aw => (READY => '0'),
      ar => (READY => '0'),
      w => (READY => '0'),
      r => (DATA => (others => '0'), RESP => (others => '0'), VALID => '0'),
      b => (RESP => (others => '0'), VALID => '0'));
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

  ctl_axi_converter : axi.lite32.raw2axi_lite32
    port map(
      clk     => ctl_in.clk,
      reset   => ctl_in.reset,
      raw_in  => props_in.raw,
      raw_out => props_out.raw,
      axi_in  => ctl_axi_converter_to_rfdc_out,
      axi_out => ctl_axi_converter_to_rfdc_in);

  rfdc_out.axi_aw_addr  <= ctl_axi_converter_to_rfdc_in.aw.addr;
  rfdc_out.axi_aw_valid <= ctl_axi_converter_to_rfdc_in.aw.valid;
  rfdc_out.axi_aw_prot  <= ctl_axi_converter_to_rfdc_in.aw.prot;
  ctl_axi_converter_to_rfdc_out.aw.ready <= rfdc_in.axi_aw_ready;
  rfdc_out.axi_ar_addr  <= ctl_axi_converter_to_rfdc_in.ar.addr;
  rfdc_out.axi_ar_valid <= ctl_axi_converter_to_rfdc_in.ar.valid;
  rfdc_out.axi_ar_prot  <= ctl_axi_converter_to_rfdc_in.ar.prot;
  ctl_axi_converter_to_rfdc_out.ar.ready <= rfdc_in.axi_ar_ready;
  rfdc_out.axi_w_data   <= ctl_axi_converter_to_rfdc_in.w.data;
  rfdc_out.axi_w_strb   <= ctl_axi_converter_to_rfdc_in.w.strb;
  rfdc_out.axi_w_valid  <= ctl_axi_converter_to_rfdc_in.w.valid;
  ctl_axi_converter_to_rfdc_out.w.ready  <= rfdc_in.axi_w_ready;
  ctl_axi_converter_to_rfdc_out.r.data   <= rfdc_in.axi_r_data;
  ctl_axi_converter_to_rfdc_out.r.resp   <= rfdc_in.axi_r_resp;
  ctl_axi_converter_to_rfdc_out.r.valid  <= rfdc_in.axi_r_valid;
  rfdc_out.axi_r_ready  <= ctl_axi_converter_to_rfdc_in.r.ready;
  ctl_axi_converter_to_rfdc_out.b.resp   <= rfdc_in.axi_b_resp;
  ctl_axi_converter_to_rfdc_out.b.valid  <= rfdc_in.axi_b_valid;
  rfdc_out.axi_b_ready  <= ctl_axi_converter_to_rfdc_in.b.ready;

  ctl_0_cdc : cdc.cdc.fifo
    generic map(
      WIDTH       => out0_out.data'length)
    port map(
      src_CLK     => rfdc_in.aclks(0),
      src_RST     => rfdc_in.aresets(0),
      src_ENQ     => rfdc_in.m_axis_0_tvalid,
      src_in      => rfdc_in.m_axis_0_tdata,
      src_FULL_N  => rfdc_out.m_axis_0_tready,
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
      clk          => rfdc_in.aclks(0),
      rst          => rfdc_in.aresets(0),
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
      src_CLK     => rfdc_in.aclks(1),
      src_RST     => rfdc_in.aresets(1),
      src_ENQ     => rfdc_in.m_axis_1_tvalid,
      src_in      => rfdc_in.m_axis_1_tdata,
      src_FULL_N  => rfdc_out.m_axis_1_tready,
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
      clk          => rfdc_in.aclks(1),
      rst          => rfdc_in.aresets(1),
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

  rfdc_out.clks_p <= clks_p;
  rfdc_out.clks_n <= clks_n;
  rfdc_out.rfs_p <= rfs_p;
  rfdc_out.rfs_n <= rfs_n;

end structural;
