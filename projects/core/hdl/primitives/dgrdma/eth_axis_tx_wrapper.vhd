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

entity eth_axis_tx_wrapper is
  generic (    
    DATA_WIDTH  : natural := 8; -- width in bits
    KEEP_ENABLE : boolean := false;
    KEEP_WIDTH  : natural := 1
  );
  port (
    -- Clock and reset
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

    -- AXI output
    m_axis_tdata  : out std_logic_vector(DATA_WIDTH-1 downto 0);
    m_axis_tkeep  : out std_logic_vector(KEEP_WIDTH-1 downto 0);
    m_axis_tvalid : out std_logic;
    m_axis_tready : in std_logic;
    m_axis_tlast  : out std_logic;
    m_axis_tuser  : out std_logic;

    -- Status signals
    busy : out std_logic    
    );  
end entity eth_axis_tx_wrapper;

architecture rtl of eth_axis_tx_wrapper is
begin

  eth_axis_tx_inst : dgrdma.verilog_ethernet.eth_axis_tx
    generic map (
      DATA_WIDTH => DATA_WIDTH,
      KEEP_ENABLE => KEEP_ENABLE,
      KEEP_WIDTH => KEEP_WIDTH         
    )
    port map (   
      -- Clock and reset   
      clk => clk,
      rst => rst,

      -- Ethernet frame input
      s_eth_hdr_valid => s_eth_hdr_valid,          
      s_eth_hdr_ready => s_eth_hdr_ready,          
      s_eth_dest_mac  => s_eth_dest_mac,           
      s_eth_src_mac   => s_eth_src_mac,            
      s_eth_type      => s_eth_type,                
      s_eth_payload_axis_tdata  => s_eth_payload_axis_tdata,
      s_eth_payload_axis_tkeep  => s_eth_payload_axis_tkeep,
      s_eth_payload_axis_tvalid => s_eth_payload_axis_tvalid,
      s_eth_payload_axis_tready => s_eth_payload_axis_tready,
      s_eth_payload_axis_tlast  => s_eth_payload_axis_tlast, 
      s_eth_payload_axis_tuser  => s_eth_payload_axis_tuser, 

      -- AXI output
      m_axis_tdata  => m_axis_tdata, 
      m_axis_tkeep  => m_axis_tkeep, 
      m_axis_tvalid => m_axis_tvalid,
      m_axis_tready => m_axis_tready,
      m_axis_tlast  => m_axis_tlast,
      m_axis_tuser  => m_axis_tuser,

      -- Status signals
      busy => busy   
    );
end rtl;
