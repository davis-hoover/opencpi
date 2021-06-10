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

-- This module is just a pacifier for unused axi HP ports.  It is an AXI master.
-- The clock and reset are injected to be supplied to both sides
library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library platform; use platform.platform_pkg.all;
library ocpi; use ocpi.types.all, ocpi.util.all;
library work; use work.axi_pkg.all, work.AXI_INTERFACE.all;

entity axinull_AXI_INTERFACE is
  port(
    clk       : in  std_logic;
    reset     : in  bool_t;
    axi_in    : in  axi_s2m_t;
    axi_out   : out axi_m2s_t
    );
end entity axinull_AXI_INTERFACE;
architecture rtl of axinull_AXI_INTERFACE is
begin
#if CLOCK_FROM_MASTER
  axi_out.A.CLK <= clk;
#endif
#if RESET_FROM_MASTER
  axi_out.A.RESETn <= '0';
#endif
  axi_out.AW.VALID <= '0';
  axi_out.W.VALID  <= '0';
  axi_out.B.READY  <= '0';              -- we are always ready for responses
  axi_out.AR.VALID <= '0';
  axi_out.R.READY  <= '0';
end rtl;
