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
library rfdc;
library protocol; use protocol.iqstream.all;
architecture structural of worker is
  -- ctl clk domain
  signal ctl_0_demarshaller_to_ctl_tx_0_converter_pro : protocol_t
                                                      := PROTOCOL_ZERO;
  signal ctl_0_demarshaller_to_ctl_tx_0_converter_rdy : std_logic := '0';
  signal ctl_tx_0_converter_to_tx_0_cdc_tdata  : std_logic_vector(32-1 downto 0)
                                               := (others => '0');
  signal ctl_tx_0_converter_to_tx_0_cdc_tvalid        : std_logic := '0';
  signal ctl_tx_0_converter_to_tx_0_cdc_tready        : std_logic := '0';
  signal ctl_1_demarshaller_to_ctl_tx_1_converter_pro : protocol_t
                                                      := PROTOCOL_ZERO;
  signal ctl_1_demarshaller_to_ctl_tx_1_converter_rdy : std_logic := '0';
  signal ctl_tx_1_converter_to_tx_1_cdc_tdata  : std_logic_vector(32-1 downto 0)
                                               := (others => '0');
  signal ctl_tx_1_converter_to_tx_1_cdc_tvalid        : std_logic := '0';
  signal ctl_tx_1_converter_to_tx_1_cdc_tready        : std_logic := '0';
  signal ctl_0_cdc_to_ctl_rx_0_converter_tdata : std_logic_vector(32-1 downto 0)
                                               := (others => '0');
  signal ctl_0_cdc_to_ctl_rx_0_converter_tvalid       : std_logic := '0';
  signal ctl_0_cdc_to_ctl_rx_0_converter_tready       : std_logic := '0';
  signal ctl_rx_0_converter_to_ctl_0_marshaller_pro   : protocol_t
                                                      := PROTOCOL_ZERO;
  signal ctl_rx_0_converter_to_ctl_0_marshaller_rdy   : std_logic := '0';
  signal ctl_1_cdc_to_ctl_rx_1_converter_tdata : std_logic_vector(32-1 downto 0)
                                               := (others => '0');
  signal ctl_1_cdc_to_ctl_rx_1_converter_tvalid       : std_logic := '0';
  signal ctl_1_cdc_to_ctl_rx_1_converter_tready       : std_logic := '0';
  signal ctl_rx_1_converter_to_ctl_1_marshaller_pro   : protocol_t
                                                      := PROTOCOL_ZERO;
  signal ctl_rx_1_converter_to_ctl_1_marshaller_rdy   : std_logic := '0';
  -- rx clk domain
  signal rx_clk                   : std_logic_vector(2-1 downto 0)
                                  := (others => '0');
  signal rx_reset                 : std_logic_vector(2-1 downto 0)
                                  := (others => '0');
  signal rfdc_to_ctl_0_cdc_tdata  : std_logic_vector(32-1 downto 0)
                                  := (others => '0');
  signal rfdc_to_ctl_0_cdc_tvalid : std_logic := '0';
  signal rfdc_to_ctl_0_cdc_tready : std_logic := '0';
  signal rfdc_to_ctl_1_cdc_tdata  : std_logic_vector(32-1 downto 0)
                                  := (others => '0');
  signal rfdc_to_ctl_1_cdc_tvalid : std_logic := '0';
  signal rfdc_to_ctl_1_cdc_tready : std_logic := '0';
  -- tx clk domain
  signal tx_clk                       : std_logic_vector(1-1 downto 0)
                                      := (others => '0');
  signal tx_0_cdc_to_rfdc_prim_tdata  : std_logic_vector(32-1 downto 0)
                                      := (others => '0');
  signal tx_0_cdc_to_rfdc_prim_tvalid : std_logic := '0';
  signal tx_0_cdc_to_rfdc_prim_tready : std_logic := '0';
  signal tx_1_cdc_to_rfdc_prim_tdata  : std_logic_vector(32-1 downto 0)
                                      := (others => '0');
  signal tx_1_cdc_to_rfdc_prim_tvalid : std_logic := '0';
  signal tx_1_cdc_to_rfdc_prim_tready : std_logic := '0';
begin

  axi_converter : axi.lite32.raw2axi_lite32
    port map(
      clk     => ctl_in.clk,
      reset   => ctl_in.reset,
      raw_in  => props_in.raw,
      raw_out => props_out.raw,
      axi_in  => axi_in,
      axi_out => axi_out);

  rfdc_prim : rfdc.rfdc_pkg.rfdc
    port map(
      rfdc_clk         => ctl_in.clk,
      rfdc_reset       => ctl_in.reset,
      rfdc_axi_in      => axi_in,
      rfdc_axi_out     => axi_out,
      rfdc_adc_axi_in  => rfdc_adc.axi_in,
      rfdc_adc_axi_out => rfdc_adc.axi_out,
      rfdc_dac_axi_in  => rfdc_dac.axi_in,
      rfdc_dac_axi_out => rfdc_dac.axi_out,
      rx_clks_p        => rfdc_adc.rx_clks_p,
      rx_clks_n        => rfdc_adc.rx_clks_n,
      tx_clks_p        => rfdc_dac.tx_clks_p,
      tx_clks_n        => rfdc_dac.tx_clks_n,
      sysref_p         => rfdc_dac.sysref_p,
      sysref_n         => rfdc_dac.sysref_n,
      rf_rx_p          => rfdc_adc.rf_rx_p,
      rf_rx_n          => rfdc_adc.rf_rx_n,
      rf_tx_p          => rfdc_dac.rf_tx_p,
      rf_tx_n          => rfdc_dac.rf_tx_n,
      tx_aclks         => rfdc_dac.tx_aclks,
      s_axis_0_tdata   => rfdc_dac.s_axis_0_tdata,
      s_axis_0_tvalid  => rfdc_dac.s_axis_0_tvalid,
      s_axis_0_tready  => rfdc_dac.s_axis_0_tready,
      s_axis_1_tdata   => rfdc_dac.s_axis_1_tdata,
      s_axis_1_tvalid  => rfdc_dac.s_axis_1_tvalid,
      s_axis_1_tready  => rfdc_dac.s_axis_1_tready,
      rx_aclks         => rfdc_adc.rx_aclks,
      rx_aresets       => rfdc_adc.rx_aresets,
      m_axis_0_tdata   => rfdc_adc.m_axis_0_tdata,
      m_axis_0_tvalid  => rfdc_adc.m_axis_0_tvalid,
      m_axis_0_tready  => rfdc_adc.m_axis_0_tready,
      m_axis_1_tdata   => rfdc_adc.m_axis_1_tdata,
      m_axis_1_tvalid  => rfdc_adc.m_axis_1_tvalid,
      m_axis_1_tready  => rfdc_adc.m_axis_1_tready);

end structural;
