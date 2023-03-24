-- THIS FILE WAS ORIGINALLY GENERATED ON Tue Mar 21 15:17:04 2023 EDT
-- BASED ON THE FILE: rfdc_dac-hdl.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: rfdc_dac
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
      WIDTH       => in0_in.data'length)
    port map(
      src_CLK     => ctl_in.clk,
      src_RST     => ctl_in.reset,
      src_ENQ     => ctl_tx_0_converter_to_tx_0_cdc_tvalid,
      src_in      => ctl_tx_0_converter_to_tx_0_cdc_tdata,
      src_FULL_N  => ctl_tx_0_converter_to_tx_0_cdc_tready,
      dst_CLK     => rfdc_in.aclks(0),
      dst_DEQ     => rfdc_in.s_axis_0_tready,
      dst_out     => rfdc_out.s_axis_0_tdata,
      dst_EMPTY_N => rfdc_out.s_axis_0_tvalid);

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
      WIDTH       => in1_in.data'length)
    port map(
      src_CLK     => ctl_in.clk,
      src_RST     => ctl_in.reset,
      src_ENQ     => ctl_tx_1_converter_to_tx_1_cdc_tvalid,
      src_in      => ctl_tx_1_converter_to_tx_1_cdc_tdata,
      src_FULL_N  => ctl_tx_1_converter_to_tx_1_cdc_tready,
      dst_CLK     => rfdc_in.aclks(0),
      dst_DEQ     => rfdc_in.s_axis_1_tready,
      dst_out     => rfdc_out.s_axis_1_tdata,
      dst_EMPTY_N => rfdc_out.s_axis_1_tvalid);

end structural;
