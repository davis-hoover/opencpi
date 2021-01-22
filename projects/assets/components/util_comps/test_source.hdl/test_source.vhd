-- THIS FILE WAS ORIGINALLY GENERATED ON Mon Sep 14 15:38:36 2020 EDT
-- BASED ON THE FILE: source.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: source

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of worker is
  signal samples : ulong_t;
  signal eof : bool_t;
  signal firstDrop : ulong_t;
  signal dropped : bool_t;
  signal firstReady : bool_t;
  signal count : uchar_t;
begin
  props_out.countBeforeBackPressure <= firstDrop;
  out_out.valid       <= to_bool(samples < props_in.valuesToSend and count = 0 and firstReady and not its(eof));
  out_out.eof         <= eof;
  out_out.data        <= std_logic_vector(samples);
  out_out.byte_enable <= (others => '1');
  out_out.opcode      <= (others => '0');
  source : process(out_in.clk)
  begin
    if rising_edge(out_in.clk) then
      if its(out_in.reset) then
        samples    <= (others => '0');
        eof        <= bfalse;
        dropped    <= bfalse;
        firstDrop  <= (others => '1');
        count      <= (others => '0');
        firstReady <= bfalse;
      elsif not firstReady then
        if its(out_in.ready) then
          firstReady <= btrue;
        end if;
      elsif count = 0 and not its(eof) then
        if its(out_in.ready) then
          if samples < props_in.valuesToSend then
            samples <= samples + 1;
          else
            eof <= btrue;
          end if;
          if props_in.clockDivisor /= 1 then
            count <= to_uchar(1);
          end if;
        elsif not dropped then
          dropped   <= btrue;
          firstDrop <= samples;
        end if;
      elsif count = (props_in.clockDivisor - 1) then
        count <= (others => '0');
      else
        count <= count + 1;
      end if;
    end if;
  end process;
end rtl;
