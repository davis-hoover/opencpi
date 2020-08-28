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

library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library protocol, dac;

entity txen_generator is
  port(
    on_off0_clk    : in  std_logic;
    wci_reset      : in  std_logic;
    on_off0_reset  : in  std_logic;
    on_off0_ready  : in  std_logic;
    on_off0_opcode : in  protocol.tx_event.opcode_t;
    on_off0_eof    : in  std_logic;
    on_off0_take   : out std_logic;
    on_off1_clk    : in  std_logic;
    on_off1_reset  : in  std_logic;
    on_off1_ready  : in  std_logic;
    on_off1_opcode : in  protocol.tx_event.opcode_t;
    on_off1_eof    : in  std_logic;
    on_off1_take   : out std_logic;
    txen           : out std_logic);
end entity txen_generator;

architecture rtl of txen_generator is
  signal on_off0_demarshaller_oprotocol : protocol.tx_event.protocol_t :=
                                          protocol.tx_event.PROTOCOL_ZERO;
  signal on_off1_demarshaller_oprotocol : protocol.tx_event.protocol_t :=
                                          protocol.tx_event.PROTOCOL_ZERO;
  signal on_off0_connected : std_logic := '0';
  signal on_off1_connected : std_logic := '0';
  signal is_operating      : std_logic := '0';
begin

  on_off0_demarshaller : protocol.tx_event.tx_event_demarshaller
    port map(
      clk       => on_off0_clk,
      rst       => on_off0_reset,
      -- INPUT
      iready    => on_off0_ready,
      iopcode   => on_off0_opcode,
      ieof      => on_off0_eof,
      itake     => on_off0_take,
      -- OUTPUT
      oprotocol => on_off0_demarshaller_oprotocol,
      ordy      => '1');
  --on_off0_out.clk <= wsi_clk;

  on_off1_demarshaller : protocol.tx_event.tx_event_demarshaller
    port map(
      clk       => on_off1_clk,
      rst       => on_off1_reset,
      -- INPUT
      iready    => on_off1_ready,
      iopcode   => on_off1_opcode,
      ieof      => on_off1_eof,
      itake     => on_off1_take,
      -- OUTPUT
      oprotocol => on_off1_demarshaller_oprotocol,
      ordy      => '1');
  --on_off1_out.clk <= wsi_clk;

  on_off0_connected <= not on_off0_reset; -- TODO / FIXME - UNDOCUMENTED AND SUBJECTED TO CHANGE
  on_off1_connected <= not on_off1_reset; -- TODO / FIXME - UNDOCUMENTED AND SUBJECTED TO CHANGE
  is_operating <= not wci_reset; -- mimicking behavior in shell

  event_in_x2_to_txen : dac.dac.event_in_x2_to_txen
    port map(
      clk                  => on_off0_clk,
      reset                => on_off0_reset,
      txon_pulse_0         => on_off0_demarshaller_oprotocol.txOn,
      txoff_pulse_0        => on_off0_demarshaller_oprotocol.txOff,
      event_in_connected_0 => on_off0_connected,
      is_operating_0       => is_operating,
      txon_pulse_1         => on_off1_demarshaller_oprotocol.txOn,
      txoff_pulse_1        => on_off1_demarshaller_oprotocol.txOff,
      event_in_connected_1 => on_off1_connected,
      is_operating_1       => is_operating,
      txen                 => txen);

end rtl;
