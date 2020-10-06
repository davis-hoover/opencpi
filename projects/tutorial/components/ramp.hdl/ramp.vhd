-- THIS FILE WAS ORIGINALLY GENERATED ON Sat Sep 12 12:08:16 2020 EDT
-- BASED ON THE FILE: ramp.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: ramp

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of worker is
  signal do_work : bool_t;
  signal out_data_i, buff_data : std_logic_vector(15 downto 0);
begin
  -- When we are allowed to process data:
  do_work <= out_in.ready and in_in.valid;
  -- Outputs:
  in_out.take <= do_work;
  out_out.valid <= do_work;
  out_data_i <= std_logic_vector(signed(in_in.data) + signed(buff_data));
  out_out.data <= out_data_i;
  -- Initialize or save off previous value when valid:
  ramp : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        buff_data <= (others => '0');
      elsif its(do_work) then
        buff_data <= out_data_i;
      end if;
    end if;
  end process ramp;
end rtl;
