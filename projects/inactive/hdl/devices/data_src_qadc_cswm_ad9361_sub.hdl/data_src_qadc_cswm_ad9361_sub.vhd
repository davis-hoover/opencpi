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

-- THIS FILE WAS ORIGINALLY GENERATED ON Thu Nov  7 14:51:57 2019 EST
-- BASED ON THE FILE: data_src_qadc_ad9361_sub.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: data_src_qadc_ad9361_sub

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library unisim; use unisim.vcomponents.all;
library util; use util.util.all;
library cdc; use cdc.all;
architecture rtl of worker is
  constant adc_width  : positive := 12; -- must not be > 16 due to WSI width and multiple of 2 due to LVDS generate loop

  -- we could expose these constants as bool parameters with default values
  -- of false, but there's nothing significant to gain from it, so we fix their
  -- values to false here (if someone wanted to change it to true for
  -- whatever reason, it passes this info up to config worker via dev signals,
  -- which in turn passes those dev signals up to the config proxy, which uses
  -- those dev signals to ensure that the corresponding registers are set
  -- properly
  constant data_bus_bits_are_reversed    : bool_t := bfalse;
  constant data_clk_p_is_inverted        : bool_t := bfalse;
  constant rx_frame_is_inverted          : bool_t := bfalse;

  constant rx_frame_usage_is_toggle      : bool_t := btrue;  -- no need for us to support non-toggle ("enable")

  -- Determine the data_width based on the mode.
  -- While the data-width to the adc/dac will be the same,
  -- the number of pins connected (via the data_sub) will
  -- be different depending on the current mode.
  function data_width (adc_width : positive)
    return positive is
  begin
    if (HALF_DUPLEX_p      = bfalse  and
        DATA_RATE_CONFIG_p = DDR_e)  and
       ((LVDS_p            = btrue   and
         SINGLE_PORT_p     = bfalse) or
        (LVDS_p            = bfalse  and
         SINGLE_PORT_p     = btrue)) then
      return adc_width/2;
    elsif (LVDS_p             = bfalse   and
           DATA_RATE_CONFIG_p = DDR_e)   and
          ((SINGLE_PORT_p     = btrue    and
            HALF_DUPLEX_p     = btrue)   or
           (SINGLE_PORT_p     = bfalse   and
            HALF_DUPLEX_p     = bfalse)) then
      return adc_width;
    else
      return adc_width*2;
    end if;
  end function data_width;

  constant data_width_from_pins : positive := data_width(adc_width);
  constant NUM_CHANS            : positive := 2;
  -- we could expose these constants as bool parameters with default values
  -- of false, but there's nothing significant to gain from it, so we fix their
  -- values to false here (if someone wanted to change it to true for
  -- whatever reason, it passes this info up to config worker via dev signals,
  -- which in turn passes those dev signals up to the config proxy, which uses
  -- those dev signals to ensure that the corresponding registers are set
  -- properly
  type state_t is (R1_11_6, R1_5_0,
                   R2_11_6, R2_5_0);
  signal state : state_t := R1_11_6;

  -- internal signals
  signal dual_port   : std_logic := '0';
  signal full_duplex : std_logic := '0';
  signal data_rate   : std_logic := '0';
  -- no clock domain / static signals
  signal ch0_worker_present : std_logic := '0';
  signal ch1_worker_present : std_logic := '0';
  signal r1_worker_present  : std_logic := '0';
  signal r2_worker_present  : std_logic := '0';
  -- WCI (control) clock domain signals
  signal wci_r1_samps_dropped_clear : std_logic := '0';
  signal wci_r2_samps_dropped_clear : std_logic := '0';
  signal wci_reset_n                : std_logic := '1';
  signal wci_channels_are_swapped   : std_logic := '0';
  -- AD9361 RX clock domain signals
  signal adc_clk_in   : std_logic := '0';
  signal adc_clk      : std_logic := '0';
  signal adc_data0    : std_logic_vector((adc_width*2)-1 downto 0) := (others => '0');
  signal adc_data1    : std_logic_vector((adc_width*2)-1 downto 0) := (others => '0');
  signal adc_rx_frame_p_buf    : std_logic := '0';
  signal adc_rx_frame_p_buf_rising_rr  : std_logic := '0';
  signal adc_rx_frame_p_buf_falling_rr : std_logic := '0';
  signal adc_rx_data_buf_ordered : std_logic_vector(data_width_from_pins-1 downto 0) := (others => '0');
  signal adc_ddr_out_rising_rr   : std_logic_vector(data_width_from_pins-1 downto 0) := (others => '0');
  signal adc_ddr_out_falling_rr  : std_logic_vector(data_width_from_pins-1 downto 0) := (others => '0');
  signal adc_r1_i_h_rrr : std_logic_vector((adc_width/2)-1 downto 0) := (others => '0');
  signal adc_r1_q_h_rrr : std_logic_vector((adc_width/2)-1 downto 0) := (others => '0');
  signal adc_r1_i_rrrr  : std_logic_vector(adc_width-1     downto 0) := (others => '0');
  signal adc_r1_q_rrrr  : std_logic_vector(adc_width-1     downto 0) := (others => '0');
  signal adc_r1_i_rrrrr : std_logic_vector(adc_width-1     downto 0) := (others => '0');
  signal adc_r1_q_rrrrr : std_logic_vector(adc_width-1     downto 0) := (others => '0');
  signal adc_r1_i_rrrrrr: std_logic_vector(adc_width-1     downto 0) := (others => '0');
  signal adc_r1_q_rrrrrr: std_logic_vector(adc_width-1     downto 0) := (others => '0');
  signal adc_r2_i_h_rrr : std_logic_vector((adc_width/2)-1 downto 0) := (others => '0');
  signal adc_r2_q_h_rrr : std_logic_vector((adc_width/2)-1 downto 0) := (others => '0');
  signal adc_r2_i_rrrr  : std_logic_vector(adc_width-1     downto 0) := (others => '0');
  signal adc_r2_q_rrrr  : std_logic_vector(adc_width-1     downto 0) := (others => '0');
  signal adc_r1_give_rrrr   : bool_t := bfalse;
  signal adc_r1_give_rrrrr  : bool_t := bfalse;
  signal adc_r1_give_rrrrrr : bool_t := bfalse;
  signal adc_r2_give_rrrr   : bool_t := bfalse;
  signal adc_r1_samps_dropped : std_logic := '0';
  signal adc_r2_samps_dropped : std_logic := '0';
  signal adc_data : std_logic_vector(data_width_from_pins-1 downto 0) := (others => '0');
  signal adc_channels_are_swapped : std_logic := '0';
  -- signals interface (ADC clock domain)
  signal RX_FRAME_P_s : std_logic := '0';

  signal wci_use_two_r_two_t_timing : std_logic;
  signal adc_use_two_r_two_t_timing_rr : std_logic;

  signal sample_clk        : std_logic := '0';
  signal sample_data_i     : adc_cswm.adc_cswm.array_data_t(0 to NUM_CHANS-1) :=
                             (others=> (others => '0'));
  signal sample_data_q     : adc_cswm.adc_cswm.array_data_t(0 to NUM_CHANS-1) :=
                             (others=> (others => '0'));
  signal sample_data_valid : std_logic_vector(0 to NUM_CHANS-1) :=
                             (others => '0');
  signal adc_data_i        : adc_cswm.adc_cswm.array_data_t(0 to NUM_CHANS-1) :=
                             (others=> (others => '0'));
  signal adc_data_q        : adc_cswm.adc_cswm.array_data_t(0 to NUM_CHANS-1) :=
                             (others=> (others => '0'));
  signal adc_data_vld      : std_logic_vector(0 to NUM_CHANS-1) :=
                             (others => '0');
  signal worker_present    : std_logic_vector(0 to NUM_CHANS-1) :=
                             (others => '0');
  
  signal adc_reset         : std_logic := '0';             

begin

  -- these dev signals are used to (eventually) tell higher level proxy(ies)
  -- about the data port configuration that was enforced when this worker was
  -- compiled, so that said proxy(ies) can set the AD9361 registers accordingly
  dual_port   <= '1' when SINGLE_PORT_p      = bfalse        else '0';
  full_duplex <= '1' when HALF_DUPLEX_p      = bfalse        else '0';
  data_rate   <= '1' when DATA_RATE_CONFIG_p = DDR_e         else '0';
  dev_cfg_data_out.ch0_handler_is_present   <= ch0_worker_present;
  dev_cfg_data_out.ch1_handler_is_present   <= ch1_worker_present;
  dev_cfg_data_out.data_bus_index_direction <= '1' when data_bus_bits_are_reversed = btrue else '0';
  dev_cfg_data_out.data_clk_is_inverted     <= '1' when data_clk_p_is_inverted     = btrue else '0';
  dev_cfg_data_out.islvds                   <= '1' when LVDS_p                     = btrue else '0';
  dev_cfg_data_out.isdualport               <= '1' when LVDS_p                     = btrue else dual_port;
  dev_cfg_data_out.isfullduplex             <= '1' when LVDS_p                     = btrue else full_duplex;
  dev_cfg_data_out.isddr                    <= '1' when LVDS_p                     = btrue else data_rate;
  dev_cfg_data_out.present <= '1';
  dev_cfg_data_rx_out.rx_frame_usage        <= '1' when rx_frame_usage_is_toggle   = '1'   else '0';
  dev_cfg_data_rx_out.rx_frame_is_inverted  <= '1' when rx_frame_is_inverted       = btrue else '0';

  -- ch0_worker_preset should always be '1' since we are it's subdevice
  ch0_worker_present <= dev_data_ch0_out_in.present;
  ch1_worker_present <= dev_data_ch1_out_in.present;

  clk_in_lvds : if (LVDS_p = btrue) and
                   (SINGLE_PORT_p = bfalse) and
                   (HALF_DUPLEX_p = bfalse) and
                   (DATA_RATE_CONFIG_p = DDR_e) generate
    BUFR_inst : BUFR
      generic map (
        BUFR_DIVIDE => "BYPASS")   -- "BYPASS", "1", "2", "3", "4", "5", "6", "7", "8"
      port map (
        O   => adc_clk_in, -- 1-bit output: Clock output port
        CE  => '1',        -- 1-bit input: Active high, clock enable (Divided modes only)
        CLR => '0',        -- 1-bit input: Active high, asynchronous clear (Divided mode only)
        I   => dev_data_clk_in.DATA_CLK_P -- 1-bit input: Clock buffer input driven by an IBUFG, MMCM or local interconnect
      );
  end generate;

  clk_in_cmos_half_duplex_DDR : if (LVDS_p = bfalse) and
                                   (HALF_DUPLEX_p = bfalse) and
                                   (DATA_RATE_CONFIG_p = DDR_e) generate
    adc_clk_in <= dev_data_clk_in.DATA_CLK_P;
  end generate;

  -- we want adc_clk to be rising edge for worker-internal logic
  gen_adc_clk : if data_clk_p_is_inverted = bfalse generate
    adc_clk <= adc_clk_in;
  end generate;

  --Register RX FRAME indicator so that it's delayed the same as ddr_out_rising_rr
  --and ddr_out_falling_rr
  gen_rx_frame_inv : if rx_frame_is_inverted = bfalse generate
  begin
    adc_rx_frame_p_buf <= RX_FRAME_P_s;
  end generate;
  gen_rx_frame_not_inv : if rx_frame_is_inverted = btrue  generate
  begin
    adc_rx_frame_p_buf <= not RX_FRAME_P_s;
  end generate;

  -- There is only one valid LVDS mode. Others should result in errors.
  data_mode_lvds_invalid : if ((LVDS_p              = btrue)   and
                               ((SINGLE_PORT_p      = btrue)   or
                                (HALF_DUPLEX_p      = btrue)   or
                                (DATA_RATE_CONFIG_p = SDR_e))) generate
  begin
    -- this OpenCPI build configuration is not supported by AD9361
    -- and should never be used
    ctl_out.error <= '1'; -- force unsuccessful end of all control operations
  end generate;

  -- TODO / FIXME support runtime dynamic enumeration for CMOS? (if so, we need to check duplex_config = runtime_dynamic)

  -- Supported data modes so far are the one valid LVDS config or one of CMOS
  -- DDR Full Duplex configs
  supported_so_far : if DATA_RATE_CONFIG_p = DDR_e    and
                        (LVDS_p            = bfalse   or
                         (SINGLE_PORT_p    = bfalse   and
                          HALF_DUPLEX_p    = bfalse)) generate
  begin

    data_bus_bits_are_not_reversed : if data_bus_bits_are_reversed = bfalse generate
      adc_rx_data_buf_ordered <= adc_data(data_width_from_pins-1 downto 0);
    end generate;
    data_bus_bits_are_reversed_t : if data_bus_bits_are_reversed = btrue generate
      buf_data : for idx in (data_width_from_pins-1) downto 0 generate
        adc_rx_data_buf_ordered(idx) <= adc_data(data_width_from_pins-1-idx);
      end generate;
    end generate;
    -- TODO / FIXME - add data bus direction reversal handling for all CMOS modes

    adc_data <= dev_data_from_pins_in.data(data_width_from_pins-1 downto 0);

    ---------------------------------------------------------------------------
    -- IDDR modules to collect rising/falling elements of rx_data

    -- allows RX_FRAME_P to have similar skew as P1_D signals, also allows us to
    -- sample RX_FRAME_P at in the middle of the clock period by using the Q2
    -- output
    rx_frame_p_ddr : IDDR
    generic map(
      DDR_CLK_EDGE => "SAME_EDGE_PIPELINED",
      INIT_Q1      => '0',
      INIT_Q2      => '0',
      SRTYPE       => "ASYNC")
    port map(
      Q1 => adc_rx_frame_p_buf_rising_rr,
      Q2 => adc_rx_frame_p_buf_falling_rr,
      C  => adc_clk,
      CE => '1',
      D  => adc_rx_frame_p_buf,
      R  => '0',
      S  => '0'
      );

    buf_data_loop : for idx in (data_width_from_pins-1) downto 0 generate
    begin
      data_ddr : IDDR
      generic map(
        DDR_CLK_EDGE => "SAME_EDGE_PIPELINED",
        INIT_Q1      => '0',
        INIT_Q2      => '0',
        SRTYPE       => "ASYNC")
      port map(
        Q1 => adc_ddr_out_rising_rr(idx),
        Q2 => adc_ddr_out_falling_rr(idx),
        C  => adc_clk,
        CE => '1',
        D  => adc_rx_data_buf_ordered(idx),
        R  => '0',
        S  => '0'
        );
    end generate;
    ---------------------------------------------------------------------------

    ---------------------------------------------------------------------------
    -- For certain modes, we need to delay r1 so that it aligns with r2
    -- The number of delay cycles are as follows (SP=Single Port, DP=Dual Port):
    --   <Mode>                      : <Delay-Cycles>
    --   CMOS Single Port Half Duplex: 1
    --   CMOS Single Port Full Duplex: 2
    --   CMOS Dual   Port Half Duplex: 1
    --   CMOS Dual   Port Full Duplex: 0
    --   LVDS Dual   Port Full Duplex: 2
    ---------------------------------------------------------------------------
    ---------------------------------------------------------------------------
    -- For CMOS SP Full Duplex, and LVDS DP Full Duplex,
    -- delay r1 by 2 to align with r2
    delay_r1_by_2 : if (HALF_DUPLEX_p      = bfalse  and DATA_RATE_CONFIG_p = DDR_e)  and
                       ((LVDS_p            = btrue   and SINGLE_PORT_p     = bfalse) or
                        (LVDS_p            = bfalse  and SINGLE_PORT_p     = btrue)) generate
    delay_r1_by_2_to_align_with_r2 : process(adc_clk)
    begin
      if rising_edge(adc_clk) then
        adc_r1_i_rrrrr  <= adc_r1_i_rrrr;
        adc_r1_q_rrrrr  <= adc_r1_q_rrrr;
        adc_r1_i_rrrrrr <= adc_r1_i_rrrrr;
        adc_r1_q_rrrrrr <= adc_r1_q_rrrrr;
        adc_r1_give_rrrrr  <= adc_r1_give_rrrr;
        adc_r1_give_rrrrrr <= adc_r1_give_rrrrr;
      end if;
    end process;

    -- simultaneously handles both possible 1R1T and 2R2T timing diagrams from
    -- AD9361_Reference_Manual_UG-570.pdf Figure 79.
    data_ingest_fsm : process(adc_clk)
    begin
      if rising_edge(adc_clk) then
        case state is
          when R1_11_6 =>
            adc_r1_give_rrrr <= '0';
            adc_r2_give_rrrr <= '0';
            -- this is why we set rx_frame_usage_is_toggle to btrue above
            if(adc_rx_frame_p_buf_falling_rr = '1') then
              adc_r1_i_h_rrr <= adc_ddr_out_rising_rr;
              adc_r1_q_h_rrr <= adc_ddr_out_falling_rr;
              state <= R1_5_0;
            end if;
          when R1_5_0 =>
            adc_r1_i_rrrr <= adc_r1_i_h_rrr & adc_ddr_out_rising_rr;
            adc_r1_q_rrrr <= adc_r1_q_h_rrr & adc_ddr_out_falling_rr;

            adc_r1_give_rrrr <= r1_worker_present;

            -- if valid first channel samples are received but there is no
            -- qadc worker to ingest them, detect the error
            adc_r1_samps_dropped <= not r1_worker_present;

            -- this is why we set rx_frame_usage_is_toggle to btrue above
            if(adc_rx_frame_p_buf_falling_rr = '1') then
              state <= R2_11_6;
            else
              state <= R1_11_6;
            end if;
          when R2_11_6 =>
            adc_r2_i_h_rrr <= adc_ddr_out_rising_rr;
            adc_r2_q_h_rrr <= adc_ddr_out_falling_rr;
            adc_r1_give_rrrr <= '0';
            state <= R2_5_0;
          when R2_5_0 =>
            adc_r2_i_rrrr <= adc_r2_i_h_rrr & adc_ddr_out_rising_rr;
            adc_r2_q_rrrr <= adc_r2_q_h_rrr & adc_ddr_out_falling_rr;

            -- it is possible (when using LVDS and 1R2T mode) for data to be
            -- received in the R2 channel slot that should be ignored -
            -- no-OS (via the ad9361_config_proxy) directs us via the
            -- config_is_two_r signal when to drop the second channel samples
            -- that should be ignored
            adc_r2_give_rrrr <= adc_use_two_r_two_t_timing_rr and
                                r2_worker_present;

            -- if valid R2 channel samples are received but there is no
            -- second qadc worker to ingest them, detect the error
            adc_r2_samps_dropped <= adc_use_two_r_two_t_timing_rr and
                                    (not r2_worker_present);

            state <= R1_11_6;
        end case;
      end if;
    end process;
    end generate;
    ---------------------------------------------------------------------------

    ---------------------------------------------------------------------------
    -- For CMOS SP Half duplex, CMOS DP Full Duplex
    -- delay r1 by 1 to align with r2
    delay_r1_by_1_to_align_with_r2 : if (LVDS_p             = bfalse   and DATA_RATE_CONFIG_p = DDR_e)   and
                                        ((SINGLE_PORT_p     = btrue    and HALF_DUPLEX_p     = btrue)   or
                                         (SINGLE_PORT_p     = bfalse   and HALF_DUPLEX_p     = bfalse)) generate
      delay_r1_by_1 : process(adc_clk)
      begin
        if rising_edge(adc_clk) then
          -- In this case, rrrrrr is really only registered 5 times (not 6)
          adc_r1_i_rrrrrr     <= adc_r1_i_rrrr;
          adc_r1_q_rrrrrr     <= adc_r1_q_rrrr;
          adc_r1_give_rrrrrr  <= adc_r1_give_rrrr;
        end if;
      end process;
      -- simultaneously handles both possible 1R1T and 2R2T timing diagrams from
      -- AD9361_Reference_Manual_UG-570.pdf Figure 79.
      data_ingest_fsm : process(adc_clk)
      begin
        if rising_edge(adc_clk) then
          case state is
            when R1_11_6 | R1_5_0  =>
              adc_r1_give_rrrr <= '0';
              adc_r2_give_rrrr <= '0';

              -- this is why we set rx_frame_usage_is_toggle to btrue above
              if (adc_rx_frame_p_buf_rising_rr = '1') then
                adc_r1_i_rrrr <= adc_ddr_out_rising_rr;
                adc_r1_q_rrrr <= adc_ddr_out_falling_rr;

                adc_r1_give_rrrr <= r1_worker_present;

                -- if valid first channel samples are received but there is no
                -- qadc worker to ingest them, detect the error
                adc_r1_samps_dropped <= not r1_worker_present;

              end if;

              -- this is why we set rx_frame_usage_is_toggle to btrue above
              if (adc_rx_frame_p_buf_falling_rr = '1') then
                -- if we finish this state in with rx_frame still high, we are not in 1R1T mode
                --   --> move to R2 state next to handle R2 channel
                state <= R2_11_6;
                -- otherwise, we are in 1R1T mode --> stay in R1 state
              end if;

            when R2_11_6 | R2_5_0 =>
              adc_r2_i_rrrr <= adc_ddr_out_rising_rr;
              adc_r2_q_rrrr <= adc_ddr_out_falling_rr;
              adc_r1_give_rrrr <= '0';

              -- it is possible (when using LVDS and 1R2T mode) for data to be
              -- received in the R2 channel slot that should be ignored -
              -- no-OS (via the ad9361_config_proxy) directs us via the
              -- config_is_two_r signal when to drop the second channel samples
              -- that should be ignored
              adc_r2_give_rrrr <= adc_use_two_r_two_t_timing_rr and
                                  r2_worker_present;

              -- if valid R2 channel samples are received but there is no
              -- second qadc worker to ingest them, detect the error
              adc_r2_samps_dropped <= adc_use_two_r_two_t_timing_rr and
                                      (not r2_worker_present);

              state <= R1_11_6;
          end case;
        end if;
      end process;
    end generate;
    -----------------------------------------------------------------------------

    invalid_half_duplex : if HALF_DUPLEX_p      = btrue  generate
      -- this OpenCPI build configuration is not yet supported
      ctl_out.error <= '1'; -- force unsuccessful end of all control operations
    end generate;
    -----------------------------------------------------------------------------
    ---- Do not delay at all for DP Half Duplex
    --cmos_dual_port_half_duplex : if LVDS_p             = bfalse and
    --                                DATA_RATE_CONFIG_p = DDR_e  and
    --                                SINGLE_PORT_p      = bfalse and
    --                                HALF_DUPLEX_p      = btrue  generate

    --  -- In this case, rrrrrr is really only registered 4 times (not 6),
    --  -- which is the same number of times as r2. This is because r2
    --  -- comes in on the same clock as r1 in this mode.
    --  adc_r1_i_rrrrrr    <= adc_r1_i_rrrr;
    --  adc_r1_q_rrrrrr    <= adc_r1_q_rrrr;
    --  adc_r1_give_rrrrrr <= adc_r1_give_rrrr;

    --  -- simultaneously handles both possible 1R1T and 2R2T timing diagrams from
    --  -- AD9361_Reference_Manual_UG-570.pdf Figure 79.
    --  data_ingest_fsm : process(adc_clk)
    --  begin
    --    if rising_edge(adc_clk) then
    --      -- check for correct RX_FRAME orientation
    --      -- assign adc_r1_i and q from rising
    --      -- either assign the NEXT r1 i and q from falling,
    --      -- or assign r2 i and q from falling if config is 2R2T timing

    --      -- this is why we set rx_frame_usage_is_toggle to btrue above
    --      if adc_rx_frame_p_buf_rising_rr = '0' and adc_rx_frame_p_buf_falling_rr = '1' then
    --
    --        -- low bits are I data, high bits are Q
    --        adc_r1_i_rrrrr <= adc_ddr_out_rising_rr(data_width_from_pins/2-1 downto 0);
    --        adc_r1_q_rrrrr <= adc_ddr_out_rising_rr(data_width_from_pins-1 downto data_width_from_pins/2);

    --        adc_r1_give_rrrr <= r1_worker_present;
    --        -- If valid first channel samples are received but there is no
    --        -- qadc worker to ingest them, detect the error
    --        adc_r1_samps_dropped <= not r1_worker_present;

    --        -- The current configuration supports 2R2T timing.
    --        -- Collect i/q from the DDR falling edge data
    --        if dev_cfg_data_in.config_is_two_r  = '1' or
    --           dev_cfg_data_in.config_is_two_t  = '1' or
    --           dev_cfg_data_in.force_two_r_two_t_timing = '1' then

    --          -- low bits are I data, high bits are Q
    --          adc_r2_i_rrrr <= adc_ddr_out_falling_rr(data_width_from_pins/2-1 downto 0);
    --          adc_r2_q_rrrr <= adc_ddr_out_falling_rr(data_width_from_pins-1 downto data_width_from_pins/2);

    --          adc_r2_give_rrrr <= dev_cfg_data_in.config_is_two_r and
    --                              r2_worker_present;

    --          -- If valid R2 channel samples are received but there is no
    --          -- second qadc worker to ingest them, detect the error
    --          adc_r2_samps_dropped <= dev_cfg_data_in.config_is_two_r and
    --                                  not r2_worker_present;
    --        else
    --          -- The current configuration is 1R1T timing
    --          -- We get two full i/q pairs per cycle (one rising, one falling)
    --          -- TODO/FIXME: Do we need a FIFO here to handle the data coming in
    --          -- twice as fast as the adc worker can handle it?
    --          -- Otherwise, can we run the adc at twice adc_clk, and that way we can
    --          -- give it 2 samples per adc_clk cycle as is needed in 1R1T configuration

    --          -- rising_rr as already assigned to r1 I/Q. falling_rr is the next
    --          -- I/Q sample, and must be buffered in some way

    --          adc_r2_give_rrrr <= '0';
    --        end if;
    --      else
    --        adc_r1_give_rrrr <= '0';
    --        adc_r2_give_rrrr <= '0';
    --      end if;
    --    end if;
    --  end process;
    --end generate;
    ---------------------------------------------------------------------------

    ---------------------------------------------------------------------------
    -- Extract the High/Low and I/Q portions of the data in stages and construct
    -- the output data for r1_i/q and r2_i/q
    ---------------------------------------------------------------------------
  end generate;
  
  adc_reset_gen : cdc.cdc.reset
  port map(
    src_rst => ctl_in.reset,
    dst_clk => adc_clk,
    dst_rst => adc_reset); 

  -- sync (WCI clock domain) -> (ADC clock domain)
  -- note that we don't care if WCI clock is much faster and bits are
  -- dropped - props_in.channels_are_swapped is a configuration bit which is
  -- expected to change very rarely in relation to either clock
  wci_channels_are_swapped <= '1' when (props_in.channels_are_swapped = btrue) else '0';
  chan_swap_sync : cdc.cdc.single_bit
  generic map(IREG      => '1',
              RST_LEVEL => '0')
  port map   (src_clk      => ctl_in.clk,
              src_rst      => ctl_in.reset,
              src_en       => '1',
              src_in       => wci_channels_are_swapped,
              dst_clk      => adc_clk,
              dst_rst      => adc_reset,
              dst_out      => adc_channels_are_swapped);  -- delayed by one WCI clock, two ADC clocks

  r1_worker_present               <= ch0_worker_present when (adc_channels_are_swapped = bfalse) else ch1_worker_present;
  r2_worker_present               <= ch1_worker_present when (adc_channels_are_swapped = bfalse) else ch0_worker_present;

  adc_data_i(0)     <= adc_r1_i_rrrrrr when (adc_channels_are_swapped = bfalse) else adc_r2_i_rrrr;
  adc_data_i(1)     <= adc_r2_i_rrrr   when (adc_channels_are_swapped = bfalse) else adc_r1_i_rrrrrr;
  adc_data_q(0)     <= adc_r1_q_rrrrrr when (adc_channels_are_swapped = bfalse) else adc_r2_q_rrrr;
  adc_data_q(1)     <= adc_r2_q_rrrr   when (adc_channels_are_swapped = bfalse) else adc_r1_q_rrrrrr;
  adc_data_vld(0)   <= adc_r1_give_rrrrrr when (adc_channels_are_swapped = bfalse) else adc_r2_give_rrrr;
  adc_data_vld(1)   <= adc_r2_give_rrrr   when (adc_channels_are_swapped = bfalse) else adc_r1_give_rrrrrr;
  worker_present(0) <= r1_worker_present;
  worker_present(1) <= r2_worker_present;

  sample_clk_gen : entity work.one_sample_clock_per_adc_sample_generator
    generic map(
      NUM_CHANS                  => NUM_CHANS,
      FIRST_DIVIDER_TYPE         => "REGISTER",
      FIRST_DIVIDER_ROUTABILITY  => "GLOBAL",
      SECOND_DIVIDER_TYPE        => "REGISTER",
      SECOND_DIVIDER_ROUTABILITY => "GLOBAL")
    port map(
      -- to/from data_interleaver
      someclk_data_i             => adc_data_i,
      someclk_data_q             => adc_data_q,
      someclk_data_vld           => adc_data_vld,
      -- clock handling
      adc_clk                    => adc_clk,
      -- to/from supported worker
      worker_present             => worker_present,
      wci_use_two_r_two_t_timing => wci_use_two_r_two_t_timing,
      sample_clk                 => sample_clk,
      sample_data_out_i          => sample_data_i,
      sample_data_out_q          => sample_data_q,
      sample_data_out_valid      => sample_data_valid);


  -- From ADI's UG-570:
  -- "For a system with a 2R1T or a 1R2T configuration, the clock
  -- frequencies, bus transfer rates and sample periods, and data
  -- capture timing are the same as if configured for a 2R2T system.
  -- However, in the path with only a single channel used, the
  -- disabled channel’s I-Q pair in each data group is unused."
  wci_use_two_r_two_t_timing <= dev_cfg_data_in.config_is_two_r;

  -- sync (WCI clock domain) -> (ADC clock divided domain), 
  -- note that we don't care if WCI clock is much faster and bits are
  -- dropped - wci_use_two_r_two_t_timing is a configuration bit which is
  -- expected to change very rarely in relation to either clock
  second_chan_enable_sync : cdc.cdc.single_bit
    generic map(IREG      => '1',
                RST_LEVEL => '0')
    port map   (src_clk      => ctl_in.clk,
                src_rst      => ctl_in.reset,
                src_en       => '1',
                src_in       => wci_use_two_r_two_t_timing,
                dst_clk      => adc_clk,
                dst_rst      => adc_reset,
                dst_out      => adc_use_two_r_two_t_timing_rr);  -- delayed by one WCI clock, two ADC clocks


  dev_data_ch0_out_out.clk    <= sample_clk;
  dev_data_ch0_out_out.valid  <= sample_data_valid(0);

  -- i and q signal buses driven where each signal bus is MSB-justified
  -- (data_src_qadc.hdl takes care of justification standardization)
  dev_data_ch0_out_out.data_i(dev_data_ch0_out_out.data_i'left downto
                              dev_data_ch0_out_out.data_i'left-adc_width+1) <= sample_data_i(0);

  dev_data_ch0_out_out.data_i(dev_data_ch0_out_out.data_i'left-adc_width downto 0) <= (others => '0');
  dev_data_ch0_out_out.data_q(dev_data_ch0_out_out.data_q'left downto
                              dev_data_ch0_out_out.data_q'left-adc_width+1) <= sample_data_q(0);

  dev_data_ch0_out_out.data_q(dev_data_ch0_out_out.data_q'left-adc_width downto 0) <= (others => '0');

  dev_data_ch1_out_out.clk    <= sample_clk;
  dev_data_ch1_out_out.valid  <= sample_data_valid(1);

  dev_data_ch1_out_out.data_i(dev_data_ch1_out_out.data_i'left downto
                              dev_data_ch1_out_out.data_i'left-adc_width+1) <= sample_data_i(1);

  dev_data_ch1_out_out.data_i(dev_data_ch1_out_out.data_i'left-adc_width downto 0) <= (others => '0');
  dev_data_ch1_out_out.data_q(dev_data_ch1_out_out.data_q'left downto
                              dev_data_ch1_out_out.data_q'left-adc_width+1) <= sample_data_q(1);

  dev_data_ch1_out_out.data_q(dev_data_ch1_out_out.data_q'left-adc_width downto 0) <= (others => '0');

  -- if valid R1 channel samples are received but there is no
  -- qadc worker to ingest them, detect the error
  wci_r1_samps_dropped_clear <= '1'
                                 when (props_in.r1_samps_dropped_written = '1')
                                      and (props_in.r1_samps_dropped = '0')
                                 else '0';
  r1_samps_dropped_sync : util.util.sync_status
    port map   (clk         => ctl_in.clk,
                reset       => ctl_in.reset,
                operating   => ctl_in.is_operating,
                start       => ctl_in.is_operating,
                clear       => wci_r1_samps_dropped_clear,
                status      => props_out.r1_samps_dropped,
                other_clk   => adc_clk,
                other_reset => open,
                event       => adc_r1_samps_dropped);

  wci_r2_samps_dropped_clear <= '1'
                                 when (props_in.r2_samps_dropped_written = '1')
                                      and (props_in.r2_samps_dropped = '0')
                                 else '0';

  -- if valid R2 channel samples are received but there is no
  -- qadc worker to ingest them, detect the error
  r2_samps_dropped_sync : util.util.sync_status
     port map  (clk         => ctl_in.clk,
                reset       => ctl_in.reset,
                operating   => ctl_in.is_operating,
                start       => ctl_in.is_operating,
                clear       => wci_r2_samps_dropped_clear,
                status      => props_out.r2_samps_dropped,
                other_clk   => adc_clk,
                other_reset => open,
                event       => adc_r2_samps_dropped);
    -- delegate LVDS issues to the data_sub.
    RX_FRAME_P_s <= dev_data_from_pins_in.rx_frame;

end rtl;
