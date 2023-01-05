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
use work.dgrdma_util.all;

entity eth_frame_generator is
  generic (
    DATA_WIDTH : natural := 64;
    KEEP_WIDTH : natural := 8
  );
  port(
    clk              : in std_logic;
    reset            : in std_logic;

    s_tx_axis_tdata  : in std_logic_vector((DATA_WIDTH-1) downto 0);
    s_tx_axis_tkeep  : in std_logic_vector((KEEP_WIDTH-1) downto 0);
    s_tx_axis_tvalid : in std_logic;
    s_tx_axis_tready : out std_logic;
    s_tx_axis_tlast  : in std_logic;

    s_tx_hdr_src_mac : in std_logic_vector(47 downto 0);
    s_tx_hdr_type    : in std_logic_vector(15 downto 0);

    m_tx_eth_tdata   : out std_logic_vector((DATA_WIDTH-1) downto 0);
    m_tx_eth_tkeep   : out std_logic_vector((KEEP_WIDTH-1) downto 0);
    m_tx_eth_tvalid  : out std_logic;
    m_tx_eth_tready  : in std_logic;
    m_tx_eth_tlast   : out std_logic;
    m_tx_eth_tuser   : out std_logic
  );
end entity;

architecture rtl of eth_frame_generator is
begin

  eth_frame_generator32: if DATA_WIDTH = 32 generate
    eth_frame_generator : entity work.eth_frame_generator32
      generic map(
        DATA_WIDTH => DATA_WIDTH,
        KEEP_WIDTH => KEEP_WIDTH
      )
      port map(
          clk   => clk,
          reset => reset,

          s_tx_axis_tdata  => s_tx_axis_tdata,
          s_tx_axis_tkeep  => s_tx_axis_tkeep,
          s_tx_axis_tvalid => s_tx_axis_tvalid,
          s_tx_axis_tready => s_tx_axis_tready,
          s_tx_axis_tlast  => s_tx_axis_tlast,

          s_tx_hdr_src_mac => s_tx_hdr_src_mac,
          s_tx_hdr_type    => s_tx_hdr_type,

          m_tx_eth_tdata   => m_tx_eth_tdata,
          m_tx_eth_tkeep   => m_tx_eth_tkeep,
          m_tx_eth_tvalid  => m_tx_eth_tvalid,
          m_tx_eth_tready  => m_tx_eth_tready,
          m_tx_eth_tlast   => m_tx_eth_tlast,
          m_tx_eth_tuser   => m_tx_eth_tuser
      );
  end generate eth_frame_generator32;

  eth_frame_generator64: if DATA_WIDTH = 64 generate
    eth_frame_generator : entity work.eth_frame_generator64
      generic map(
        DATA_WIDTH => DATA_WIDTH,
        KEEP_WIDTH => KEEP_WIDTH
      )
      port map(
          clk   => clk,
          reset => reset,

          s_tx_axis_tdata  => s_tx_axis_tdata,
          s_tx_axis_tkeep  => s_tx_axis_tkeep,
          s_tx_axis_tvalid => s_tx_axis_tvalid,
          s_tx_axis_tready => s_tx_axis_tready,
          s_tx_axis_tlast  => s_tx_axis_tlast,

          s_tx_hdr_src_mac => s_tx_hdr_src_mac,
          s_tx_hdr_type    => s_tx_hdr_type,

          m_tx_eth_tdata   => m_tx_eth_tdata,
          m_tx_eth_tkeep   => m_tx_eth_tkeep,
          m_tx_eth_tvalid  => m_tx_eth_tvalid,
          m_tx_eth_tready  => m_tx_eth_tready,
          m_tx_eth_tlast   => m_tx_eth_tlast,
          m_tx_eth_tuser   => m_tx_eth_tuser
      );
  end generate eth_frame_generator64;

  eth_frame_generator128: if DATA_WIDTH = 128 generate
    eth_frame_generator : entity work.eth_frame_generator128
      generic map(
        DATA_WIDTH => DATA_WIDTH,
        KEEP_WIDTH => KEEP_WIDTH
      )
      port map(
          clk   => clk,
          reset => reset,

          s_tx_axis_tdata  => s_tx_axis_tdata,
          s_tx_axis_tkeep  => s_tx_axis_tkeep,
          s_tx_axis_tvalid => s_tx_axis_tvalid,
          s_tx_axis_tready => s_tx_axis_tready,
          s_tx_axis_tlast  => s_tx_axis_tlast,

          s_tx_hdr_src_mac => s_tx_hdr_src_mac,
          s_tx_hdr_type    => s_tx_hdr_type,

          m_tx_eth_tdata   => m_tx_eth_tdata,
          m_tx_eth_tkeep   => m_tx_eth_tkeep,
          m_tx_eth_tvalid  => m_tx_eth_tvalid,
          m_tx_eth_tready  => m_tx_eth_tready,
          m_tx_eth_tlast   => m_tx_eth_tlast,
          m_tx_eth_tuser   => m_tx_eth_tuser
      );
  end generate eth_frame_generator128;

end rtl;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------