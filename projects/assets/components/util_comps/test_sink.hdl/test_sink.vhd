-- THIS FILE WAS ORIGINALLY GENERATED ON Mon Sep 14 15:38:36 2020 EDT
-- BASED ON THE FILE: source.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: source

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of worker is
  signal data_seen_r   : bool_t;
  signal eof_r         : bool_t;
  signal count_error_r : bool_t;
  signal count_r       : ulong_t;
  signal time_first_r  : ulonglong_t;
  signal time_eof_r    : ulonglong_t;
begin
  props_out.countError <= count_error_r;
  props_out.valuesReceived <= count_r;
  props_out.timeFirst <= time_first_r;
  props_out.timeEOF <= time_eof_r;

  in_out.take         <= btrue;
  ctl_out.finished    <= eof_r;

  source : process(in_in.clk)
  begin
    if rising_edge(in_in.clk) then
      if its(in_in.reset) then
        count_r         <= (others => '0');
        count_error_r   <= bfalse;
        time_first_r    <= (others => '0');
        time_eof_r      <= (others => '0');
        data_seen_r     <= bfalse;
        eof_r           <= bfalse;
      elsif its(in_in.valid) then
        data_seen_r     <= btrue;
        if not data_seen_r then
          time_first_r  <= time_in.seconds & time_in.fraction;
        end if;
        if to_ulong(in_in.data) /= count_r then
          count_error_r <= btrue;
        end if;
        count_r <= count_r + 1;
      elsif in_in.eof and not its(eof_r) then
        time_eof_r <= time_in.seconds & time_in.fraction;
        eof_r      <= btrue;
      end if;
    end if;
  end process;
end rtl;
