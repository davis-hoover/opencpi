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
library axi;

architecture rtl of worker is

  signal raw_in_s : ocpi.wci.raw_in_t;
  signal raw_out_s : ocpi.wci.raw_out_t; 
  signal axi_s2m_in  : axi.lite32.axi_s2m_t; 
  signal axi_m2s_out : axi.lite32.axi_m2s_t; 

  constant c_ID : std_logic_vector(31 downto 0) := x"01234567"; 

  signal s_is_working : std_logic;
  signal s_scratch_value : std_logic_vector(31 downto 0);

begin

  s_is_working <= props_in.is_working;                   -- ensures raw write path exists
  props_out.scratch_readback <= to_ulong(s_scratch_value); -- ensures raw read path exists
  
  raw2axi : axi.lite32.raw2axi_lite32 
    port map ( 
      clk 	=> ctl_in.clk,
      reset	=> ctl_in.reset,
      raw_in 	=> props_in.raw, 
      raw_out 	=> props_out.raw, 
      axi_in 	=> axi_s2m_in, 
      axi_out 	=> axi_m2s_out
    );

  internal_register : entity work.opencpi_test_regs
    generic map (
        AXI_ADDR_WIDTH => 32,
        BASEADDR => x"00000000"
    )
    port map(
        -- Clock and Reset
        axi_aclk    => axi_m2s_out.a.clk,
        axi_aresetn => axi_m2s_out.a.resetn,
        -- AXI Write Address Channel
        s_axi_awaddr  => axi_m2s_out.aw.addr,
        s_axi_awprot  => axi_m2s_out.aw.prot,
        s_axi_awvalid => axi_m2s_out.aw.valid,
        s_axi_awready => axi_s2m_in.aw.ready,
        -- AXI Write Data Channel
        s_axi_wdata   => axi_m2s_out.w.data,
        s_axi_wstrb   => axi_m2s_out.w.strb,
        s_axi_wvalid  => axi_m2s_out.w.valid,
        s_axi_wready  => axi_s2m_in.w.ready,
        -- AXI Read Address Channel
        s_axi_araddr  => axi_m2s_out.ar.addr,
        s_axi_arprot  => axi_m2s_out.ar.prot,
        s_axi_arvalid => axi_m2s_out.ar.valid,
        s_axi_arready => axi_s2m_in.ar.ready,
        -- AXI Read Data Channel
        s_axi_rdata   => axi_s2m_in.r.data,
        s_axi_rresp   => axi_s2m_in.r.resp,
        s_axi_rvalid  => axi_s2m_in.r.valid,
        s_axi_rready  => axi_m2s_out.r.ready,
        -- AXI Write Response Channel
        s_axi_bresp   => axi_s2m_in.b.resp,
        s_axi_bvalid  => axi_s2m_in.b.valid,
        s_axi_bready  => axi_m2s_out.b.ready,
        -- User Ports
        id_strobe => open,
        id_value => c_ID,
        scratch_strobe => open,
        scratch_value => s_scratch_value
    );

end rtl;
