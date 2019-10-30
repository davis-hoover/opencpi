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

-- TODO Once there is a generic MMCM/PLL, modifiy this to use it instead and move this module to cdc_testing in misc prims 
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all; use ieee.math_real.all; use ieee.std_logic_misc.all;
library ocpi; use ocpi.types.all,  ocpi.util.all;
library cdc;

entity gen_clk is
    generic (src_clk_hz : real := 100000000.0;
             dst_clk_hz : real := 100000000.0);
    port (
	ctl_clk      : in std_logic;
	ctl_rst      : in std_logic;
        src_clk      : out std_logic;
        src_rst      : out std_logic;
        dst_clk      : out std_logic;
        dst_rst      : out std_logic);
end entity gen_clk;

architecture rtl of gen_clk is

  component mmcm_100_to_50_and_25
    port(
      clk_in1           : in     std_logic;
      clk_out1          : out    std_logic; -- 50 MHz output
      clk_out2          : out    std_logic; -- 25 MHz output
      reset             : in     std_logic;
      locked            : out    std_logic);
  end component;

  signal s_src_clk          : std_logic := '0';
  signal s_src_rst          : std_logic;
  signal s_dst_clk          : std_logic := '0';
  signal s_dst_rst          : std_logic;
  signal s_locked : std_logic;
  signal s_not_locked : std_logic;

begin

 src_clk <= s_src_clk;
 src_rst <= s_src_rst;
 dst_clk <= s_dst_clk;
 dst_rst <= s_dst_rst;


  gen_equal_clk_freq : if (src_clk_hz = dst_clk_hz) generate
   s_src_clk <= ctl_clk;
   s_src_rst <= ctl_rst;
   s_dst_clk <= ctl_clk;
   s_dst_rst <= ctl_rst;
  end generate gen_equal_clk_freq;

  gen_diff_clk_freq : if (src_clk_hz /= dst_clk_hz) generate

      s_not_locked <= not s_locked;
      reset_sync_s_not_locked_to_src : cdc.cdc.reset
        port map   (
          src_rst   => s_not_locked,
          dst_clk   => s_src_clk,
          dst_rst   => s_src_rst);

      reset_sync_s_not_locked_to_dst : cdc.cdc.reset
        port map   (
          src_rst   => s_not_locked,
          dst_clk   => s_dst_clk,
          dst_rst   => s_dst_rst);


    gen_1_to_2_clk : if (src_clk_hz = 50000000.0) generate

       s_dst_clk <= ctl_clk;
       inst_mmcm_100_to_50_and_25 : component mmcm_100_to_50_and_25
	 port map (
	  clk_in1 => ctl_clk,
	  clk_out1 => s_src_clk,
	  clk_out2 => open,
	  reset => ctl_rst,
	  locked => s_locked);

    end generate gen_1_to_2_clk;

    gen_1_to_4_clk : if (src_clk_hz = 25000000.0) generate

       s_dst_clk <= ctl_clk;
       inst_mmcm_100_to_50_and_25 : component mmcm_100_to_50_and_25
	 port map (
	  clk_in1 => ctl_clk,
	  clk_out1 => open,
	  clk_out2 => s_src_clk,
	  reset => ctl_rst,
	  locked => s_locked);

    end generate gen_1_to_4_clk;

    gen_2_to_1_clk : if (dst_clk_hz = 50000000.0) generate

   	s_src_clk <= ctl_clk;
	inst_mmcm_100_to_50_and_25 : component mmcm_100_to_50_and_25
	 port map (
	  clk_in1 => ctl_clk,
	  clk_out1 => s_dst_clk,
	  clk_out2 => open,
	  reset => ctl_rst,
	  locked => s_locked);

    end generate gen_2_to_1_clk;

    gen_4_to_1_clk : if (dst_clk_hz = 25000000.0) generate

      s_src_clk <= ctl_clk;
       inst_mmcm_100_to_50_and_25 : component mmcm_100_to_50_and_25
	 port map (
	  clk_in1 => ctl_clk,
	  clk_out1 => open,
	  clk_out2 => s_dst_clk,
	  reset => ctl_rst,
	  locked => s_locked);

    end generate gen_4_to_1_clk;

  end generate gen_diff_clk_freq;

end rtl;
