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

-- Xilinx-specific input buffer, supports both single ended and differential
-- iostandards
library IEEE;
use IEEE.std_logic_1164.all, ieee.numeric_std.all;
use work.platform_pkg.all;
library unisim; use unisim.vcomponents.all;
entity BUFFER_IN_N is
  generic (width        :     natural;
           IOSTANDARD   :     iostandard_t := UNSPECIFIED;
           DIFFERENTIAL :     boolean; -- only used if IOSTANDARD is UNSPECIFIED
           GLOBAL_CLOCK :     boolean       := FALSE);
  port (   I            : in  std_logic_vector(width-1 downto 0);
           IBAR         : in  std_logic_vector(width-1 downto 0) := (others => 'X'); -- only used if relevant to IOSTANDARD
           O            : out std_logic_vector(width-1 downto 0));
end entity BUFFER_IN_N;
architecture rtl of BUFFER_IN_N is
begin

  -- technology: unspecified, supply voltage: unspecified
  UNSPECIFIED_gen : if IOSTANDARD = UNSPECIFIED generate
    single_ended_prim : if DIFFERENTIAL = false generate
      buf_generic : if GLOBAL_CLOCK = false generate
        gen_loop : for idx in width-1 downto 0 generate
          buf : IBUF
            port map(
              I  => I(idx),
              O  => O(idx)); -- equivalent to Altera ALT_INBUF
        end generate;
      end generate;

      buf_clk : if GLOBAL_CLOCK = true generate
        gen_loop : for idx in width-1 downto 0 generate
          buf : IBUFG
            port map(
              I  => I(idx),
              O  => O(idx)); -- equivalent to Altera ALT_INBUF + GLOBAL
        end generate;
      end generate;
    end generate;

    differential_prim : if DIFFERENTIAL = true generate
      buf_generic : if GLOBAL_CLOCK = false generate
        gen_loop : for idx in width-1 downto 0 generate
          buf : IBUFDS
            port map(
              I  => I(idx),
              IB => IBAR(idx),
              O  => O(idx)); -- equivalent to Altera ALT_INBUF_DIFF
        end generate;
      end generate;

      buf_clk : if GLOBAL_CLOCK = true generate
        gen_loop : for idx in width-1 downto 0 generate
          buf : IBUFGDS
            port map(
              I  => I(idx),
              IB => IBAR(idx),
              O  => O(idx)); -- equivalent to Altera ALT_INBUF_DIFF + GLOBAL
        end generate;
      end generate;
    end generate;
  end generate;

  -- technology: CMOS, supply voltage: 1.8V
  CMOS18_gen : if IOSTANDARD = CMOS18 generate
    buf_generic : if GLOBAL_CLOCK = false generate
      gen_loop : for idx in width-1 downto 0 generate
        buf : IBUF
          generic map(
            IOSTANDARD => "LVCMOS18")
          port map(
            I  => I(idx),
            O  => O(idx)); -- equivalent to Altera ALT_INBUF
      end generate;
    end generate;

    buf_clk : if GLOBAL_CLOCK = true generate
      gen_loop : for idx in width-1 downto 0 generate
        buf : IBUFG
          generic map(
            IOSTANDARD => "LVCMOS18")
          port map(
            I  => I(idx),
            O  => O(idx)); -- equivalent to Altera ALT_INBUF + GLOBAL
      end generate;
    end generate;
  end generate;

  -- technology: CMOS, supply voltage: 2.5V
  CMOS25_gen : if IOSTANDARD = CMOS25 generate
    buf_generic : if GLOBAL_CLOCK = false generate
      gen_loop : for idx in width-1 downto 0 generate
        buf : IBUF
          generic map(
            IOSTANDARD => "LVCMOS25")
          port map(
            I  => I(idx),
            O  => O(idx)); -- equivalent to Altera ALT_INBUF
      end generate;
    end generate;

    buf_clk : if GLOBAL_CLOCK = true generate
      gen_loop : for idx in width-1 downto 0 generate
        buf : IBUFG
          generic map(
            IOSTANDARD => "LVCMOS25")
          port map(
            I  => I(idx),
            O  => O(idx)); -- equivalent to Altera ALT_INBUF + GLOBAL
      end generate;
    end generate;
  end generate;

  -- technology: LVDS (TIA/EIA-644 specification), supply voltage: 2.5V
  LVDS_25_gen : if IOSTANDARD = LVDS25 generate
    buf_generic : if GLOBAL_CLOCK = false generate
      gen_loop : for idx in width-1 downto 0 generate
        buf : IBUFDS
          generic map(
            IOSTANDARD => "LVDS_25")
          port map(
            I  => I(idx),
            IB => IBAR(idx),
            O  => O(idx)); -- equivalent to Altera ALT_INBUF_DIFF
      end generate;
    end generate;

    buf_clk : if GLOBAL_CLOCK = true generate
      gen_loop : for idx in width-1 downto 0 generate
        buf : IBUFGDS
          generic map(
            IOSTANDARD => "LVDS_25")
          port map(
            I  => I(idx),
            IB => IBAR(idx),
            O  => O(idx)); -- equivalent to Altera ALT_INBUF_DIFF + GLOBAL
      end generate;
    end generate;
  end generate;

end rtl;

