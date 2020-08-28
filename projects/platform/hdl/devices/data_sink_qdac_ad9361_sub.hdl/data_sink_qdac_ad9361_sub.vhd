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
library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library dac; use dac.ad936x.all;

architecture rtl of worker is
  constant DATA_BUS_BITS_ARE_REVERSED : boolean := false;
  signal wci_is_operating             : std_logic := '0';
  signal wci_use_two_r_two_t_timing   : std_logic := '0';
  signal dacddr_tx_data               : std_logic_vector(5 downto 0);
  signal wsi_clk                      : std_logic := '0';
  signal wsi_ch0_data_i               : std_logic_vector(dac.ad936x.DATA_BIT_WIDTH-1 downto 0) :=
                                        (others => '0');
  signal wsi_ch1_data_i               : std_logic_vector(dac.ad936x.DATA_BIT_WIDTH-1 downto 0) :=
                                        (others => '0');
  signal wsi_ch0_data_q               : std_logic_vector(dac.ad936x.DATA_BIT_WIDTH-1 downto 0) :=
                                        (others => '0');
  signal wsi_ch1_data_q               : std_logic_vector(dac.ad936x.DATA_BIT_WIDTH-1 downto 0) :=
                                        (others => '0');
  signal wsi_ch0_valid                : std_logic := '0';
  signal wsi_ch1_valid                : std_logic := '0';
  signal wsi_txen                     : std_logic := '0';
  signal wsi_in0_opcode               : protocol.tx_event.opcode_t
                                      := protocol.tx_event.TXOFF;
  signal wsi_in1_opcode               : protocol.tx_event.opcode_t
                                      := protocol.tx_event.TXOFF;
begin
  
  wci_is_operating <= not wci_reset; -- mimicking behavior in shell

  wsi_ch0_data_i    <= dev_data_ch0_in_in.data_i(
      dev_data_ch0_in_in.data_i'left downto 
      dev_data_ch0_in_in.data_i'left-dac.ad936x.DATA_BIT_WIDTH+1);
  wsi_ch1_data_i    <= dev_data_ch1_in_in.data_i(
      dev_data_ch0_in_in.data_i'left downto 
      dev_data_ch0_in_in.data_i'left-dac.ad936x.DATA_BIT_WIDTH+1);
  wsi_ch0_data_q    <= dev_data_ch0_in_in.data_q(
      dev_data_ch0_in_in.data_i'left downto 
      dev_data_ch0_in_in.data_i'left-dac.ad936x.DATA_BIT_WIDTH+1);
  wsi_ch1_data_q    <= dev_data_ch1_in_in.data_q(
      dev_data_ch0_in_in.data_i'left downto 
      dev_data_ch0_in_in.data_i'left-dac.ad936x.DATA_BIT_WIDTH+1);
  wsi_ch0_valid <= dev_data_ch0_in_in.valid;
  wsi_ch1_valid <= dev_data_ch1_in_in.valid;

  data_rate_config_sdr : if (DATA_RATE_CONFIG_p = SDR_e) generate
  begin

    control_interfacer : entity work.control_interfacer
      generic map(
        LVDS_P                     => its(LVDS_p),
        HALF_DUPLEX_P              => its(HALF_DUPLEX_p),
        SINGLE_PORT_P              => its(SINGLE_PORT_p),
        DATA_RATE_CONFIG_P         => SDR,
        DATA_BUS_BITS_ARE_REVERSED => DATA_BUS_BITS_ARE_REVERSED)
      port map(
        -- wci
        wci_clk                      => wci_Clk,
        wci_reset                    => wci_reset,
        wci_is_operating             => wci_is_operating,
        -- dev_cfg_data
        wci_config_is_two_r          => dev_cfg_data_in.config_is_two_r,
        wci_ch0_handler_is_present   => dev_cfg_data_out.ch0_handler_is_present,
        wci_ch1_handler_is_present   => dev_cfg_data_out.ch1_handler_is_present,
        wci_data_bus_index_direction => dev_cfg_data_out.data_bus_index_direction,
        wci_data_clk_is_inverted     => dev_cfg_data_out.data_clk_is_inverted,
        wci_islvds                   => dev_cfg_data_out.islvds,
        wci_isdualport               => dev_cfg_data_out.isdualport,
        wci_isfullduplex             => dev_cfg_data_out.isfullduplex,
        wci_isddr                    => dev_cfg_data_out.isddr,
        wci_present                  => dev_cfg_data_out.present,
        -- dev_cfg_data_tx
        wci_config_is_two_t          => dev_cfg_data_tx_in.config_is_two_t,
        wci_force_two_r_two_t_timing => dev_cfg_data_tx_in.force_two_r_two_t_timing,
        -- dev_data_ch0
        static_ch0_in_present        => dev_data_ch0_in_in.present,
        -- dev_data_ch1
        static_ch1_in_present        => dev_data_ch1_in_in.present,
        -- business logic
        wci_use_two_r_two_t_timing   => wci_use_two_r_two_t_timing);

    interleaver : entity work.interleaver
      generic map(
        LVDS_P             => its(LVDS_p),
        HALF_DUPLEX_P      => its(HALF_DUPLEX_p),
        SINGLE_PORT_P      => its(SINGLE_PORT_p),
        DATA_RATE_CONFIG_P => SDR)
      port map(
        -- data_sink_dac_ad9361_sub
        wci_clk                      => wci_clk,
        wci_rst                      => wci_reset,
        wci_use_two_r_two_t_timing   => wci_use_two_r_two_t_timing,
        wsi_txen                     => wsi_txen,
        -- dev_cfg_data_tx
        wci_force_two_r_two_t_timing => dev_cfg_data_tx_in.force_two_r_two_t_timing,
        -- dev_data_clk
        dac_clk                      => dev_data_clk_in.DATA_CLK_P,
        -- dev_data_to_pins
        dacddr_data_to_pins          => dev_data_to_pins_out.data,
        dacddr_tx_frame              => dev_data_to_pins_out.tx_frame,
        -- dev_data_ch0
        wsi_ch0_data_i               => wsi_ch0_data_i,
        wsi_ch0_data_q               => wsi_ch0_data_q,
        wsi_ch0_valid                => wsi_ch0_valid,
        wsi_ch0_clk                  => dev_data_ch0_in_out.clk,
        -- dev_data_ch1
        wsi_ch1_data_i               => wsi_ch1_data_i,
        wsi_ch1_data_q               => wsi_ch1_data_q,
        wsi_ch1_valid                => wsi_ch1_valid,
        wsi_ch1_clk                  => dev_data_ch1_in_out.clk,
        -- dev_txen
        dac_txen                     => dev_txen_out.txen);

  end generate data_rate_config_sdr;

  data_rate_config_ddr : if (DATA_RATE_CONFIG_p = DDR_e) generate
  begin

    control_interfacer : entity work.control_interfacer
      generic map(
        LVDS_P                     => its(LVDS_p),
        HALF_DUPLEX_P              => its(HALF_DUPLEX_p),
        SINGLE_PORT_P              => its(SINGLE_PORT_p),
        DATA_RATE_CONFIG_P         => DDR,
        DATA_BUS_BITS_ARE_REVERSED => DATA_BUS_BITS_ARE_REVERSED)
      port map(
        -- wci
        wci_clk                      => wci_Clk,
        wci_reset                    => wci_reset,
        wci_is_operating             => wci_is_operating,
        -- dev_cfg_data
        wci_config_is_two_r          => dev_cfg_data_in.config_is_two_r,
        wci_ch0_handler_is_present   => dev_cfg_data_out.ch0_handler_is_present,
        wci_ch1_handler_is_present   => dev_cfg_data_out.ch1_handler_is_present,
        wci_data_bus_index_direction => dev_cfg_data_out.data_bus_index_direction,
        wci_data_clk_is_inverted     => dev_cfg_data_out.data_clk_is_inverted,
        wci_islvds                   => dev_cfg_data_out.islvds,
        wci_isdualport               => dev_cfg_data_out.isdualport,
        wci_isfullduplex             => dev_cfg_data_out.isfullduplex,
        wci_isddr                    => dev_cfg_data_out.isddr,
        wci_present                  => dev_cfg_data_out.present,
        -- dev_cfg_data_tx
        wci_config_is_two_t          => dev_cfg_data_tx_in.config_is_two_t,
        wci_force_two_r_two_t_timing => dev_cfg_data_tx_in.force_two_r_two_t_timing,
        -- dev_data_ch0
        static_ch0_in_present        => dev_data_ch0_in_in.present,
        -- dev_data_ch1
        static_ch1_in_present        => dev_data_ch1_in_in.present,
        -- business logic
        wci_use_two_r_two_t_timing   => wci_use_two_r_two_t_timing);

    interleaver : entity work.interleaver
      generic map(
        LVDS_P             => its(LVDS_p),
        HALF_DUPLEX_P      => its(HALF_DUPLEX_p),
        SINGLE_PORT_P      => its(SINGLE_PORT_p),
        DATA_RATE_CONFIG_P => DDR)
      port map(
        -- data_sink_dac_ad9361_sub
        wci_clk                      => wci_clk,
        wci_rst                      => wci_reset,
        wci_use_two_r_two_t_timing   => wci_use_two_r_two_t_timing,
        wsi_txen                     => wsi_txen,
        -- dev_cfg_data_tx
        wci_force_two_r_two_t_timing => dev_cfg_data_tx_in.force_two_r_two_t_timing,
        -- dev_data_clk
        dac_clk                      => dev_data_clk_in.DATA_CLK_P,
        -- dev_data_to_pins
        dacddr_data_to_pins          => dev_data_to_pins_out.data,
        dacddr_tx_frame              => dev_data_to_pins_out.tx_frame,
        -- dev_data_ch0
        wsi_ch0_data_i               => wsi_ch0_data_i,
        wsi_ch0_data_q               => wsi_ch0_data_q,
        wsi_ch0_valid                => wsi_ch0_valid,
        wsi_ch0_clk                  => dev_data_ch0_in_out.clk,
        -- dev_data_ch1
        wsi_ch1_data_i               => wsi_ch1_data_i,
        wsi_ch1_data_q               => wsi_ch1_data_q,
        wsi_ch1_valid                => wsi_ch1_valid,
        wsi_ch1_clk                  => dev_data_ch1_in_out.clk,
        -- dev_txen
        dac_txen                     => dev_txen_out.txen);

  end generate data_rate_config_ddr;

  wsi_in0_opcode <=
      protocol.tx_event.TXOFF when on_off0_in.opcode = tx_event_txOff_op_e else
      protocol.tx_event.TXON when on_off0_in.opcode = tx_event_txOn_op_e  else
      protocol.tx_event.TXOFF;
  wsi_in1_opcode <= 
      protocol.tx_event.TXOFF when on_off0_in.opcode = tx_event_txOff_op_e else
      protocol.tx_event.TXON  when on_off0_in.opcode = tx_event_txOn_op_e  else
      protocol.tx_event.TXOFF;

  wsi_txen_generator : entity work.txen_generator
    port map(
      on_off0_clk     => on_off0_in.clk,
      wci_reset       => wci_reset,
      on_off0_reset   => on_off0_in.reset,
      on_off0_ready   => on_off0_in.ready,
      on_off0_opcode  => wsi_in0_opcode,
      on_off0_eof     => on_off0_in.eof,
      on_off0_take    => on_off0_out.take,
      on_off1_clk     => on_off1_in.clk,
      on_off1_reset   => on_off1_in.reset,
      on_off1_ready   => on_off1_in.ready,
      on_off1_opcode  => wsi_in1_opcode,
      on_off1_eof     => on_off1_in.eof,
      on_off1_take    => on_off1_out.take,
      txen            => wsi_txen);

end rtl;
