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
library protocol; use protocol.iqstream.all;

-- The TDATA and/or TUSER are intended to be packed in a similar order to a WSI
-- implementation (in this case, Q is MSB and I is LSB)
entity iqstream_to_axis_converter is
  port(
    iprotocol     : in  protocol_t;
    irdy          : out std_logic;
    m_axis_tdata  : out std_logic_vector(OP_IQ_BIT_WIDTH-1 downto 0);
    m_axis_tvalid : out std_logic;
    m_axis_tready : in  std_logic);
end entity;
architecture rtl of iqstream_to_axis_converter is
begin

  m_axis_tdata  <= iprotocol.iq.data.q & iprotocol.iq.data.i;
  m_axis_tvalid <= iprotocol.iq_vld;
  irdy          <= m_axis_tready;

end rtl;
