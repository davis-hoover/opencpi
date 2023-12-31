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
library timed_sample_prot;
package adc_csts is

constant DATA_BIT_WIDTH : positive := 12;
constant SAMP_COUNT_BIT_WIDTH : positive := 32;
constant DROPPED_SAMPS_BIT_WIDTH : positive := 32;

type data_complex_t is record
  real : std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
  imaginary : std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
end record data_complex_t;

type samp_drop_detector_status_t is record
  error_samp_drop                   : std_logic;
  samp_count_before_first_samp_drop : std_logic_vector(SAMP_COUNT_BIT_WIDTH-1 downto 0);
  num_dropped_samps                 : std_logic_vector(DROPPED_SAMPS_BIT_WIDTH-1 downto 0);
end record samp_drop_detector_status_t;

-- useful for data ingress from multi-ADC devices
type array_data_t is array(natural range<>)  of std_logic_vector(DATA_BIT_WIDTH-1 downto 0);


component samp_drop_detector is
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    status    : out samp_drop_detector_status_t;
    -- INPUT
    idata     : in  data_complex_t;
    ivld      : in  std_logic;
    -- OUTPUT
    odata     : out data_complex_t;
    osamp_drop: out std_logic;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end component;

component data_widener is
  generic(
    BITS_PACKED_INTO_MSBS : boolean := true);
  port(
    -- CTRL
    clk        : in  std_logic;
    rst        : in  std_logic;
    -- INPUT
    idata      : in  data_complex_t;
    isamp_drop : in  std_logic;
    ivld       : in  std_logic;
    irdy       : out std_logic;
    -- OUTPUT
    oprotocol  : out timed_sample_prot.complex_short_timed_sample.protocol_t;
    ordy       : in  std_logic);
end component;

component maximal_lfsr_data_src is
  port(
    -- CTRL
    clk                : in  std_logic;
    rst                : in  std_logic;
    stop_on_period_cnt : in  std_logic;
    stopped            : out std_logic;
    -- OUTPUT
    odata              : out data_complex_t;
    ovld               : out std_logic;
    ordy               : in  std_logic);
end component;

end package adc_csts;
