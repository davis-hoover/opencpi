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

-- This primitive handles sending samples and sync opcodes for workers that 
-- are data soruces and use insert_eom='true' on their output port

library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library ocpi;
library protocol; use protocol.complex_short_with_metadata.all;

entity out_port_cswm_samples_and_sync is
  generic(
    WSI_DATA_WIDTH    : positive := 16; -- 16 is default of codegen, but
                                        -- MUST USE 32 FOR NOW
    WSI_MBYTEEN_WIDTH : positive := 4);
  port(
    clk               : in  std_logic;
    rst               : in  std_logic;
    -- INPUT
    iprotocol         : in  protocol.complex_short_with_metadata.protocol_t;
    iready            : in  ocpi.types.Bool_t;
    isuppress_sync_op : in  ocpi.types.Bool_t;
    -- OUTPUT
    odata             : out std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ovalid            : out ocpi.types.Bool_t;
    obyte_enable      : out std_logic_vector(WSI_MBYTEEN_WIDTH-1 downto 0);
    ogive             : out ocpi.types.Bool_t;
    osom              : out ocpi.types.Bool_t;
    oeom              : out ocpi.types.Bool_t;
    oopcode           : out protocol.complex_short_with_metadata.opcode_t);
end entity;
architecture rtl of out_port_cswm_samples_and_sync is

  signal out_give               : std_logic;
  signal out_valid              : std_logic;
  signal out_som                : std_logic;
  signal out_eom                : std_logic;
  signal sync_ready_r           : std_logic;
  signal sync                   : std_logic;
  signal sync_sticky_r          : std_logic;
  signal out_opcode : protocol.complex_short_with_metadata.opcode_t;

begin
  wsi_data_width_32 : if(WSI_DATA_WIDTH = 32) generate
    out_opcode <=  protocol.complex_short_with_metadata.SYNC when (sync_ready_r = '1' and isuppress_sync_op = '0')     else
               protocol.complex_short_with_metadata.SAMPLES;

    out_som   <= sync_ready_r; -- start sync message
    out_valid <= (iready and iprotocol.samples_vld) when (out_opcode = protocol.complex_short_with_metadata.SAMPLES) else '0';
    out_eom   <= sync or sync_ready_r; -- end current message when a sync occurs or end sync message
    out_give  <= (out_som or out_eom or out_valid) and iready;
    
    sync <= (iprotocol.sync or sync_sticky_r) and not isuppress_sync_op;
    
    -- Register sync when it happens in case the output port is not ready.
    -- And also get ready to start the sync message
    sync_ready_reg : process (clk)
    begin
        if rising_edge(clk) then
          if (rst = '1' or isuppress_sync_op = '1') then
            sync_ready_r <= '0';
            sync_sticky_r <= '0';
          elsif (isuppress_sync_op = '0') then
            if (sync = '1' and sync_ready_r = '0' and iready = '1') then
              sync_ready_r  <= '1';
              sync_sticky_r <= '0';
            elsif (sync_ready_r = '1' and iready = '1') then
              sync_ready_r <= '0';
            elsif (iprotocol.sync = '1') then 
              sync_sticky_r <= '1';
            end if;
          end if;
        end if;
    end process sync_ready_reg;

    odata        <= iprotocol.samples.iq.q & iprotocol.samples.iq.i;
    ovalid       <= out_valid;
    ogive        <= out_give;
    osom         <= out_som;
    oeom         <= out_eom;
    obyte_enable <= (others => '1');
    oopcode      <= out_opcode;
  end generate wsi_data_width_32;
end rtl;
