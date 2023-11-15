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

entity udp_frame_generator is
  generic (
    UDP_DATA_WIDTH : natural := 64;
    UDP_KEEP_WIDTH : natural := 8;
    DATA_WIDTH : natural := 64;
    KEEP_WIDTH : natural := 8
  );
  port(
    clk              : in std_logic;
    reset            : in std_logic;

    s_tx_axis_tdata  : in std_logic_vector(DATA_WIDTH-1 downto 0);
    s_tx_axis_tkeep  : in std_logic_vector(KEEP_WIDTH-1 downto 0);
    s_tx_axis_tvalid : in std_logic;
    s_tx_axis_tready : out std_logic;
    s_tx_axis_tlast  : in std_logic;
    
    local_ip_addr    : in std_logic_vector(31 downto 0);
    tx_hdr_type      : in std_logic_vector(15 downto 0);

    m_udp_hdr_valid           : out std_logic;
    m_udp_hdr_ready           : in std_logic;
    m_udp_ip_dscp             : out std_logic_vector(5 downto 0);
    m_udp_ip_ecn              : out std_logic_vector(1 downto 0);
    m_udp_ip_ttl              : out std_logic_vector(7 downto 0);
    m_udp_ip_source_ip        : out std_logic_vector(31 downto 0);
    m_udp_ip_dest_ip          : out std_logic_vector(31 downto 0);
    m_udp_source_port         : out std_logic_vector(15 downto 0);
    m_udp_dest_port           : out std_logic_vector(15 downto 0);
    m_udp_length              : out std_logic_vector(15 downto 0);
    m_udp_checksum            : out std_logic_vector(15 downto 0);

    m_udp_payload_axis_tdata  : out std_logic_vector(UDP_DATA_WIDTH-1 downto 0);
    m_udp_payload_axis_tkeep  : out std_logic_vector(UDP_KEEP_WIDTH-1 downto 0);
    m_udp_payload_axis_tvalid : out std_logic;
    m_udp_payload_axis_tready : in std_logic;
    m_udp_payload_axis_tlast  : out std_logic;
    m_udp_payload_axis_tuser  : out std_logic
  );
end entity;

architecture rtl of udp_frame_generator is

signal axis_tdata  : std_logic_vector(DATA_WIDTH-1 downto 0);
signal axis_tkeep  : std_logic_vector(KEEP_WIDTH-1 downto 0);
signal axis_tvalid : std_logic;
signal axis_tready : std_logic;
signal axis_tlast  : std_logic;

begin

  -- this implementation supports these combinations of UDP payload data width
  -- and AXI-Stream width  
  assert ((UDP_DATA_WIDTH = 8  and DATA_WIDTH = 32) or 
          (UDP_DATA_WIDTH = 32 and DATA_WIDTH = 32) or
          (UDP_DATA_WIDTH = 64 and DATA_WIDTH = 64))
    report "Unsupported SDP width!"
    severity error;

  -- -----------------------------------------------------------------------------
  udp_frame_generator_8_32_gen: if (UDP_DATA_WIDTH = 8 and DATA_WIDTH = 32) generate

    udp_frame_generator_32_32_inst : entity work.udp_frame_generator32
      generic map(
        DATA_WIDTH => DATA_WIDTH,
        KEEP_WIDTH => KEEP_WIDTH
      )
      port map(
        clk                       => clk,   
        reset                     => reset,
        s_tx_axis_tdata           => s_tx_axis_tdata, 
        s_tx_axis_tkeep           => s_tx_axis_tkeep,
        s_tx_axis_tvalid          => s_tx_axis_tvalid,
        s_tx_axis_tready          => s_tx_axis_tready,
        s_tx_axis_tlast           => s_tx_axis_tlast,

        local_ip_addr             => local_ip_addr,
        tx_hdr_type               => tx_hdr_type,

        m_udp_hdr_valid           => m_udp_hdr_valid,    
        m_udp_hdr_ready           => m_udp_hdr_ready,   
        m_udp_ip_dscp             => m_udp_ip_dscp,    
        m_udp_ip_ecn              => m_udp_ip_ecn,    
        m_udp_ip_ttl              => m_udp_ip_ttl,   
        m_udp_ip_source_ip        => m_udp_ip_source_ip,    
        m_udp_ip_dest_ip          => m_udp_ip_dest_ip,    
        m_udp_source_port         => m_udp_source_port,   
        m_udp_dest_port           => m_udp_dest_port,   
        m_udp_length              => m_udp_length,    
        m_udp_checksum            => m_udp_checksum,  

        m_udp_payload_axis_tdata  => axis_tdata, 
        m_udp_payload_axis_tkeep  => axis_tkeep, 
        m_udp_payload_axis_tvalid => axis_tvalid, 
        m_udp_payload_axis_tready => axis_tready, 
        m_udp_payload_axis_tlast  => axis_tlast, 
        m_udp_payload_axis_tuser  => open 
      );

      udp_frame_narrow_32_8_inst: entity work.axis_width_narrow
      generic map(
        NBYTES => (DATA_WIDTH/8)
      )
      port map(
        clk   => clk,
        reset => reset,

        s_axis_tdata  => axis_tdata,
        s_axis_tkeep  => axis_tkeep,
        s_axis_tvalid => axis_tvalid,
        s_axis_tready => axis_tready,
        s_axis_tlast  => axis_tlast,

        m_axis_tdata  => m_udp_payload_axis_tdata,
        m_axis_tvalid => m_udp_payload_axis_tvalid,
        m_axis_tready => m_udp_payload_axis_tready,
        m_axis_tlast  => m_udp_payload_axis_tlast
      );

      m_udp_payload_axis_tkeep <= (others => '1');
      m_udp_payload_axis_tuser <= '0';

  end generate udp_frame_generator_8_32_gen;    

  -- -----------------------------------------------------------------------------
  udp_frame_generator_32_32_gen: if (UDP_DATA_WIDTH = 32 and DATA_WIDTH = 32) generate

    udp_frame_generator_32_32_inst : entity work.udp_frame_generator32
      generic map(
        DATA_WIDTH => DATA_WIDTH,
        KEEP_WIDTH => KEEP_WIDTH
      )
      port map(
        clk                       => clk,   
        reset                     => reset,
        s_tx_axis_tdata           => s_tx_axis_tdata, 
        s_tx_axis_tkeep           => s_tx_axis_tkeep,
        s_tx_axis_tvalid          => s_tx_axis_tvalid,
        s_tx_axis_tready          => s_tx_axis_tready,
        s_tx_axis_tlast           => s_tx_axis_tlast,

        local_ip_addr             => local_ip_addr,
        tx_hdr_type               => tx_hdr_type,

        m_udp_hdr_valid           => m_udp_hdr_valid,    
        m_udp_hdr_ready           => m_udp_hdr_ready,   
        m_udp_ip_dscp             => m_udp_ip_dscp,    
        m_udp_ip_ecn              => m_udp_ip_ecn,    
        m_udp_ip_ttl              => m_udp_ip_ttl,   
        m_udp_ip_source_ip        => m_udp_ip_source_ip,    
        m_udp_ip_dest_ip          => m_udp_ip_dest_ip,    
        m_udp_source_port         => m_udp_source_port,   
        m_udp_dest_port           => m_udp_dest_port,   
        m_udp_length              => m_udp_length,    
        m_udp_checksum            => m_udp_checksum,  

        m_udp_payload_axis_tdata  => m_udp_payload_axis_tdata, 
        m_udp_payload_axis_tkeep  => m_udp_payload_axis_tkeep, 
        m_udp_payload_axis_tvalid => m_udp_payload_axis_tvalid, 
        m_udp_payload_axis_tready => m_udp_payload_axis_tready, 
        m_udp_payload_axis_tlast  => m_udp_payload_axis_tlast, 
        m_udp_payload_axis_tuser  => m_udp_payload_axis_tuser 
      );
  end generate udp_frame_generator_32_32_gen;

  -- -----------------------------------------------------------------------------
  udp_frame_generator_64_64_gen: if DATA_WIDTH = 64 generate

    udp_frame_generator_64_64_inst : entity work.udp_frame_generator64
      generic map(
        DATA_WIDTH => DATA_WIDTH,
        KEEP_WIDTH => KEEP_WIDTH
      )
      port map(
        clk                       => clk,   
        reset                     => reset,
        s_tx_axis_tdata           => s_tx_axis_tdata, 
        s_tx_axis_tkeep           => s_tx_axis_tkeep,
        s_tx_axis_tvalid          => s_tx_axis_tvalid,
        s_tx_axis_tready          => s_tx_axis_tready,
        s_tx_axis_tlast           => s_tx_axis_tlast,

        local_ip_addr             => local_ip_addr,
        tx_hdr_type               => tx_hdr_type,

        m_udp_hdr_valid           => m_udp_hdr_valid,    
        m_udp_hdr_ready           => m_udp_hdr_ready,   
        m_udp_ip_dscp             => m_udp_ip_dscp,    
        m_udp_ip_ecn              => m_udp_ip_ecn,    
        m_udp_ip_ttl              => m_udp_ip_ttl,   
        m_udp_ip_source_ip        => m_udp_ip_source_ip,    
        m_udp_ip_dest_ip          => m_udp_ip_dest_ip,    
        m_udp_source_port         => m_udp_source_port,   
        m_udp_dest_port           => m_udp_dest_port,   
        m_udp_length              => m_udp_length,    
        m_udp_checksum            => m_udp_checksum, 

        m_udp_payload_axis_tdata  => m_udp_payload_axis_tdata, 
        m_udp_payload_axis_tkeep  => m_udp_payload_axis_tkeep, 
        m_udp_payload_axis_tvalid => m_udp_payload_axis_tvalid, 
        m_udp_payload_axis_tready => m_udp_payload_axis_tready, 
        m_udp_payload_axis_tlast  => m_udp_payload_axis_tlast, 
        m_udp_payload_axis_tuser  => m_udp_payload_axis_tuser 
      );
  end generate udp_frame_generator_64_64_gen;

end rtl;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------