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


package body complex_short_timed_sample is

-- sample
function to_slv(sample : in op_sample_t) return std_logic_vector is
begin
  return sample.data.real &
         sample.data.imaginary;
end to_slv;

function from_slv(slv : in std_logic_vector) return op_sample_t is
  variable ret : op_sample_t;
begin
  ret.data.real      := slv(ret.data.real'range);
  ret.data.imaginary := slv(ret.data.imaginary'range);
  return ret;
end from_slv;

-- time
function to_slv(time : in op_time_t) return std_logic_vector is
begin
  return time.fraction &
         time.seconds;
end to_slv;

function from_slv(slv : in std_logic_vector) return op_time_t is
  variable ret : op_time_t;
begin
  ret.fraction         := slv(ret.fraction'range);
  ret.seconds          := slv(ret.seconds'range);
  return ret;
end from_slv;

-- sample_interval
function to_slv(sample_interval : in op_sample_interval_t) return std_logic_vector is
begin
  return sample_interval.fraction &
         sample_interval.seconds;
end to_slv;

function from_slv(slv : in std_logic_vector) return op_sample_interval_t is
  variable ret : op_sample_interval_t;
begin
  ret.fraction         := slv(ret.fraction'range);
  ret.seconds          := slv(ret.seconds'range);
  return ret;
end from_slv;

--metadata
function to_slv(metadata : in op_metadata_t) return std_logic_vector is
begin
  return metadata.value &
         metadata.id;
end to_slv;

function from_slv(slv : in std_logic_vector) return op_metadata_t is
  variable ret : op_metadata_t;
begin
  ret.value         := slv(ret.value'range);
  ret.id            := slv(ret.id'range);
  return ret;
end from_slv;


function to_slv(protocol : in protocol_t) return std_logic_vector is
begin
  return to_slv(protocol.sample) &
         protocol.sample_vld &
         to_slv(protocol.time) &
         protocol.time_vld &
         to_slv(protocol.sample_interval) &
         protocol.sample_interval_vld &
         protocol.flush &
         protocol.discontinuity &
         to_slv(protocol.metadata) &
         protocol.metadata_vld;
end to_slv;

function from_slv(slv : in std_logic_vector) return protocol_t is
  variable ret : protocol_t;
begin
  ret.sample.data.real             := slv(277 downto 262); --16
  ret.sample.data.imaginary        := slv(261 downto 246); --16
  ret.sample_vld                   := slv(245);
  ret.time.fraction                := slv(244 downto 205); --40
  ret.time.seconds                 := slv(204 downto 173); --32
  ret.time_vld                     := slv(172);
  ret.sample_interval.fraction     := slv(171 downto 132); --40
  ret.sample_interval.seconds      := slv(131 downto 100); --32
  ret.sample_interval_vld          := slv(99);
  ret.flush                        := slv(98);
  ret.discontinuity                := slv(97);
  ret.metadata.value               := slv(96 downto 33); --64
  ret.metadata.id                  := slv(32 downto 1); --32
  ret.metadata_vld                 := slv(0);
  return ret;
end from_slv;

end complex_short_timed_sample;
