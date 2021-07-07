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
library util;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
use work.timestamper_scdcd_csts_pkg.all;
library timed_sample_prot;
library ocpi; use ocpi.types.all;



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
    iprotocol : in  timed_sample_prot.complex_short_timed_sample.protocol_t;
    ieof      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    oprotocol : out timed_sample_prot.complex_short_timed_sample.protocol_t;
    oeof      : out std_logic;
    ordy      : in  std_logic);
end entity time_downsampler;
architecture rtl of time_downsampler is
  signal protocol_r        : timed_sample_prot.complex_short_timed_sample.protocol_t :=
                             timed_sample_prot.complex_short_timed_sample.PROTOCOL_ZERO;
  signal data_counter_rst  : std_logic := '0';
  signal data_counter_en   : std_logic := '0';
  signal data_counter_cnt  : unsigned(DATA_COUNTER_BIT_WIDTH-1 downto 0) :=
                             (others => '0');
  signal allow_time_xfer   : std_logic := '0';

  signal timestamp         : timed_sample_prot.complex_short_timed_sample.op_time_t;
  signal timestamp_vld     : bool_t;

  signal interval          : timed_sample_prot.complex_short_timed_sample.op_sample_interval_t;
  signal interval_vld      : bool_t;
  signal insert_interval_fraction_r : bool_t;
  signal insert_interval_fraction   : bool_t;
  signal insert_interval_seconds_r  : bool_t;
  signal insert_interval_seconds    : bool_t;
begin

  timestamp_vld   <= iprotocol.time_vld when its(ctrl.bypass) else ctrl.time_vld and allow_time_xfer;
  timestamp       <= iprotocol.time when its(ctrl.bypass) else ctrl.time;

  interval_vld             <= iprotocol.sample_interval_vld when its(ctrl.bypass) else insert_interval_fraction or insert_interval_seconds;
  insert_interval_fraction <= ctrl.insert_interval_fraction or insert_interval_fraction_r;
  insert_interval_seconds  <= ctrl.insert_interval_seconds or insert_interval_seconds_r;
  interval                 <= ctrl.interval when its(insert_interval_fraction or insert_interval_seconds) else iprotocol.sample_interval;

  pipeline : process(clk)
  begin
    if rising_edge(clk) then
      if rst = '1' then
        protocol_r        <= timed_sample_prot.complex_short_timed_sample.PROTOCOL_ZERO;
        oeof              <= '0';
        insert_interval_fraction_r <= bfalse;
        insert_interval_seconds_r <= bfalse;
      elsif ordy = '1' then
        protocol_r.sample                         <= iprotocol.sample;
        protocol_r.sample_vld                     <= iprotocol.sample_vld;
        protocol_r.time                           <= timestamp;
        protocol_r.time_vld                       <= timestamp_vld;
        protocol_r.sample_interval                <= interval;
        protocol_r.sample_interval_vld            <= interval_vld;
        protocol_r.flush                          <= iprotocol.flush;
        protocol_r.discontinuity                  <= iprotocol.discontinuity;
        protocol_r.metadata                       <= iprotocol.metadata;
        protocol_r.metadata_vld                   <= iprotocol.metadata_vld;
        oeof                                      <= ieof;
        insert_interval_fraction_r                <= bfalse;
        insert_interval_seconds_r                 <= bfalse;
      else
        if its(ctrl.insert_interval_fraction) then
          insert_interval_fraction_r                <= btrue; 
        end if;
        if its(ctrl.insert_interval_seconds) then
          insert_interval_seconds_r                <= btrue;
        end if;
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
  data_counter_en  <= ordy and iprotocol.sample_vld;

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
