-- modified version of circuit in section "4.5 Closed loop solution" in
-- http://www.sunburst-design.com/papers/CummingsSNUG2008Boston_CDC.pdf,
-- modified to support sticky bit output and clear in destination clock domain
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;

entity fast_pulse_to_slow_sticky is
  port(
    -- fast clock domain
    fast_clk    : in  std_logic;
    fast_rst    : in  std_logic;
    fast_pulse  : in  std_logic; -- pulse to be detected w/ sticky bit out
    -- slow clock domain
    slow_clk    : in  std_logic;
    slow_rst    : in  std_logic;
    slow_clr    : in  std_logic;  -- clears sticky bit
    slow_sticky : out std_logic); -- sticky bit set when fast_pulse is high,
                                  -- sync'd to slow clock domain
end entity fast_pulse_to_slow_sticky;
architecture rtl of fast_pulse_to_slow_sticky is
  signal fast_pulse_sticky : std_logic := '0';
  signal fast_clr          : std_logic := '0';
  signal slow_sticky_r2    : std_logic := '0';
  signal slow_sticky_s     : std_logic := '0';
begin

  ------------------------------------------------------------------------------
  -- fast clock domain
  ------------------------------------------------------------------------------

  fast_pulse_sticky_gen : process(fast_clk)
  begin
    if(rising_edge(fast_clk)) then
      if(fast_rst = '1') then
        fast_pulse_sticky <= '0';
      else
        fast_pulse_sticky <= (fast_pulse or fast_pulse_sticky) and
                             (not fast_clr);
      end if;
    end if;
  end process fast_pulse_sticky_gen;

  clr_two_reg_sync : work.cdc.single_bit
    generic map(
      N         => 2,
      IREG      => '1',
      RST_LEVEL => '0')
    port map(
      src_clk => slow_clk,
      src_rst => slow_rst,
      src_en  => '1',
      src_in  => slow_clr,
      dst_clk => fast_clk,
      dst_rst => fast_rst,
      dst_out => fast_clr);

  ------------------------------------------------------------------------------
  -- slow clock domain
  ------------------------------------------------------------------------------

  sticky_two_reg_sync : work.cdc.single_bit
    generic map(
      N         => 2,
      IREG      => '0', -- no input reg, since it is effectively done by
                        -- fast_pulse_sticky_gen
      RST_LEVEL => '0')
    port map(
      src_clk => fast_clk,
      src_rst => fast_rst,
      src_en  => '1',
      src_in  => fast_pulse_sticky,
      dst_clk => slow_clk,
      dst_rst => slow_rst,
      dst_out => slow_sticky_r2);

  slow_sticky_reg : process(slow_clk)
  begin
    if(rising_edge(slow_clk)) then
      if(slow_rst = '1') then
        slow_sticky_s <= '0';
      else
        -- introduce combinatorial clear *after* the 2-reg sync to mitigate
        -- metastability
        slow_sticky_s <= slow_sticky_r2 and (not slow_clr);
      end if;
    end if;
  end process slow_sticky_reg;

  slow_sticky <= slow_sticky_s;

end rtl;
