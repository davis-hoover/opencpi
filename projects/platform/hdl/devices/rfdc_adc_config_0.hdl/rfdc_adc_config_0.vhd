-- THIS FILE WAS ORIGINALLY GENERATED ON Tue Mar 21 15:16:55 2023 EDT
-- YOU *ARE* EXPECTED TO EDIT IT
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
library axi;
architecture rtl of worker is
  -- ctl clk domain
  signal axi_converter_to_rfdc_in : axi.lite32.axi_m2s_t := (
      a => (CLK => '0', RESETn => '0'),
      aw => (ADDR => (others => '0'), VALID => '0', PROT => (others => '0')),
      ar => (ADDR => (others => '0'), VALID => '0', PROT => (others => '0')),
      w => (DATA => (others => '0'), STRB => (others => '0'), VALID => '0'),
      r => (READY => '0'),
      b => (READY => '0'));
  signal axi_converter_to_rfdc_out : axi.lite32.axi_s2m_t := (
      aw => (READY => '0'),
      ar => (READY => '0'),
      w => (READY => '0'),
      r => (DATA => (others => '0'), RESP => (others => '0'), VALID => '0'),
      b => (RESP => (others => '0'), VALID => '0'));
begin

  axi_converter : axi.lite32.raw2axi_lite32
    port map(
      clk     => ctl_in.clk,
      reset   => ctl_in.reset,
      raw_in  => props_in.raw,
      raw_out => props_out.raw,
      axi_in  => axi_converter_to_rfdc_out,
      axi_out => axi_converter_to_rfdc_in);

  m_axi_out.aw_addr                  <= axi_converter_to_rfdc_in.aw.addr;
  m_axi_out.aw_valid                 <= axi_converter_to_rfdc_in.aw.valid;
  m_axi_out.aw_prot                  <= axi_converter_to_rfdc_in.aw.prot;
  axi_converter_to_rfdc_out.aw.ready <= m_axi_in.aw_ready;
  m_axi_out.ar_addr                  <= axi_converter_to_rfdc_in.ar.addr;
  m_axi_out.ar_valid                 <= axi_converter_to_rfdc_in.ar.valid;
  m_axi_out.ar_prot                  <= axi_converter_to_rfdc_in.ar.prot;
  axi_converter_to_rfdc_out.ar.ready <= m_axi_in.ar_ready;
  m_axi_out.w_data                   <= axi_converter_to_rfdc_in.w.data;
  m_axi_out.w_strb                   <= axi_converter_to_rfdc_in.w.strb;
  m_axi_out.w_valid                  <= axi_converter_to_rfdc_in.w.valid;
  axi_converter_to_rfdc_out.w.ready  <= m_axi_in.w_ready;
  axi_converter_to_rfdc_out.r.data   <= m_axi_in.r_data;
  axi_converter_to_rfdc_out.r.resp   <= m_axi_in.r_resp;
  axi_converter_to_rfdc_out.r.valid  <= m_axi_in.r_valid;
  m_axi_out.r_ready                  <= axi_converter_to_rfdc_in.r.ready;
  axi_converter_to_rfdc_out.b.resp   <= m_axi_in.b_resp;
  axi_converter_to_rfdc_out.b.valid  <= m_axi_in.b_valid;
  m_axi_out.b_ready                  <= axi_converter_to_rfdc_in.b.ready;

end rtl;
