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

-- Corrects time_in value by subtracting time_correction. Both the time being
-- correct and the correction amount are unsigned in
-- order to allow UNIX EPOCH format. Note that corrected time may overflow.

library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all;
library protocol;

entity time_corrector is
  -- the DATA PIPE LATENCY CYCLES is currently 0
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    ctrl      : in  time_corrector_ctrl_t;
    status    : out time_corrector_status_t;
    -- INPUT
    iprotocol : in  protocol.complex_short_with_metadata.protocol_t;
    ieof      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    oprotocol : out protocol.complex_short_with_metadata.protocol_t;
    oeof      : out std_logic;
    ordy      : in  std_logic);
end time_corrector;
architecture rtl of time_corrector is
  signal itime_slv           : std_logic_vector(
      protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH-1 downto 0) :=
      (others => '0');
  signal tmp                 : signed(
      protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH+1 downto 0) :=
      (others => '0');
  signal tmp_lower_than_min  : std_logic := '0';
  signal tmp_larger_than_max : std_logic := '0';
  signal time_time           : unsigned(
      protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH-1 downto 0) :=
      (others => '0');
  signal overflow            : std_logic := '0';
  signal protocol_s : protocol.complex_short_with_metadata.protocol_t :=
                      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
begin
  itime_slv <= iprotocol.time.sec & iprotocol.time.fract_sec;
  tmp <= resize(signed(itime_slv), tmp'length) -
         resize(signed(ctrl.time_correction), tmp'length);

  tmp_lower_than_min  <= tmp(tmp'left); -- sign bit
  tmp_larger_than_max <= tmp(tmp'left-1); -- largest amplitude bit
  overflow            <= (tmp_lower_than_min or tmp_larger_than_max) and
                         iprotocol.time_vld;
  status.overflow     <= overflow;
  time_time           <= unsigned(tmp(tmp'left-2 downto 0));

  protocol_s.samples        <= iprotocol.samples;
  protocol_s.samples_vld    <= iprotocol.samples_vld;
  protocol_s.time.sec       <= iprotocol.time.sec when (ctrl.bypass = '1')
      else std_logic_vector(time_time(time_time'left downto time_time'left -
      protocol.complex_short_with_metadata.OP_TIME_ARG_SEC_BIT_WIDTH+1));
  protocol_s.time.fract_sec <= iprotocol.time.fract_sec when (ctrl.bypass = '1')
      else std_logic_vector(time_time(
      protocol.complex_short_with_metadata.OP_TIME_ARG_FRACT_SEC_BIT_WIDTH-1
      downto 0));
  protocol_s.time_vld       <= iprotocol.time_vld and (not overflow);
  protocol_s.interval       <= iprotocol.interval;
  protocol_s.interval_vld   <= iprotocol.interval_vld;
  protocol_s.flush          <= iprotocol.flush;
  protocol_s.sync           <= iprotocol.sync;
  protocol_s.end_of_samples <= iprotocol.end_of_samples;

  oprotocol <= protocol_s;
  oeof      <= ieof;
  irdy      <= ordy;
end rtl;
