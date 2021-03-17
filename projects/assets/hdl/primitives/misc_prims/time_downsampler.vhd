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

-- This module inserts timestamps and sampling interval as requested.
-- Timestamps are inserted unless the "bypass" control signal is true,
-- They are inserted *before* every "samples_per_timestamp" samples

-- Sampling interval is inserted on demand, which is indicated by the
-- rising edge of the "insert_interval" input.

library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library util;
library protocol;
library misc_prims; use misc_prims.misc_prims.all;
library ocpi; use ocpi.types.all;

-- for metadata, registers time every data_count_between_time I/Q values,
-- effectively downsampling time
entity time_downsampler is
  generic(
    -- the DATA PIPE LATENCY CYCLES is currently 1
    DATA_COUNTER_BIT_WIDTH : positive := 32);
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    ctrl      : in  time_downsampler_ctrl_t;
    -- INPUT
    iprotocol : in  protocol.complex_short_with_metadata.protocol_t;
    ieof      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    oprotocol : out protocol.complex_short_with_metadata.protocol_t;
    oeof      : out std_logic;
    ordy      : in  std_logic);
end entity time_downsampler;
architecture rtl of time_downsampler is
  signal protocol_r        : protocol.complex_short_with_metadata.protocol_t :=
                             protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal data_counter_rst  : std_logic := '0';
  signal data_counter_en   : std_logic := '0';
  signal data_counter_cnt  : unsigned(DATA_COUNTER_BIT_WIDTH-1 downto 0) :=
                             (others => '0');
  signal allow_time_xfer   : std_logic := '0';

  signal timestamp         : protocol.complex_short_with_metadata.op_time_t;
  signal timestamp_vld     : bool_t;

  signal interval          : protocol.complex_short_with_metadata.op_interval_t;
  signal interval_vld      : bool_t;
  signal insert_interval_r : bool_t;
  signal insert_interval   : bool_t;
begin

  timestamp_vld   <= iprotocol.time_vld when its(ctrl.bypass) else ctrl.time_vld and allow_time_xfer;
  timestamp       <= iprotocol.time when its(ctrl.bypass) else ctrl.time;

  interval_vld    <= iprotocol.interval_vld when its(ctrl.bypass) else insert_interval;
  insert_interval <= ctrl.insert_interval or insert_interval_r;
  interval        <= ctrl.interval when its(insert_interval) else iprotocol.interval;

  pipeline : process(clk)
  begin
    if rising_edge(clk) then
      if rst = '1' then
        protocol_r        <= protocol.complex_short_with_metadata.PROTOCOL_ZERO;
        oeof              <= '0';
        insert_interval_r <= bfalse;
      elsif ordy = '1' then
        protocol_r.samples        <= iprotocol.samples;
        protocol_r.samples_vld    <= iprotocol.samples_vld;
        protocol_r.time           <= timestamp;
        protocol_r.time_vld       <= timestamp_vld;
        protocol_r.interval       <= interval;
        protocol_r.interval_vld   <= interval_vld;
        protocol_r.flush          <= iprotocol.flush;
        protocol_r.sync           <= iprotocol.sync;
        protocol_r.end_of_samples <= iprotocol.end_of_samples;
        oeof                      <= ieof;
        insert_interval_r         <= bfalse;
      elsif its(ctrl.insert_interval) then
        insert_interval_r <= btrue;
      end if;
    end if;
  end process pipeline;

  ------------------------------------------------------------------------------
  -- counter to initiate time selection for downsampling
  ------------------------------------------------------------------------------

  allow_time_xfer <= '1' when (
                     (data_counter_en = '1') and
                     ((data_counter_cnt = 0) or
                     (ctrl.samples_per_timestamp = 0)))
                     else '0';

  data_counter_rst <= '1' when (rst = '1') or (
                      (data_counter_en = '1') and
                      ((data_counter_cnt = (ctrl.samples_per_timestamp-1)) or
                      (ctrl.samples_per_timestamp = 0)))
                      else '0';
  data_counter_en  <= ordy and iprotocol.samples_vld;

  data_counter : util.util.counter
    generic map(
      BIT_WIDTH => DATA_COUNTER_BIT_WIDTH)
    port map(
      clk => clk,
      rst => data_counter_rst,
      en  => data_counter_en,
      cnt => data_counter_cnt);

  ------------------------------------------------------------------------------
  -- output data/metadata generation
  ------------------------------------------------------------------------------

  oprotocol <= protocol_r;
  irdy      <= ordy;

end rtl;
