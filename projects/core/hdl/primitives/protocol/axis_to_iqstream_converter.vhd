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
entity axis_to_iqstream_converter is
  port(
    s_axis_tdata  : in  std_logic_vector(OP_IQ_BIT_WIDTH-1 downto 0);
    s_axis_tvalid : in  std_logic;
    s_axis_tready : out std_logic;
    oprotocol     : out protocol_t;
    ordy          : in  std_logic);
end entity;
architecture rtl of axis_to_iqstream_converter is
begin

  oprotocol.iq.data.i <= s_axis_tdata(16-1 downto 0);
  oprotocol.iq.data.q <= s_axis_tdata(32-1 downto 16);
  oprotocol.iq_vld    <= s_axis_tvalid;

end rtl;
