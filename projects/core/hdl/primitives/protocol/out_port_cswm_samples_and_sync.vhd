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

entity out_port_cswm_samples_and_sync is
  generic(
    WSI_DATA_WIDTH    : positive := 16; -- 16 is default of codegen, but
                                        -- MUST USE 32 FOR NOW
    WSI_MBYTEEN_WIDTH : positive := 4);
  port(
    clk          : in  std_logic;
    rst          : in  std_logic;
    -- INPUT
    iprotocol    : in  protocol.complex_short_with_metadata.protocol_t;
    oready       : in  ocpi.types.Bool_t;
    -- OUTPUT
    odata        : out std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ovalid       : out ocpi.types.Bool_t;
    obyte_enable : out std_logic_vector(WSI_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out ocpi.types.Bool_t;
    osom         : out ocpi.types.Bool_t;
    oeom         : out ocpi.types.Bool_t;
    oopcode      : out protocol.complex_short_with_metadata.opcode_t;
    iready       : out std_logic);
end entity;
architecture rtl of out_port_cswm_samples_and_sync is

  constant SAMPLES_MESSAGE_SIZE_BIT_WIDTH : positive :=  ocpi.util.width_for_max(protocol.complex_short_with_metadata.OP_SAMPLES_ARG_IQ_SEQUENCE_LENGTH-1);

  signal give                   : std_logic;
  signal valid                  : std_logic;
  signal som                    : std_logic;
  signal eom                    : std_logic;
  signal sync_ready_r           : std_logic;
  signal opcode : protocol.complex_short_with_metadata.opcode_t :=
                  protocol.complex_short_with_metadata.SAMPLES;

begin
  wsi_data_width_32 : if(WSI_DATA_WIDTH = 32) generate
    opcode <=  protocol.complex_short_with_metadata.SYNC      when (sync_ready_r = '1' and give = '1')     else
               protocol.complex_short_with_metadata.SAMPLES;

    som       <= sync_ready_r;
    valid     <= (oready and iprotocol.samples_vld) when (opcode = protocol.complex_short_with_metadata.SAMPLES) else '0';
    eom       <= iprotocol.sync or sync_ready_r;
    give      <= (som or eom or valid) and oready;

    sync_ready_reg : process (clk)
    begin
        if rising_edge(clk) then
          if rst = '1' then
            sync_ready_r <= '0';
          else
            if (iprotocol.sync = '1' and sync_ready_r = '0') then
              sync_ready_r <= '1';
            elsif (sync_ready_r = '1' and oready = '1') then
              sync_ready_r <= '0';
            end if;
          end if;
        end if;
    end process sync_ready_reg;

    iready       <= oready;
    odata        <= iprotocol.samples.iq.q & iprotocol.samples.iq.i;
    ovalid       <= valid;
    ogive        <= give;
    osom         <= som;
    oeom         <= eom;
    obyte_enable <= (others => '1');
    oopcode      <= opcode;
  end generate wsi_data_width_32;
end rtl;
