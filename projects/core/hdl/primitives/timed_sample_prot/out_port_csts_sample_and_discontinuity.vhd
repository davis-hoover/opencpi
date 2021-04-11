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

-- This primitive handles sending samples and discontinuity opcodes for workers that 
-- are data soruces and use insert_eom='true' on their output port

library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library ocpi;
library timed_sample_prot; use timed_sample_prot.complex_short_timed_sample.all;


entity out_port_csts_sample_and_discontinuity is
  generic(
    WSI_DATA_WIDTH    : positive := 32; 
    WSI_MBYTEEN_WIDTH : positive := 4);
  port(
    clk               : in  std_logic;
    rst               : in  std_logic;
    -- INPUT
    iprotocol         : in  timed_sample_prot.complex_short_timed_sample.protocol_t;
    iready            : in  ocpi.types.Bool_t;
    isuppress_discontinuity_op : in  ocpi.types.Bool_t;
    -- OUTPUT
    odata             : out std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ovalid            : out ocpi.types.Bool_t;
    obyte_enable      : out std_logic_vector(WSI_MBYTEEN_WIDTH-1 downto 0);
    ogive             : out ocpi.types.Bool_t;
    osom              : out ocpi.types.Bool_t;
    oeom              : out ocpi.types.Bool_t;
    oopcode           : out timed_sample_prot.complex_short_timed_sample.opcode_t);
end entity;
architecture rtl of out_port_csts_sample_and_discontinuity is

  signal out_give               : std_logic;
  signal out_valid              : std_logic;
  signal out_som                : std_logic;
  signal out_eom                : std_logic;
  signal discontinuity_ready_r           : std_logic;
  signal discontinuity                   : std_logic;
  signal discontinuity_sticky_r          : std_logic;
  signal out_opcode : timed_sample_prot.complex_short_timed_sample.opcode_t;

begin
    out_opcode <=  timed_sample_prot.complex_short_timed_sample.DISCONTINUITY when (discontinuity_ready_r = '1' and isuppress_discontinuity_op = '0')     else
               timed_sample_prot.complex_short_timed_sample.SAMPLE;

    out_som   <= discontinuity_ready_r; -- start discontinuity message
    out_valid <= (iready and iprotocol.sample_vld) when (out_opcode = timed_sample_prot.complex_short_timed_sample.SAMPLE) else '0';
    out_eom   <= discontinuity or discontinuity_ready_r; -- end current message when a discontinuity occurs or end discontinuity message
    out_give  <= (out_som or out_eom or out_valid) and iready;
    
    discontinuity <= (iprotocol.discontinuity or discontinuity_sticky_r) and not isuppress_discontinuity_op;
    
    -- Register discontinuity when it happens in case the output port is not ready.
    -- And also get ready to start the discontinuity message
    discontinuity_ready_reg : process (clk)
    begin
        if rising_edge(clk) then
          if (rst = '1' or isuppress_discontinuity_op = '1') then
            discontinuity_ready_r <= '0';
            discontinuity_sticky_r <= '0';
          elsif (isuppress_discontinuity_op = '0') then
            if (discontinuity = '1' and discontinuity_ready_r = '0' and iready = '1') then
              discontinuity_ready_r  <= '1';
              discontinuity_sticky_r <= '0';
            elsif (discontinuity_ready_r = '1' and iready = '1') then
              discontinuity_ready_r <= '0';
            elsif (iprotocol.discontinuity = '1') then 
              discontinuity_sticky_r <= '1';
            end if;
          end if;
        end if;
    end process discontinuity_ready_reg;

    odata        <= iprotocol.sample.data.real & iprotocol.sample.data.imaginary;
    ovalid       <= out_valid;
    ogive        <= out_give;
    osom         <= out_som;
    oeom         <= out_eom;
    obyte_enable <= (others => '1');
    oopcode      <= out_opcode;
end rtl;
