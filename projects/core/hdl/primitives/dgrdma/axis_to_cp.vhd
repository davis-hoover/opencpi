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

library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library platform;
use platform.all;

entity axis_to_cp is

generic(
    data_width  : natural := 64;
    keep_width  : natural := 8
  );

port( clk                :  in std_logic;
      reset              :  in std_logic;

      eth0_mac_addr      :  in std_logic_vector(47 downto 0);

      s_axis_tdata       :  in std_logic_vector((DATA_WIDTH-1) downto 0);
      s_axis_tkeep       :  in std_logic_vector((KEEP_WIDTH-1) downto 0);
      s_axis_tvalid      :  in std_logic;
      s_axis_tlast       :  in std_logic;
      s_axis_tready      : out std_logic;

      m_axis_tdata       : out std_logic_vector((DATA_WIDTH-1) downto 0);
      m_axis_tkeep       : out std_logic_vector((KEEP_WIDTH-1) downto 0);
      m_axis_tvalid      : out std_logic;
      m_axis_tlast       : out std_logic;
      m_axis_tready      :  in std_logic;

      cp_in              :  in platform_pkg.occp_out_t;
      cp_out             : out platform_pkg.occp_in_t;

      flag_addr          :  in std_logic_vector(23 downto 0);
      flag_data          :  in std_logic_vector(31 downto 0);
      flag_valid         :  in std_logic;
      flag_take          : out std_logic;

      debug_select       :  in std_logic_vector(23 downto 0);
      debug              : out std_logic_vector(31 downto 0);

      test_points        : out std_logic_vector(11 downto 0) );
end axis_to_cp;

architecture rtl of axis_to_cp is
  signal s_axis_tdata_8  : std_logic_vector(7 downto 0);
  signal s_axis_tvalid_8 : std_logic;
  signal s_axis_tlast_8  : std_logic;
  signal s_axis_tready_8 : std_logic;

  signal m_axis_tdata_8  : std_logic_vector(7 downto 0);
  signal m_axis_tvalid_8 : std_logic;
  signal m_axis_tlast_8  : std_logic;
  signal m_axis_tready_8 : std_logic;
begin

cp_master : entity work.axis_to_cp8
port map(
  clk   => clk,
  reset => reset,

  eth0_mac_addr => eth0_mac_addr,

  s_axis_tdata  => s_axis_tdata_8,
  s_axis_tvalid => s_axis_tvalid_8,
  s_axis_tlast  => s_axis_tlast_8,
  s_axis_tready => s_axis_tready_8,

  m_axis_tdata  => m_axis_tdata_8,
  m_axis_tvalid => m_axis_tvalid_8,
  m_axis_tlast  => m_axis_tlast_8,
  m_axis_tready => m_axis_tready_8,

  cp_in  => cp_in,
  cp_out => cp_out,

  flag_addr  => flag_addr,
  flag_data  => flag_data,
  flag_valid => flag_valid,
  flag_take  => flag_take,

  debug_select => debug_select,
  debug        => debug,
  test_points  => test_points
);

cp_narrow : entity work.axis_width_narrow
generic map(
  NBYTES => DATA_WIDTH / 8
)
port map(
  clk   => clk,
  reset => reset,

  s_axis_tdata  => s_axis_tdata,
  s_axis_tkeep  => s_axis_tkeep,
  s_axis_tvalid => s_axis_tvalid,
  s_axis_tready => s_axis_tready,
  s_axis_tlast  => s_axis_tlast,

  m_axis_tdata  => s_axis_tdata_8,
  m_axis_tvalid => s_axis_tvalid_8,
  m_axis_tready => s_axis_tready_8,
  m_axis_tlast  => s_axis_tlast_8
);

cp_widen : entity work.axis_width_widen
generic map(
  NBYTES => DATA_WIDTH / 8
)
port map(
  clk   => clk,
  reset => reset,

  s_axis_tdata  => m_axis_tdata_8,
  s_axis_tvalid => m_axis_tvalid_8,
  s_axis_tready => m_axis_tready_8,
  s_axis_tlast  => m_axis_tlast_8,

  m_axis_tdata  => m_axis_tdata,
  m_axis_tkeep  => m_axis_tkeep,
  m_axis_tvalid => m_axis_tvalid,
  m_axis_tready => m_axis_tready,
  m_axis_tlast  => m_axis_tlast
);

end rtl;
