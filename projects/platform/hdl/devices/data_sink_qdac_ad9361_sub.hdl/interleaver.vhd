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
library dac; use dac.ad936x.all;

-- clock domains:
-- static_*  - clock domain independent (constant value)
-- wci_*     - worker control interface
-- wsi_*     - worker streaming interface (one clock/sample, samples coming in from data_sink_dac.hdl)
-- dac_*     - AD9361 DATA_CLK
--
-- latency:
-- deterministic, but not constant, as there is a backpressure mechanism within the config-specific
-- interleavers for purposes of framing alignment
entity interleaver is
  generic(
    DATA_BUS_BITS_ARE_REVERSED : boolean := false;
    LVDS_P                     : boolean;
    HALF_DUPLEX_P              : boolean;
    SINGLE_PORT_P              : boolean;
    DATA_RATE_CONFIG_P         : dac.ad936x.data_rate_config_t);
  port(
    -- data_sink_dac_ad9361_sub
    wci_clk                      : in  std_logic;
    wci_rst                      : in  std_logic;
    wci_use_two_r_two_t_timing   : in  std_logic;
    wsi_txen                     : in  std_logic;
    -- dev_cfg_data_tx
    wci_force_two_r_two_t_timing : in  std_logic;
    -- dev_data_clk
    dac_clk                      : in  std_logic;
    -- dev_data_to_pins
    dacddr_data_to_pins          : out std_logic_vector(24-1 downto 0);
    dacddr_tx_frame              : out std_logic;
    -- dev_data_ch0
    wsi_ch0_data_i               : in  std_logic_vector(dac.ad936x.DATA_BIT_WIDTH-1 downto 0);
    wsi_ch0_data_q               : in  std_logic_vector(dac.ad936x.DATA_BIT_WIDTH-1 downto 0);
    wsi_ch0_valid                : in  std_logic;
    wsi_ch0_clk                  : out std_logic;
    -- dev_data_ch1
    wsi_ch1_data_i               : in  std_logic_vector(dac.ad936x.DATA_BIT_WIDTH-1 downto 0);
    wsi_ch1_data_q               : in  std_logic_vector(dac.ad936x.DATA_BIT_WIDTH-1 downto 0);
    wsi_ch1_valid                : in  std_logic;
    wsi_ch1_clk                  : out std_logic;
    -- dev_txen
    dac_txen                     : out std_logic);
end entity interleaver;
architecture rtl of interleaver is
  signal dacddr_tx_data  : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) := (others => '0');
  signal wsi_clk         : std_logic := '0';
begin

  --------------------------------------------------------------------------------------------------
  -- account for INVALID config options
  --------------------------------------------------------------------------------------------------

  data_mode_invalid : if (LVDS_P and
      (SINGLE_PORT_P or HALF_DUPLEX_P or (DATA_RATE_CONFIG_P = SDR))) generate
    --report "AD936x configuration: LVDS=true, SINGLE_PORT=" & SINGLE_PORT_P & ", HALF_DUPLEX=" &
    --    HALF_DUPLEX_P & ", DATA_RATE_CONFIG=" & DATA_RATE_CONFIG_P severity failure;
    dacddr_tx_data  <= (others => '0');
    dacddr_tx_frame <= '0';
    wsi_clk         <= '0';
    dac_txen        <= '0';
  end generate;

  --------------------------------------------------------------------------------------------------
  -- I/Q DATA PROCESSING (LVDS)
  --------------------------------------------------------------------------------------------------

  data_mode_lvds : if LVDS_P generate
  begin
    -- AD9361 T1/T2 channels correspond to dev signal channels 0/1 (we are taking
    -- ADI-specific terminology and exposing it generically)
    interleaver : dac.ad936x.ad936x_ocps_lvds_interleaver
      port map(
        -- command/control
        ctrl_clk                    => wci_clk,
        ctrl_rst                    => wci_rst,
        ctrl_use_two_r_two_t_timing => wci_use_two_r_two_t_timing,
        -- data ingress (one clock per DAC sample)
        ocps_clk                    => wsi_clk,
        ocps_data_i_t1              => wsi_ch0_data_i,
        ocps_data_q_t1              => wsi_ch0_data_q,
        ocps_data_i_t2              => wsi_ch1_data_i,
        ocps_data_q_t2              => wsi_ch1_data_q,
        ocps_ready_t1               => wsi_ch0_valid,
        ocps_ready_t2               => wsi_ch1_valid,
        ocps_txen                   => wsi_txen,
        -- data egress (to/from AD9361 pins)
        dac_clk                     => dac_clk,
        dac_txen                    => dac_txen,
        dacddr_tx_frame             => dacddr_tx_frame,
        dacddr_tx_data              => dacddr_tx_data);
  end generate data_mode_lvds;

  --------------------------------------------------------------------------------------------------
  -- I/Q data interleaving (CMOS)
  --------------------------------------------------------------------------------------------------

  data_mode_cmos : if (LVDS_P = false) generate
  begin
    -- TODO / FIXME support runtime dynamic enumeration for CMOS? (if so, we need to check duplex_config = runtime_dynamic)
    single_port_fdd_ddr : if SINGLE_PORT_P and (HALF_DUPLEX_P = false) and
        (DATA_RATE_CONFIG_P = dac.ad936x.DDR) generate
      -- AD9361 T1/T2 channels correspond to dev signal channels 0/1 (we are taking
      -- ADI-specific terminology and exposing it generically)
      interleaver : dac.ad936x.ad936x_ocps_cmos_single_port_fdd_ddr_interleaver
        port map(
          -- command/control
          ctrl_clk                    => wci_clk,
          ctrl_rst                    => wci_rst,
          ctrl_use_two_r_two_t_timing => wci_use_two_r_two_t_timing,
          -- data ingress (one clock per DAC sample)
          ocps_clk                    => wsi_clk,
          ocps_data_i_t1              => wsi_ch0_data_i,
          ocps_data_q_t1              => wsi_ch0_data_q,
          ocps_data_i_t2              => wsi_ch1_data_i,
          ocps_data_q_t2              => wsi_ch1_data_q,
          ocps_ready_t1               => wsi_ch0_valid,
          ocps_ready_t2               => wsi_ch1_valid,
          ocps_txen                   => wsi_txen,
          -- data egress (to/from AD9361 pins)
          dac_clk                     => dac_clk,
          dac_txen                    => dac_txen,
          dacddr_tx_frame             => dacddr_tx_frame,
          dacddr_tx_data              => dacddr_tx_data);
    end generate single_port_fdd_ddr;
  end generate data_mode_cmos;

  --------------------------------------------------------------------------------------------------
  -- generic functionality
  --------------------------------------------------------------------------------------------------

  wsi_ch0_clk <= wsi_clk;
  wsi_ch1_clk <= wsi_clk;

  dacddr_data_to_pins(dacddr_data_to_pins'left downto dacddr_tx_data'length) <=
      (others => '0');
  data_bus_bits_are_reversed_true : if data_bus_bits_are_reversed generate
    buf_data : for idx in dacddr_tx_data'left downto 0 generate
      dacddr_data_to_pins(idx) <= dacddr_tx_data(dacddr_tx_data'left-idx);
    end generate;
  end generate;
  data_bus_bits_are_reversed_false : if (data_bus_bits_are_reversed = false) generate
    buf_data : for idx in dacddr_tx_data'left downto 0 generate
      dacddr_data_to_pins(idx) <= dacddr_tx_data(idx);
    end generate;
  end generate;

end rtl;
