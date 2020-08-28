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

library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library util;

entity clock_forward is
  generic (
    INVERT_CLOCK : boolean := false;
    SINGLE_ENDED : boolean := true;
    INCLUDE_BUF  : boolean := true
  );
  port (
    RST       : in  std_logic;
    CLK_IN    : in  std_logic;
    CLK_OUT_P : out std_logic;
    CLK_OUT_N : out std_logic
  );
end entity clock_forward;

architecture rtl of clock_forward is

  signal clk_fwd : std_logic;
  signal din_ris : std_logic := '0';
  signal din_fal : std_logic := '0';
  signal o_s     : std_logic := '0';
  signal obar_s  : std_logic := '0';

begin

  din_ris <= '0' when INVERT_CLOCK else '1';
  din_fal <= '1' when INVERT_CLOCK else '0';

  clock_generator : util.util.oddr
    port map(
      clk     => CLK_IN,
      rst     => RST,
      din_ris => din_ris,
      din_fal => din_fal,
      ddr_out => clk_fwd);

  out_buffer : util.util.BUFFER_OUT_1
    generic map(
      DIFFERENTIAL => SINGLE_ENDED)
    port map(
      I    => clk_fwd,
      O    => o_s,
      OBAR => obar_s);

  CLK_OUT_P <= o_s when INCLUDE_BUF else clk_fwd;
  CLK_OUT_N <= (not clk_fwd) when (SINGLE_ENDED or (INCLUDE_BUF = false)) else obar_s;

end rtl;
