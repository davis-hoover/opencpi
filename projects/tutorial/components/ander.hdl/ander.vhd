-- THIS FILE WAS ORIGINALLY GENERATED ON Sat Sep 12 12:08:28 2020 EDT
-- BASED ON THE FILE: ander.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: ander

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of worker is
  signal do_work : bool_t;
begin
  -- When we are allowed to process:
  do_work <= out_in.ready and in1_in.valid and in2_in.valid;
  -- Outputs:
  in1_out.take <= do_work;
  in2_out.take <= do_work;
  out_out.valid <= do_work;
  out_out.data(15 downto 0) <= in1_in.data and in2_in.data;
  out_out.data(31 downto 16) <= in1_in.data;
end rtl;
