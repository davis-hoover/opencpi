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

library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all; use ieee.math_real.all; use ieee.std_logic_misc.all;
library ocpi; use ocpi.types.all,  ocpi.util.all;
library cdc;
library misc_prims; use misc_prims.misc_prims.all;

entity gen_reset_sync is
    generic (sim_src_clk_hz : real := 100000000.0;
             sim_dst_clk_hz : real := 100000000.0;
             simulation : std_logic := '1';
             hw_src_dst_clk_ratio : real := 1.0);
    port (
        src_clk                   : in  std_logic;
        src_rst                   : in  std_logic;
        dst_clk                   : in  std_logic;
        dst_rst                   : in  std_logic;
	      synced_dst_to_scr_rst     : out std_logic;
	      synced_src_to_dst_rst     : out std_logic);

end entity gen_reset_sync;

architecture rtl of gen_reset_sync is

constant c_src_dst_ratio : real := src_dst_ratio(sim_src_clk_hz, sim_dst_clk_hz, simulation, hw_src_dst_clk_ratio);

begin

 gen_sync_rst_dst_to_src : if (c_src_dst_ratio >= 1.0) generate
   -- faster or same clock frequency source needs to wait until slow or same
   -- clock frequency destination has come out of reset
   gen_fast_to_slow : if (c_src_dst_ratio > 1.0) generate
     reset_sync_dst_to_src : cdc.cdc.reset
       generic map (RST_DELAY => natural(ceil(c_src_dst_ratio)))
       port map   (
         src_rst   => dst_rst,
         dst_clk   => src_clk,
         dst_rst   => synced_dst_to_scr_rst);
   end generate gen_fast_to_slow;

   gen_equal_clk : if (c_src_dst_ratio = 1.0) generate
     reset_sync_dst_to_src : cdc.cdc.reset
       generic map (RST_DELAY => 2)
       port map   (
         src_rst   => dst_rst,
         dst_clk   => src_clk,
         dst_rst   => synced_dst_to_scr_rst);
   end generate gen_equal_clk;

 end generate gen_sync_rst_dst_to_src;

 gen_sync_rst_src_to_dst : if (c_src_dst_ratio <= 1.0) generate
 -- faster or same clock frequency destination needs to wait until slow or same
 -- clock frequency source has come out of reset
   gen_slow_to_fast : if (c_src_dst_ratio < 1.0) generate
     reset_sync_src_to_dst : cdc.cdc.reset
       generic map (RST_DELAY => natural(ceil(1.0/c_src_dst_ratio)))
       port map   (
         src_rst   => src_rst,
         dst_clk   => dst_clk,
         dst_rst   => synced_src_to_dst_rst);
   end generate gen_slow_to_fast;

   gen_equal_clk : if (c_src_dst_ratio = 1.0) generate
     reset_sync_src_to_dst : cdc.cdc.reset
       generic map (RST_DELAY => 2)
       port map   (
         src_rst   => src_rst,
         dst_clk   => dst_clk,
         dst_rst   => synced_src_to_dst_rst);
   end generate gen_equal_clk;

 end generate gen_sync_rst_src_to_dst;

end rtl;
