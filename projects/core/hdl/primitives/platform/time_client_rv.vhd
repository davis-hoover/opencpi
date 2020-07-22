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

library IEEE; use IEEE.std_logic_1164.all, IEEE.numeric_std.all;
library ocpi; use ocpi.all, ocpi.types.all;
library work; use work.platform_pkg.all; use work.time_client_defs.all; 
library cdc;
entity time_client_rv is
  port(
    wci_Clk     : in std_logic;
    wci_Reset_n : in std_logic;
    time_in     : in  time_service_t;
    wti_in      : in  wti_in_t;
    wti_out     : out wti_out_t
    );
end entity time_client_rv;
architecture rtl of time_client_rv is

  signal wci_reset          : std_logic;
  signal wci2timebase_reset : std_logic;
  signal sync_reg_in        : std_logic_vector(time_in.now'length downto 0);
  signal sync_reg_out       : std_logic_vector(time_in.now'length downto 0);

begin

  wci_reset <= not wci_Reset_n;

  wci2timebase_rst : cdc.cdc.reset
    port map   (src_rst => wci_reset,
                dst_clk => time_in.clk,
                dst_rst => wci2timebase_reset);

  sync_reg_in <= time_in.valid & std_logic_vector(time_in.now);
  
  syncReg : cdc.cdc.bits_feedback
    generic map (
      width => time_in.now'length+1) -- +1 is for the valid flag
    port map (
      src_CLK => time_in.clk,
      dst_CLK => wti_in.Clk,
      src_RST => wci2timebase_reset,
      dst_rst => wci_reset, -- this will be released earlier than the time will be used.
      src_IN  => sync_reg_in,
      src_EN  => '1',
      dst_OUT => sync_reg_out,
      src_RDY => open);

  wti_out.MData <= sync_reg_out(time_in.now'length-1 downto 0);
  wti_out.MCmd <= ocp.MCmd_WRITE when its(sync_reg_out(time_in.now'length)) else
                  ocp.MCmd_IDLE;
end architecture rtl;
