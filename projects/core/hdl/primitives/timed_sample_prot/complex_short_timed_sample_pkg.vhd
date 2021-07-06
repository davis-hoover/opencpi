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
library ocpi;
package complex_short_timed_sample is

--------------------------------------------------------------------------------
-- map protocol definition to data structures
--------------------------------------------------------------------------------

type opcode_t is (
  SAMPLE, TIME_TIME, SAMPLE_INTERVAL, FLUSH, DISCONTINUITY, METADATA);

-- operation sample
constant OP_SAMPLE_ARG_DATA_SEQUENCE_LENGTH : positive := 4096;
constant OP_SAMPLE_ARG_DATA_REAL_BIT_WIDTH     : positive := 16;
constant OP_SAMPLE_ARG_DATA_IMAGINARY_BIT_WIDTH     : positive := 16;
constant OP_SAMPLE_BIT_WIDTH              : positive :=
    OP_SAMPLE_ARG_DATA_REAL_BIT_WIDTH +
    OP_SAMPLE_ARG_DATA_IMAGINARY_BIT_WIDTH;
type op_sample_arg_data_t is record
  real : std_logic_vector(OP_SAMPLE_ARG_DATA_REAL_BIT_WIDTH - 1 downto 0);
  imaginary : std_logic_vector(OP_SAMPLE_ARG_DATA_IMAGINARY_BIT_WIDTH - 1 downto 0);
end record;
constant OP_SAMPLE_ARG_DATA_ZERO : op_sample_arg_data_t := (
    real => (others => '0'),
    imaginary => (others => '0'));
type op_sample_t is record
  data : op_sample_arg_data_t;
end record;
constant OP_SAMPLE_ZERO : op_sample_t := (
    data => OP_SAMPLE_ARG_data_ZERO);
function to_slv(sample : in op_sample_t)     return std_logic_vector;
function from_slv(slv   : in std_logic_vector) return op_sample_t;

-- operation time
constant OP_TIME_ARG_SECONDS_BIT_WIDTH       : positive := 32;
constant OP_TIME_ARG_FRACTION_BIT_WIDTH      : positive := 40;
constant OP_TIME_BIT_WIDTH                   : positive :=
    OP_TIME_ARG_SECONDS_BIT_WIDTH +
    OP_TIME_ARG_FRACTION_BIT_WIDTH;
type op_time_t is record
  fraction : std_logic_vector(OP_TIME_ARG_FRACTION_BIT_WIDTH-1 downto 0);
  seconds       : std_logic_vector(OP_TIME_ARG_SECONDS_BIT_WIDTH-1 downto 0);
end record;
constant OP_TIME_ZERO : op_time_t := ((others => '0'), (others => '0'));
function to_slv(time  : in op_time_t)        return std_logic_vector;
function from_slv(slv : in std_logic_vector) return op_time_t;

-- operation sample_interval
constant OP_SAMPLE_INTERVAL_ARG_SECONDS_BIT_WIDTH       : positive := 32;
constant OP_SAMPLE_INTERVAL_ARG_FRACTION_BIT_WIDTH      : positive := 40;
constant OP_SAMPLE_INTERVAL_BIT_WIDTH                   : positive :=
    OP_SAMPLE_INTERVAL_ARG_SECONDS_BIT_WIDTH +
    OP_SAMPLE_INTERVAL_ARG_FRACTION_BIT_WIDTH;
type op_sample_interval_t is record
  fraction : std_logic_vector(OP_SAMPLE_INTERVAL_ARG_FRACTION_BIT_WIDTH-1 downto 0);
  seconds       : std_logic_vector(OP_SAMPLE_INTERVAL_ARG_SECONDS_BIT_WIDTH-1 downto 0);
end record;
constant OP_SAMPLE_INTERVAL_ZERO : op_sample_interval_t := ((others => '0'), (others => '0'));
function to_slv(sample_interval  : in op_sample_interval_t)        return std_logic_vector;
function from_slv(slv : in std_logic_vector) return op_sample_interval_t;


-- operation flush
constant OP_FLUSH_BIT_WIDTH : positive := 1;

-- operation discontinuity
constant OP_DISCONTINUITY_BIT_WIDTH : positive := 1;

-- operation metadata
constant OP_METADATA_ARG_ID_BIT_WIDTH       : positive := 32;
constant OP_METADATA_ARG_VALUE_BIT_WIDTH : positive := 64;
constant OP_METADATA_BIT_WIDTH               : positive :=
    OP_METADATA_ARG_ID_BIT_WIDTH +
    OP_METADATA_ARG_VALUE_BIT_WIDTH;
type op_metadata_t is record
  value : std_logic_vector(OP_METADATA_ARG_VALUE_BIT_WIDTH-1 downto 0);
  id       : std_logic_vector(OP_METADATA_ARG_ID_BIT_WIDTH-1 downto 0);
end record;
constant OP_METADATA_ZERO : op_metadata_t := ((others => '0'), (others => '0'));
function to_slv(metadata  : in op_metadata_t)        return std_logic_vector;
function from_slv(slv : in std_logic_vector) return op_metadata_t;


-- protocol containing all operations
constant PROTOCOL_BIT_WIDTH : positive := OP_SAMPLE_BIT_WIDTH+1 +
                                          OP_TIME_BIT_WIDTH+1 +
                                          OP_SAMPLE_INTERVAL_BIT_WIDTH+1 +
                                          OP_FLUSH_BIT_WIDTH +
                                          OP_DISCONTINUITY_BIT_WIDTH +
                                          OP_METADATA_BIT_WIDTH+1;
type protocol_t is record
  sample               : op_sample_t;
  sample_vld           : std_logic;
  time                 : op_time_t;
  time_vld             : std_logic;
  sample_interval      : op_sample_interval_t;
  sample_interval_vld  : std_logic;
  flush                : std_logic;
  discontinuity        : std_logic;
  metadata             : op_metadata_t;
  metadata_vld         : std_logic;
end record;
function to_slv(protocol : in protocol_t)       return std_logic_vector;
function from_slv(slv    : in std_logic_vector) return protocol_t;
constant PROTOCOL_ZERO : protocol_t := (
  sample                => OP_SAMPLE_ZERO,
  sample_vld            => '0',
  time                  => OP_TIME_ZERO,
  time_vld              => '0',
  sample_interval       => OP_SAMPLE_INTERVAL_ZERO,
  sample_interval_vld   => '0',
  flush                 => '0',
  discontinuity         => '0',
  metadata              => OP_METADATA_ZERO,
  metadata_vld          => '0');

--------------------------------------------------------------------------------
-- marshalling
--------------------------------------------------------------------------------

component complex_short_timed_sample_marshaller is
  generic(
    WSI_DATA_WIDTH    : positive := 32;
    WSI_MBYTEEN_WIDTH : positive);
  port(
    clk          : in  std_logic;
    rst          : in  std_logic;
    -- INPUT
    iprotocol    : in  protocol_t;
    ieof         : in  ocpi.types.Bool_t;
    irdy         : out std_logic;
    -- OUTPUT
    odata        : out std_logic_vector(31 downto 0);
    ovalid       : out ocpi.types.Bool_t;
    obyte_enable : out std_logic_vector(WSI_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out ocpi.types.Bool_t;
    osom         : out ocpi.types.Bool_t;
    oeom         : out ocpi.types.Bool_t;
    oopcode      : out opcode_t;
    oeof         : out ocpi.types.Bool_t;
    oready       : in  ocpi.types.Bool_t);
end component;

component complex_short_timed_sample_demarshaller is
  generic(
    WSI_DATA_WIDTH : positive := 32);
  port(
    clk         : in  std_logic;
    rst         : in  std_logic;
    -- INPUT
    idata       : in  std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ivalid      : in  ocpi.types.Bool_t;
    iready      : in  ocpi.types.Bool_t;
    isom        : in  ocpi.types.Bool_t;
    ieom        : in  ocpi.types.Bool_t;
    iopcode     : in  opcode_t;
    ieof        : in  ocpi.types.Bool_t;
    itake       : out ocpi.types.Bool_t;
    -- OUTPUT
    oprotocol   : out protocol_t;
    oeof        : out ocpi.types.Bool_t;
    ordy        : in  std_logic);
end component;

component out_port_csts_sample_and_discontinuity is
  generic(
    WSI_DATA_WIDTH    : positive := 32;
    WSI_MBYTEEN_WIDTH : positive);
  port(
    clk : in  std_logic;
    rst : in  std_logic;
    -- INPUT
    iprotocol                  : in  protocol_t;
    iready                     : in  ocpi.types.Bool_t;
    isuppress_discontinuity_op : in  ocpi.types.Bool_t;
    -- OUTPUT
    odata             : out std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ovalid            : out ocpi.types.Bool_t;
    obyte_enable      : out std_logic_vector(WSI_MBYTEEN_WIDTH-1 downto 0);
    ogive             : out ocpi.types.Bool_t;
    osom              : out ocpi.types.Bool_t;
    oeom              : out ocpi.types.Bool_t;
    oopcode           : out opcode_t);
end component;

end package complex_short_timed_sample;
