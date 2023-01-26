-- ad9361_prbs_test_xs HDL implementation.
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
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of worker is

  constant q_low_c  : integer := 16;
  constant q_high_c   : integer := 27;
  constant i_low_c  : integer := 0;
  constant i_high_c  : integer := 11;

  signal data_in_i  : std_logic_vector((i_high_c - i_low_c) downto 0);
  signal data_in_q  : std_logic_vector((q_high_c - q_low_c) downto 0);

  --AD9361 PRBG is 16 bits long
  signal prbg_data    : std_logic_vector(15 downto 0);
  signal ad9361_prbg_data : std_logic_vector(15 downto 0);

  signal sync_test_counter_en : std_logic;
  signal output_reg_en    : std_logic;

  signal match_counter    : unsigned(31 downto 0);
  signal sync_test_counter  : unsigned(31 downto 0);

  signal time_out_counter   : unsigned(31 downto 0);

  type state_t is (idle_s, check_sync_s, get_result_s, done_s);

  signal current_sync_state : state_t;
  signal next_sync_state : state_t;

  --Only 8 bits of Q are shared with I. Only need to reverse these 8 bit
  signal q_rev    : std_logic_vector(7 downto 0);
  --High when the 8 shared bits of I and Q are equal
  signal i_q_equal  : std_logic;

  signal valid : std_logic;

  signal valid_counter : unsigned(31 downto 0);
  signal valid_data_counter : unsigned(31 downto 0);

  type stl_array_t is array (natural range<>) of std_logic_vector(31 downto 0);
  signal last_values : stl_array_t(0 to 7) := (others=>(others=>'0'));

  signal ramp_data         : std_logic_vector(11 downto 0);
  signal ramp_match_i      : std_logic;
  signal ramp_match_q      : std_logic;

begin

  -- This worker is designed to synchronise with the pseudo random bit generator
  -- which is part of the built in self test unit in the AD9361 RF transceiver IC.
  -- The PRBG can inject directly into the Rx data port of the AD9361, thus
  -- allowing the integrity of the connection between the AD9361 and the FPGA
  -- to be tested. Since the polynomial of the PRBG is known this module will
  -- attempt to synchronise a local PRBG with the one in the AD9361.
  -- If the data connection between the AD9361 and the FPGA is good then once
  -- synchronised both the local PRBG and data from the AD9361 PRBG should
  -- always match.

  -- The polynomial for the PRBG is given as:
  -- G(x) = x^16 + x^15 + x^14 + x^13 + x^12 + x^11 + x^10 + x^9 + x^8 + x^7 + x^6 + x^5 + x^3 + x^2 + 1

  -- Always take data when it is available
  input_out.take <= input_in.ready;
  valid <= '1' when input_in.valid = '1' and input_in.opcode = complex_short_timed_sample_sample_op_e else '0';

  -- Split I and Q data
  data_in_i <= input_in.data(i_high_c downto i_low_c);
  data_in_q <= input_in.data(q_high_c downto q_low_c);

  -- The AD9361 PRBG is 16 bits wide, but the I and Q signals are only 12 bits each
  -- The I data is the 12 MSBs of the PRBG output
  -- The Q data is the 12 MSBs of the reflected PRBG
  -- Therefore the whole 16 bit PRBG can be reconstructed
  -- PSBS 15 14 13 12 11 10 09 08 07 06 05 04 03 02 01 00 (Bit number of PRBG)
  -- Rx   11 10 09 08 07 06 05 04 03 02 01 00 (Bit number of truncated signals
  -- I  15 14 13 12 11 10 09 08 07 06 05 04 (Use all bits of I)
  -- Q  00 01 02 03 04 05 06 07 08 09 10 11 (Use bits 8,9,10,11 of Q)
  ad9361_prbg_data <= data_in_i & data_in_q(8) & data_in_q(9) & data_in_q(10) & data_in_q(11);

  -- Calculate a local version of the AD9361 PRBG
  prbg_p : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        -- This is the seed value of the AD9361 PRBG
        prbg_data <= X"0A54";
      elsif valid = '1'then
        if ad9361_prbg_data = prbg_data then
          -- If the local and remote PRBG match then advance the local PRBG
          prbg_data <= prbg_data(14 downto 0) &
                (prbg_data(1) xor prbg_data(2) xor prbg_data(4)
                xor prbg_data(5) xor prbg_data(6) xor prbg_data(7)
                xor prbg_data(8) xor prbg_data(9) xor prbg_data(10)
                xor prbg_data(11) xor prbg_data(12) xor prbg_data(13)
                xor prbg_data(14) xor prbg_data(15));
        else
          -- If the local and remote PGBG do not match then initialise
          -- the local PRBG to the value of the remote one, and advance it
          prbg_data <= ad9361_prbg_data(14 downto 0) &
                (ad9361_prbg_data(1) xor ad9361_prbg_data(2) xor ad9361_prbg_data(4)
                xor ad9361_prbg_data(5) xor ad9361_prbg_data(6) xor ad9361_prbg_data(7)
                xor ad9361_prbg_data(8) xor ad9361_prbg_data(9) xor ad9361_prbg_data(10)
                xor ad9361_prbg_data(11) xor ad9361_prbg_data(12) xor ad9361_prbg_data(13)
                xor ad9361_prbg_data(14) xor ad9361_prbg_data(15));
        end if;
      end if;
    end if;
  end process;

  --Calculate local version of the ramp (used for loopback testing for ramp)
  rampProcess : process(ctl_in.clk)
  begin
     if (rising_edge(ctl_in.clk)) then
        if (ctl_in.reset = '1') then
           ramp_data                      <= (others => '0');
        elsif (valid = '1') then
           if (data_in_i = ramp_data) then
              ramp_data                   <= ramp_data + 1;
           else
              ramp_data                   <= data_in_i + 1;
           end if;
        end if;
     end if;
  end process;

  --Set flags if they match
  ramp_match_i                            <= '1' when (ramp_data = data_in_i) else '0';
  ramp_match_q                            <= '1' when (not(ramp_data) = data_in_q) else '0';

  -- Some of the bits should be the same in both I and Q
  -- Rx 11 10 09 08 07 06 05 04 03 02 01 00 (Bit number of truncated signals
  -- I  XX XX XX XX 11 10 09 08 07 06 05 04 Bits 7 downto 0 of I
  -- Q  XX XX XX XX 04 05 06 07 08 09 10 11 Bits 0 upto 7 of Q
  -- To ensure Rx/Tx data port integrity this is tested

  -- First Reverse Q
  q_rev <= data_in_q(0) & data_in_q(1) & data_in_q(2) & data_in_q(3)
      & data_in_q(4) & data_in_q(5) & data_in_q(6) & data_in_q(7);

  -- Then Test I and reverse of Q are equal
  i_q_equal <= '1' when data_in_i(7 downto 0) = q_rev else '0';

  -- Synchronously advances the main state machine
  check_sync_adv_p : process(ctl_in.clk)
  begin

    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        current_sync_state <= idle_s;
      else
        current_sync_state <= next_sync_state;
      end if;
    end if;

  end process;

  -- Main state machine
  -- Handles GO and DONE commands from the OpenCPI control plane
  -- On a go signal the module will count in props_in.test_length samples
  -- and record for how many samples the local PRBG matched the AD9361s PRBG output
  -- The done signal is set when the test completes. The state machine returns to
  -- idle when the go signal is returned to low after done is set.
  check_sync_p : process(current_sync_state, props_in.go, sync_test_counter,
                         props_in.test_length, time_out_counter, props_in.time_out)
  begin

    next_sync_state <= current_sync_state;
    sync_test_counter_en <= '0';
    output_reg_en <= '0';
    props_out.done <= '0';

    case current_sync_state is
      when idle_s =>
        -- Wait until given the GO signal
        if props_in.go = '1' then
          next_sync_state <= check_sync_s;
        end if;

      when check_sync_s =>
        --Enable the test counter and match counter
        sync_test_counter_en <= '1';
        --When enough samples have been recieved
        if sync_test_counter >= props_in.test_length - 1 then
          next_sync_state <= get_result_s;
        elsif time_out_counter >= props_in.time_out then
          --This occurs if an input sample has not been received for
          --longer than the time_out interval.
          next_sync_state <= get_result_s;
        end if;
      when get_result_s =>
        --Register how many time the local PRBG matched the remote one
        output_reg_en <= '1';
        next_sync_state <= done_s;

      when done_s =>
        --Indicate on the control plane that the test is done
        props_out.done <= '1';
        --Wait until the GO signal is set low, then return to idle state
        if props_in.go = '0' then
          next_sync_state <= idle_s;
        end if;
      when others =>
        next_sync_state <= idle_s;
    end case;
  end process;

  -- Counts valid input samples so that a test of a set length can be run
  -- Set to zero when not enabled
  sync_test_counter_p : process(ctl_in.clk)
  begin

    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        sync_test_counter <= (others => '0');
      elsif valid = '1' then
        if sync_test_counter_en = '1' then
          sync_test_counter <= sync_test_counter + 1;
        else
          sync_test_counter <= (others => '0');
        end if;
      end if;
    end if;
  end process;

  -- Counts the number of times in a row the local PRBG matched
  -- the AD9361's PRBG.
  -- Set to zero when not enabled
  match_counter_p : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        match_counter <= (others => '0');
      elsif valid = '1' then
        if sync_test_counter_en = '1' then
          if (props_in.mode = 0) then
             if ad9361_prbg_data = prbg_data and i_q_equal = '1' then
               match_counter <= match_counter + 1;
             else
               match_counter <= (others => '0');
            end if;
         else
            if (ramp_match_i = '1' and ramp_match_q = '1') then
               match_counter <= match_counter + 1;
            else
               match_counter <= (others => '0');
            end if;
         end if;
        else
          match_counter <= (others => '0');
        end if;
      end if;
    end if;
  end process;

  -- Registers the output of the sync count so that it can
  -- be read over the OpenCPI control plane
  sync_count_reg_p : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        props_out.result <= (others => '0');
      else
        if output_reg_en = '1' then
          props_out.result <= match_counter;
        end if;
      end if;
    end if;
  end process;

  -- Time out counter
  -- If there is no data is being received this time out
  -- triggers the test to end.
  time_out_counter_p : process(ctl_in.clk)
  begin

    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        time_out_counter <= (others => '0');
      elsif ctl_in.is_operating = '1' then
        if sync_test_counter_en = '1' then
          if valid = '1' then
            -- Reset timer every time a new sample is recieved
            time_out_counter <= (others => '0');
          else
            -- Otherwise start counting up
            time_out_counter <= time_out_counter + 1;
          end if;
        else
          -- When counter is disabled reset counter to 0
          time_out_counter <= (others => '0');
        end if;
      end if;
    end if;
  end process;

  debug_sample_counter : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        valid_data_counter <= (others=>'0');
        valid_counter <= (others=>'0');
      else
        if valid = '1' then
        valid_data_counter <= valid_data_counter + 1;
        end if;

        if input_in.valid = '1' then
          valid_counter <= valid_counter + 1;
        end if;
      end if;
    end if;
  end process;
  props_out.valid_data_counter <= valid_data_counter;
  props_out.valid_counter <= valid_counter;


  last_value_reg_p : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if valid = '1' and props_in.last_values_store = '1' then

        last_values(0) <= input_in.data;

        last_value_reg_g : for gen_var in 0 to 6 loop
          last_values(gen_var+1) <= last_values(gen_var);
        end loop last_value_reg_g;

      end if;
    end if;
  end process;


  GEN_REG: for I in 0 to 7 generate
    props_out.last_values(I) <= unsigned(last_values(I));
  end generate GEN_REG;

end rtl;

