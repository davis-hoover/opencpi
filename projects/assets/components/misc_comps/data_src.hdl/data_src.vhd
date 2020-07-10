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
-- A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
-- details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.

library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of worker is
  constant WIDTH      : integer := to_integer(DATA_BIT_WIDTH_p);

  signal enable        : std_logic := '0';
  signal data_count    : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
  signal data_count_32 : long_t := (others => '0');
  signal data_walking      : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
  signal data_lfsr         : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
  signal data_lfsr_ordered : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
  signal data_lfsr_rev     : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
  signal data              : std_logic_vector(WIDTH-1 downto 0) := (others => '0');

  signal data_Q : std_logic_vector(15 downto 0) := (others => '0');
  signal data_I : std_logic_vector(15 downto 0) := (others => '0');
  signal out_Q  : std_logic_vector(15 downto 0) := (others => '0');
  signal out_I  : std_logic_vector(15 downto 0) := (others => '0');

  signal num_samples_valid : bool_t := bfalse;
  signal eof_req           : bool_t := bfalse; -- eof is indicated now
  signal eof_r             : bool_t := bfalse; -- we are in the sticky EOF state
begin
  props_out.debug <= data_count_32;
  ------------------------------------------------------------------------------
  -- out port
  ------------------------------------------------------------------------------

  out_out.valid       <= enable; -- implies give, only accepted if out_in.ready
  out_out.byte_enable <= (others => '1');
  out_out.eof         <= eof_r;
  odata_width_32 : if ODATA_WIDTH_p = 32 generate

    -- iqstream w/ DataWidth=32 formats Q in most significant bits, I in least
    -- significant (see OpenCPI_HDL_Development section on Message Payloads vs.
    -- Physical Data Width on Data Interfaces)
    out_out.data <= out_Q & out_I;

  end generate odata_width_32;

  -- from the component data sheet: "Data_Src selects one DATA_BIT_WIDTH_p
  -- bits-wide data bus from multiple data generation sources, packs the
  -- DATA_BIT_WIDTH_p bits in bit-forward order in the least significant bits of
  -- the I data bus and bit-reverse order in the most significant bits of the Q
  -- data bus"
  data_I(15 downto 15-WIDTH+1) <= data;
  data_I(15-WIDTH downto 0) <= (others => '0');
  data_rev : for idx in 0 to WIDTH-1 generate
    data_Q(15-idx) <= data(idx);
  end generate;
  data_Q(15-WIDTH downto 0) <= (others => '0');

  enable <= out_in.ready and props_in.enable and num_samples_valid and
            (to_bool(props_in.num_samples = -1) or
             to_bool(data_count_32 < props_in.num_samples));

  lfsr : misc_prims.misc_prims.lfsr
    generic map (
      POLYNOMIAL => std_logic_vector(LFSR_POLYNOMIAL_p),
      SEED       => std_logic_vector(LFSR_SEED_p))
    port map (
      CLK        => ctl_in.clk,
      RST        => ctl_in.reset,
      EN         => enable,
      REG        => data_lfsr);

  lfsr_rev : for idx in 0 to WIDTH-1 generate
    data_lfsr_rev(WIDTH-1-idx) <= data_lfsr(idx);
  end generate;

  data_regs : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        data_count_32 <= (others => '0');
        data_count <= (others => '0');
        data_walking(data_walking'left) <= '1';
        data_walking(data_walking'left-1 downto 0) <= (others => '0');
      elsif ctl_in.is_operating and enable = '1' then
        data_count_32 <= data_count_32 + 1;
        data_count <= std_logic_vector(unsigned(data_count) + 1);
        data_walking <= data_walking(0) &
                        data_walking(data_walking'length-1 downto 1);
      end if;
    end if;
  end process data_regs;

  -- watch for num_samples being set and running out of samples to assert EOF
  do_samples : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        eof_r             <= bfalse;
        num_samples_valid <= bfalse;
      -- assert EOF when number of samples sent (if num_samples is not -1)
      elsif (its(ZLM_WHEN_NUM_SAMPLES_REACHED_p or EOF_WHEN_NUM_SAMPLES_REACHED_p) and
             num_samples_valid and props_in.num_samples /= -1 and
             data_count_32 >= props_in.num_samples) then
        eof_r <= btrue;
      elsif its(props_in.num_samples_written) then
        num_samples_valid <= btrue;
      end if;
    end if;
  end process do_samples;

  ------------------------------------------------------------------------------
  -- mask_I, mask_Q properties
  ------------------------------------------------------------------------------

  out_Q <= data_Q and std_logic_vector(props_in.mask_Q);
  out_I <= data_I and std_logic_vector(props_in.mask_I);

  ------------------------------------------------------------------------------
  -- mode property
  ------------------------------------------------------------------------------

  with props_in.mode select
    data <= data_count           when count_e,
            data_walking         when walking_e,
            data_lfsr_ordered    when lfsr_e,
            std_logic_vector(props_in.fixed_value) when others;

  ------------------------------------------------------------------------------
  -- LFSR_bit_reverse property
  ------------------------------------------------------------------------------

  data_lfsr_ordered <= data_lfsr_rev when (props_in.LFSR_bit_reverse = btrue)
                       else data_lfsr;

end rtl;
