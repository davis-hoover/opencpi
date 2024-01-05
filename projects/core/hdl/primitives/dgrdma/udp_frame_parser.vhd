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
-- Parse incoming UDP Frame
-- The incoming UDP frame (from the UDP Complete component) has been separated
-- out into header information and payload. The source IPaddress and source
-- UDP Port are stored and prepended to the payload (48 bits in total).
-- The destination UDP Port is also stored and output as udp_dest_port
-- The destination UDP Port is used later to route control and data traffic
-- back to the sender.
-- DG-RDMA specifies that the first 2 bytes of the UDP payload are unused
-- padding so these are discarded.
-- ---------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
use work.dgrdma_util.all;

entity udp_frame_parser is
  generic (
    UDP_DATA_WIDTH : natural := 64;
    UDP_KEEP_WIDTH : natural := 8;
    DATA_WIDTH : natural := 64;
    KEEP_WIDTH : natural := 8
  );
  port(
    clk   : in std_logic;
    reset : in std_logic;

    local_mac_addr            : in std_logic_vector(47 downto 0);
    local_ip_addr             : in std_logic_vector(31 downto 0);

    s_udp_hdr_valid           : in std_logic;
    s_udp_hdr_ready           : out std_logic;
    s_udp_eth_dest_mac        : in std_logic_vector(47 downto 0);
    s_udp_eth_src_mac         : in std_logic_vector(47 downto 0);
    s_udp_eth_type            : in std_logic_vector(15 downto 0);
    s_udp_ip_version          : in std_logic_vector(3 downto 0);
    s_udp_ip_ihl              : in std_logic_vector(3 downto 0);
    s_udp_ip_dscp             : in std_logic_vector(5 downto 0);
    s_udp_ip_ecn              : in std_logic_vector(1 downto 0);
    s_udp_ip_length           : in std_logic_vector(15 downto 0);
    s_udp_ip_identification   : in std_logic_vector(15 downto 0);
    s_udp_ip_flags            : in std_logic_vector(2 downto 0);
    s_udp_ip_fragment_offset  : in std_logic_vector(12 downto 0);
    s_udp_ip_ttl              : in std_logic_vector(7 downto 0);
    s_udp_ip_protocol         : in std_logic_vector(7 downto 0);
    s_udp_ip_header_checksum  : in std_logic_vector(15 downto 0);
    s_udp_ip_source_ip        : in std_logic_vector(31 downto 0);
    s_udp_ip_dest_ip          : in std_logic_vector(31 downto 0);
    s_udp_source_port         : in std_logic_vector(15 downto 0);
    s_udp_dest_port           : in std_logic_vector(15 downto 0);
    s_udp_length              : in std_logic_vector(15 downto 0);
    s_udp_checksum            : in std_logic_vector(15 downto 0);
    s_udp_payload_axis_tdata  : in std_logic_vector(UDP_DATA_WIDTH-1 downto 0);
    s_udp_payload_axis_tkeep  : in std_logic_vector(UDP_KEEP_WIDTH-1 downto 0);
    s_udp_payload_axis_tvalid : in std_logic;
    s_udp_payload_axis_tready : out std_logic;
    s_udp_payload_axis_tlast  : in std_logic;
    s_udp_payload_axis_tuser  : in std_logic;

    m_rx_axis_tdata   : out std_logic_vector(DATA_WIDTH-1 downto 0);
    m_rx_axis_tkeep   : out std_logic_vector(KEEP_WIDTH-1 downto 0);
    m_rx_axis_tvalid  : out std_logic;
    m_rx_axis_tready  : in std_logic;
    m_rx_axis_tlast   : out std_logic;

    udp_dest_port     : out std_logic_vector(15 downto 0)   
  );
end entity;

architecture rtl of udp_frame_parser is

signal axis_tdata  : std_logic_vector(DATA_WIDTH-1 downto 0);
signal axis_tkeep  : std_logic_vector(KEEP_WIDTH-1 downto 0);
signal axis_tvalid : std_logic;
signal axis_tready : std_logic;
signal axis_tlast  : std_logic;
signal axis_tuser  : std_logic;

begin

  -- this implementation supports these combinations of UDP payload data width
  -- and AXI-Stream width  
  assert ((UDP_DATA_WIDTH = 8  and DATA_WIDTH = 32) or 
          (UDP_DATA_WIDTH = 32 and DATA_WIDTH = 32) or
          (UDP_DATA_WIDTH = 64 and DATA_WIDTH = 64))
    report "Unsupported SDP width!"
    severity error;

  -- -----------------------------------------------------------------------------
  udp_frame_parser8_32_gen: if (UDP_DATA_WIDTH = 8 and DATA_WIDTH = 32) generate

    udp_frame_widen_8_32_inst: entity work.axis_width_widen
      generic map(
        NBYTES => (DATA_WIDTH/8)
      )
      port map (
        clk       => clk,
        reset     => reset,

        s_axis_tdata  => s_udp_payload_axis_tdata,
        s_axis_tvalid => s_udp_payload_axis_tvalid,
        s_axis_tready => s_udp_payload_axis_tready,
        s_axis_tlast  => s_udp_payload_axis_tlast,

        m_axis_tdata  => axis_tdata,
        m_axis_tkeep  => axis_tkeep,
        m_axis_tvalid => axis_tvalid,
        m_axis_tready => axis_tready,
        m_axis_tlast  => axis_tlast
      );

      axis_tuser <= '0';

    udp_frame_parser_32_32_inst : entity work.udp_frame_parser32
      generic map(
        DATA_WIDTH => DATA_WIDTH,
        KEEP_WIDTH => KEEP_WIDTH
      )
      port map(
        clk                       => clk,
        reset                     => reset,
        local_mac_addr            => local_mac_addr,
        local_ip_addr             => local_ip_addr,
        s_udp_hdr_valid           => s_udp_hdr_valid,
        s_udp_hdr_ready           => s_udp_hdr_ready,
        s_udp_eth_dest_mac        => s_udp_eth_dest_mac,
        s_udp_eth_src_mac         => s_udp_eth_src_mac,
        s_udp_eth_type            => s_udp_eth_type,
        s_udp_ip_version          => s_udp_ip_version,
        s_udp_ip_ihl              => s_udp_ip_ihl,
        s_udp_ip_dscp             => s_udp_ip_dscp,
        s_udp_ip_ecn              => s_udp_ip_ecn,
        s_udp_ip_length           => s_udp_ip_length,
        s_udp_ip_identification   => s_udp_ip_identification,
        s_udp_ip_flags            => s_udp_ip_flags,
        s_udp_ip_fragment_offset  => s_udp_ip_fragment_offset,
        s_udp_ip_ttl              => s_udp_ip_ttl,
        s_udp_ip_protocol         => s_udp_ip_protocol,
        s_udp_ip_header_checksum  => s_udp_ip_header_checksum,
        s_udp_ip_source_ip        => s_udp_ip_source_ip,
        s_udp_ip_dest_ip          => s_udp_ip_dest_ip,
        s_udp_source_port         => s_udp_source_port,
        s_udp_dest_port           => s_udp_dest_port,
        s_udp_length              => s_udp_length,
        s_udp_checksum            => s_udp_checksum,

        s_udp_payload_axis_tdata  => axis_tdata,
        s_udp_payload_axis_tkeep  => axis_tkeep,
        s_udp_payload_axis_tvalid => axis_tvalid,
        s_udp_payload_axis_tready => axis_tready,
        s_udp_payload_axis_tlast  => axis_tlast,
        s_udp_payload_axis_tuser  => axis_tuser,

        m_rx_axis_tdata           => m_rx_axis_tdata,
        m_rx_axis_tkeep           => m_rx_axis_tkeep,
        m_rx_axis_tvalid          => m_rx_axis_tvalid,
        m_rx_axis_tready          => m_rx_axis_tready,
        m_rx_axis_tlast           => m_rx_axis_tlast,
        udp_dest_port             => udp_dest_port
      );
  end generate udp_frame_parser8_32_gen;

  -- -----------------------------------------------------------------------------
  udp_frame_parser32_32_gen: if (UDP_DATA_WIDTH = 32 and DATA_WIDTH = 32) generate

    udp_frame_parser_32_32_inst : entity work.udp_frame_parser32     
      generic map(
        DATA_WIDTH => DATA_WIDTH,
        KEEP_WIDTH => KEEP_WIDTH
      )
      port map(
        clk                       => clk,
        reset                     => reset,
        local_mac_addr            => local_mac_addr,
        local_ip_addr             => local_ip_addr,
        s_udp_hdr_valid           => s_udp_hdr_valid,
        s_udp_hdr_ready           => s_udp_hdr_ready,
        s_udp_eth_dest_mac        => s_udp_eth_dest_mac,
        s_udp_eth_src_mac         => s_udp_eth_src_mac,
        s_udp_eth_type            => s_udp_eth_type,
        s_udp_ip_version          => s_udp_ip_version,
        s_udp_ip_ihl              => s_udp_ip_ihl,
        s_udp_ip_dscp             => s_udp_ip_dscp,
        s_udp_ip_ecn              => s_udp_ip_ecn,
        s_udp_ip_length           => s_udp_ip_length,
        s_udp_ip_identification   => s_udp_ip_identification,
        s_udp_ip_flags            => s_udp_ip_flags,
        s_udp_ip_fragment_offset  => s_udp_ip_fragment_offset,
        s_udp_ip_ttl              => s_udp_ip_ttl,
        s_udp_ip_protocol         => s_udp_ip_protocol,
        s_udp_ip_header_checksum  => s_udp_ip_header_checksum,
        s_udp_ip_source_ip        => s_udp_ip_source_ip,
        s_udp_ip_dest_ip          => s_udp_ip_dest_ip,
        s_udp_source_port         => s_udp_source_port,
        s_udp_dest_port           => s_udp_dest_port,
        s_udp_length              => s_udp_length,
        s_udp_checksum            => s_udp_checksum,

        s_udp_payload_axis_tdata  => s_udp_payload_axis_tdata,
        s_udp_payload_axis_tkeep  => s_udp_payload_axis_tkeep,
        s_udp_payload_axis_tvalid => s_udp_payload_axis_tvalid,
        s_udp_payload_axis_tready => s_udp_payload_axis_tready,
        s_udp_payload_axis_tlast  => s_udp_payload_axis_tlast,
        s_udp_payload_axis_tuser  => s_udp_payload_axis_tuser,

        m_rx_axis_tdata           => m_rx_axis_tdata,
        m_rx_axis_tkeep           => m_rx_axis_tkeep,
        m_rx_axis_tvalid          => m_rx_axis_tvalid,
        m_rx_axis_tready          => m_rx_axis_tready,
        m_rx_axis_tlast           => m_rx_axis_tlast,
        udp_dest_port             => udp_dest_port
      );
  end generate udp_frame_parser32_32_gen;

  -- -----------------------------------------------------------------------------
  udp_frame_parser64_64_gen: if (UDP_DATA_WIDTH = 64 and DATA_WIDTH = 64) generate

    udp_frame_parser_64_64_inst : entity work.udp_frame_parser64
      generic map(
        DATA_WIDTH => DATA_WIDTH,
        KEEP_WIDTH => KEEP_WIDTH
      )
      port map(
        clk                       => clk,
        reset                     => reset,
        local_mac_addr            => local_mac_addr,
        local_ip_addr             => local_ip_addr,
        s_udp_hdr_valid           => s_udp_hdr_valid,
        s_udp_hdr_ready           => s_udp_hdr_ready,
        s_udp_eth_dest_mac        => s_udp_eth_dest_mac,
        s_udp_eth_src_mac         => s_udp_eth_src_mac,
        s_udp_eth_type            => s_udp_eth_type,
        s_udp_ip_version          => s_udp_ip_version,
        s_udp_ip_ihl              => s_udp_ip_ihl,
        s_udp_ip_dscp             => s_udp_ip_dscp,
        s_udp_ip_ecn              => s_udp_ip_ecn,
        s_udp_ip_length           => s_udp_ip_length,
        s_udp_ip_identification   => s_udp_ip_identification,
        s_udp_ip_flags            => s_udp_ip_flags,
        s_udp_ip_fragment_offset  => s_udp_ip_fragment_offset,
        s_udp_ip_ttl              => s_udp_ip_ttl,
        s_udp_ip_protocol         => s_udp_ip_protocol,
        s_udp_ip_header_checksum  => s_udp_ip_header_checksum,
        s_udp_ip_source_ip        => s_udp_ip_source_ip,
        s_udp_ip_dest_ip          => s_udp_ip_dest_ip,
        s_udp_source_port         => s_udp_source_port,
        s_udp_dest_port           => s_udp_dest_port,
        s_udp_length              => s_udp_length,
        s_udp_checksum            => s_udp_checksum,

        s_udp_payload_axis_tdata  => s_udp_payload_axis_tdata,
        s_udp_payload_axis_tkeep  => s_udp_payload_axis_tkeep,
        s_udp_payload_axis_tvalid => s_udp_payload_axis_tvalid,
        s_udp_payload_axis_tready => s_udp_payload_axis_tready,
        s_udp_payload_axis_tlast  => s_udp_payload_axis_tlast,
        s_udp_payload_axis_tuser  => s_udp_payload_axis_tuser,

        m_rx_axis_tdata           => m_rx_axis_tdata,
        m_rx_axis_tkeep           => m_rx_axis_tkeep,
        m_rx_axis_tvalid          => m_rx_axis_tvalid,
        m_rx_axis_tready          => m_rx_axis_tready,
        m_rx_axis_tlast           => m_rx_axis_tlast,
        udp_dest_port             => udp_dest_port
      );
  end generate udp_frame_parser64_64_gen;

end rtl;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------