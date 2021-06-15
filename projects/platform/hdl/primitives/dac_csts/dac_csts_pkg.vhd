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
library timed_sample_prot; use timed_sample_prot.complex_short_timed_sample.all;
package dac_csts is

-- represents the width of each of I and Q
constant DATA_BIT_WIDTH : positive := 12;
constant SAMP_COUNT_BIT_WIDTH : positive := 32;
constant NUM_UNDERRUNS_BIT_WIDTH : positive := 32;

type data_complex_t is record
  real      : std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
  imaginary : std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
end record data_complex_t;

type metadata_t is record
  underrun_error : std_logic; -- samples were not available for one or
                              -- more dac clock cycles
  ctrl_tx_on_off : std_logic; -- high when transmitter should be powered on
                              -- low when transmitter should be powered off
end record metadata_t;

type underrun_detector_status_t is record
  underrun_error : std_logic;
  samp_count_before_first_underrun : std_logic_vector(SAMP_COUNT_BIT_WIDTH-1 downto 0);
  num_underruns                    : std_logic_vector(NUM_UNDERRUNS_BIT_WIDTH-1 downto 0);
end record underrun_detector_status_t;

-- useful for data egress to multi-DAC devices
type array_data_t is array(natural range<>)  of std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
-- useful for data egress to multi-quadrate DAC devices
type array_qdata_t is array(natural range<>)  of std_logic_vector(2*DATA_BIT_WIDTH-1 downto 0);

component underrun_detector is
  port(
    -- CTRL
    clk           : in  std_logic;
    rst           : in  std_logic;
    status        : out underrun_detector_status_t;
    -- INPUT
    iprotocol     : in  timed_sample_prot.complex_short_timed_sample.protocol_t;
    imetadata     : in  metadata_t;
    imetadata_vld : in  std_logic;
    irdy          : out std_logic;
    -- OUTPUT
    -- if ometadata.underrun_error and timed_sample_prot.sample_vld are both 1, error is
    -- assumed to have happened before the current valid sample
    oprotocol     : out timed_sample_prot.complex_short_timed_sample.protocol_t;
    ometadata     : out metadata_t;
    ometadata_vld : out std_logic;
    ordy          : in  std_logic);
end component;

component data_narrower is
  generic(
    BITS_PACKED_INTO_LSBS : boolean := false);
  port(
    -- CTRL
    clk           : in  std_logic;
    rst           : in  std_logic;
    -- INPUT
    iprotocol     : in  timed_sample_prot.complex_short_timed_sample.protocol_t;
    imetadata     : in  metadata_t;
    imetadata_vld : in  std_logic;
    irdy          : out std_logic;
    -- OUTPUT
    odata         : out data_complex_t;
    odata_vld     : out std_logic;
    ometadata     : out metadata_t;
    ometadata_vld : out std_logic;
    ordy          : in  std_logic);
end component;

component event_in_x2_to_txen is
  port(
    clk                    : in  std_logic;
    reset                  : in  std_logic;
    -- TX channel 0 (channel indices are treated identically)
    txon_pulse_0           : in  std_logic;
    txoff_pulse_0          : in  std_logic;
    event_in_connected_0   : in  std_logic;
    is_operating_0         : in  std_logic;
    -- TX channel 1 (channel indices are treated identically)
    txon_pulse_1           : in  std_logic;
    txoff_pulse_1          : in  std_logic;
    event_in_connected_1   : in  std_logic;
    is_operating_1         : in  std_logic;
    -- tx enable output
    txen                   : out std_logic);
end component;

end package dac_csts;
