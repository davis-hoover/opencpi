-- ad9361_prbs_gen_xs HDL implementation.
--
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
-- A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
-- more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all; use ieee.std_logic_unsigned.all;
library ocpi; use ocpi.types.all;

architecture rtl of worker is

  --PRBG Signals
  signal prbg_out     : std_logic_vector(31 downto 0);
  signal prbg_data    : std_logic_vector(15 downto 0);

  --Count signals
  signal ramp_data    : std_logic_vector(11 downto 0);
  signal ramp_out     : std_logic_vector(31 downto 0);

  --Output signals
  signal data_out     : std_logic_vector(output_out.data'length - 1 downto 0);

begin

  -- Calculate a local version of the AD9361 PRBG
  prbg_p : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        -- This is the seed value of the AD9361 PRBG
        prbg_data <= X"0A54";
      elsif output_in.ready = '1' then
        -- If the local and remote PRBG match then advance the local PRBG
        prbg_data <= prbg_data(14 downto 0) &
                    (prbg_data(1) xor prbg_data(2) xor prbg_data(4)
                    xor prbg_data(5) xor prbg_data(6) xor prbg_data(7)
                    xor prbg_data(8) xor prbg_data(9) xor prbg_data(10)
                    xor prbg_data(11) xor prbg_data(12) xor prbg_data(13)
                    xor prbg_data(14) xor prbg_data(15));
      end if;
    end if;
  end process;

  -- The AD9361 PRBG is 16bits wide, but the I & Q signals are only 12bits each
  -- The I data is the 12 MSBs of the PRBG output
  -- The Q data is the 12 MSBs of the reflected PRBG
  -- Therefore the whole 16 bit PRBG can be reconstructed
  -- PSBS 15 14 13 12 11 10 09 08 07 06 05 04 03 02 01 00 (Bit number of PRBG)
  -- Rx   11 10 09 08 07 06 05 04 03 02 01 00 (Bit number of truncated signals
  -- I    15 14 13 12 11 10 09 08 07 06 05 04 (Use all bits of I)
  -- Q    00 01 02 03 04 05 06 07 08 09 10 11 (Use bits 8,9,10,11 of Q)

  -- Set I
  prbg_out(15 downto 0) <= prbg_data(15 downto 4) & X"0";

  -- Set Q
  prbg_out(31 downto 16) <= prbg_data(0) & prbg_data(1) & prbg_data(2)
                            & prbg_data(3) & prbg_data(4) & prbg_data(5)
                            & prbg_data(6) & prbg_data(7) & prbg_data(8)
                            & prbg_data(9) & prbg_data(10) & prbg_data(11) & X"0";

  CountProcess : process(ctl_in.clk)
  begin
    if (rising_edge(ctl_in.clk)) then
       if (ctl_in.reset = '1') then
         ramp_data            <= (others => '0');
       elsif (output_in.ready = '1') then
         ramp_data            <= ramp_data + 1;
       end if;
    end if;
  end process;

  --Set ramp output
  ramp_out(15 downto 0)       <= ramp_data & X"0";
  ramp_out(31 downto 16)      <= not(ramp_data) & X"0";

  -- Registered output mux
  out_reg_p : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        data_out <= (others => '0');
      elsif output_in.ready = '1' then
        -- Zero values output samples
        if props_in.mode = 0 then
          data_out <= X"00000000";
        -- Full scale valued samples
        elsif props_in.mode = 1 then
          data_out <= X"7FF00000";
        -- PRBS
        elsif props_in.mode = 2 then
          data_out <= prbg_out;
        --Set value
        elsif props_in.mode = 3 then
          data_out <= std_logic_vector(props_in.set_value);
        --Count
        elsif props_in.mode = 4 then
          data_out <= ramp_out;
        else
          data_out <= (others => '0');
        end if;
      end if;
    end if;
  end process;

  -- Output streaming interface
  output_out.data         <= data_out;
  output_out.valid        <= output_in.ready when props_in.mode <= 4 else '0';
  output_out.opcode       <= complex_short_timed_sample_sample_op_e;
  output_out.byte_enable  <= (others => '1');

end rtl;

