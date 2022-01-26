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

--================================================================================
-- Adapt the raw control plane interface to attach to an AXI (lite) slave.
-- We will try to compile for non-AXI-lite variants, but it only really
-- works for AXI-LITE32
library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all, ocpi.util.all;
library work; use work.axi_pkg.all, work.AXI_INTERFACE.all;
entity raw2axi_AXI_INTERFACE is
  port(clk     : in std_logic;
       reset   : in bool_t;
       raw_in  : in ocpi.wci.raw_in_t;
       raw_out : out ocpi.wci.raw_out_t;
       axi_in  : in  axi_s2m_t;
       axi_out : out axi_m2s_t);
end entity raw2axi_AXI_INTERFACE;
architecture rtl of raw2axi_AXI_INTERFACE is
begin
  -- global signals for all channels, we are supplying clock and reset
#if CLOCK_FROM_MASTER
  axi_out.a.clk    <= clk;
#else
  // This is not really supported - it should only compile
#endif
#if RESET_FROM_MASTER
  axi_out.a.resetn <= not reset;
#else
  // This is not really supported - it should only compile
#endif
  -- Write signalling
  axi_out.aw.addr  <= slv(std_logic_vector(raw_in.address), axi_out.aw.addr'length);
  axi_out.aw.prot  <= (others => '0');
  axi_out.aw.valid <= raw_in.is_write;
#if !AXI4_LITE
  axi_out.aw.len   <= (others => '0');
  axi_out.aw.lock  <= (others => '0');
  axi_out.aw.cache <= (others => '0');
  axi_out.aw.size  <= "010"; -- 4 bytes
  axi_out.aw.burst <= "00"; -- fixed address in single word burst
  axi_out.w.last   <= '1';
#endif
  axi_out.w.strb   <= slv(raw_in.byte_enable, axi_out.w.strb'length);
  axi_out.w.valid  <= raw_in.is_write;
  axi_out.w.data   <= slv(raw_in.data, axi_out.w.data'length);
  axi_out.b.ready  <= '1';  -- we are always ready to receive a response
  -- b.resp is ignored and assume to be OKAY

  -- Read signalling
  axi_out.ar.addr  <= slv(std_logic_vector(raw_in.address), axi_out.ar.addr'length);
  axi_out.ar.prot  <= (others => '0');
  axi_out.ar.valid <= raw_in.is_read;
#if !AXI4_LITE
  axi_out.ar.len   <= (others => '0');
  axi_out.ar.lock  <= (others => '0');
  axi_out.ar.cache <= (others => '0');
  axi_out.ar.size  <= "010"; -- 4 bytes
  axi_out.ar.burst <= "00"; -- fixed address in single word burst
#endif
  axi_out.r.ready  <= '1';  -- we are always ready to receive read data if we asked for it
  raw_out.data     <= axi_in.r.data(raw_out.data'range);
  -- r.resp is ignored and assumed to be OKAY
  -- r.last is ignored (or not present with lite)

  -- Combined handshaking to produce the raw_out.done signal.
  -- We will be driven by the responses being valid.
  raw_out.done     <= axi_in.b.valid or axi_in.r.valid;
  raw_out.error    <='0';
end rtl;
