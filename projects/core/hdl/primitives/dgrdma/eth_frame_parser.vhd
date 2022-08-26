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

-- ---------------------------------------------------------------------------
-- Parse incoming Ethernet Frame, stripping out the ether-type, source and
-- destination MAC addresses.
-- The source MAC address is placed in the first 6 bytes of output
-- ---------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
use work.dgrdma_util.all;

entity eth_frame_parser is
  generic (
    DATA_WIDTH : natural := 64;
    KEEP_WIDTH : natural := 8
  );
  port(
    clk               : in std_logic;
    reset             : in std_logic;

    s_rx_eth_tdata    : in std_logic_vector((DATA_WIDTH-1) downto 0);
    s_rx_eth_tkeep    : in std_logic_vector((KEEP_WIDTH-1) downto 0);
    s_rx_eth_tvalid   : in std_logic;
    s_rx_eth_tready   : out std_logic;
    s_rx_eth_tlast    : in std_logic;
    s_rx_eth_tuser    : in std_logic;

    m_rx_axis_tdata   : out std_logic_vector((DATA_WIDTH-1) downto 0);
    m_rx_axis_tkeep   : out std_logic_vector((KEEP_WIDTH-1) downto 0);
    m_rx_axis_tvalid  : out std_logic;
    m_rx_axis_tready  : in std_logic;
    m_rx_axis_tlast   : out std_logic;

    m_rx_hdr_src_mac  : out std_logic_vector(47 downto 0);
    m_rx_hdr_dest_mac : out std_logic_vector(47 downto 0);
    m_rx_hdr_type     : out std_logic_vector(15 downto 0)
  );
end entity;

architecture rtl of eth_frame_parser is
begin

  eth_frame_parser32: if DATA_WIDTH = 32 generate
    eth_frame_parser : entity work.eth_frame_parser32
      generic map(
        DATA_WIDTH => DATA_WIDTH,
        KEEP_WIDTH => KEEP_WIDTH
      )
      port map(
          clk   => clk,
          reset => reset,

          s_rx_eth_tdata   => s_rx_eth_tdata,
          s_rx_eth_tkeep   => s_rx_eth_tkeep,
          s_rx_eth_tvalid  => s_rx_eth_tvalid,
          s_rx_eth_tready  => s_rx_eth_tready,
          s_rx_eth_tlast   => s_rx_eth_tlast,
          s_rx_eth_tuser   => s_rx_eth_tuser,

          m_rx_axis_tdata   => m_rx_axis_tdata,
          m_rx_axis_tkeep   => m_rx_axis_tkeep,
          m_rx_axis_tvalid  => m_rx_axis_tvalid,
          m_rx_axis_tready  => m_rx_axis_tready,
          m_rx_axis_tlast   => m_rx_axis_tlast,

          m_rx_hdr_src_mac  => m_rx_hdr_src_mac,
          m_rx_hdr_dest_mac => m_rx_hdr_dest_mac,
          m_rx_hdr_type     => m_rx_hdr_type
      );
  end generate eth_frame_parser32;

  eth_frame_parser64: if DATA_WIDTH = 64 generate
    eth_frame_parser : entity work.eth_frame_parser64
      generic map(
        DATA_WIDTH => DATA_WIDTH,
        KEEP_WIDTH => KEEP_WIDTH
      )
      port map(
          clk   => clk,
          reset => reset,

          s_rx_eth_tdata   => s_rx_eth_tdata,
          s_rx_eth_tkeep   => s_rx_eth_tkeep,
          s_rx_eth_tvalid  => s_rx_eth_tvalid,
          s_rx_eth_tready  => s_rx_eth_tready,
          s_rx_eth_tlast   => s_rx_eth_tlast,
          s_rx_eth_tuser   => s_rx_eth_tuser,

          m_rx_axis_tdata   => m_rx_axis_tdata,
          m_rx_axis_tkeep   => m_rx_axis_tkeep,
          m_rx_axis_tvalid  => m_rx_axis_tvalid,
          m_rx_axis_tready  => m_rx_axis_tready,
          m_rx_axis_tlast   => m_rx_axis_tlast,

          m_rx_hdr_src_mac  => m_rx_hdr_src_mac,
          m_rx_hdr_dest_mac => m_rx_hdr_dest_mac,
          m_rx_hdr_type     => m_rx_hdr_type
      );
  end generate eth_frame_parser64;

  eth_frame_parser128: if DATA_WIDTH = 128 generate
    eth_frame_parser : entity work.eth_frame_parser128
      generic map(
        DATA_WIDTH => DATA_WIDTH,
        KEEP_WIDTH => KEEP_WIDTH
      )
      port map(
          clk   => clk,
          reset => reset,

          s_rx_eth_tdata   => s_rx_eth_tdata,
          s_rx_eth_tkeep   => s_rx_eth_tkeep,
          s_rx_eth_tvalid  => s_rx_eth_tvalid,
          s_rx_eth_tready  => s_rx_eth_tready,
          s_rx_eth_tlast   => s_rx_eth_tlast,
          s_rx_eth_tuser   => s_rx_eth_tuser,

          m_rx_axis_tdata   => m_rx_axis_tdata,
          m_rx_axis_tkeep   => m_rx_axis_tkeep,
          m_rx_axis_tvalid  => m_rx_axis_tvalid,
          m_rx_axis_tready  => m_rx_axis_tready,
          m_rx_axis_tlast   => m_rx_axis_tlast,

          m_rx_hdr_src_mac  => m_rx_hdr_src_mac,
          m_rx_hdr_dest_mac => m_rx_hdr_dest_mac,
          m_rx_hdr_type     => m_rx_hdr_type
      );
  end generate eth_frame_parser128;

end rtl;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------