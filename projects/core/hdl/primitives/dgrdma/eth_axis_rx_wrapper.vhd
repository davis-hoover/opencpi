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

entity eth_axis_rx_wrapper is
  generic (   
    DATA_WIDTH  : natural := 8; -- width in bits
    KEEP_ENABLE : boolean := false;
    KEEP_WIDTH  : natural := 1
  );
  port (
    -- Clock and reset
    clk : in std_logic;
    rst : in std_logic;
    
    -- AXI input    
    s_axis_tdata  : in std_logic_vector(DATA_WIDTH-1 downto 0);
    s_axis_tkeep  : in std_logic_vector(KEEP_WIDTH-1 downto 0);
    s_axis_tvalid : in std_logic;
    s_axis_tready : out std_logic;
    s_axis_tlast  : in std_logic;
    s_axis_tuser  : in std_logic;
    
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

     -- Status signals
    busy                           : out std_logic;
    error_header_early_termination : out std_logic
    );  
end entity eth_axis_rx_wrapper;

architecture rtl of eth_axis_rx_wrapper is
begin

  eth_axis_rx_inst : dgrdma.verilog_ethernet.eth_axis_rx
    generic map (
      DATA_WIDTH => DATA_WIDTH,
      KEEP_ENABLE => KEEP_ENABLE,
      KEEP_WIDTH => KEEP_WIDTH         
    )
    port map (   
      -- Clock and reset   
      clk => clk,
      rst => rst,

      -- AXI input    
      s_axis_tdata  => s_axis_tdata,
      s_axis_tkeep  => s_axis_tkeep,
      s_axis_tvalid => s_axis_tvalid,
      s_axis_tready => s_axis_tready,
      s_axis_tlast  => s_axis_tlast,
      s_axis_tuser  => s_axis_tuser,

      -- Ethernet frame output
      m_eth_hdr_valid => m_eth_hdr_valid,          
      m_eth_hdr_ready => m_eth_hdr_ready,         
      m_eth_dest_mac  => m_eth_dest_mac,         
      m_eth_src_mac   => m_eth_src_mac,             
      m_eth_type      => m_eth_type,          
      m_eth_payload_axis_tdata => m_eth_payload_axis_tdata,
      m_eth_payload_axis_tkeep  => m_eth_payload_axis_tkeep,
      m_eth_payload_axis_tvalid => m_eth_payload_axis_tvalid,
      m_eth_payload_axis_tready => m_eth_payload_axis_tready,
      m_eth_payload_axis_tlast  => m_eth_payload_axis_tlast,
      m_eth_payload_axis_tuser  => m_eth_payload_axis_tuser,

      -- Status signals
      busy => busy,                         
      error_header_early_termination => error_header_early_termination   
    );
end rtl;
