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
use work.timestamper_scdcd_csts_pkg.all;
library timed_sample_prot;
library ocpi; use ocpi.types.all;

entity time_corrector is
  -- the DATA PIPE LATENCY CYCLES is currently 0
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    ctrl      : in  time_corrector_ctrl_t;
    status    : out time_corrector_status_t;
    -- INPUT
    iprotocol : in  timed_sample_prot.complex_short_timed_sample.protocol_t;
    ieof      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    oprotocol : out timed_sample_prot.complex_short_timed_sample.protocol_t;
    oeof      : out std_logic;
    ordy      : in  std_logic);
end time_corrector;
architecture rtl of time_corrector is
  signal itime_slv           : std_logic_vector(
      timed_sample_prot.complex_short_timed_sample.OP_TIME_BIT_WIDTH-1 downto 0) :=
      (others => '0');
  signal tmp                 : signed(
      timed_sample_prot.complex_short_timed_sample.OP_TIME_BIT_WIDTH+1 downto 0) :=
      (others => '0');
  signal tmp_lower_than_min  : std_logic := '0';
  signal tmp_larger_than_max : std_logic := '0';
  signal time_time           : unsigned(
      timed_sample_prot.complex_short_timed_sample.OP_TIME_BIT_WIDTH-1 downto 0) :=
      (others => '0');
  signal overflow            : std_logic := '0';
  signal protocol_s : timed_sample_prot.complex_short_timed_sample.protocol_t :=
                      timed_sample_prot.complex_short_timed_sample.PROTOCOL_ZERO;
begin
  itime_slv <= iprotocol.time.seconds & iprotocol.time.fraction;
  tmp <= resize(signed(itime_slv), tmp'length) -
         resize(signed(ctrl.time_correction), tmp'length);

  tmp_lower_than_min  <= tmp(tmp'left); -- sign bit
  tmp_larger_than_max <= tmp(tmp'left-1); -- largest amplitude bit
  overflow            <= (tmp_lower_than_min or tmp_larger_than_max) and
                         iprotocol.time_vld;
  status.overflow     <= overflow;
  time_time           <= unsigned(tmp(tmp'left-2 downto 0));

  protocol_s.sample         <= iprotocol.sample;
  protocol_s.sample_vld     <= iprotocol.sample_vld;
  protocol_s.time.seconds   <= iprotocol.time.seconds when (ctrl.bypass = '1')
      else std_logic_vector(time_time(time_time'left downto time_time'left -
      timed_sample_prot.complex_short_timed_sample.OP_TIME_ARG_SECONDS_BIT_WIDTH+1));
  protocol_s.time.fraction  <= iprotocol.time.fraction when (ctrl.bypass = '1')
      else std_logic_vector(time_time(
      timed_sample_prot.complex_short_timed_sample.OP_TIME_ARG_FRACTION_BIT_WIDTH-1
      downto 0));
  protocol_s.time_vld       <= iprotocol.time_vld and (not overflow);
  protocol_s.sample_interval       <= iprotocol.sample_interval;
  protocol_s.sample_interval_vld   <= iprotocol.sample_interval_vld;
  protocol_s.flush          <= iprotocol.flush;
  protocol_s.discontinuity  <= iprotocol.discontinuity;
  protocol_s.metadata       <= iprotocol.metadata;
  protocol_s.metadata_vld   <= iprotocol.metadata_vld;

  oprotocol <= protocol_s;
  oeof      <= ieof;
  irdy      <= ordy;
end rtl;
