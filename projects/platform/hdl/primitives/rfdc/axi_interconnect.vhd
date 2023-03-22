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

entity axi_interconnect is
  port(
    rfdc_axi_in      : in  axi_s2m_t;
    rfdc_axi_out     : out axi_m2s_t;
    rfdc_adc_axi_in  : in  axi_s2m_t;
    rfdc_adc_axi_out : out axi_m2s_t;
    rfdc_dac_axi_in  : in  axi_s2m_t;
    rfdc_dac_axi_out : out axi_m2s_t;
    axi_in           : in  axi_s2m_t;
    axi_out          : out axi_m2s_t);
end entity axi_interconnect;
architecture rtl of axi_interconnect is
  type state_t is (CMD_WRITE, CMD_READ, DAC_WRITE, DAC_READ, ADC_WRITE, ADC_READ);
  signal state : state_t := CMD_READ;
  signal cmd_write   : std_logic := '0';
  signal dac_write   : std_logic := '0';
  signal adc_write   : std_logic := '0';
  signal dac_read    : std_logic := '0';
  signal adc_read    : std_logic := '0';
  signal cmd_aw_addr : std_logic_vector(18-1 downto 0)
                     := (others => '0');
  signal cmd_ar_addr : std_logic_vector(18-1 downto 0)
                     := (others => '0');
  signal dac_aw_addr : std_logic_vector(18-1 downto 0)
                     := (others => '0');
  signal dac_ar_addr : std_logic_vector(18-1 downto 0)
                     := (others => '0');
  signal adc_aw_addr : std_logic_vector(18-1 downto 0)
                     := (others => '0');
  signal adc_ar_addr : std_logic_vector(18-1 downto 0)
                     := (others => '0');
begin

  cmd_write <= rfdc_axi_in.aw.valid and axi_in.aw.ready;
  dac_write <= rfdc_dac_axi_in.aw.valid and axi_in.aw.ready;
  adc_write <= rfdc_adc_axi_in.aw.valid and axi_in.aw.ready;
  cmd_read  <= rfdc_axi_in.ar.valid and axi_in.ar.ready;
  dac_read  <= rfdc_dac_axi_in.ar.valid and axi_in.ar.ready;
  adc_read  <= rfdc_adc_axi_in.ar.valid and axi_in.ar.ready;

  -- from 0x0000 - 0x03FFF (which has 14 bits of address)
  -- to   0x0000 - 0x03FFF (with 18 bit address)
  cmd_aw_addr <= to_unsigned(rfdc_adc_axi_in.aw.addr(14-1 downto 0),18);
  cmd_ar_addr <= to_unsigned(rfdc_adc_axi_in.ar.addr(14-1 downto 0),18);
  -- from 0x00000 - 0x0FFFF (which has 16 bits of address)
  -- to   0x04000 - 0x13FF (with 18 bit address)
  dac_aw_addr <= to_unsigned(rfdc_adc_axi_in.aw.addr(16-1 downto 0),18)+x"04000";
  dac_ar_addr <= to_unsigned(rfdc_adc_axi_in.ar.addr(16-1 downto 0),18)+x"04000";
  -- from 0x00000 - 0x0FFFF (which has 16 bits of address)
  -- to   0x14000 - 0x23FFF (with 18 bit address)
  adc_aw_addr <= to_unsigned(rfdc_adc_axi_in.aw.addr(16-1 downto 0),18)+x"14000";
  adc_ar_addr <= to_unsigned(rfdc_adc_axi_in.ar.addr(16-1 downto 0),18)+x"14000";

  fsm : process(rfdc_axi_in.a.clk)
    if rising_edge(rfdc_axi_in.a.clk)
      if rfdc_axi_in.a.resetn = '0' then
        state <= CMD_READ;
      elsif dac_write
        state <= DAC_WRITE;
      elsif dac_read
        state <= DAC_READ;
      elsif adc_write
        state <= ADC_WRITE;
      elsif adc_read
        state <= ADC_READ;
      elsif w
        state <= CMD_WRITE;
      else
        state <= CMD_READ;
      end if;
    end if;
  end process;

  -- a channel interconnect
  axi_out.a.clk    <= rfdc_axi_in.a.clk;
  axi_out.a.resetn <= rfdc_axi_in.a.resetn;
  -- aw channel interconnect
  axi_out.aw.addr  <= dac_aw_addr when dac_write = '1' else
                      adc_aw_addr when adc_write = '1' else
                      cmd_aw_addr;
  axi_out.aw.valid <= rfdc_dac_axi_out.aw.valid when dac_write = '1' else
                      rfdc_adc_axi_out.aw.valid when adc_write = '1' else
                      rfdc_axi_out.aw.valid;
  axi_out.aw.prot  <= rfdc_adac_xi_out.aw.prot when dac_write = '1' else
                      rfdc_adc_axi_out.aw.prot when adc_write = '1' else
                      rfdc_dxi_out.aw.prot;
  rfdc_dac_axi_out.aw.ready <= axi_in.aw.ready;
  rfdc_adc_axi_out.aw.ready <= axi_in.aw.ready;
  rfdc_axi_out.aw.ready     <= axi_in.aw.ready;;
  -- ar channel interconnect
  axi_out.ar.addr  <= dac_ar_addr when dac_read = '1' else
                      adc_ar_addr when adc_read = '1' else
                      cmd_ar_addr;
  axi_out.ar.valid <= rfdc_dac_axi_out.ar.valid when dac_read = '1' else
                      rfdc_adc_axi_out.ar.valid when adc_read = '1' else
                      rfdc_axi_out.ar.valid;
  axi_out.ar.prot  <= rfdc_adac_xi_out.ar.prot when dac_read = '1' else
                      rfdc_adc_axi_out.ar.prot when adc_read = '1' else
                      rfdc_dxi_out.ar.prot;
  rfdc_dac_axi_out.ar.ready <= axi_in.ar.ready;
  rfdc_adc_axi_out.ar.ready <= axi_in.ar.ready;
  rfdc_axi_out.ar.ready     <= axi_in.ar.ready;;
  -- w channel interconnect
  axi_out.w.data  <= rfdc_dac_axi_out.w.data when state = DAC_WRITE else
                     rfdc_adc_axi_out.w.data when state = ADC_WRITE else
                     rfdc_axi_out.w.data;
  axi_out.w.strb  <= rfdc_dac_axi_out.w.strb when state = DAC_WRITE else
                     rfdc_adc_axi_out.w.strb when state = ADC_WRITE else
                     rfdc_axi_out.w.strb;
  axi_out.w.valid <= rfdc_dac_axi_out.w.valid when state = DAC_WRITE else
                     rfdc_adc_axi_out.w.valid when state = ADC_WRITE else
                     rfdc_axi_out.w.valid;
  rfdc_dac_axi_out.w.ready <= axi_in.w.ready;
  rfdc_adc_axi_out.w.ready <= axi_in.w.ready;
  rfdc_axi_out.w.ready     <= axi_in.w.ready;;
  -- r channel interconnect
  rfdc_dac_axi_out.r.data <= axi_in.r.data;
  rfdc_adc_axi_out.r.data <= axi_in.r.data;
  rfdc_axi_out.r.data     <= axi_in.r.data;;
  rfdc_dac_axi_out.r.resp <= axi_in.r.resp;
  rfdc_adc_axi_out.r.resp <= axi_in.r.resp;
  rfdc_axi_out.r.resp     <= axi_in.r.resp;;
  rfdc_dac_axi_out.r.valid <= axi_in.r.valid when state = DAC_READ else '0';
  rfdc_adc_axi_out.r.valid <= axi_in.r.valid when state = ADC_READ else '0';
  rfdc_axi_out.r.valid     <= axi_in.r.valid when state = CMD_READ else '0';
  axi_out.r.ready <= rfdc_dac_axi_out.r.ready when state = DAC_READ else
                     rfdc_adc_axi_out.r.ready when state = ADC_READ else
                     rfdc_axi_out.r.ready;
  -- b channel
  rfdc_dac_axi_in.b.resp <= axi_in.b.resp;
  rfdc_adc_axi_in.b.resp <= axi_in.b.resp;
  rfdc_axi_in.b.resp     <= axi_in.b.resp;
  rfdc_dac_axi_in.b.valid <= axi_in.b.valid when state = DAC_WRITE else '0';
  rfdc_adc_axi_in.b.valid <= axi_in.b.valid when state = ADC_WRITE else '0';
  rfdc_axi_in.b.valid     <= axi_in.b.valid when state = CMD_WRITE else '0';
  axi_out.b.ready  <= rfdc_dac_axi_out.b.ready when state = DAC_WRITE else
                      rfdc_adc_axi_out.b.ready when state = ADC_WRITE else
                      rfdc_axi_out.b.ready;

end rtl;
