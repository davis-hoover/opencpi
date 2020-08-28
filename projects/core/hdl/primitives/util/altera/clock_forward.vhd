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

library IEEE;
use IEEE.std_logic_1164.all, IEEE.numeric_std.all;
library altera_mf;
use altera_mf.altera_mf_components.all;
library util;

entity clock_forward is
  generic (
    INVERT_CLOCK : boolean := false;
    SINGLE_ENDED : boolean := true
  );
  port (
    RST       : in  std_logic;
    CLK_IN    : in  std_logic;
    CLK_OUT_P : out std_logic;
    CLK_OUT_N : out std_logic
  );
end entity clock_forward;

architecture rtl of clock_forward is

  signal clk_fwd : std_logic_vector(0 downto 0);
  signal clk_p   : std_logic_vector(0 downto 0);
  signal clk_n   : std_logic_vector(0 downto 0);
  signal din_ris : std_logic := '0';
  signal din_fal : std_logic := '0';

begin

  din_ris <= '0' when INVERT_CLOCK else '1';
  din_fal <= '1' when INVERT_CLOCK else '0';

  prim : util.util.oddr
    port map(
      clk     => CLK_IN,
      rst     => RST,
      din_ris => din_ris,
      din_fal => din_fal,
      ddr_out => clk_fwd(0));

  -- TODO / FIXME - investigate replacement of altera_mf.altera_mf_components.altiobuf_out w/ util.util.BUFFER_OUT_1

  diff_clk_out : if (SINGLE_ENDED = false) generate
    altiobuf_out_inst : altiobuf_out
      generic map (
        intended_device_family                => "unused",
        enable_bus_hold                       => "FALSE",
        left_shift_series_termination_control => "FALSE",
        number_of_channels                    => 1,
        open_drain_output                     => "FALSE",
        pseudo_differential_mode              => "FALSE",
        use_differential_mode                 => "TRUE",
        use_oe                                => "FALSE",
        use_out_dynamic_delay_chain1          => "FALSE",
        use_out_dynamic_delay_chain2          => "FALSE",
        use_termination_control               => "FALSE",
        width_ptc                             => 14,
        width_stc                             => 14,
        lpm_hint                              => "UNUSED",
        lpm_type                              => "altiobuf_out"
      )
      port map (
        datain                       => clk_fwd,
        dataout                      => clk_p,
        dataout_b                    => clk_n,
        io_config_clk                => '0',
        io_config_clkena             => (others => '0'),
        io_config_datain             => '0',
        io_config_update             => '0',
        oe                           => (others => '1'),
        oe_b                         => (others => '1'),
        parallelterminationcontrol   => (others => '0'),
        parallelterminationcontrol_b => (others => '0'),
        seriesterminationcontrol     => (others => '0'),
        seriesterminationcontrol_b   => (others => '0')
      );

    CLK_OUT_P <= clk_p(0);
    CLK_OUT_N <= clk_n(0);

  end generate diff_clk_out;

  single_clk_out : if (SINGLE_ENDED = true) generate
    altiobuf_out_inst : altiobuf_out
      generic map (
        intended_device_family                => "unused",
        enable_bus_hold                       => "FALSE",
        left_shift_series_termination_control => "FALSE",
        number_of_channels                    => 1,
        open_drain_output                     => "FALSE",
        pseudo_differential_mode              => "FALSE",
        use_differential_mode                 => "FALSE",
        use_oe                                => "FALSE",
        use_out_dynamic_delay_chain1          => "FALSE",
        use_out_dynamic_delay_chain2          => "FALSE",
        use_termination_control               => "FALSE",
        width_ptc                             => 14,
        width_stc                             => 14,
        lpm_hint                              => "UNUSED",
        lpm_type                              => "altiobuf_out"
      )
      port map (
        datain                       => clk_fwd,
        dataout                      => clk_p,
        dataout_b                    => open,
        io_config_clk                => '0',
        io_config_clkena             => (others => '0'),
        io_config_datain             => '0',
        io_config_update             => '0',
        oe                           => (others => '1'),
        oe_b                         => (others => '1'),
        parallelterminationcontrol   => (others => '0'),
        parallelterminationcontrol_b => (others => '0'),
        seriesterminationcontrol     => (others => '0'),
        seriesterminationcontrol_b   => (others => '0')
      );

    CLK_OUT_P <= clk_p(0);
    CLK_OUT_N <= '0';

  end generate single_clk_out;

end rtl;
