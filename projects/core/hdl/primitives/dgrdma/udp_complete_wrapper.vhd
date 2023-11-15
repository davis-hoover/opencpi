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
library dgrdma;

entity udp_complete_wrapper is
  generic (
    DATA_WIDTH                      : natural := 64; -- width in bits    
    KEEP_WIDTH                      : natural := 8;    
    UDP_CHECKSUM_GEN_ENABLE         : natural := 1;
    UDP_CHECKSUM_PAYLOAD_FIFO_DEPTH : natural := 2048;
    UDP_CHECKSUM_HEADER_FIFO_DEPTH  : natural := 8
  );
  port (
    clk : in std_logic;    
    rst : in std_logic;
    
    -- Ethernet frame input
    s_eth_hdr_valid           : in std_logic;
    s_eth_hdr_ready           : out std_logic;
    s_eth_dest_mac            : in std_logic_vector(47 downto 0);
    s_eth_src_mac             : in std_logic_vector(47 downto 0);
    s_eth_type                : in std_logic_vector(15 downto 0);
    s_eth_payload_axis_tdata  : in std_logic_vector(DATA_WIDTH-1 downto 0);
    s_eth_payload_axis_tkeep  : in std_logic_vector(KEEP_WIDTH-1 downto 0);
    s_eth_payload_axis_tvalid : in std_logic;
    s_eth_payload_axis_tready : out std_logic;
    s_eth_payload_axis_tlast  : in std_logic;
    s_eth_payload_axis_tuser  : in std_logic;

    -- Ethernet frame output
    m_eth_hdr_valid           : out std_logic;
    m_eth_hdr_ready           : in std_logic;
    m_eth_dest_mac            : out std_logic_vector(47 downto 0);
    m_eth_src_mac             : out std_logic_vector(47 downto 0);
    m_eth_type                : out std_logic_vector(15 downto 0);
    m_eth_payload_axis_tdata  : out std_logic_vector(DATA_WIDTH-1 downto 0);
    m_eth_payload_axis_tkeep  : out std_logic_vector(KEEP_WIDTH-1 downto 0);
    m_eth_payload_axis_tvalid : out std_logic;
    m_eth_payload_axis_tready : in std_logic;
    m_eth_payload_axis_tlast  : out std_logic;
    m_eth_payload_axis_tuser  : out std_logic;

    -- IP input
    s_ip_hdr_valid           : in std_logic;
    s_ip_hdr_ready           : out std_logic;
    s_ip_dscp                : in std_logic_vector(5 downto 0);
    s_ip_ecn                 : in std_logic_vector(1 downto 0);
    s_ip_length              : in std_logic_vector(15 downto 0);
    s_ip_ttl                 : in std_logic_vector(7 downto 0);
    s_ip_protocol            : in std_logic_vector(7 downto 0);
    s_ip_source_ip           : in std_logic_vector(31 downto 0);
    s_ip_dest_ip             : in std_logic_vector(31 downto 0);
    s_ip_payload_axis_tdata  : in std_logic_vector(DATA_WIDTH-1 downto 0);
    s_ip_payload_axis_tkeep  : in std_logic_vector(KEEP_WIDTH-1 downto 0);
    s_ip_payload_axis_tvalid : in std_logic;
    s_ip_payload_axis_tready : out std_logic;
    s_ip_payload_axis_tlast  : in std_logic;
    s_ip_payload_axis_tuser  : in std_logic;

    -- IP output
    m_ip_hdr_valid           : out std_logic;
    m_ip_hdr_ready           : in std_logic;
    m_ip_eth_dest_mac        : out std_logic_vector(47 downto 0);
    m_ip_eth_src_mac         : out std_logic_vector(47 downto 0);
    m_ip_eth_type            : out std_logic_vector(15 downto 0);
    m_ip_version             : out std_logic_vector(3 downto 0);
    m_ip_ihl                 : out std_logic_vector(3 downto 0);
    m_ip_dscp                : out std_logic_vector(5 downto 0);
    m_ip_ecn                 : out std_logic_vector(1 downto 0);
    m_ip_length              : out std_logic_vector(15 downto 0);
    m_ip_identification      : out std_logic_vector(15 downto 0);
    m_ip_flags               : out std_logic_vector(2 downto 0);
    m_ip_fragment_offset     : out std_logic_vector(12 downto 0);
    m_ip_ttl                 : out std_logic_vector(7 downto 0);
    m_ip_protocol            : out std_logic_vector(7 downto 0);
    m_ip_header_checksum     : out std_logic_vector(15 downto 0);
    m_ip_source_ip           : out std_logic_vector(31 downto 0);
    m_ip_dest_ip             : out std_logic_vector(31 downto 0);
    m_ip_payload_axis_tdata  : out std_logic_vector(DATA_WIDTH-1 downto 0);
    m_ip_payload_axis_tkeep  : out std_logic_vector(KEEP_WIDTH-1 downto 0);
    m_ip_payload_axis_tvalid : out std_logic;
    m_ip_payload_axis_tready : in std_logic;
    m_ip_payload_axis_tlast  : out std_logic;
    m_ip_payload_axis_tuser  : out std_logic;

    -- UDP input
    s_udp_hdr_valid           : in std_logic;
    s_udp_hdr_ready           : out std_logic;
    s_udp_ip_dscp             : in std_logic_vector(5 downto 0);
    s_udp_ip_ecn              : in std_logic_vector(1 downto 0);
    s_udp_ip_ttl              : in std_logic_vector(7 downto 0);
    s_udp_ip_source_ip        : in std_logic_vector(31 downto 0);
    s_udp_ip_dest_ip          : in std_logic_vector(31 downto 0);
    s_udp_source_port         : in std_logic_vector(15 downto 0);
    s_udp_dest_port           : in std_logic_vector(15 downto 0);
    s_udp_length              : in std_logic_vector(15 downto 0);
    s_udp_checksum            : in std_logic_vector(15 downto 0);
    s_udp_payload_axis_tdata  : in std_logic_vector(DATA_WIDTH-1 downto 0);
    s_udp_payload_axis_tkeep  : in std_logic_vector(KEEP_WIDTH-1 downto 0);
    s_udp_payload_axis_tvalid : in std_logic;
    s_udp_payload_axis_tready : out std_logic;
    s_udp_payload_axis_tlast  : in std_logic;
    s_udp_payload_axis_tuser  : in std_logic;

    -- UDP output
    m_udp_hdr_valid           : out std_logic;
    m_udp_hdr_ready           : in std_logic;
    m_udp_eth_dest_mac        : out std_logic_vector(47 downto 0);
    m_udp_eth_src_mac         : out std_logic_vector(47 downto 0);
    m_udp_eth_type            : out std_logic_vector(15 downto 0);
    m_udp_ip_version          : out std_logic_vector(3 downto 0);
    m_udp_ip_ihl              : out std_logic_vector(3 downto 0);
    m_udp_ip_dscp             : out std_logic_vector(5 downto 0);
    m_udp_ip_ecn              : out std_logic_vector(1 downto 0);
    m_udp_ip_length           : out std_logic_vector(15 downto 0);
    m_udp_ip_identification   : out std_logic_vector(15 downto 0);
    m_udp_ip_flags            : out std_logic_vector(2 downto 0);
    m_udp_ip_fragment_offset  : out std_logic_vector(12 downto 0);
    m_udp_ip_ttl              : out std_logic_vector(7 downto 0);
    m_udp_ip_protocol         : out std_logic_vector(7 downto 0);
    m_udp_ip_header_checksum  : out std_logic_vector(15 downto 0);
    m_udp_ip_source_ip        : out std_logic_vector(31 downto 0);
    m_udp_ip_dest_ip          : out std_logic_vector(31 downto 0);
    m_udp_source_port         : out std_logic_vector(15 downto 0);
    m_udp_dest_port           : out std_logic_vector(15 downto 0);
    m_udp_length              : out std_logic_vector(15 downto 0);
    m_udp_checksum            : out std_logic_vector(15 downto 0);
    m_udp_payload_axis_tdata  : out std_logic_vector(DATA_WIDTH-1 downto 0);
    m_udp_payload_axis_tkeep  : out std_logic_vector(KEEP_WIDTH-1 downto 0);
    m_udp_payload_axis_tvalid : out std_logic;
    m_udp_payload_axis_tready : in std_logic;
    m_udp_payload_axis_tlast  : out std_logic;
    m_udp_payload_axis_tuser  : out std_logic;

    -- Status
    ip_rx_busy                             : out std_logic;
    ip_tx_busy                             : out std_logic;
    udp_rx_busy                            : out std_logic;
    udp_tx_busy                            : out std_logic;
    ip_rx_error_header_early_termination   : out std_logic;
    ip_rx_error_payload_early_termination  : out std_logic;
    ip_rx_error_invalid_header             : out std_logic;
    ip_rx_error_invalid_checksum           : out std_logic;
    ip_tx_error_payload_early_termination  : out std_logic;
    ip_tx_error_arp_failed                 : out std_logic;
    udp_rx_error_header_early_termination  : out std_logic;
    udp_rx_error_payload_early_termination : out std_logic;
    udp_tx_error_payload_early_termination : out std_logic;

    -- Configuration
    local_mac       : in std_logic_vector(47 downto 0);
    local_ip        : in std_logic_vector(31 downto 0);
    gateway_ip      : in std_logic_vector(31 downto 0);
    subnet_mask     : in std_logic_vector(31 downto 0);
    clear_arp_cache : in std_logic    
  );
end entity udp_complete_wrapper;

architecture rtl of udp_complete_wrapper is
begin

-- this implementation supports either 8-bit or 64-bit data only 
assert (DATA_WIDTH = 8 or DATA_WIDTH = 64)
  report "Unsupported SDP width!"
  severity error;

-- --------------------------------------------------------------------
udp_8_gen: if DATA_WIDTH = 8 generate
  udp_inst : dgrdma.verilog_ethernet.udp_complete
  generic map (
      UDP_CHECKSUM_GEN_ENABLE => UDP_CHECKSUM_GEN_ENABLE,
      UDP_CHECKSUM_PAYLOAD_FIFO_DEPTH => UDP_CHECKSUM_PAYLOAD_FIFO_DEPTH,
      UDP_CHECKSUM_HEADER_FIFO_DEPTH => UDP_CHECKSUM_HEADER_FIFO_DEPTH      
    )
    port map (   
      -- clock and reset   
      clk => clk,
      rst => rst,
    
      -- Ethernet frame input
      s_eth_hdr_valid => s_eth_hdr_valid,
      s_eth_hdr_ready => s_eth_hdr_ready,
      s_eth_dest_mac => s_eth_dest_mac,
      s_eth_src_mac => s_eth_src_mac,
      s_eth_type => s_eth_type,
      s_eth_payload_axis_tdata => s_eth_payload_axis_tdata,      
      s_eth_payload_axis_tvalid => s_eth_payload_axis_tvalid,
      s_eth_payload_axis_tready => s_eth_payload_axis_tready,
      s_eth_payload_axis_tlast => s_eth_payload_axis_tlast,
      s_eth_payload_axis_tuser => s_eth_payload_axis_tuser,
        
      -- Ethernet frame output
      m_eth_hdr_valid => m_eth_hdr_valid,
      m_eth_hdr_ready => m_eth_hdr_ready,
      m_eth_dest_mac => m_eth_dest_mac,
      m_eth_src_mac => m_eth_src_mac,
      m_eth_type => m_eth_type,
      m_eth_payload_axis_tdata => m_eth_payload_axis_tdata,      
      m_eth_payload_axis_tvalid => m_eth_payload_axis_tvalid,
      m_eth_payload_axis_tready => m_eth_payload_axis_tready,
      m_eth_payload_axis_tlast => m_eth_payload_axis_tlast,
      m_eth_payload_axis_tuser => m_eth_payload_axis_tuser,
    
      -- IP input
      s_ip_hdr_valid => s_ip_hdr_valid,
      s_ip_hdr_ready => s_ip_hdr_ready,
      s_ip_dscp => s_ip_dscp,
      s_ip_ecn => s_ip_ecn,
      s_ip_length => s_ip_length,
      s_ip_ttl => s_ip_ttl,
      s_ip_protocol => s_ip_protocol,
      s_ip_source_ip => s_ip_source_ip,
      s_ip_dest_ip => s_ip_dest_ip,
      s_ip_payload_axis_tdata => s_ip_payload_axis_tdata,      
      s_ip_payload_axis_tvalid => s_ip_payload_axis_tvalid,
      s_ip_payload_axis_tready => s_ip_payload_axis_tready,
      s_ip_payload_axis_tlast => s_ip_payload_axis_tlast,
      s_ip_payload_axis_tuser => s_ip_payload_axis_tuser,
    
      -- IP output
      m_ip_hdr_valid => m_ip_hdr_valid,
      m_ip_hdr_ready => m_ip_hdr_ready,
      m_ip_eth_dest_mac => m_ip_eth_dest_mac,
      m_ip_eth_src_mac => m_ip_eth_src_mac,
      m_ip_eth_type => m_ip_eth_type,
      m_ip_version => m_ip_version,
      m_ip_ihl => m_ip_ihl,
      m_ip_dscp => m_ip_dscp,
      m_ip_ecn => m_ip_ecn,
      m_ip_length => m_ip_length,
      m_ip_identification => m_ip_identification,
      m_ip_flags => m_ip_flags,
      m_ip_fragment_offset => m_ip_fragment_offset,
      m_ip_ttl => m_ip_ttl,
      m_ip_protocol => m_ip_protocol,
      m_ip_header_checksum => m_ip_header_checksum,
      m_ip_source_ip => m_ip_source_ip,
      m_ip_dest_ip => m_ip_dest_ip,
      m_ip_payload_axis_tdata => m_ip_payload_axis_tdata,      
      m_ip_payload_axis_tvalid => m_ip_payload_axis_tvalid,
      m_ip_payload_axis_tready => m_ip_payload_axis_tready,
      m_ip_payload_axis_tlast => m_ip_payload_axis_tlast,
      m_ip_payload_axis_tuser => m_ip_payload_axis_tuser,
    
      -- UDP input
      s_udp_hdr_valid => s_udp_hdr_valid,
      s_udp_hdr_ready => s_udp_hdr_ready,
      s_udp_ip_dscp => s_udp_ip_dscp,
      s_udp_ip_ecn => s_udp_ip_ecn,
      s_udp_ip_ttl => s_udp_ip_ttl,
      s_udp_ip_source_ip => s_udp_ip_source_ip,
      s_udp_ip_dest_ip => s_udp_ip_dest_ip,
      s_udp_source_port => s_udp_source_port,
      s_udp_dest_port => s_udp_dest_port,
      s_udp_length => s_udp_length,
      s_udp_checksum => s_udp_checksum,
      s_udp_payload_axis_tdata => s_udp_payload_axis_tdata,      
      s_udp_payload_axis_tvalid => s_udp_payload_axis_tvalid,
      s_udp_payload_axis_tready => s_udp_payload_axis_tready,
      s_udp_payload_axis_tlast => s_udp_payload_axis_tlast,
      s_udp_payload_axis_tuser => s_udp_payload_axis_tuser,
    
      -- UDP output
      m_udp_hdr_valid => m_udp_hdr_valid,
      m_udp_hdr_ready => m_udp_hdr_ready,
      m_udp_eth_dest_mac => m_udp_eth_dest_mac,
      m_udp_eth_src_mac => m_udp_eth_src_mac,
      m_udp_eth_type => m_udp_eth_type,
      m_udp_ip_version => m_udp_ip_version,
      m_udp_ip_ihl => m_udp_ip_ihl,
      m_udp_ip_dscp => m_udp_ip_dscp,
      m_udp_ip_ecn => m_udp_ip_ecn,
      m_udp_ip_length => m_udp_ip_length,
      m_udp_ip_identification => m_udp_ip_identification,
      m_udp_ip_flags => m_udp_ip_flags,
      m_udp_ip_fragment_offset => m_udp_ip_fragment_offset,
      m_udp_ip_ttl => m_udp_ip_ttl,
      m_udp_ip_protocol => m_udp_ip_protocol,
      m_udp_ip_header_checksum => m_udp_ip_header_checksum,
      m_udp_ip_source_ip => m_udp_ip_source_ip,
      m_udp_ip_dest_ip => m_udp_ip_dest_ip,
      m_udp_source_port => m_udp_source_port,
      m_udp_dest_port => m_udp_dest_port,
      m_udp_length => m_udp_length,
      m_udp_checksum => m_udp_checksum,
      m_udp_payload_axis_tdata => m_udp_payload_axis_tdata,      
      m_udp_payload_axis_tvalid => m_udp_payload_axis_tvalid,
      m_udp_payload_axis_tready => m_udp_payload_axis_tready,
      m_udp_payload_axis_tlast => m_udp_payload_axis_tlast,
      m_udp_payload_axis_tuser => m_udp_payload_axis_tuser,

      -- Status
      ip_rx_busy => ip_rx_busy,
      ip_tx_busy => ip_tx_busy,
      udp_rx_busy => udp_rx_busy,
      udp_tx_busy => udp_tx_busy,
      ip_rx_error_header_early_termination => ip_rx_error_header_early_termination,
      ip_rx_error_payload_early_termination => ip_rx_error_payload_early_termination,
      ip_rx_error_invalid_header => ip_rx_error_invalid_header,
      ip_rx_error_invalid_checksum => ip_rx_error_invalid_checksum,
      ip_tx_error_payload_early_termination => ip_tx_error_payload_early_termination,
      ip_tx_error_arp_failed => ip_tx_error_arp_failed,
      udp_rx_error_header_early_termination => udp_rx_error_header_early_termination,
      udp_rx_error_payload_early_termination => udp_rx_error_payload_early_termination,
      udp_tx_error_payload_early_termination => udp_tx_error_payload_early_termination,

      -- Configuration
      local_mac => local_mac,
      local_ip => local_ip,
      gateway_ip => gateway_ip,
      subnet_mask => subnet_mask,
      clear_arp_cache => clear_arp_cache
    ); 

    -- keep signals aren't used with 8-bit data path
    m_eth_payload_axis_tkeep <= (others => '1');
    m_ip_payload_axis_tkeep <= (others => '1');
    m_udp_payload_axis_tkeep <= (others => '1');

end generate udp_8_gen;

-- --------------------------------------------------------------------
udp_64_gen: if DATA_WIDTH = 64 generate
  udp_inst : dgrdma.verilog_ethernet.udp_complete_64
    generic map (
      UDP_CHECKSUM_GEN_ENABLE => UDP_CHECKSUM_GEN_ENABLE,
      UDP_CHECKSUM_PAYLOAD_FIFO_DEPTH => UDP_CHECKSUM_PAYLOAD_FIFO_DEPTH,
      UDP_CHECKSUM_HEADER_FIFO_DEPTH => UDP_CHECKSUM_HEADER_FIFO_DEPTH      
    )
    port map (   
      -- clock and reset   
      clk => clk,
      rst => rst,
    
      -- Ethernet frame input
      s_eth_hdr_valid => s_eth_hdr_valid,
      s_eth_hdr_ready => s_eth_hdr_ready,
      s_eth_dest_mac => s_eth_dest_mac,
      s_eth_src_mac => s_eth_src_mac,
      s_eth_type => s_eth_type,
      s_eth_payload_axis_tdata => s_eth_payload_axis_tdata,
      s_eth_payload_axis_tkeep => s_eth_payload_axis_tkeep,
      s_eth_payload_axis_tvalid => s_eth_payload_axis_tvalid,
      s_eth_payload_axis_tready => s_eth_payload_axis_tready,
      s_eth_payload_axis_tlast => s_eth_payload_axis_tlast,
      s_eth_payload_axis_tuser => s_eth_payload_axis_tuser,
        
      -- Ethernet frame output
      m_eth_hdr_valid => m_eth_hdr_valid,
      m_eth_hdr_ready => m_eth_hdr_ready,
      m_eth_dest_mac => m_eth_dest_mac,
      m_eth_src_mac => m_eth_src_mac,
      m_eth_type => m_eth_type,
      m_eth_payload_axis_tdata => m_eth_payload_axis_tdata,
      m_eth_payload_axis_tkeep => m_eth_payload_axis_tkeep,
      m_eth_payload_axis_tvalid => m_eth_payload_axis_tvalid,
      m_eth_payload_axis_tready => m_eth_payload_axis_tready,
      m_eth_payload_axis_tlast => m_eth_payload_axis_tlast,
      m_eth_payload_axis_tuser => m_eth_payload_axis_tuser,
    
      -- IP input
      s_ip_hdr_valid => s_ip_hdr_valid,
      s_ip_hdr_ready => s_ip_hdr_ready,
      s_ip_dscp => s_ip_dscp,
      s_ip_ecn => s_ip_ecn,
      s_ip_length => s_ip_length,
      s_ip_ttl => s_ip_ttl,
      s_ip_protocol => s_ip_protocol,
      s_ip_source_ip => s_ip_source_ip,
      s_ip_dest_ip => s_ip_dest_ip,
      s_ip_payload_axis_tdata => s_ip_payload_axis_tdata,
      s_ip_payload_axis_tkeep => s_ip_payload_axis_tkeep,
      s_ip_payload_axis_tvalid => s_ip_payload_axis_tvalid,
      s_ip_payload_axis_tready => s_ip_payload_axis_tready,
      s_ip_payload_axis_tlast => s_ip_payload_axis_tlast,
      s_ip_payload_axis_tuser => s_ip_payload_axis_tuser,
    
      -- IP output
      m_ip_hdr_valid => m_ip_hdr_valid,
      m_ip_hdr_ready => m_ip_hdr_ready,
      m_ip_eth_dest_mac => m_ip_eth_dest_mac,
      m_ip_eth_src_mac => m_ip_eth_src_mac,
      m_ip_eth_type => m_ip_eth_type,
      m_ip_version => m_ip_version,
      m_ip_ihl => m_ip_ihl,
      m_ip_dscp => m_ip_dscp,
      m_ip_ecn => m_ip_ecn,
      m_ip_length => m_ip_length,
      m_ip_identification => m_ip_identification,
      m_ip_flags => m_ip_flags,
      m_ip_fragment_offset => m_ip_fragment_offset,
      m_ip_ttl => m_ip_ttl,
      m_ip_protocol => m_ip_protocol,
      m_ip_header_checksum => m_ip_header_checksum,
      m_ip_source_ip => m_ip_source_ip,
      m_ip_dest_ip => m_ip_dest_ip,
      m_ip_payload_axis_tdata => m_ip_payload_axis_tdata,
      m_ip_payload_axis_tkeep => m_ip_payload_axis_tkeep,
      m_ip_payload_axis_tvalid => m_ip_payload_axis_tvalid,
      m_ip_payload_axis_tready => m_ip_payload_axis_tready,
      m_ip_payload_axis_tlast => m_ip_payload_axis_tlast,
      m_ip_payload_axis_tuser => m_ip_payload_axis_tuser,
    
      -- UDP input
      s_udp_hdr_valid => s_udp_hdr_valid,
      s_udp_hdr_ready => s_udp_hdr_ready,
      s_udp_ip_dscp => s_udp_ip_dscp,
      s_udp_ip_ecn => s_udp_ip_ecn,
      s_udp_ip_ttl => s_udp_ip_ttl,
      s_udp_ip_source_ip => s_udp_ip_source_ip,
      s_udp_ip_dest_ip => s_udp_ip_dest_ip,
      s_udp_source_port => s_udp_source_port,
      s_udp_dest_port => s_udp_dest_port,
      s_udp_length => s_udp_length,
      s_udp_checksum => s_udp_checksum,
      s_udp_payload_axis_tdata => s_udp_payload_axis_tdata,
      s_udp_payload_axis_tkeep => s_udp_payload_axis_tkeep,
      s_udp_payload_axis_tvalid => s_udp_payload_axis_tvalid,
      s_udp_payload_axis_tready => s_udp_payload_axis_tready,
      s_udp_payload_axis_tlast => s_udp_payload_axis_tlast,
      s_udp_payload_axis_tuser => s_udp_payload_axis_tuser,
    
      -- UDP output
      m_udp_hdr_valid => m_udp_hdr_valid,
      m_udp_hdr_ready => m_udp_hdr_ready,
      m_udp_eth_dest_mac => m_udp_eth_dest_mac,
      m_udp_eth_src_mac => m_udp_eth_src_mac,
      m_udp_eth_type => m_udp_eth_type,
      m_udp_ip_version => m_udp_ip_version,
      m_udp_ip_ihl => m_udp_ip_ihl,
      m_udp_ip_dscp => m_udp_ip_dscp,
      m_udp_ip_ecn => m_udp_ip_ecn,
      m_udp_ip_length => m_udp_ip_length,
      m_udp_ip_identification => m_udp_ip_identification,
      m_udp_ip_flags => m_udp_ip_flags,
      m_udp_ip_fragment_offset => m_udp_ip_fragment_offset,
      m_udp_ip_ttl => m_udp_ip_ttl,
      m_udp_ip_protocol => m_udp_ip_protocol,
      m_udp_ip_header_checksum => m_udp_ip_header_checksum,
      m_udp_ip_source_ip => m_udp_ip_source_ip,
      m_udp_ip_dest_ip => m_udp_ip_dest_ip,
      m_udp_source_port => m_udp_source_port,
      m_udp_dest_port => m_udp_dest_port,
      m_udp_length => m_udp_length,
      m_udp_checksum => m_udp_checksum,
      m_udp_payload_axis_tdata => m_udp_payload_axis_tdata,
      m_udp_payload_axis_tkeep => m_udp_payload_axis_tkeep,
      m_udp_payload_axis_tvalid => m_udp_payload_axis_tvalid,
      m_udp_payload_axis_tready => m_udp_payload_axis_tready,
      m_udp_payload_axis_tlast => m_udp_payload_axis_tlast,
      m_udp_payload_axis_tuser => m_udp_payload_axis_tuser,

      -- Status
      ip_rx_busy => ip_rx_busy,
      ip_tx_busy => ip_tx_busy,
      udp_rx_busy => udp_rx_busy,
      udp_tx_busy => udp_tx_busy,
      ip_rx_error_header_early_termination => ip_rx_error_header_early_termination,
      ip_rx_error_payload_early_termination => ip_rx_error_payload_early_termination,
      ip_rx_error_invalid_header => ip_rx_error_invalid_header,
      ip_rx_error_invalid_checksum => ip_rx_error_invalid_checksum,
      ip_tx_error_payload_early_termination => ip_tx_error_payload_early_termination,
      ip_tx_error_arp_failed => ip_tx_error_arp_failed,
      udp_rx_error_header_early_termination => udp_rx_error_header_early_termination,
      udp_rx_error_payload_early_termination => udp_rx_error_payload_early_termination,
      udp_tx_error_payload_early_termination => udp_tx_error_payload_early_termination,

      -- Configuration
      local_mac => local_mac,
      local_ip => local_ip,
      gateway_ip => gateway_ip,
      subnet_mask => subnet_mask,
      clear_arp_cache => clear_arp_cache
    ); 
  end generate udp_64_gen;

end rtl;
