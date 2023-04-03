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
library axi, ocpi;
package rfdc_pkg is

component rfdc is
  port(
    -- AXI-Lite slave ports
    s_ctrl_axi_in   : in  axi.lite32.axi_m2s_t;
    s_ctrl_axi_out  : out axi.lite32.axi_s2m_t;
    s_dac0_axi_in   : in  axi.lite32.axi_m2s_t;
    s_dac0_axi_out  : out axi.lite32.axi_s2m_t;
    s_dac1_axi_in   : in  axi.lite32.axi_m2s_t;
    s_dac1_axi_out  : out axi.lite32.axi_s2m_t;
    s_dac2_axi_in   : in  axi.lite32.axi_m2s_t;
    s_dac2_axi_out  : out axi.lite32.axi_s2m_t;
    s_dac3_axi_in   : in  axi.lite32.axi_m2s_t;
    s_dac3_axi_out  : out axi.lite32.axi_s2m_t;
    s_adc0_axi_in   : in  axi.lite32.axi_m2s_t;
    s_adc0_axi_out  : out axi.lite32.axi_s2m_t;
    s_adc1_axi_in   : in  axi.lite32.axi_m2s_t;
    s_adc1_axi_out  : out axi.lite32.axi_s2m_t;
    s_adc2_axi_in   : in  axi.lite32.axi_m2s_t;
    s_adc2_axi_out  : out axi.lite32.axi_s2m_t;
    s_adc3_axi_in   : in  axi.lite32.axi_m2s_t;
    s_adc3_axi_out  : out axi.lite32.axi_s2m_t;
    -- RX path clock inputs
    rx_clks_p        : in  std_logic_vector(2-1 downto 0);
    rx_clks_n        : in  std_logic_vector(2-1 downto 0);
    -- TX path clock inputs
    tx_clks_p        : in  std_logic_vector(1-1 downto 0);
    tx_clks_n        : in  std_logic_vector(1-1 downto 0);
    -- sysref clock input pair
    sysref_p         : in  std_logic;
    sysref_n         : in  std_logic;
    -- RF inputs
    rf_rxs_p         : in  std_logic_vector(2-1 downto 0);
    rf_rxs_n         : in  std_logic_vector(2-1 downto 0);
    rf_txs_p         : out std_logic_vector(4-1 downto 0);
    rf_txs_n         : out std_logic_vector(4-1 downto 0);
    -- AXI-Stream ports for complex TX paths, TDATA is Q [31:16], I [15:0]
    tx_aclks         : out std_logic_vector(1-1 downto 0); -- associated with all s_axis
    s_axis_0_tdata   : in  std_logic_vector(32-1 downto 0);
    s_axis_0_tvalid  : in  std_logic;
    s_axis_0_tready  : out std_logic;
    s_axis_1_tdata   : in  std_logic_vector(32-1 downto 0);
    s_axis_1_tvalid  : in  std_logic;
    s_axis_1_tready  : out std_logic;
    -- AXI-Stream ports for complex RX paths, TDATA is Q [31:16], I [15:0]
    rx_aclks         : out std_logic_vector(2-1 downto 0); -- associated with all m_axis
    rx_aresets       : out std_logic_vector(2-1 downto 0); -- active-high, associated with all m_axis
    m_axis_0_tdata   : out std_logic_vector(32-1 downto 0);
    m_axis_0_tvalid  : out std_logic;
    m_axis_0_tready  : in  std_logic;
    m_axis_1_tdata   : out std_logic_vector(32-1 downto 0);
    m_axis_1_tvalid  : out std_logic;
    m_axis_1_tready  : in  std_logic);
end component rfdc;

component axi_interconnect is
  port(
    s_ctrl_axi_in  : in  axi.lite32.axi_m2s_t;
    s_ctrl_axi_out : out axi.lite32.axi_s2m_t;
    s_dac0_axi_in  : in  axi.lite32.axi_m2s_t;
    s_dac0_axi_out : out axi.lite32.axi_s2m_t;
    s_dac1_axi_in  : in  axi.lite32.axi_m2s_t;
    s_dac1_axi_out : out axi.lite32.axi_s2m_t;
    s_dac2_axi_in  : in  axi.lite32.axi_m2s_t;
    s_dac2_axi_out : out axi.lite32.axi_s2m_t;
    s_dac3_axi_in  : in  axi.lite32.axi_m2s_t;
    s_dac3_axi_out : out axi.lite32.axi_s2m_t;
    s_adc0_axi_in  : in  axi.lite32.axi_m2s_t;
    s_adc0_axi_out : out axi.lite32.axi_s2m_t;
    s_adc1_axi_in  : in  axi.lite32.axi_m2s_t;
    s_adc1_axi_out : out axi.lite32.axi_s2m_t;
    s_adc2_axi_in  : in  axi.lite32.axi_m2s_t;
    s_adc2_axi_out : out axi.lite32.axi_s2m_t;
    s_adc3_axi_in  : in  axi.lite32.axi_m2s_t;
    s_adc3_axi_out : out axi.lite32.axi_s2m_t;
    m_axi_in       : in  axi.lite32.axi_s2m_t;
    m_axi_out      : out axi.lite32.axi_m2s_t);
end component axi_interconnect;

end package rfdc_pkg;
