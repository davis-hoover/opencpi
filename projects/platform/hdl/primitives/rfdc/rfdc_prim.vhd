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

entity rfdc is
  generic(
    NUM_RX_CHANS : positive; -- must be 2 for now
    NUM_TX_CHANS : positive); -- must be 2 for now
  port(
    -- WCI / raw props
    raw_clk         : in  std_logic;
    raw_reset       : in  std_logic;
    raw_in          : in  ocpi.wci.raw_in_t;
    raw_out         : out ocpi.wci.raw_out_t;
    -- RX path clock inputs
    rx_clks_p       : in  std_logic_vector(NUM_RX_CHANS-1 downto 0);
    rx_clks_n       : in  std_logic_vector(NUM_RX_CHANS-1 downto 0);
    -- TX path clock inputs
    tx_clks_p       : in  std_logic_vector(NUM_TX_CHANS-1 downto 0);
    tx_clks_n       : in  std_logic_vector(NUM_TX_CHANS-1 downto 0);
    -- sysref clock input pair
    sysref_p        : in  std_logic;
    sysref_n        : in  std_logic;
    -- RF inputs
    rf_rx_p         : in  std_logic_vector(NUM_RX_CHANS-1 downto 0);
    rf_rx_n         : in  std_logic_vector(NUM_RX_CHANS-1 downto 0);
    rf_tx_p         : out std_logic_vector(NUM_TX_CHANS-1 downto 0);
    rf_tx_n         : out std_logic_vector(NUM_TX_CHANS-1 downto 0);
    -- AXI-Stream ports for complex TX paths, TDATA is Q [31:16], I [15:0]
    s_axis_0_aclk   : out std_logic;
    s_axis_0_tdata  : in  std_logic_vector(32-1 downto 0);
    s_axis_0_tvalid : in  std_logic;
    s_axis_0_tuser  : in  std_logic_vector(128-1 downto 0);
    s_axis_0_tready : out std_logic;
    s_axis_1_aclk   : out std_logic;
    s_axis_1_tdata  : in  std_logic_vector(32-1 downto 0);
    s_axis_1_tvalid : in  std_logic;
    s_axis_1_tuser  : in  std_logic_vector(128-1 downto 0);
    s_axis_1_tready : out std_logic;
    -- AXI-Stream ports for complex RX paths, TDATA is Q [31:16], I [15:0]
    m_axis_0_tdata  : out std_logic_vector(32-1 downto 0);
    m_axis_0_tvalid : out std_logic;
    m_axis_0_tuser  : out std_logic_vector(128-1 downto 0);
    m_axis_0_tready : in  std_logic;
    m_axis_1_tdata  : out std_logic_vector(32-1 downto 0);
    m_axis_1_tvalid : out std_logic;
    m_axis_1_tuser  : out std_logic_vector(128-1 downto 0);
    m_axis_1_tready : in  std_logic);
end entity rfdc;
architecture structural of rfdc is
  signal rx_clks : std_logic_vector(NUM_RX_CHANS-1 downto 0)
                 := (others => '0');
  signal tx_clks : std_logic_vector(NUM_RX_CHANS-1 downto 0)
                 := (others => '0');
begin

  axi_converter : raw2axi_lite32
    port map(
      clk     => clk,
      reset   => reset,
      raw_in  => props_in.raw,
      raw_out => props_out.raw,
      axi_in  => axi_converter_to_ip_axi_in,
      axi_out => axi_converter_to_ip_axi_out);

  s_axis_0_aclk <= tx_clks(0);
  s_axis_1_aclk <= tx_clks(1);
  m_axis_0_aclk <= rx_clks(0);
  m_axis_1_aclk <= rx_clks(1);

  config_0 : if NUM_RX_CHANS = 2 and NUM_TX_CHANS = 2 generate
    ip : rfdc_ip
      port map(
        adc0_clk_p => rx_clks_p(0),
        adc0_clk_n => rx_clks_n(0),
        clk_adc0 => rx_clks(0),
        adc2_clk_p => rx_clks_p(1),
        adc2_clk_n => rx_clks_n(1),
        clk_adc2 => rx_clks(1),
        dac2_clk_p => tx_clks_p(0),
        dac2_clk_n => tx_clks_n(0),
        clk_dac2 => tx_clks(0),
        clk_dac3 => tx_clks(1),
        s_axi_aclk => raw_clk,
        s_axi_aresetn => raw_reset,
        s_axi_awaddr  => axi_converter_to_rfdc_prim_axi_out.aw.ADDR,
        s_axi_awvalid => axi_converter_to_rfdc_prim_axi_out.aw.VALID,
        s_axi_awready => axi_converter_to_rfdc_prim_axi_in.aw.READY,
        s_axi_wdata   => axi_converter_to_rfdc_prim_axi_out.w.DATA,
        s_axi_wstrb   => axi_converter_to_rfdc_prim_axi_out.w.STRB,
        s_axi_wvalid  => axi_converter_to_rfdc_prim_axi_out.w.VALID,
        s_axi_wready  => axi_converter_to_rfdc_prim_axi_in.w.READY,
        s_axi_bresp   => axi_converter_to_rfdc_prim_axi_in.b.RESP,
        s_axi_bvalid  => axi_converter_to_rfdc_prim_axi_in.b.VALID,
        s_axi_bready  => axi_converter_to_rfdc_prim_axi_out.b.READY,
        s_axi_araddr  => axi_converter_to_rfdc_prim_axi_out.ar.ADDR,
        s_axi_arvalid => axi_converter_to_rfdc_prim_axi_out.ar.VALID,
        s_axi_arready => axi_converter_to_rfdc_prim_axi_in.ar.READY,
        s_axi_rdata   => axi_converter_to_rfdc_prim_axi_in.r.DATA,
        s_axi_rresp   => axi_converter_to_rfdc_prim_axi_in.r.RESP,
        s_axi_rvalid  => axi_converter_to_rfdc_prim_axi_in.r.VALID,
        s_axi_rready  => axi_converter_to_rfdc_prim_axi_out.r.READY,
        irq => open,
        sysref_in_p => sysref_p,
        sysref_in_n => sysref_n,
        -- Tile_224 ADC0 I data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        vin0_01_p => rf_rx_p(0),
        vin0_01_n => rf_rx_n(0),
        -- Tile_224 ADC0 Q data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        vin2_01_p => rf_rx_p(1),
        vin2_01_n => rf_rx_n(1),
        vout20_p => open,
        vout20_n => open,
        vout22_p => open,
        vout22_n => open,
        vout30_p => rf_tx_p(0),
        vout30_n => rf_tx_n(0),
        vout32_p => rf_tx_p(1),
        vout32_n => rf_tx_n(1),
        m0_axis_aresetn => rx_resetn(0),
        m0_axis_aclk => rx_clks(0),
        -- Tile_224 ADC0 I data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        m00_axis_tdata  => m_axis_0_tdata(16-1 downto 0),
        m00_axis_tvalid => m_axis_0_tvalid,
        m00_axis_tready => m_axis_0_tready,
        -- Tile_224 ADC0 Q data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        m01_axis_tdata  => m_axis_0_tdata(32-1 downto 16),
        m01_axis_tvalid => m_axis_0_tvalid,
        m01_axis_tready => m_axis_0_tready,
        m2_axis_aresetn => rx_resetn(1),
        m2_axis_aclk => rx_clks(1),
        -- Tile_224 ADC1 I data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        m20_axis_tdata => m_axis_1_tdata(16-1 downto 0),
        m20_axis_tvalid => m_axis_1_tvalid,
        m20_axis_tready => m_axis_1_tready,
        -- Tile_224 ADC1 Q data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        m21_axis_tdata => m_axis_1_tdata(32-1 downto 16),
        m21_axis_tvalid => m_axis_1_tvalid,
        m21_axis_tready => m_axis_1_tready,
        s2_axis_aresetn => tx_resetn(0),
        s2_axis_aclk => tx_clks(0),
        s20_axis_tdata => open,
        s20_axis_tvalid => open,
        s20_axis_tready => '1',
        s22_axis_tdata => open,
        s22_axis_tvalid => open,
        s22_axis_tready => '1',
        s3_axis_aresetn => tx_resetn(1),
        s3_axis_aclk => tx_clks(1),
        -- Tile_231 DAC0 data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        s30_axis_tdata => s_axis_0_tdata,
        s30_axis_tvalid => s_axis_0_tvalid,
        s30_axis_tready => s_axis_0_tready,
        -- Tile_231 DAC2 data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        s32_axis_tdata => s_axis_1_tdata,
        s32_axis_tvalid => s_axis_1_tvalid,
        s32_axis_tready => s_axis_1_tready);

    s_axis_2_tready <= '0';
    s_axis_3_tready <= '0';
    m_axis_0_tuser  <= (others => '0');
    m_axis_1_tuser  <= (others => '0');

  end generate config_0;

end rtl;
