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
library axi;

entity axi_interconnect is
  port(
    s_ctrl_axi_in  : in  axi.lite32.axi_m2s_t;
    s_ctrl_axi_out : out axi.lite32.axi_s2m_t;
    s_dac0_axi_in  : in  axi.lite32.axi_m2s_t;
    s_dac0_axi_out : out axi.lite32.axi_s2m_t;
    s_dac1_axi_in  : in  axi.lite32.axi_m2s_t;
    s_dac1_axi_out : out axi.lite32.axi_s2m_t;
    s_dac2_axi_in  : in  axi.lite32.axi_m2s_t;
    s_dac2_axi_out : out axi.lite32.axi_s2m_t;
    s_dac3_axi_in  : in  axi.lite32.axi_m2s_t;
    s_dac3_axi_out : out axi.lite32.axi_s2m_t;
    s_adc0_axi_in  : in  axi.lite32.axi_m2s_t;
    s_adc0_axi_out : out axi.lite32.axi_s2m_t;
    s_adc1_axi_in  : in  axi.lite32.axi_m2s_t;
    s_adc1_axi_out : out axi.lite32.axi_s2m_t;
    s_adc2_axi_in  : in  axi.lite32.axi_m2s_t;
    s_adc2_axi_out : out axi.lite32.axi_s2m_t;
    s_adc3_axi_in  : in  axi.lite32.axi_m2s_t;
    s_adc3_axi_out : out axi.lite32.axi_s2m_t;
    m_axi_in       : in  axi.lite32.axi_s2m_t;
    m_axi_out      : out axi.lite32.axi_m2s_t);
end entity axi_interconnect;
architecture rtl of axi_interconnect is
  type state_t is (
      INIT,
      CTRL_WRITE, CTRL_READ,
      DAC0_WRITE, DAC0_READ,
      DAC1_WRITE, DAC1_READ,
      DAC2_WRITE, DAC2_READ,
      DAC3_WRITE, DAC3_READ,
      ADC0_WRITE, ADC0_READ,
      ADC1_WRITE, ADC1_READ,
      ADC2_WRITE, ADC2_READ,
      ADC3_WRITE, ADC3_READ);
  signal state        : state_t := INIT;
  signal s_ctrl_write : std_logic := '0';
  signal s_ctrl_read  : std_logic := '0';
  signal s_dac0_write : std_logic := '0';
  signal s_dac0_read  : std_logic := '0';
  signal s_dac1_write : std_logic := '0';
  signal s_dac1_read  : std_logic := '0';
  signal s_dac2_write : std_logic := '0';
  signal s_dac2_read  : std_logic := '0';
  signal s_dac3_write : std_logic := '0';
  signal s_dac3_read  : std_logic := '0';
  signal s_adc0_write : std_logic := '0';
  signal s_adc0_read  : std_logic := '0';
  signal s_adc1_write : std_logic := '0';
  signal s_adc1_read  : std_logic := '0';
  signal s_adc2_read  : std_logic := '0';
  signal s_adc2_write : std_logic := '0';
  signal s_adc3_write : std_logic := '0';
  signal s_adc3_read  : std_logic := '0';
  signal cl_w_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal cl_r_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal d0_w_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal d0_r_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal d1_w_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal d1_r_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal d2_w_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal d2_r_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal d3_w_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal d3_r_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal a0_w_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal a0_r_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal a1_w_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal a1_r_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal a2_w_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal a2_r_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal a3_w_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal a3_r_addr    : unsigned(18-1 downto 0)
                      := (others => '0');
  signal cl_aw_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal cl_ar_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal d0_aw_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal d0_ar_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal d1_aw_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal d1_ar_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal d2_aw_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal d2_ar_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal d3_aw_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal d3_ar_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal a0_aw_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal a0_ar_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal a1_aw_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal a1_ar_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal a2_aw_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal a2_ar_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal a3_aw_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
  signal a3_ar_addr   : std_logic_vector(32-1 downto 0)
                      := (others => '0');
begin

  s_ctrl_write <= s_ctrl_axi_in.aw.valid and m_axi_in.aw.ready;
  s_ctrl_read  <= s_ctrl_axi_in.ar.valid and m_axi_in.ar.ready;
  s_dac0_write <= s_dac0_axi_in.aw.valid and m_axi_in.aw.ready;
  s_dac0_read  <= s_dac0_axi_in.ar.valid and m_axi_in.ar.ready;
  s_dac1_write <= s_dac1_axi_in.aw.valid and m_axi_in.aw.ready;
  s_dac1_read  <= s_dac1_axi_in.ar.valid and m_axi_in.ar.ready;
  s_dac2_write <= s_dac2_axi_in.aw.valid and m_axi_in.aw.ready;
  s_dac2_read  <= s_dac2_axi_in.ar.valid and m_axi_in.ar.ready;
  s_dac3_write <= s_dac3_axi_in.aw.valid and m_axi_in.aw.ready;
  s_dac3_read  <= s_dac3_axi_in.ar.valid and m_axi_in.ar.ready;
  s_adc0_write <= s_adc0_axi_in.aw.valid and m_axi_in.aw.ready;
  s_adc0_read  <= s_adc0_axi_in.ar.valid and m_axi_in.ar.ready;
  s_adc1_write <= s_adc1_axi_in.aw.valid and m_axi_in.aw.ready;
  s_adc1_read  <= s_adc1_axi_in.ar.valid and m_axi_in.ar.ready;
  s_adc2_write <= s_adc2_axi_in.aw.valid and m_axi_in.aw.ready;
  s_adc2_read  <= s_adc2_axi_in.ar.valid and m_axi_in.ar.ready;
  s_adc3_write <= s_adc3_axi_in.aw.valid and m_axi_in.aw.ready;
  s_adc3_read  <= s_adc3_axi_in.ar.valid and m_axi_in.ar.ready;

  -- convert 14 bit addresses to 18-bit addresses
  cl_w_addr <= unsigned("0000" & s_ctrl_axi_in.aw.addr(14-1 downto 0));
  d0_w_addr <= unsigned("0000" & s_dac0_axi_in.aw.addr(14-1 downto 0));
  d1_w_addr <= unsigned("0000" & s_dac1_axi_in.aw.addr(14-1 downto 0));
  d2_w_addr <= unsigned("0000" & s_dac2_axi_in.aw.addr(14-1 downto 0));
  d3_w_addr <= unsigned("0000" & s_dac3_axi_in.aw.addr(14-1 downto 0));
  a0_w_addr <= unsigned("0000" & s_adc0_axi_in.aw.addr(14-1 downto 0));
  a1_w_addr <= unsigned("0000" & s_adc1_axi_in.aw.addr(14-1 downto 0));
  a2_w_addr <= unsigned("0000" & s_adc2_axi_in.aw.addr(14-1 downto 0));
  a3_w_addr <= unsigned("0000" & s_adc3_axi_in.aw.addr(14-1 downto 0));
  cl_r_addr <= unsigned("0000" & s_ctrl_axi_in.ar.addr(14-1 downto 0));
  d0_r_addr <= unsigned("0000" & s_dac0_axi_in.ar.addr(14-1 downto 0));
  d1_r_addr <= unsigned("0000" & s_dac1_axi_in.ar.addr(14-1 downto 0));
  d2_r_addr <= unsigned("0000" & s_dac2_axi_in.ar.addr(14-1 downto 0));
  d3_r_addr <= unsigned("0000" & s_dac3_axi_in.ar.addr(14-1 downto 0));
  a0_r_addr <= unsigned("0000" & s_adc0_axi_in.ar.addr(14-1 downto 0));
  a1_r_addr <= unsigned("0000" & s_adc1_axi_in.ar.addr(14-1 downto 0));
  a2_r_addr <= unsigned("0000" & s_adc2_axi_in.ar.addr(14-1 downto 0));
  a3_r_addr <= unsigned("0000" & s_adc3_axi_in.ar.addr(14-1 downto 0));

  -- convert 18-bit address to the address from:
  -- https://docs.xilinx.com/r/en-US/pg269-rf-data-converter/Register-Space
  -- (but on a 32-bit bus since it was decided to use the existing axi.lite32
  -- package for convenience)
  -- 0x00000 - 0x03FFF
  cl_aw_addr <= "00000000000000" & std_logic_vector(cl_w_addr);
  cl_ar_addr <= "00000000000000" & std_logic_vector(cl_r_addr);
  -- 0x04000 - 0x07FFF
  d0_aw_addr <= "00000000000000" & std_logic_vector(d0_w_addr+"00010000000000");
  d0_ar_addr <= "00000000000000" & std_logic_vector(d0_r_addr+"00010000000000");
  -- 0x08000 - 0x0BFFF
  d1_aw_addr <= "00000000000000" & std_logic_vector(d1_w_addr+"00100000000000");
  d1_ar_addr <= "00000000000000" & std_logic_vector(d1_r_addr+"00100000000000");
  -- 0x0C000 - 0x0FFFF
  d2_aw_addr <= "00000000000000" & std_logic_vector(d2_w_addr+"00110000000000");
  d2_ar_addr <= "00000000000000" & std_logic_vector(d2_r_addr+"00110000000000");
  -- 0x10000 - 0x13FFF
  d3_aw_addr <= "00000000000000" & std_logic_vector(d3_w_addr+"01000000000000");
  d3_ar_addr <= "00000000000000" & std_logic_vector(d3_r_addr+"01000000000000");
  -- 0x14000 - 0x17FFF
  a0_aw_addr <= "00000000000000" & std_logic_vector(a0_w_addr+"01010000000000");
  a0_ar_addr <= "00000000000000" & std_logic_vector(a0_r_addr+"01010000000000");
  -- 0x18000 - 0x1BFFF
  a1_aw_addr <= "00000000000000" & std_logic_vector(a1_w_addr+"01100000000000");
  a1_ar_addr <= "00000000000000" & std_logic_vector(a1_r_addr+"01100000000000");
  -- 0x1C000 - 0x1FFFF
  a2_aw_addr <= "00000000000000" & std_logic_vector(a2_w_addr+"01110000000000");
  a2_ar_addr <= "00000000000000" & std_logic_vector(a2_r_addr+"01110000000000");
  -- 0x20000 - 0x23FFF
  a3_aw_addr <= "00000000000000" & std_logic_vector(a3_w_addr+"10000000000000");
  a3_ar_addr <= "00000000000000" & std_logic_vector(a3_r_addr+"10000000000000");

  fsm : process(s_ctrl_axi_in.a.clk)
  begin
    if rising_edge(s_ctrl_axi_in.a.clk) then
      if s_ctrl_axi_in.a.resetn = '0' then
        state <= INIT;
      elsif s_ctrl_write = '1' then
        state <= CTRL_WRITE;
      elsif s_dac0_write = '1' then
        state <= DAC0_WRITE;
      elsif s_dac1_write = '1' then
        state <= DAC1_WRITE;
      elsif s_dac2_write = '1' then
        state <= DAC2_WRITE;
      elsif s_dac3_write = '1' then
        state <= DAC3_WRITE;
      elsif s_adc0_write = '1' then
        state <= ADC0_WRITE;
      elsif s_adc1_write = '1' then
        state <= ADC1_WRITE;
      elsif s_adc2_write = '1' then
        state <= ADC2_WRITE;
      elsif s_adc3_write = '1' then
        state <= ADC3_WRITE;
      elsif s_ctrl_read = '1' then
        state <= CTRL_READ;
      elsif s_dac0_read = '1' then
        state <= DAC0_READ;
      elsif s_dac1_read = '1' then
        state <= DAC1_READ;
      elsif s_dac2_read = '1' then
        state <= DAC2_READ;
      elsif s_dac3_read = '1' then
        state <= DAC3_READ;
      elsif s_adc0_read = '1' then
        state <= ADC0_READ;
      elsif s_adc1_read = '1' then
        state <= ADC1_READ;
      elsif s_adc2_read = '1' then
        state <= ADC2_READ;
      elsif s_adc3_read = '1' then
        state <= ADC3_READ;
      else
        state <= INIT;
      end if;
    end if;
  end process;

  -- a channel
  m_axi_out.a.clk    <= s_ctrl_axi_in.a.clk;
  m_axi_out.a.resetn <= s_ctrl_axi_in.a.resetn;
  -- aw channel
  m_axi_out.aw.addr  <= d0_aw_addr when s_dac0_write = '1' else
                        d1_aw_addr when s_dac1_write = '1' else
                        d2_aw_addr when s_dac2_write = '1' else
                        d3_aw_addr when s_dac3_write = '1' else
                        a0_aw_addr when s_adc0_write = '1' else
                        a1_aw_addr when s_adc1_write = '1' else
                        a2_aw_addr when s_adc2_write = '1' else
                        a3_aw_addr when s_adc3_write = '1' else
                        cl_aw_addr;
  m_axi_out.aw.valid <= s_dac0_axi_in.aw.valid when s_dac0_write = '1' else
                        s_dac1_axi_in.aw.valid when s_dac1_write = '1' else
                        s_dac2_axi_in.aw.valid when s_dac2_write = '1' else
                        s_dac3_axi_in.aw.valid when s_dac3_write = '1' else
                        s_adc0_axi_in.aw.valid when s_adc0_write = '1' else
                        s_adc1_axi_in.aw.valid when s_adc1_write = '1' else
                        s_adc2_axi_in.aw.valid when s_adc2_write = '1' else
                        s_adc3_axi_in.aw.valid when s_adc3_write = '1' else
                        s_ctrl_axi_in.aw.valid;
  m_axi_out.aw.prot  <= s_dac0_axi_in.aw.prot when s_dac0_write = '1' else
                        s_dac1_axi_in.aw.prot when s_dac1_write = '1' else
                        s_dac2_axi_in.aw.prot when s_dac2_write = '1' else
                        s_dac3_axi_in.aw.prot when s_dac3_write = '1' else
                        s_adc0_axi_in.aw.prot when s_adc0_write = '1' else
                        s_adc1_axi_in.aw.prot when s_adc1_write = '1' else
                        s_adc2_axi_in.aw.prot when s_adc2_write = '1' else
                        s_adc3_axi_in.aw.prot when s_adc3_write = '1' else
                        s_ctrl_axi_in.aw.prot;
  s_dac0_axi_out.aw.ready <= m_axi_in.aw.ready;
  s_dac1_axi_out.aw.ready <= m_axi_in.aw.ready;
  s_dac2_axi_out.aw.ready <= m_axi_in.aw.ready;
  s_dac3_axi_out.aw.ready <= m_axi_in.aw.ready;
  s_adc0_axi_out.aw.ready <= m_axi_in.aw.ready;
  s_adc1_axi_out.aw.ready <= m_axi_in.aw.ready;
  s_adc2_axi_out.aw.ready <= m_axi_in.aw.ready;
  s_adc3_axi_out.aw.ready <= m_axi_in.aw.ready;
  s_ctrl_axi_out.aw.ready <= m_axi_in.aw.ready;
  -- ar channel
  m_axi_out.ar.addr  <= d0_ar_addr when s_dac0_write = '1' else
                        d1_ar_addr when s_dac1_write = '1' else
                        d2_ar_addr when s_dac2_write = '1' else
                        d3_ar_addr when s_dac3_write = '1' else
                        a0_ar_addr when s_adc0_write = '1' else
                        a1_ar_addr when s_adc1_write = '1' else
                        a2_ar_addr when s_adc2_write = '1' else
                        a3_ar_addr when s_adc3_write = '1' else
                        cl_ar_addr;
  m_axi_out.ar.valid <= s_dac0_axi_in.ar.valid when s_dac0_write = '1' else
                        s_dac1_axi_in.ar.valid when s_dac1_write = '1' else
                        s_dac2_axi_in.ar.valid when s_dac2_write = '1' else
                        s_dac3_axi_in.ar.valid when s_dac3_write = '1' else
                        s_adc0_axi_in.ar.valid when s_adc0_write = '1' else
                        s_adc1_axi_in.ar.valid when s_adc1_write = '1' else
                        s_adc2_axi_in.ar.valid when s_adc2_write = '1' else
                        s_adc3_axi_in.ar.valid when s_adc3_write = '1' else
                        s_ctrl_axi_in.ar.valid;
  m_axi_out.ar.prot  <= s_dac0_axi_in.ar.prot when s_dac0_write = '1' else
                        s_dac1_axi_in.ar.prot when s_dac1_write = '1' else
                        s_dac2_axi_in.ar.prot when s_dac2_write = '1' else
                        s_dac3_axi_in.ar.prot when s_dac3_write = '1' else
                        s_adc0_axi_in.ar.prot when s_adc0_write = '1' else
                        s_adc1_axi_in.ar.prot when s_adc1_write = '1' else
                        s_adc2_axi_in.ar.prot when s_adc2_write = '1' else
                        s_adc3_axi_in.ar.prot when s_adc3_write = '1' else
                        s_ctrl_axi_in.ar.prot;
  s_dac0_axi_out.ar.ready <= m_axi_in.ar.ready;
  s_dac1_axi_out.ar.ready <= m_axi_in.ar.ready;
  s_dac2_axi_out.ar.ready <= m_axi_in.ar.ready;
  s_dac3_axi_out.ar.ready <= m_axi_in.ar.ready;
  s_adc0_axi_out.ar.ready <= m_axi_in.ar.ready;
  s_adc1_axi_out.ar.ready <= m_axi_in.ar.ready;
  s_adc2_axi_out.ar.ready <= m_axi_in.ar.ready;
  s_adc3_axi_out.ar.ready <= m_axi_in.ar.ready;
  s_ctrl_axi_out.ar.ready <= m_axi_in.ar.ready;
  -- w channel
  m_axi_out.w.data  <= s_ctrl_axi_in.w.data when state = CTRL_WRITE else
                       s_dac0_axi_in.w.data when state = DAC0_WRITE else
                       s_dac1_axi_in.w.data when state = DAC1_WRITE else
                       s_dac2_axi_in.w.data when state = DAC2_WRITE else
                       s_dac3_axi_in.w.data when state = DAC3_WRITE else
                       s_adc0_axi_in.w.data when state = ADC0_WRITE else
                       s_adc1_axi_in.w.data when state = ADC1_WRITE else
                       s_adc2_axi_in.w.data when state = ADC2_WRITE else
                       s_adc3_axi_in.w.data when state = ADC3_WRITE else
                       s_ctrl_axi_in.w.data;
  m_axi_out.w.strb  <= s_ctrl_axi_in.w.strb when state = CTRL_WRITE else
                       s_dac0_axi_in.w.strb when state = DAC0_WRITE else
                       s_dac1_axi_in.w.strb when state = DAC1_WRITE else
                       s_dac2_axi_in.w.strb when state = DAC2_WRITE else
                       s_dac3_axi_in.w.strb when state = DAC3_WRITE else
                       s_adc0_axi_in.w.strb when state = ADC0_WRITE else
                       s_adc1_axi_in.w.strb when state = ADC1_WRITE else
                       s_adc2_axi_in.w.strb when state = ADC2_WRITE else
                       s_adc3_axi_in.w.strb when state = ADC3_WRITE else
                       s_ctrl_axi_in.w.strb;
  m_axi_out.w.valid <= s_ctrl_axi_in.w.valid when state = CTRL_WRITE else
                       s_dac0_axi_in.w.valid when state = DAC0_WRITE else
                       s_dac1_axi_in.w.valid when state = DAC1_WRITE else
                       s_dac2_axi_in.w.valid when state = DAC2_WRITE else
                       s_dac3_axi_in.w.valid when state = DAC3_WRITE else
                       s_adc0_axi_in.w.valid when state = ADC0_WRITE else
                       s_adc1_axi_in.w.valid when state = ADC1_WRITE else
                       s_adc2_axi_in.w.valid when state = ADC2_WRITE else
                       s_adc3_axi_in.w.valid when state = ADC3_WRITE else
                       s_ctrl_axi_in.w.valid;
  s_ctrl_axi_out.w.ready <= m_axi_in.w.ready;
  s_dac0_axi_out.w.ready <= m_axi_in.w.ready;
  s_dac1_axi_out.w.ready <= m_axi_in.w.ready;
  s_dac2_axi_out.w.ready <= m_axi_in.w.ready;
  s_dac3_axi_out.w.ready <= m_axi_in.w.ready;
  s_adc0_axi_out.w.ready <= m_axi_in.w.ready;
  s_adc1_axi_out.w.ready <= m_axi_in.w.ready;
  s_adc2_axi_out.w.ready <= m_axi_in.w.ready;
  s_adc3_axi_out.w.ready <= m_axi_in.w.ready;
  -- r channel
  s_ctrl_axi_out.r.data <= m_axi_in.r.data;
  s_dac0_axi_out.r.data <= m_axi_in.r.data;
  s_dac1_axi_out.r.data <= m_axi_in.r.data;
  s_dac2_axi_out.r.data <= m_axi_in.r.data;
  s_dac3_axi_out.r.data <= m_axi_in.r.data;
  s_adc0_axi_out.r.data <= m_axi_in.r.data;
  s_adc1_axi_out.r.data <= m_axi_in.r.data;
  s_adc2_axi_out.r.data <= m_axi_in.r.data;
  s_adc3_axi_out.r.data <= m_axi_in.r.data;
  s_ctrl_axi_out.r.resp <= m_axi_in.r.resp;
  s_dac0_axi_out.r.resp <= m_axi_in.r.resp;
  s_dac1_axi_out.r.resp <= m_axi_in.r.resp;
  s_dac2_axi_out.r.resp <= m_axi_in.r.resp;
  s_dac3_axi_out.r.resp <= m_axi_in.r.resp;
  s_adc0_axi_out.r.resp <= m_axi_in.r.resp;
  s_adc1_axi_out.r.resp <= m_axi_in.r.resp;
  s_adc2_axi_out.r.resp <= m_axi_in.r.resp;
  s_adc3_axi_out.r.resp <= m_axi_in.r.resp;
  s_ctrl_axi_out.r.valid <= m_axi_in.r.valid when state = CTRL_READ else '0';
  s_dac0_axi_out.r.valid <= m_axi_in.r.valid when state = DAC0_READ else '0';
  s_dac1_axi_out.r.valid <= m_axi_in.r.valid when state = DAC1_READ else '0';
  s_dac2_axi_out.r.valid <= m_axi_in.r.valid when state = DAC2_READ else '0';
  s_dac3_axi_out.r.valid <= m_axi_in.r.valid when state = DAC3_READ else '0';
  s_adc0_axi_out.r.valid <= m_axi_in.r.valid when state = ADC0_READ else '0';
  s_adc1_axi_out.r.valid <= m_axi_in.r.valid when state = ADC1_READ else '0';
  s_adc2_axi_out.r.valid <= m_axi_in.r.valid when state = ADC2_READ else '0';
  s_adc3_axi_out.r.valid <= m_axi_in.r.valid when state = ADC3_READ else '0';
  m_axi_out.r.ready <= s_ctrl_axi_in.r.ready when state = CTRL_READ else
                       s_dac0_axi_in.r.ready when state = DAC0_READ else
                       s_dac1_axi_in.r.ready when state = DAC1_READ else
                       s_dac2_axi_in.r.ready when state = DAC2_READ else
                       s_dac3_axi_in.r.ready when state = DAC3_READ else
                       s_adc0_axi_in.r.ready when state = ADC0_READ else
                       s_adc1_axi_in.r.ready when state = ADC1_READ else
                       s_adc2_axi_in.r.ready when state = ADC2_READ else
                       s_adc3_axi_in.r.ready when state = ADC3_READ else
                       s_ctrl_axi_in.r.ready;
  -- b channel
  s_ctrl_axi_out.b.resp <= m_axi_in.b.resp;
  s_dac0_axi_out.b.resp <= m_axi_in.b.resp;
  s_dac1_axi_out.b.resp <= m_axi_in.b.resp;
  s_dac2_axi_out.b.resp <= m_axi_in.b.resp;
  s_dac3_axi_out.b.resp <= m_axi_in.b.resp;
  s_adc0_axi_out.b.resp <= m_axi_in.b.resp;
  s_adc1_axi_out.b.resp <= m_axi_in.b.resp;
  s_adc2_axi_out.b.resp <= m_axi_in.b.resp;
  s_adc3_axi_out.b.resp <= m_axi_in.b.resp;
  s_ctrl_axi_out.b.valid <= m_axi_in.b.valid when state = CTRL_WRITE else '0';
  s_dac0_axi_out.b.valid <= m_axi_in.b.valid when state = DAC0_WRITE else '0';
  s_dac1_axi_out.b.valid <= m_axi_in.b.valid when state = DAC1_WRITE else '0';
  s_dac2_axi_out.b.valid <= m_axi_in.b.valid when state = DAC2_WRITE else '0';
  s_dac3_axi_out.b.valid <= m_axi_in.b.valid when state = DAC3_WRITE else '0';
  s_adc0_axi_out.b.valid <= m_axi_in.b.valid when state = ADC0_WRITE else '0';
  s_adc1_axi_out.b.valid <= m_axi_in.b.valid when state = ADC1_WRITE else '0';
  s_adc2_axi_out.b.valid <= m_axi_in.b.valid when state = ADC2_WRITE else '0';
  s_adc3_axi_out.b.valid <= m_axi_in.b.valid when state = ADC3_WRITE else '0';
  m_axi_out.b.ready  <= s_ctrl_axi_in.b.ready when state = CTRL_WRITE else
                        s_dac0_axi_in.b.ready when state = DAC0_WRITE else
                        s_dac1_axi_in.b.ready when state = DAC1_WRITE else
                        s_dac2_axi_in.b.ready when state = DAC2_WRITE else
                        s_dac3_axi_in.b.ready when state = DAC3_WRITE else
                        s_adc0_axi_in.b.ready when state = ADC0_WRITE else
                        s_adc1_axi_in.b.ready when state = ADC1_WRITE else
                        s_adc2_axi_in.b.ready when state = ADC2_WRITE else
                        s_adc3_axi_in.b.ready when state = ADC3_WRITE else
                        s_ctrl_axi_in.b.ready;

end rtl;
