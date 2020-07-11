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
package complex_short_with_metadata is

--------------------------------------------------------------------------------
-- map protocol definition to data structures
--------------------------------------------------------------------------------

type opcode_t is (
  SAMPLES, TIME_TIME, INTERVAL, FLUSH, SYNC, END_OF_SAMPLES);

-- operation samples
constant OP_SAMPLES_ARG_IQ_SEQUENCE_LENGTH : positive := 4092;
constant OP_SAMPLES_ARG_IQ_I_BIT_WIDTH     : positive := 16;
constant OP_SAMPLES_ARG_IQ_Q_BIT_WIDTH     : positive := 16;
constant OP_SAMPLES_BIT_WIDTH              : positive :=
    OP_SAMPLES_ARG_IQ_I_BIT_WIDTH +
    OP_SAMPLES_ARG_IQ_Q_BIT_WIDTH;
type op_samples_arg_iq_t is record
  i : std_logic_vector(OP_SAMPLES_ARG_IQ_I_BIT_WIDTH - 1 downto 0);
  q : std_logic_vector(OP_SAMPLES_ARG_IQ_Q_BIT_WIDTH - 1 downto 0);
end record;
constant OP_SAMPLES_ARG_IQ_ZERO : op_samples_arg_iq_t := (
    i => (others => '0'),
    q => (others => '0'));
type op_samples_t is record
  iq : op_samples_arg_iq_t;
end record;
constant OP_SAMPLES_ZERO : op_samples_t := (
    iq => OP_SAMPLES_ARG_IQ_ZERO);
function to_slv(samples : in op_samples_t)     return std_logic_vector;
function from_slv(slv   : in std_logic_vector) return op_samples_t;

-- operation time
constant OP_TIME_ARG_SEC_BIT_WIDTH       : positive := 32;
constant OP_TIME_ARG_FRACT_SEC_BIT_WIDTH : positive := 32;
constant OP_TIME_BIT_WIDTH               : positive :=
    OP_TIME_ARG_SEC_BIT_WIDTH +
    OP_TIME_ARG_FRACT_SEC_BIT_WIDTH;
type op_time_t is record
  fract_sec : std_logic_vector(OP_TIME_ARG_FRACT_SEC_BIT_WIDTH-1 downto 0);
  sec       : std_logic_vector(OP_TIME_ARG_SEC_BIT_WIDTH-1 downto 0);
end record;
constant OP_TIME_ZERO : op_time_t := ((others => '0'), (others => '0'));
function to_slv(time  : in op_time_t)        return std_logic_vector;
function from_slv(slv : in std_logic_vector) return op_time_t;

-- operation interval
constant OP_INTERVAL_ARG_DELTA_TIME_BIT_WIDTH : positive := 64;
constant OP_INTERVAL_BIT_WIDTH                : positive :=
    OP_INTERVAL_ARG_DELTA_TIME_BIT_WIDTH;
type op_interval_t is record
  delta_time : std_logic_vector(OP_INTERVAL_ARG_DELTA_TIME_BIT_WIDTH-1 downto 0);
end record;
constant OP_INTERVAL_ZERO : op_interval_t := (delta_time => (others => '0'));
function to_slv(interval : in op_interval_t)    return std_logic_vector;
function from_slv(slv    : in std_logic_vector) return op_interval_t;

-- operation flush
constant OP_FLUSH_BIT_WIDTH : positive := 1;

-- operation sync
constant OP_SYNC_BIT_WIDTH : positive := 1;

-- operation end_of_samples
constant OP_END_OF_SAMPLES_BIT_WIDTH : positive := 1;

-- protocol containing all operations
constant PROTOCOL_BIT_WIDTH : positive := OP_SAMPLES_BIT_WIDTH+1 +
                                          OP_TIME_BIT_WIDTH+1 +
                                          OP_INTERVAL_BIT_WIDTH+1 +
                                          OP_FLUSH_BIT_WIDTH +
                                          OP_SYNC_BIT_WIDTH +
                                          OP_END_OF_SAMPLES_BIT_WIDTH;
type protocol_t is record
  samples           : op_samples_t;
  samples_vld       : std_logic;
  time              : op_time_t;
  time_vld          : std_logic;
  interval          : op_interval_t;
  interval_vld      : std_logic;
  flush             : std_logic;
  sync              : std_logic;
  end_of_samples    : std_logic;
end record;
function to_slv(protocol : in protocol_t)       return std_logic_vector;
function from_slv(slv    : in std_logic_vector) return protocol_t;
constant PROTOCOL_ZERO : protocol_t := (
  samples        => OP_SAMPLES_ZERO,
  samples_vld    => '0',
  time           => OP_TIME_ZERO,
  time_vld       => '0',
  interval       => OP_INTERVAL_ZERO,
  interval_vld   => '0',
  flush          => '0',
  sync           => '0',
  end_of_samples => '0');

--------------------------------------------------------------------------------
-- marshalling
--------------------------------------------------------------------------------

component complex_short_with_metadata_marshaller is
  generic(
    WSI_DATA_WIDTH    : positive := 16; -- 16 is default of codegen, but
                                        -- MUST USE 32 FOR NOW
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

component complex_short_with_metadata_demarshaller is
  generic(
    WSI_DATA_WIDTH : positive := 16); -- 16 is default of codegen, but
                                      -- MUST USE 32 FOR NOW
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

-- TODO / FIXME - consolidate w/ complex_short_with_metadata_marshaller_old
component complex_short_with_metadata_marshaller_old is
  generic(
    OUT_PORT_MBYTEEN_WIDTH : positive);
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
    obyte_enable : out std_logic_vector(OUT_PORT_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out ocpi.types.Bool_t;
    osom         : out ocpi.types.Bool_t;
    oeom         : out ocpi.types.Bool_t;
    oopcode      : out opcode_t;
    oeof         : out ocpi.types.Bool_t;
    oready       : in  ocpi.types.Bool_t);
end component;

end package complex_short_with_metadata;
