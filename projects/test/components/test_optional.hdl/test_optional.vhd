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


library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of worker is
 signal samples_doit : bool_t;
 signal timestamps_doit : bool_t;
begin
-- Pure combinatorial implementation
  samples_doit        <= ctl_in.is_operating and samples_in_in.ready and samples_out_in.ready;
  timestamps_doit     <= ctl_in.is_operating and timestamps_in_in.ready and timestamps_out_in.ready;
-- samples ports
-- WSI input interface outputs
  samples_in_out.take         <= samples_doit;
-- WSI output interface outputs
  samples_out_out.give        <= samples_doit;
  samples_out_out.data        <= samples_in_in.data;
  samples_out_out.som         <= samples_in_in.som;
  samples_out_out.eom         <= samples_in_in.eom;
  samples_out_out.valid       <= samples_in_in.valid;
  samples_out_out.byte_enable <= samples_in_in.byte_enable; -- only necessary due to BSV protocol sharing
  samples_out_out.opcode      <= samples_in_in.opcode;
-- timestamps port
-- WSI input interface outputs
  timestamps_in_out.take         <= timestamps_doit;
-- WSI output interface outputs
  timestamps_out_out.give        <= timestamps_doit;
  timestamps_out_out.data        <= timestamps_in_in.data;
  timestamps_out_out.som         <= timestamps_in_in.som;
  timestamps_out_out.eom         <= timestamps_in_in.eom;
  timestamps_out_out.valid       <= timestamps_in_in.valid;
  timestamps_out_out.byte_enable <= timestamps_in_in.byte_enable; -- only necessary due to BSV protocol sharing
  timestamps_out_out.opcode      <= timestamps_in_in.opcode;
end rtl;
