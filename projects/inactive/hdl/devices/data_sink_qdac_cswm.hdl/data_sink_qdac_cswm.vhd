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
library ocpi, cdc; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library util, dac_cswm;
library protocol; use protocol.complex_short_with_metadata.all;
architecture rtl of worker is
  signal dac_rst                                : std_logic;
  signal dac_status                             : dac_cswm.dac_cswm.underrun_detector_status_t;
  signal dac_opcode                             : opcode_t := SAMPLES;
  signal dac_in_demarshaller_oprotocol          : protocol_t := PROTOCOL_ZERO;
  signal dac_in_demarshaller_oeof               : std_logic := '0';

  signal dac_underrun_detector_imetadata        : dac_cswm.dac_cswm.metadata_t;
  signal dac_underrun_detector_irdy             : std_logic := '0';
  signal dac_underrun_detector_oprotocol        :
      protocol.complex_short_with_metadata.protocol_t;
  signal dac_underrun_detector_ometadata        : dac_cswm.dac_cswm.metadata_t;
  signal dac_underrun_detector_ometadata_vld    : std_logic := '0';

  signal dac_data_narrower_irdy                 : std_logic := '0';
  signal dac_data_narrower_ordy                 : std_logic := '0';
  signal dac_data_narrower_odata                : dac_cswm.dac_cswm.data_complex_t;
  signal dac_data_narrower_odata_vld            : std_logic;

  signal dac_clk_unused_opcode_detected         : std_logic;
  signal ctrl_clr_underrun_sticky_error         : bool_t;
  signal ctrl_clr_unused_opcode_detected_sticky : bool_t;

  signal tx_on_off_s, tx_on_off_r               : std_logic;
  signal start_samples, end_samples             : std_logic;
  signal event_pending, event_present           : std_logic;
  signal ctl_finished_r, ctl_eof                : bool_t;
  -- debug signals
  signal dac_clk_r, dac_clk_rr, dac_clk_rrr     : std_logic; -- debug
  signal ctl_count_r, dac_count_r               : ulong_t;   -- debug
begin
  ctl_out.finished    <= ctl_finished_r;

  -- get the EOF status back into the control clock domain
  -- note that the DAC clock might not be ticking with the dac_rst stuck on
  ctl_eof_cdc : cdc.cdc.single_bit
    port map(src_clk => dev_in.clk,
             src_rst => dac_rst,
             src_en  => '1',
             src_in  => dac_in_demarshaller_oeof,
             dst_clk => ctl_in.clk,
             dst_rst => ctl_in.reset,
             dst_out => ctl_eof);

  -- make the worker finished when the eof comes from the data clock domain
  -- make sure the worker exits the finished state under control reset
  -- EVEN IF THE DAC CLK IS NOT ALIVE AND TICKING
  process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if its(ctl_in.reset) then
        ctl_finished_r <= bfalse;
      else
        if ctl_in.is_operating and ctl_eof then
          ctl_finished_r <= btrue;
        end if;
      end if;
    end if;
  end process;

  in_clk_gen : util.util.in2out
    port map(in_port  => dev_in.clk,
             out_port => in_out.clk);

  dac_rst <= in_in.reset;

  dac_opcode <=
      SAMPLES   when in_in.opcode = ComplexShortWithMetadata_samples_op_e  else
      TIME_TIME when in_in.opcode = ComplexShortWithMetadata_time_op_e     else
      INTERVAL  when in_in.opcode = ComplexShortWithMetadata_interval_op_e else
      FLUSH     when in_in.opcode = ComplexShortWithMetadata_flush_op_e    else
      SYNC      when in_in.opcode = ComplexShortWithMetadata_sync_op_e     else
      SAMPLES;

  props_out.samp_count_before_first_underrun <= to_ulong(dac_status.samp_count_before_first_underrun);
  props_out.num_underruns <= to_ulong(dac_status.num_underruns);

    in_demarshaller : complex_short_with_metadata_demarshaller
      generic map(
        WSI_DATA_WIDTH => to_integer(IN_PORT_DATA_WIDTH))
      port map(
        clk       => dev_in.clk,
        rst       => dac_rst,
        -- INPUT
        idata     => in_in.data,
        ivalid    => in_in.valid,
        iready    => in_in.ready,
        isom      => in_in.som,
        ieom      => in_in.eom,
        iopcode   => dac_opcode,
        ieof      => in_in.eof,
        itake     => in_out.take,
        -- OUTPUT
        oprotocol => dac_in_demarshaller_oprotocol,
        oeof      => dac_in_demarshaller_oeof,
        ordy      => dac_underrun_detector_irdy);

    dac_clk_unused_opcode_detected <=
        not(dac_in_demarshaller_oprotocol.end_of_samples or
        dac_in_demarshaller_oprotocol.samples_vld);

    --On/Off signal used to qualify underrun
    start_samples <= dac_in_demarshaller_oprotocol.samples_vld and
                     not tx_on_off_r;
    end_samples   <= dac_in_demarshaller_oprotocol.end_of_samples or 
                     dac_in_demarshaller_oprotocol.flush or 
                     dac_in_demarshaller_oeof;
    tx_on_off_s   <= start_samples or (tx_on_off_r and not end_samples);

    process(dev_in.clk)
    begin
      if rising_edge(dev_in.clk) then
        if its(dac_rst) then
          tx_on_off_r <= '0';
        else
          tx_on_off_r <= tx_on_off_s;
        end if;
      end if;
    end process;

    dac_underrun_detector_imetadata.underrun_error <= '0';
    dac_underrun_detector_imetadata.ctrl_tx_on_off <= tx_on_off_s;

    --On/Off port logic
    event_present <= start_samples or end_samples;

    --Note that OWD includes Clock='in' for on_off port which means that the
    --on_off port operates in the same clock domain as the in port (dev_in.clk)
    process(dev_in.clk)
    begin
      if rising_edge(dev_in.clk) then
        --reset is used as a way to know whether port is connected
        if its(dac_rst) or its(on_off_in.reset) then
          event_pending <= '0';
        elsif its(not on_off_in.ready) then
          event_pending <= event_present;
        else
          event_pending <= '0';
        end if;
      end if;
    end process;

    on_off_out.give   <= on_off_in.ready and (event_present or event_pending);
    on_off_out.opcode <= tx_event_txOn_op_e  when its(tx_on_off_s)  else tx_event_txOff_op_e;
    dac_underrun_detector : dac_cswm.dac_cswm.underrun_detector
      port map(
        -- CTRL
        clk           => dev_in.clk,
        rst           => dac_rst,
        status        => dac_status,
        -- INPUT
        iprotocol     => dac_in_demarshaller_oprotocol,
        imetadata     => dac_underrun_detector_imetadata,
        imetadata_vld => tx_on_off_s,
        irdy          => dac_underrun_detector_irdy,
        -- OUTPUT
        oprotocol     => dac_underrun_detector_oprotocol,
        ometadata     => dac_underrun_detector_ometadata,
        ometadata_vld => dac_underrun_detector_ometadata_vld,
        ordy          => dac_data_narrower_irdy);

    data_narrower : dac_cswm.dac_cswm.data_narrower
      generic map(
        BITS_PACKED_INTO_LSBS => to_boolean(DAC_OUTPUT_IS_LSB_OF_IN_PORT))
      port map(
        -- CTRL INTERFACE
        clk           => dev_in.clk,
        rst           => dac_rst,
        -- INPUT INTERFACE
        iprotocol     => dac_underrun_detector_oprotocol,
        imetadata     => dac_underrun_detector_ometadata,
        imetadata_vld => dac_underrun_detector_ometadata_vld,
        irdy          => dac_data_narrower_irdy,
        -- OUTPUT INTERFACE
        odata         => dac_data_narrower_odata,
        odata_vld     => dac_data_narrower_odata_vld,
        ometadata     => open,
        ometadata_vld => open,
        ordy          => dac_data_narrower_ordy);

    dac_data_narrower_ordy <= not dac_rst;

    -- outputs to DAC device
    dev_out.present <= '1';
    dev_out.valid <= dac_data_narrower_odata_vld;
    dev_out.data_i(dev_out.data_i'left downto
        dev_out.data_i'left-dac_cswm.dac_cswm.DATA_BIT_WIDTH+1) <=
        dac_data_narrower_odata.i;
    dev_out.data_i(dev_out.data_i'left-dac_cswm.dac_cswm.DATA_BIT_WIDTH downto 0) <=
        (others => '0');
    dev_out.data_q(dev_out.data_q'left downto
        dev_out.data_q'left-dac_cswm.dac_cswm.DATA_BIT_WIDTH+1) <=
        dac_data_narrower_odata.q;
    dev_out.data_q(dev_out.data_q'left-dac_cswm.dac_cswm.DATA_BIT_WIDTH downto 0) <=
        (others => '0');

  ctrl_clr_underrun_sticky_error <= props_in.clr_underrun_sticky_error_written and
                                    props_in.clr_underrun_sticky_error;

  underrun : component cdc.cdc.fast_pulse_to_slow_sticky
    port map(
      fast_clk    => dev_in.clk,
      fast_rst    => dac_rst,
      fast_pulse  => dac_status.underrun_error,
      slow_clk    => ctl_in.clk,
      slow_rst    => ctl_in.reset,
      slow_sticky => props_out.underrun_sticky_error,
      slow_clr    => ctrl_clr_underrun_sticky_error);

  ctrl_clr_unused_opcode_detected_sticky <= props_in.clr_unused_opcode_detected_sticky_written and
                                            props_in.clr_unused_opcode_detected_sticky;

  unused_opcode : component cdc.cdc.fast_pulse_to_slow_sticky
    port map(
      fast_clk    => dev_in.clk,
      fast_rst    => dac_rst,
      fast_pulse  => dac_clk_unused_opcode_detected,
      slow_clk    => ctl_in.clk,
      slow_rst    => ctl_in.reset,
      slow_sticky => props_out.unused_opcode_detected_sticky,
      slow_clr    => ctrl_clr_unused_opcode_detected_sticky);


    -- debug logic
debug: if its(ocpi_debug) generate
    props_out.status <= ushort_t("010100" & in_in.reset & dac_in_demarshaller_oeof &
                        std_logic_vector(to_unsigned(ocpi.wci.state_t'pos(ctl_in.state),3)) &
                        ctl_in.is_operating & dac_rst & in_in.ready & in_in.eof & in_in.valid);
    props_out.ctl_count <= ctl_count_r;
    props_out.dac_count <= dac_count_r;

    process(ctl_in.clk)
    begin
      if rising_edge(ctl_in.clk) then
        if its(ctl_in.reset) then
          ctl_count_r <= (others => '0');
          dac_count_r <= (others => '0');
          dac_clk_r   <= '0';
          dac_clk_rr  <= '0';
          dac_clk_rrr <= '0';
        else
          dac_clk_r   <= dev_in.clk; -- metastable
          dac_clk_rr  <= dac_clk_r;
          dac_clk_rrr <= dac_clk_rr;
          if dac_clk_rr = '1' and dac_clk_rrr = '0' then
            dac_count_r <= dac_count_r + 1;
          end if;
          ctl_count_r <= ctl_count_r + 1;
        end if;
      end if;
    end process;
  end generate;

end rtl;
