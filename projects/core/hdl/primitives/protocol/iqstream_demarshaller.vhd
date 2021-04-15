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
library ocpi; use ocpi.types.all;
library protocol; use protocol.iqstream.all;

entity iqstream_demarshaller is
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
    iopcode   : in  protocol.iqstream.opcode_t;
    ieof      : in  ocpi.types.Bool_t;
    itake     : out ocpi.types.Bool_t;
    -- OUTPUT
    oprotocol : out protocol.iqstream.protocol_t;
    oeof      : out ocpi.types.Bool_t;
    ordy      : in  std_logic);
end entity;
architecture rtl of iqstream_demarshaller is

  signal eozlm   : std_logic := '0';
  signal iinfo   : std_logic := '0';
  signal ixfer   : std_logic := '0';
  signal take    : std_logic := '0';
  signal itake_s : std_logic := '0';

  signal protocol_s : protocol.iqstream.protocol_t :=
                      protocol.iqstream.PROTOCOL_ZERO;

  signal arg_31_0 : std_logic_vector(31 downto 0) := (others => '0');
begin

  wsi_data_width_32 : if(WSI_DATA_WIDTH = 32) generate

    iinfo <= '1' when ((iready = '1') and (ivalid = '1')) else '0';

    take  <= iinfo and ordy;
    ixfer <= iinfo and itake_s;
    --ixfer <= take;

    -- reference https://opencpi.github.io/OpenCPI_HDL_Development.pdf section
    -- 3.8.1 Message Payloads vs. Physical Data Width on Data Interfaces
    arg_31_0 <= idata;

    -- this is the heart of the demarshalling functionality
    protocol_s.iq.data.i <= arg_31_0(15 downto 0);
    protocol_s.iq.data.q <= arg_31_0(31 downto 16);
    protocol_s.iq_vld    <= '1' when (iopcode =
        protocol.iqstream.IQ) and (ixfer = '1') else '0';

    -- necessary to prevent combinatorial loop, depending an what's connected to
    -- ordy
    pipeline : process(clk)
    begin
      if(rising_edge(clk)) then
        if(rst = '1') then
          oprotocol <= PROTOCOL_ZERO;
          oeof <= bfalse;
          --itake_s <= '0';
        else
          --itake_s <= take;
          if(ordy = '1') then
          --else
            oprotocol <= protocol_s;
            oeof      <= ieof;
           end if;
        end if;
      end if;
    end process pipeline;

    itake_s <= take;

    itake <= itake_s;
    --itake <= take;

  end generate wsi_data_width_32;

end rtl;
