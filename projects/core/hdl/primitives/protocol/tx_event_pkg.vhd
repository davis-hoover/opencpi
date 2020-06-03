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
library ocpi;

package tx_event is

--------------------------------------------------------------------------------
-- map protocol definition to data structures
--------------------------------------------------------------------------------

type opcode_t is (
  TXOFF, TXON);

-- operation txOff

-- operation txOn

-- protocol containing all operations
constant PROTOCOL_BIT_WIDTH : positive := 1 + 1;
type protocol_t is record
  txOff : std_logic;
  txOn  : std_logic;
end record;
function to_slv(protocol : in protocol_t)       return std_logic_vector;
function from_slv(slv    : in std_logic_vector) return protocol_t;
constant PROTOCOL_ZERO : protocol_t := (
  txOff => '0',
  txOn  => '0');

--------------------------------------------------------------------------------
-- marshalling
--------------------------------------------------------------------------------

component tx_event_demarshaller is
  port(
    clk       : in  std_logic;
    rst       : in  std_logic;
    -- INPUT
    iready    : in  ocpi.types.Bool_t;
    iopcode   : in  opcode_t;
    ieof      : in  ocpi.types.Bool_t;
    itake     : out ocpi.types.Bool_t;
    -- OUTPUT
    oprotocol : out protocol_t;
    oeof      : out std_logic;
    ordy      : in  std_logic);
end component;

end package tx_event;
