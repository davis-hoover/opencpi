-- THIS FILE WAS ORIGINALLY GENERATED ON Mon Sep 14 15:38:36 2020 EDT
-- BASED ON THE FILE: source.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: source

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of worker is
  signal do_work : bool_t;
  signal samples : ulong_t;
  signal eof : bool_t;
begin
  out_out.data  <= from_short(props_in.value);
  out_out.valid <= to_bool(its(out_in.ready) and samples < props_in.nsamples);
  out_out.eof   <= eof;
  source : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        samples <= (others => '0');
        eof     <= bfalse;
      elsif its(out_in.ready) then
        if samples < props_in.nsamples then
          samples <= samples + 1;
        else
          eof <= btrue;
        end if;
      end if;
    end if;
  end process;
end rtl;
