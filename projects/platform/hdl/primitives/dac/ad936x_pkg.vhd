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
library ieee; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;

package ad936x is

-- represents the width of each of I and Q
constant DATA_BIT_WIDTH : positive := 12;

type data_rate_config_t is (SDR, DDR);

component ad936x_clock_per_sample_generator is
  port(
    async_select_0_d2_1_d4 : in  std_logic; -- 0: divide-by-2, 1: divide-by-4
    dac_clk                : in  std_logic;
    dacd2_clk              : out std_logic;
    dacd4_clk              : out std_logic;
    ocps_clk               : out std_logic);
end component;

component ad936x_cmos_single_port_fdd_ddr_interleaver is
  port(
    dac_clk            : in  std_logic; -- AD9361 DATA_CLK
    dac_two_r_two_t_en : in  std_logic; -- indicates whether 2R2T is to be used
    dac_i_t1           : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dac_q_t1           : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dac_i_t2           : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dac_q_t2           : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dac_ready_t1       : in  std_logic; -- data...{i,q}_t1 are valid and ready
    dac_ready_t2       : in  std_logic; -- data...{i,q}_t2 are valid and ready
    dac_take_t1        : out std_logic; -- facilitates backpressure for framing alignment
    dac_take_t2        : out std_logic; -- facilitates backpressure for framing alignment
    dacddr_tx_frame    : out std_logic; -- AD9361 TX_FRAME
    dacddr_tx_data     : out std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0));
end component;

component ad936x_lvds_interleaver is
  port(
    dac_clk              : in  std_logic; -- AD9361 DATA_CLK
    dacd2_clk            : in  std_logic;
    dacd2_two_r_two_t_en : in  std_logic; -- indicates whether 2R2T is to be used
    dacd2_i_t1           : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dacd2_q_t1           : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dacd2_i_t2           : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dacd2_q_t2           : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dacd2_ready_t1       : in  std_logic; -- data...{i,q}_t1 are valid and ready
    dacd2_ready_t2       : in  std_logic; -- data...{i,q}_t2 are valid and ready
    dacd2_take_t1        : out std_logic; -- facilitates backpressure for framing alignment
    dacd2_take_t2        : out std_logic; -- facilitates backpressure for framing alignment
    dacddr_tx_frame      : out std_logic; -- AD9361 TX_FRAME
    dacddr_tx_data       : out std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0)); -- AD9361 P0 or P1
end component;

component ad936x_ocps_cmos_single_port_fdd_ddr_interleaver is
  port(
    -- command/control
    ctrl_clk                    : in  std_logic;
    ctrl_rst                    : in  std_logic;
    ctrl_use_two_r_two_t_timing : in  std_logic;
    -- data ingress (one DAC clock per sample)
    ocps_clk                    : out std_logic; -- one clock/sample
    ocps_data_i_t1              : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    ocps_data_q_t1              : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    ocps_data_i_t2              : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    ocps_data_q_t2              : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    ocps_ready_t1               : in  std_logic;
    ocps_ready_t2               : in  std_logic;
    ocps_txen                   : in  std_logic;
    -- data egress (to/from AD9361 pins)
    dac_clk                     : in  std_logic; -- AD9361 DATA_CLK
    dac_txen                    : out std_logic; -- AD9361 transmitter on/off
    dacddr_tx_frame             : out std_logic; -- AD9361 TX_FRAME
    dacddr_tx_data              : out std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0)); --AD9361 P0/P1
end component;

component ad936x_ocps_lvds_interleaver is
  port(
    -- command/control
    ctrl_clk                    : in  std_logic;
    ctrl_rst                    : in  std_logic;
    ctrl_use_two_r_two_t_timing : in  std_logic;
    -- data ingress (one DAC clock per sample)
    ocps_clk                    : out std_logic; -- one clock/sample
    ocps_data_i_t1              : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    ocps_data_q_t1              : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    ocps_data_i_t2              : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    ocps_data_q_t2              : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    ocps_ready_t1               : in  std_logic;
    ocps_ready_t2               : in  std_logic;
    ocps_txen                   : in  std_logic;
    -- data egress (to/from AD9361 pins)
    dac_clk                     : in  std_logic; -- AD9361 DATA_CLK
    dac_txen                    : out std_logic; -- AD9361 transmitter on/off
    dacddr_tx_frame             : out std_logic; -- AD9361 TX_FRAME
    dacddr_tx_data              : out std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0)); -- AD9361 P0 or P1
end component;

end package ad936x;
