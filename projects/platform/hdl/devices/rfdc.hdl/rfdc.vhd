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
library axi, rfdc;
library protocol; use protocol.iqstream.all;
architecture structural of worker is
  -- ctl clk domain
  signal ctl_in_resetn : std_logic := '0';
  signal ctl_axi_converter_to_rfdc_prim_rfdc_axi_in : axi.lite32.axi_m2s_t := (
      a => (CLK => '0', RESETn => '0'),
      aw => (ADDR => (others => '0'), VALID => '0', PROT => (others => '0')),
      ar => (ADDR => (others => '0'), VALID => '0', PROT => (others => '0')),
      w => (DATA => (others => '0'), STRB => (others => '0'), VALID => '0'),
      r => (READY => '0'),
      b => (READY => '0'));
  signal ctl_axi_converter_to_rfdc_prim_rfdc_axi_out : axi.lite32.axi_s2m_t := (
      aw => (READY => '0'),
      ar => (READY => '0'),
      w => (READY => '0'),
      r => (DATA => (others => '0'), RESP => (others => '0'), VALID => '0'),
      b => (RESP => (others => '0'), VALID => '0'));
  signal ctl_rfdc_dac_axi_in : axi.lite32.axi_m2s_t := (
      a => (CLK => '0', RESETn => '0'),
      aw => (ADDR => (others => '0'), VALID => '0', PROT => (others => '0')),
      ar => (ADDR => (others => '0'), VALID => '0', PROT => (others => '0')),
      w => (DATA => (others => '0'), STRB => (others => '0'), VALID => '0'),
      r => (READY => '0'),
      b => (READY => '0'));
  signal ctl_rfdc_dac_axi_out : axi.lite32.axi_s2m_t := (
      aw => (READY => '0'),
      ar => (READY => '0'),
      w => (READY => '0'),
      r => (DATA => (others => '0'), RESP => (others => '0'), VALID => '0'),
      b => (RESP => (others => '0'), VALID => '0'));
  signal ctl_rfdc_adc_axi_in : axi.lite32.axi_m2s_t := (
      a => (CLK => '0', RESETn => '0'),
      aw => (ADDR => (others => '0'), VALID => '0', PROT => (others => '0')),
      ar => (ADDR => (others => '0'), VALID => '0', PROT => (others => '0')),
      w => (DATA => (others => '0'), STRB => (others => '0'), VALID => '0'),
      r => (READY => '0'),
      b => (READY => '0'));
  signal ctl_rfdc_adc_axi_out : axi.lite32.axi_s2m_t := (
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
  -- rx clk domain
  signal rx_clk                   : std_logic_vector(2-1 downto 0)
                                  := (others => '0');
  signal rx_reset                 : std_logic_vector(2-1 downto 0)
                                  := (others => '0');
  signal rfdc_to_ctl_0_cdc_tdata  : std_logic_vector(32-1 downto 0)
                                  := (others => '0');
  signal rfdc_to_ctl_0_cdc_tvalid : std_logic := '0';
  signal rfdc_to_ctl_0_cdc_tready : std_logic := '0';
  signal rfdc_to_ctl_1_cdc_tdata  : std_logic_vector(32-1 downto 0)
                                  := (others => '0');
  signal rfdc_to_ctl_1_cdc_tvalid : std_logic := '0';
  signal rfdc_to_ctl_1_cdc_tready : std_logic := '0';
  -- tx clk domain
  signal tx_clk                       : std_logic_vector(1-1 downto 0)
                                      := (others => '0');
  signal tx_0_cdc_to_rfdc_prim_tdata  : std_logic_vector(32-1 downto 0)
                                      := (others => '0');
  signal tx_0_cdc_to_rfdc_prim_tvalid : std_logic := '0';
  signal tx_0_cdc_to_rfdc_prim_tready : std_logic := '0';
  signal tx_1_cdc_to_rfdc_prim_tdata  : std_logic_vector(32-1 downto 0)
                                      := (others => '0');
  signal tx_1_cdc_to_rfdc_prim_tvalid : std_logic := '0';
  signal tx_1_cdc_to_rfdc_prim_tready : std_logic := '0';
begin

  ctl_axi_converter : axi.lite32.raw2axi_lite32
    port map(
      clk     => ctl_in.clk,
      reset   => ctl_in.reset,
      raw_in  => props_in.raw,
      raw_out => props_out.raw,
      axi_in  => ctl_axi_converter_to_rfdc_prim_rfdc_axi_out,
      axi_out => ctl_axi_converter_to_rfdc_prim_rfdc_axi_in);

  ctl_rfdc_dac_axi_in.a.clk    <= ctl_in.clk;
  ctl_rfdc_dac_axi_in.a.resetn <= ctl_in_resetn;
  ctl_rfdc_dac_axi_in.aw.addr  <= rfdc_dac_in.axi_aw_addr;
  ctl_rfdc_dac_axi_in.aw.valid <= rfdc_dac_in.axi_aw_valid;
  ctl_rfdc_dac_axi_in.aw.prot  <= rfdc_dac_in.axi_aw_prot;
  rfdc_dac_out.axi_aw_ready    <= ctl_rfdc_dac_axi_out.aw.ready;
  ctl_rfdc_dac_axi_in.ar.addr  <= rfdc_dac_in.axi_ar_addr;
  ctl_rfdc_dac_axi_in.ar.valid <= rfdc_dac_in.axi_ar_valid;
  ctl_rfdc_dac_axi_in.ar.prot  <= rfdc_dac_in.axi_ar_prot;
  rfdc_dac_out.axi_ar_ready    <= ctl_rfdc_dac_axi_out.ar.ready;
  ctl_rfdc_dac_axi_in.w.data   <= rfdc_dac_in.axi_w_data;
  ctl_rfdc_dac_axi_in.w.strb   <= rfdc_dac_in.axi_w_strb;
  ctl_rfdc_dac_axi_in.w.valid  <= rfdc_dac_in.axi_w_valid;
  rfdc_dac_out.axi_w_ready     <= ctl_rfdc_dac_axi_out.w.ready;
  rfdc_dac_out.axi_r_data      <= ctl_rfdc_dac_axi_out.r.data;
  rfdc_dac_out.axi_r_resp      <= ctl_rfdc_dac_axi_out.r.resp;
  rfdc_dac_out.axi_r_valid     <= ctl_rfdc_dac_axi_out.r.valid;
  ctl_rfdc_dac_axi_in.r.ready  <= rfdc_dac_in.axi_r_ready;
  rfdc_dac_out.axi_b_resp      <= ctl_rfdc_dac_axi_out.b.resp;
  rfdc_dac_out.axi_b_valid     <= ctl_rfdc_dac_axi_out.b.valid;
  ctl_rfdc_dac_axi_in.b.ready  <= rfdc_dac_in.axi_b_ready;

  ctl_rfdc_adc_axi_in.a.clk    <= ctl_in.clk;
  ctl_rfdc_adc_axi_in.a.resetn <= ctl_in_resetn;
  ctl_rfdc_adc_axi_in.aw.addr  <= rfdc_adc_in.axi_aw_addr;
  ctl_rfdc_adc_axi_in.aw.valid <= rfdc_adc_in.axi_aw_valid;
  ctl_rfdc_adc_axi_in.aw.prot  <= rfdc_adc_in.axi_aw_prot;
  rfdc_adc_out.axi_aw_ready    <= ctl_rfdc_adc_axi_out.aw.ready;
  ctl_rfdc_adc_axi_in.ar.addr  <= rfdc_adc_in.axi_ar_addr;
  ctl_rfdc_adc_axi_in.ar.valid <= rfdc_adc_in.axi_ar_valid;
  ctl_rfdc_adc_axi_in.ar.prot  <= rfdc_adc_in.axi_ar_prot;
  rfdc_adc_out.axi_ar_ready    <= ctl_rfdc_adc_axi_out.ar.ready;
  ctl_rfdc_adc_axi_in.w.data   <= rfdc_adc_in.axi_w_data;
  ctl_rfdc_adc_axi_in.w.strb   <= rfdc_adc_in.axi_w_strb;
  ctl_rfdc_adc_axi_in.w.valid  <= rfdc_adc_in.axi_w_valid;
  rfdc_adc_out.axi_w_ready     <= ctl_rfdc_adc_axi_out.w.ready;
  rfdc_adc_out.axi_r_data      <= ctl_rfdc_adc_axi_out.r.data;
  rfdc_adc_out.axi_r_resp      <= ctl_rfdc_adc_axi_out.r.resp;
  rfdc_adc_out.axi_r_valid     <= ctl_rfdc_adc_axi_out.r.valid;
  ctl_rfdc_adc_axi_in.r.ready  <= rfdc_adc_in.axi_r_ready;
  rfdc_adc_out.axi_b_resp      <= ctl_rfdc_adc_axi_out.b.resp;
  rfdc_adc_out.axi_b_valid     <= ctl_rfdc_adc_axi_out.b.valid;
  ctl_rfdc_adc_axi_in.b.ready  <= rfdc_adc_in.axi_b_ready;

  ctl_in_resetn <= not ctl_in.reset;

  rfdc_prim : rfdc.rfdc_pkg.rfdc
    port map(
      rfdc_axi_in      => ctl_axi_converter_to_rfdc_prim_rfdc_axi_in,
      rfdc_axi_out     => ctl_axi_converter_to_rfdc_prim_rfdc_axi_out,
      rfdc_adc_axi_in  => ctl_rfdc_adc_axi_in,
      rfdc_adc_axi_out => ctl_rfdc_adc_axi_out,
      rfdc_dac_axi_in  => ctl_rfdc_dac_axi_in,
      rfdc_dac_axi_out => ctl_rfdc_dac_axi_out,
      rx_clks_p        => rfdc_adc_in.clks_p,
      rx_clks_n        => rfdc_adc_in.clks_n,
      tx_clks_p        => rfdc_dac_in.clks_p,
      tx_clks_n        => rfdc_dac_in.clks_n,
      sysref_p         => rfdc_dac_in.sysref_p,
      sysref_n         => rfdc_dac_in.sysref_n,
      rf_rxs_p         => rfdc_adc_in.rfs_p,
      rf_rxs_n         => rfdc_adc_in.rfs_n,
      rf_txs_p         => rfdc_dac_out.rfs_p,
      rf_txs_n         => rfdc_dac_out.rfs_n,
      tx_aclks         => rfdc_dac_out.aclks,
      s_axis_0_tdata   => rfdc_dac_in.s_axis_0_tdata,
      s_axis_0_tvalid  => rfdc_dac_in.s_axis_0_tvalid,
      s_axis_0_tready  => rfdc_dac_out.s_axis_0_tready,
      s_axis_1_tdata   => rfdc_dac_in.s_axis_1_tdata,
      s_axis_1_tvalid  => rfdc_dac_in.s_axis_1_tvalid,
      s_axis_1_tready  => rfdc_dac_out.s_axis_1_tready,
      rx_aclks         => rfdc_adc_out.aclks,
      rx_aresets       => rfdc_adc_out.aresets,
      m_axis_0_tdata   => rfdc_adc_out.m_axis_0_tdata,
      m_axis_0_tvalid  => rfdc_adc_out.m_axis_0_tvalid,
      m_axis_0_tready  => rfdc_adc_in.m_axis_0_tready,
      m_axis_1_tdata   => rfdc_adc_out.m_axis_1_tdata,
      m_axis_1_tvalid  => rfdc_adc_out.m_axis_1_tvalid,
      m_axis_1_tready  => rfdc_adc_in.m_axis_1_tready);

end structural;
