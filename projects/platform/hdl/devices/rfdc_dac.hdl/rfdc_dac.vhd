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
      dst_CLK     => rfdc.tx_aclks(0),
      dst_DEQ     => rfdc.s_axis_0_tready,
      dst_out     => rfdc.s_axis_0_tdata,
      dst_EMPTY_N => rfdc.s_axis_0_tvalid);

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
      dst_CLK     => rfdc.tx_aclks(0),
      dst_DEQ     => rfdc.s_axis_1_tready,
      dst_out     => rfdc.s_axis_1_tdata,
      dst_EMPTY_N => rfdc.s_axis_1_tvalid);

end structural;
