-- THIS FILE WAS ORIGINALLY GENERATED ON Sat Sep 12 12:08:22 2020 EDT
-- BASED ON THE FILE: square.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: square

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of worker is
  signal do_work : bool_t;
  signal cnt : unsigned(7 downto 0);
begin
  -- When we are allowed to process data:
  do_work <= out_in.ready;
  -- Outputs:
  out_out.data <= (others => '1') when cnt < 32 else (others => '0');
  out_out.valid <= do_work;
  -- Generate the square pulse's counter
  square : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        cnt <= (others => '0');
      elsif its(do_work) then -- advance when we are pushing
        cnt <= cnt + 1;
        if cnt = 63 then
          cnt <= (others => '0');
        end if;
      end if;
    end if;
  end process square;
end rtl;
