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
library timed_sample_prot; use timed_sample_prot.complex_short_timed_sample.all;


entity complex_short_timed_sample_demarshaller is
  generic(
    WSI_DATA_WIDTH : positive := 32); --set to 32 will probably change once data_width is parameterized 
  port(
    clk       : in  std_logic;
    rst       : in  std_logic;
    -- INPUT
    idata     : in  std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ivalid    : in  ocpi.types.Bool_t;
    iready    : in  ocpi.types.Bool_t;
    isom      : in  ocpi.types.Bool_t;
    ieom      : in  ocpi.types.Bool_t;
    iopcode   : in  timed_sample_prot.complex_short_timed_sample.opcode_t;
    ieof      : in  ocpi.types.Bool_t;
    itake     : out ocpi.types.Bool_t;
    -- OUTPUT
    oprotocol : out timed_sample_prot.complex_short_timed_sample.protocol_t;
    oeof      : out ocpi.types.Bool_t;
    ordy      : in  std_logic);
end entity;
architecture rtl of complex_short_timed_sample_demarshaller is
  signal eozlm   : std_logic := '0';
  signal iinfo   : std_logic := '0';
  signal ixfer   : std_logic := '0';
  signal take    : std_logic := '0';
  signal take_r  : std_logic := '0';
  signal itake_s : std_logic := '0';
  signal data_r  : std_logic_vector(31 downto 0) :=
                   (others => '0');
  signal data_r2 : std_logic_vector(31 downto 0) :=
                   (others => '0');

  signal timed_sample_prot_s : timed_sample_prot.complex_short_timed_sample.protocol_t :=
                      timed_sample_prot.complex_short_timed_sample.PROTOCOL_ZERO;
  signal take_time_final_r         : std_logic := '0';
  signal take_samp_period_final_r  : std_logic := '0';
  signal take_metadata_final_r     : std_logic := '0';
  signal take_time_final_r2        : std_logic := '0';
  signal take_samp_period_final_r2 : std_logic := '0';
  signal take_metadata_final_r2    : std_logic := '0';

  signal arg_31_0 : std_logic_vector(31 downto 0) := (others => '0');
  signal arg_95_0 : std_logic_vector(95 downto 0) := (others => '0');
begin

--  wsi_data_width_32 : if(WSI_DATA_WIDTH = 32) generate

    eozlm_gen : ocpi.util.zlm_detector
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
          data_r2 <= (others => '0');
        elsif(take = '1') then
          data_r  <= idata;
          data_r2 <= data_r;
        end if;
      end if;
    end process data_reg;

    take_final_regs : process(clk)
    begin
      if(rising_edge(clk)) then
        if(rst = '1') then
          take_time_final_r         <= '0';
          take_time_final_r2        <= '0';
          take_samp_period_final_r  <= '0';
          take_samp_period_final_r2 <= '0';
          take_metadata_final_r     <= '0';
          take_metadata_final_r2    <= '0';

        elsif(take = '1') then
          if(iopcode = timed_sample_prot.complex_short_timed_sample.TIME_TIME) then
            take_time_final_r <= not take_time_final_r;
            take_time_final_r2 <= take_time_final_r;
          else
            take_time_final_r  <= '0';
            take_time_final_r2 <= '0';
          end if;
          if(iopcode = timed_sample_prot.complex_short_timed_sample.SAMPLE_INTERVAL) then
            take_samp_period_final_r <= not take_samp_period_final_r;
            take_samp_period_final_r2 <= take_samp_period_final_r;
          else
            take_samp_period_final_r  <= '0';
            take_samp_period_final_r2 <= '0';
          end if;
          if(iopcode = timed_sample_prot.complex_short_timed_sample.METADATA) then
            take_metadata_final_r <= not take_metadata_final_r;
            take_metadata_final_r2 <= take_metadata_final_r;
          else
            take_metadata_final_r  <= '0';
            take_metadata_final_r2 <= '0';
          end if;
        end if;
      end if;
    end process take_final_regs;

    -- reference https://opencpi.github.io/OpenCPI_HDL_Development.pdf section
    -- 3.8.1 Message Payloads vs. Physical Data Width on Data Interfaces
    arg_31_0 <= idata;
    arg_95_0 <= idata & data_r & data_r2;

    -- this is the heart of the demarshalling functionality
    timed_sample_prot_s.sample.data.real             <= arg_31_0(15 downto 0);
    timed_sample_prot_s.sample.data.imaginary        <= arg_31_0(31 downto 16);
    timed_sample_prot_s.sample_vld                   <= '1' when (iopcode =
        timed_sample_prot.complex_short_timed_sample.SAMPLE) and (ixfer = '1') else '0';

    timed_sample_prot_s.time.fraction(39 downto 32)  <=arg_95_0(63 downto 56); --Fraction is type ulonglong
    timed_sample_prot_s.time.fraction(31 downto 0)   <=arg_95_0(55 downto 24); 
    timed_sample_prot_s.time.seconds                 <= arg_95_0(95 downto 64); -- Seconds is only 32 bits
    timed_sample_prot_s.time_vld                     <= '1' when (take_time_final_r2 = '1') and (ixfer = '1')
                                                        else '0';

    timed_sample_prot_s.sample_interval.fraction(39 downto 32)  <=arg_95_0(63 downto 56); --Fraction is type ulonglong
    timed_sample_prot_s.sample_interval.fraction(31 downto 0)   <=arg_95_0(55 downto 24); 
    timed_sample_prot_s.sample_interval.seconds      <= arg_95_0(95 downto 64); -- Seconds is only 32 bits
    timed_sample_prot_s.sample_interval_vld                 <= '1' when (take_samp_period_final_r2 = '1') and
                                                        (ixfer = '1') else '0';

    timed_sample_prot_s.flush                        <= '1' when (iopcode =
        timed_sample_prot.complex_short_timed_sample.FLUSH) and (ixfer = '1') else '0';

    timed_sample_prot_s.discontinuity                <= '1' when (iopcode =
        timed_sample_prot.complex_short_timed_sample.DISCONTINUITY) and (ixfer = '1') else '0';

    timed_sample_prot_s.metadata.value(63 downto 32)  <=arg_95_0(63 downto 32); --Metadata mimics what is done by the time and sample_interval opcodes
    timed_sample_prot_s.metadata.value(31 downto 0)   <=arg_95_0(31 downto 0); 
    timed_sample_prot_s.metadata.id                  <= arg_95_0(95 downto 64);
    timed_sample_prot_s.metadata_vld                 <= '1' when (take_metadata_final_r2 = '1') and (ixfer = '1') 
                                                        else '0';

--    timed_sample_prot_s.end_of_samples      <= '1' when (iopcode =
--        timed_sample_prot.complex_short_timed_sample.END_OF_SAMPLES) and (ixfer = '1') else '0';

    -- necessary to prevent combinatorial loop, depending an what's connected to
    -- ordy
    pipeline : process(clk)
    begin
      if(rising_edge(clk)) then
        if(rst = '1') then
          oprotocol <= PROTOCOL_ZERO;
          oeof      <= '0';
          --itake_s <= '0';
        else
          --itake_s <= take;
          if(ordy = '1') then
          --else
            oprotocol <= timed_sample_prot_s;
            oeof      <= ieof;
           end if;
        end if;
      end if;
    end process pipeline;

    itake_s <= take;

    itake <= itake_s;
    --itake <= take;

--  end generate wsi_data_width_32;

end rtl;
