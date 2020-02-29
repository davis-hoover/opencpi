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
library ocpi;
library protocol; use protocol.complex_short_with_metadata.all;

entity complex_short_with_metadata_demarshaller is
  generic(
    WSI_DATA_WIDTH : positive := 16); -- 16 is default of codegen, but
                                      -- MUST USE 32 FOR NOW
  port(
    clk       : in  std_logic;
    rst       : in  std_logic;
    -- INPUT
    idata     : in  std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ivalid    : in  ocpi.types.Bool_t;
    iready    : in  ocpi.types.Bool_t;
    isom      : in  ocpi.types.Bool_t;
    ieom      : in  ocpi.types.Bool_t;
    iopcode   : in  protocol.complex_short_with_metadata.opcode_t;
    ieof      : in  ocpi.types.Bool_t;
    itake     : out ocpi.types.Bool_t;
    -- OUTPUT
    oprotocol : out protocol.complex_short_with_metadata.protocol_t;
    ordy      : in  std_logic);
end entity;
architecture rtl of complex_short_with_metadata_demarshaller is

  signal eozlm   : std_logic := '0';
  signal iinfo   : std_logic := '0';
  signal ixfer   : std_logic := '0';
  signal take    : std_logic := '0';
  signal itake_s : std_logic := '0';
  signal data_r  : std_logic_vector(31 downto 0) :=
                   (others => '0');

  signal protocol_s : protocol.complex_short_with_metadata.protocol_t :=
                      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal take_time_final        : std_logic := '0';
  signal take_samp_period_final : std_logic := '0';

  signal arg_31_0 : std_logic_vector(31 downto 0) := (others => '0');
  signal arg_63_0 : std_logic_vector(63 downto 0) := (others => '0');
begin

  wsi_data_width_32 : if(WSI_DATA_WIDTH = 32) generate

    eozlm_gen : protocol.protocol.zlm_detector
      port map(
        clk         => clk,
        reset       => rst,
        som         => isom,
        valid       => ivalid,
        eom         => ieom,
        ready       => iready,
        take        => itake_s,
        eozlm_pulse => open,
        eozlm       => eozlm);

    iinfo <= '1' when ((iready = '1') and ((ivalid = '1') or (eozlm = '1')))
             else '0';

    take  <= iinfo and ordy;
    ixfer <= iinfo and itake_s;
    --ixfer <= take;

    data_reg : process(clk)
    begin
      if(rising_edge(clk)) then
        if(rst = '1') then
          data_r <= (others => '0');
        elsif(take = '1') then
          data_r <= idata;
        end if;
      end if;
    end process data_reg;

    take_final_regs : process(clk)
    begin
      if(rising_edge(clk)) then
        if(rst = '1') then
          take_time_final        <= '0';
          take_samp_period_final <= '0';
        elsif(take = '1') then
          if(iopcode = protocol.complex_short_with_metadata.TIME_TIME) then
            take_time_final <= (not take_time_final);
          else
            take_time_final <= '0';
          end if;
          if(iopcode = protocol.complex_short_with_metadata.INTERVAL) then
            take_samp_period_final <= (not take_samp_period_final);
          else
            take_samp_period_final <= '0';
          end if;
        end if;
      end if;
    end process take_final_regs;

    -- reference https://opencpi.github.io/OpenCPI_HDL_Development.pdf section
    -- 3.8.1 Message Payloads vs. Physical Data Width on Data Interfaces
    arg_31_0 <= idata;
    arg_63_0 <= idata & data_r;

    -- this is the heart of the demarshalling functionality
    protocol_s.samples.iq.i        <= arg_31_0(15 downto 0);
    protocol_s.samples.iq.q        <= arg_31_0(31 downto 16);
    protocol_s.samples_vld         <= '1' when (iopcode =
        protocol.complex_short_with_metadata.SAMPLES) and (ixfer = '1') else '0';
    protocol_s.time.fract_sec      <= arg_63_0(31 downto 0);
    protocol_s.time.sec            <= arg_63_0(63 downto 32);
    protocol_s.time_vld            <= '1' when (take_time_final = '1') and (ixfer = '1')
                                      else '0';
    protocol_s.interval.delta_time <= arg_63_0;
    protocol_s.interval_vld        <= '1' when (take_samp_period_final = '1') and
                                      (ixfer = '1') else '0';
    protocol_s.flush               <= '1' when (iopcode =
        protocol.complex_short_with_metadata.FLUSH) and (ixfer = '1') else '0';
    protocol_s.sync                <= '1' when (iopcode =
        protocol.complex_short_with_metadata.SYNC) and (ixfer = '1') else '0';
    protocol_s.end_of_samples      <= '1' when (iopcode =
        protocol.complex_short_with_metadata.END_OF_SAMPLES) and (ixfer = '1') else '0';
    protocol_s.eof                 <= ieof;

    -- necessary to prevent combinatorial loop, depending an what's connected to
    -- ordy
    pipeline : process(clk)
    begin
      if(rising_edge(clk)) then
        if(rst = '1') then
          oprotocol <= PROTOCOL_ZERO;
          --itake_s <= '0';
        else
          --itake_s <= take;
          if(ordy = '1') then
          --else
            oprotocol <= protocol_s;
           end if;
        end if;
      end if;
    end process pipeline;

    itake_s <= take;

    itake <= itake_s;
    --itake <= take;

  end generate wsi_data_width_32;

end rtl;
