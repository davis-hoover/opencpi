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
library ocpi, protocol; use protocol.tx_event.all;

entity tx_event_demarshaller is
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
end entity;
architecture rtl of tx_event_demarshaller is
  signal iinfo : std_logic := '0';
  signal ixfer : std_logic := '0';
begin
  iinfo <= '1' when(iready = ocpi.types.btrue) else '0';
  ixfer <= iinfo and ordy;
  itake <= ixfer;
  oprotocol.txOff <= '1' when ((ixfer = '1') and (iopcode = TXOFF)) else '0';
  oprotocol.txOn  <= '1' when ((ixfer = '1') and (iopcode = TXON)) else '0';
  oeof <= ieof;
end rtl;
