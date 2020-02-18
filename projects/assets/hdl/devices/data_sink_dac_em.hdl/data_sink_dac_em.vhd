library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi, platform; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library util;
architecture rtl of worker is
  signal   dac_clk    : std_logic;
  signal   first, eof : bool_t;
begin
  -- generate dac clock
  clock : platform.platform_pkg.sim_clk
    generic map(frequency => from_float(dac_clk_freq_hz))
    port map   (clk => dac_clk, reset => open);

  dev_clk_gen : util.util.in2out
    port map(
      in_port  => dac_clk,
      out_port => dev_out.clk);
  out_clk_gen : util.util.in2out
    port map(
      in_port  => dac_clk,
      out_port => out_out.clk);

  out_out.valid <= out_in.ready and dev_in.valid;
  
  --TODO: Need data widener
  out_out.data  <= dev_in.data_Q & dev_in.data_I;

  process(dac_clk)
  begin
    if rising_edge(dac_clk) then
      if its(out_in.reset) then
        first <= bfalse;
        eof   <= bfalse;
      elsif its(out_in.ready and dev_in.valid and not first) then
        first <= btrue;
      elsif its(out_in.ready and first and not dev_in.valid and not eof) then
        eof <= btrue;
      end if;
    end if;
  end process;

  out_out.eof <= eof;
end rtl;

