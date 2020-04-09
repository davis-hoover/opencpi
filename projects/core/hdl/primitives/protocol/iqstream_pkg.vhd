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

package iqstream is

type opcode_t is (
  IQ);

-- operation iq
constant OP_IQ_ARG_DATA_SEQUENCE_LENGTH : positive := 2048;
constant OP_IQ_ARG_DATA_I_BIT_WIDTH     : positive := 16;
constant OP_IQ_ARG_DATA_Q_BIT_WIDTH     : positive := 16;
constant OP_IQ_BIT_WIDTH                : positive :=
    OP_IQ_ARG_DATA_I_BIT_WIDTH+
    OP_IQ_ARG_DATA_Q_BIT_WIDTH;
type op_iq_arg_data_t is record
  i : std_logic_vector(OP_IQ_ARG_DATA_I_BIT_WIDTH -1 downto 0);
  q : std_logic_vector(OP_IQ_ARG_DATA_Q_BIT_WIDTH -1 downto 0);
end record;
constant OP_IQ_ARG_DATA_ZERO : op_iq_arg_data_t := (
    i => (others => '0'),
    q => (others => '0'));
type op_iq_t is record
  data : op_iq_arg_data_t;
end record;
constant OP_IQ_ZERO : op_iq_t := (
    data => OP_IQ_ARG_DATA_ZERO);

-- protocol containing all operations
type protocol_t is record
  iq     : op_iq_t;
  iq_vld : std_logic;
end record;
function to_slv(protocol : in protocol_t)       return std_logic_vector;
function from_slv(slv    : in std_logic_vector) return protocol_t;
constant PROTOCOL_ZERO : protocol_t := (OP_IQ_ZERO, '0');

component iqstream_marshaller is
  generic(
    WSI_DATA_WIDTH    : positive := 16; -- 16 is default of codegen, but
                                        -- MUST USE 32 FOR NOW
    WSI_MBYTEEN_WIDTH : positive);
  port(
    -- CTRL
    clk          : in  std_logic;
    rst          : in  std_logic;
    -- INPUT
    iprotocol    : in  protocol_t;
    irdy         : out std_logic;
    -- OUTPUT (WSI)
    odata        : out std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ovalid       : out ocpi.types.Bool_t;
    obyte_enable : out std_logic_vector(WSI_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out ocpi.types.Bool_t;
    osom         : out ocpi.types.Bool_t;
    oeom         : out ocpi.types.Bool_t;
    oeof         : out ocpi.types.Bool_t;
    oready       : in  ocpi.types.Bool_t);
end component;

end package iqstream;
