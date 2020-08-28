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
library altera_mf;

entity oddr is
  port(
    clk     : in  std_logic;
    rst     : in  std_logic; -- synchronous w/ the rising clock edge
    din_ris : in  std_logic;
    din_fal : in  std_logic;
    ddr_out : out std_logic);
end entity oddr;

architecture rtl of oddr is
  constant DIN_WIDTH : positive := 1;
  signal din_ris_s : std_logic_vector(DIN_WIDTH-1 downto 0) := (others => '0');
  signal din_fal_s : std_logic_vector(DIN_WIDTH-1 downto 0) := (others => '0');
  signal ddr_out_s : std_logic_vector(DIN_WIDTH-1 downto 0) := (others => '0');
begin

  din_ris_s(0) <= din_ris;
  din_fal_s(0) <= din_fal;
  ddr_out <= ddr_out_s(0);

  -- ref https://www.intel.com/content/dam/www/programmable/us/en/pdfs/literature/ug/mfug_ddio.pdf
  prim : altera_mf.altera_mf_components.altddio_out
    generic map(
      intended_device_family => "unused",
      extend_oe_disable      => "OFF",
      invert_output          => "OFF",
      oe_reg                 => "UNREGISTERED",
      power_up_high          => "OFF",
      width                  => DIN_WIDTH,
      lpm_hint               => "UNUSED",
      lpm_type               => "altddio_out"
    )
    port map(
      aclr       => '0',
      aset       => '0',
      datain_h   => din_ris_s,
      datain_l   => din_fal_s,
      dataout    => ddr_out_s,
      oe         => '1',
      oe_out     => open,
      outclock   => clk,
      outclocken => '1',
      sclr       => rst,
      sset       => '0'
    );

end rtl;
