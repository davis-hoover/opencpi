-- THIS FILE WAS ORIGINALLY GENERATED ON Mon Sep 14 15:38:36 2020 EDT
-- BASED ON THE FILE: source.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: source

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of worker is
  signal samples_r        : ulong_t;
  signal eof_r            : bool_t;
  signal firstDrop_r      : ulong_t;
  signal dropped_r        : bool_t;
  signal firstReady_r     : bool_t;
  signal count_r          : uchar_t;
  signal sendTimestamp    : bool_t;
  signal sendTime1_r      : bool_t; -- send LSB of time
  signal sendTime2_r      : bool_t; -- send LSM of time
  signal time_to_send_r   : ulonglong_t;
  signal fraction_written : bool_t;
begin
  fraction_written                  <= props_in.fraction_written and ctl_in.is_operating;
  props_out.countBeforeBackPressure <= firstDrop_r;
  props_out.time_to_send            <= time_to_send_r;
  props_out.valuesSent              <= samples_r;
  out_out.valid                     <= to_bool(its(sendTime1_r) or sendTime2_r or
                                               (samples_r < props_in.valuesToSend and count_r = 0 and
                                                firstReady_r and not its(eof_r)));
  out_out.eof         <= eof_r;
  out_out.data        <= std_logic_vector(time_to_send_r(31 downto 0)) when its(sendTime1_r) else
                         std_logic_vector(time_to_send_r(63 downto 32)) when its(sendTime2_r) else
                         std_logic_vector(samples_r);
  out_out.eom         <= sendTime2_r;
  out_out.byte_enable <= (others => '1');
  out_out.opcode      <= (0 => '1', others => '0') when sendTime1_r or sendTime2_r else (others => '0');
  pulse : cdc.cdc.pulse
    port map(src_clk => ctl_in.clk,
             src_rst => ctl_in.reset,
             src_in  => fraction_written,
             src_rdy => open,
             dst_clk => out_in.clk,
             dst_rst => out_in.reset,
             dst_out => sendTimestamp);

  source : process(out_in.clk)
  begin
    if rising_edge(out_in.clk) then
      if its(out_in.reset) then
        samples_r       <= (others => '0');
        eof_r           <= bfalse;
        dropped_r       <= bfalse;
        firstDrop_r     <= (others => '1');
        count_r         <= (others => '0');
        firstReady_r    <= bfalse;
        sendTime1_r     <= bfalse;
        sendTime2_r     <= bfalse;
        time_to_send_r  <= (others => '0');
      elsif sendTimestamp and props_in.timed then
        sendTime1_r    <= btrue;
        time_to_send_r <= (time_in.seconds & time_in.fraction) + props_in.fraction;
      elsif sendTime1_r and out_in.ready then
        sendTime2_r    <= btrue;
        sendTime1_r    <= bfalse;
      elsif not its(firstReady_r) and (not its(props_in.timed) or sendTime2_r) then
        sendTime2_r    <= bfalse;
        if its(out_in.ready) then
          firstReady_r <= btrue;
        end if;
      elsif firstReady_r and not its(eof_r) then -- operating after first out_in.ready
        if count_r = 0 then
          if its(out_in.ready) then
            if samples_r < props_in.valuesToSend then
              samples_r <= samples_r + 1;
            else
              eof_r <= btrue;
            end if;
            if props_in.clockDivisor /= 1 then
              count_r <= to_uchar(1);
            end if;
          elsif not dropped_r then
            dropped_r <= btrue;
            firstDrop_r <= samples_r;
          end if;
        elsif count_r = (props_in.clockDivisor - 1) then
          count_r <= (others => '0');
        else
          count_r <= count_r + 1;
        end if;
      end if;
    end if;
  end process;
end rtl;
