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
use ieee.math_real.all;
library ocpi, axi, cdc;
library ocpi_core_bsv; use ocpi_core_bsv.all;

entity rfdc is
  generic(
    NUM_RX_CHANS        : positive; -- must be 2 for now
    NUM_TX_CHANS        : positive; -- must be 2 for now
    AXI_STREAM_LOOPBACK : boolean := false);
  port(
    -- WCI / raw props
    raw_props_clk   : in  std_logic;
    raw_props_reset : in  std_logic;
    raw_props_in    : in  ocpi.wci.raw_in_t;
    raw_props_out   : out ocpi.wci.raw_out_t;
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
    s_axis_0_tready : out std_logic;
    s_axis_1_aclk   : out std_logic;
    s_axis_1_tdata  : in  std_logic_vector(32-1 downto 0);
    s_axis_1_tvalid : in  std_logic;
    s_axis_1_tready : out std_logic;
    -- AXI-Stream ports for complex RX paths, TDATA is Q [31:16], I [15:0]
    m_axis_0_aclk   : out std_logic;
    m_axis_0_areset : out std_logic;
    m_axis_0_tdata  : out std_logic_vector(32-1 downto 0);
    m_axis_0_tvalid : out std_logic;
    m_axis_0_tready : in  std_logic;
    m_axis_1_aclk   : out std_logic;
    m_axis_1_areset : out std_logic;
    m_axis_1_tdata  : out std_logic_vector(32-1 downto 0);
    m_axis_1_tvalid : out std_logic;
    m_axis_1_tready : in  std_logic);
end entity rfdc;
architecture structural of rfdc is
  constant FIFO_DEPTH : positive := 16;
  signal zeros_32 : std_logic_vector(32-1 downto 0)
                  := (others => '0');
  signal zero     : std_logic := '0';
  -- raw clk domain
  signal axi_converter_to_xilinx_rfdc_ip_axi_in : axi.lite32.axi_s2m_t := (
      aw => (READY => '0'),
      ar => (READY => '0'),
      w => (READY => '0'),
      r => (DATA => (others => '0'), RESP => (others => '0'), VALID => '0'),
      b => (RESP => (others => '0'), VALID => '0'));
  signal axi_converter_to_xilinx_rfdc_ip_axi_out : axi.lite32.axi_m2s_t := (
      a => (CLK => '0', RESETn => '0'),
      aw => (ADDR => (others => '0'), VALID => '0', PROT => (others => '0')),
      ar => (ADDR => (others => '0'), VALID => '0', PROT => (others => '0')),
      w => (DATA => (others => '0'), STRB => (others => '0'), VALID => '0'),
      r => (READY => '0'),
      b => (READY => '0'));
  -- rx_0 clk domain
  signal rx_0_clk                   : std_logic := '0';
  signal rx_0_reset                 : std_logic := '0';
  signal rx_0_resetn                : std_logic := '0';
  signal rfdc_to_rx_0_i_fifo_tdata  : std_logic_vector(16-1 downto 0)
                                    := (others => '0');
  signal rfdc_to_rx_0_i_fifo_tvalid : std_logic := '0';
  signal rfdc_to_rx_0_i_fifo_tready : std_logic := '0';
  signal rfdc_to_rx_0_q_fifo_tdata  : std_logic_vector(16-1 downto 0)
                                    := (others => '0');
  signal rfdc_to_rx_0_q_fifo_tvalid : std_logic := '0';
  signal rfdc_to_rx_0_q_fifo_tready : std_logic := '0';
  signal rx_0_i_fifo_deq            : std_logic := '0';
  signal rx_0_q_fifo_deq            : std_logic := '0';
  signal rx_0_i_fifo_tvalid         : std_logic := '0';
  signal rx_0_q_fifo_tvalid         : std_logic := '0';
  -- rx_1 clk domain
  signal rx_1_clk                   : std_logic := '0';
  signal rx_1_reset                 : std_logic := '0';
  signal rx_1_resetn                : std_logic := '0';
  signal rfdc_to_rx_1_i_fifo_tdata  : std_logic_vector(16-1 downto 0)
                                    := (others => '0');
  signal rfdc_to_rx_1_i_fifo_tvalid : std_logic := '0';
  signal rfdc_to_rx_1_i_fifo_tready : std_logic := '0';
  signal rfdc_to_rx_1_q_fifo_tdata  : std_logic_vector(16-1 downto 0)
                                    := (others => '0');
  signal rfdc_to_rx_1_q_fifo_tvalid : std_logic := '0';
  signal rfdc_to_rx_1_q_fifo_tready : std_logic := '0';
  signal rx_1_i_fifo_deq            : std_logic := '0';
  signal rx_1_q_fifo_deq            : std_logic := '0';
  signal rx_1_i_fifo_tvalid         : std_logic := '0';
  signal rx_1_q_fifo_tvalid         : std_logic := '0';
  -- tx_0 clk domain
  signal tx_0_clk    : std_logic := '0';
  signal tx_0_reset  : std_logic := '0';
  signal tx_0_resetn : std_logic := '0';
  -- tx_1 clk domain
  signal tx_1_clk    : std_logic := '0';
  signal tx_1_reset  : std_logic := '0';
  signal tx_1_resetn : std_logic := '0';
begin

  axi_converter : axi.lite32.raw2axi_lite32
    port map(
      clk     => raw_props_clk,
      reset   => raw_props_reset,
      raw_in  => raw_props_in,
      raw_out => raw_props_out,
      axi_in  => axi_converter_to_xilinx_rfdc_ip_axi_in,
      axi_out => axi_converter_to_xilinx_rfdc_ip_axi_out);

  s_axis_0_aclk <= tx_0_clk;
  s_axis_1_aclk <= tx_1_clk;
  m_axis_0_aclk <= rx_0_clk;
  m_axis_1_aclk <= rx_1_clk;
  m_axis_0_areset <= rx_0_reset;
  m_axis_1_areset <= rx_1_reset;

  axi_stream_loopback_true : if AXI_STREAM_LOOPBACK generate
    tx_0_clk        <= raw_props_clk;
    tx_1_clk        <= raw_props_clk;
    rx_0_clk        <= raw_props_clk;
    rx_1_clk        <= raw_props_clk;
    m_axis_0_areset <= raw_reset;
    m_axis_1_areset <= raw_reset;
    m_axis_0_tdata  <= s_axis_0_tdata;
    m_axis_0_tvalid <= s_axis_0_tvalid;
    s_axis_0_tready <= s_axis_0_tready;
    m_axis_1_tdata  <= s_axis_1_tdata;
    m_axis_1_tvalid <= s_axis_1_tvalid;
    s_axis_1_tready <= m_axis_1_tready;
  end generate;

  rx_2_tx_2 : if (AXI_STREAM_LOOPBACK = false) and NUM_RX_CHANS = 2 and
      NUM_TX_CHANS = 2 generate

    rx_0_reset_synchronizer : cdc.cdc.reset
      generic map(
        SRC_RST_VALUE => '0')
      port map(
        src_rst   => raw_props_reset,
        dst_clk   => rx_0_clk,
        dst_rst   => rx_0_reset,
        dst_rst_n => rx_0_resetn);

    rx_1_reset_synchronizer : cdc.cdc.reset
      generic map(
        SRC_RST_VALUE => '0')
      port map(
        src_rst   => raw_props_reset,
        dst_clk   => rx_1_clk,
        dst_rst   => rx_1_reset,
        dst_rst_n => rx_1_resetn);

    tx_0_reset_synchronizer : cdc.cdc.reset
      generic map(
        SRC_RST_VALUE => '0')
      port map(
        src_rst   => raw_props_reset,
        dst_clk   => tx_0_clk,
        dst_rst   => tx_0_reset,
        dst_rst_n => tx_0_resetn);

    tx_1_reset_synchronizer : cdc.cdc.reset
      generic map(
        SRC_RST_VALUE => '0')
      port map(
        src_rst   => raw_props_reset,
        dst_clk   => tx_1_clk,
        dst_rst   => tx_1_reset,
        dst_rst_n => tx_1_resetn);

    xilinx_rfdc_ip : rfdc_ip
      port map(
        adc0_clk_p => rx_clks_p(0),
        adc0_clk_n => rx_clks_n(0),
        clk_adc0 => rx_0_clk,
        adc2_clk_p => rx_clks_p(1),
        adc2_clk_n => rx_clks_n(1),
        clk_adc2 => rx_1_clk,
        dac2_clk_p => tx_clks_p(0),
        dac2_clk_n => tx_clks_n(0),
        clk_dac2 => tx_0_clk,
        clk_dac3 => tx_1_clk,
        s_axi_aclk => raw_props_clk,
        s_axi_aresetn => raw_props_reset,
        s_axi_awaddr  => axi_converter_to_xilinx_rfdc_ip_axi_out.aw.ADDR(18-1 downto 0),
        s_axi_awvalid => axi_converter_to_xilinx_rfdc_ip_axi_out.aw.VALID,
        s_axi_awready => axi_converter_to_xilinx_rfdc_ip_axi_in.aw.READY,
        s_axi_wdata   => axi_converter_to_xilinx_rfdc_ip_axi_out.w.DATA,
        s_axi_wstrb   => axi_converter_to_xilinx_rfdc_ip_axi_out.w.STRB,
        s_axi_wvalid  => axi_converter_to_xilinx_rfdc_ip_axi_out.w.VALID,
        s_axi_wready  => axi_converter_to_xilinx_rfdc_ip_axi_in.w.READY,
        s_axi_bresp   => axi_converter_to_xilinx_rfdc_ip_axi_in.b.RESP,
        s_axi_bvalid  => axi_converter_to_xilinx_rfdc_ip_axi_in.b.VALID,
        s_axi_bready  => axi_converter_to_xilinx_rfdc_ip_axi_out.b.READY,
        s_axi_araddr  => axi_converter_to_xilinx_rfdc_ip_axi_out.ar.ADDR(18-1 downto 0),
        s_axi_arvalid => axi_converter_to_xilinx_rfdc_ip_axi_out.ar.VALID,
        s_axi_arready => axi_converter_to_xilinx_rfdc_ip_axi_in.ar.READY,
        s_axi_rdata   => axi_converter_to_xilinx_rfdc_ip_axi_in.r.DATA,
        s_axi_rresp   => axi_converter_to_xilinx_rfdc_ip_axi_in.r.RESP,
        s_axi_rvalid  => axi_converter_to_xilinx_rfdc_ip_axi_in.r.VALID,
        s_axi_rready  => axi_converter_to_xilinx_rfdc_ip_axi_out.r.READY,
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
        m0_axis_aresetn => rx_0_resetn,
        m0_axis_aclk => rx_0_clk,
        -- Tile_224 ADC0 I data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        m00_axis_tdata  => rfdc_to_rx_0_i_fifo_tdata,
        m00_axis_tvalid => rfdc_to_rx_0_i_fifo_tvalid,
        m00_axis_tready => rfdc_to_rx_0_i_fifo_tready,
        -- Tile_224 ADC0 Q data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        m01_axis_tdata  => rfdc_to_rx_0_i_fifo_tdata,
        m01_axis_tvalid => rfdc_to_rx_0_i_fifo_tvalid,
        m01_axis_tready => rfdc_to_rx_0_i_fifo_tready,
        m2_axis_aresetn => rx_1_resetn,
        m2_axis_aclk => rx_1_clk,
        -- Tile_224 ADC1 I data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        m20_axis_tdata => rfdc_to_rx_1_i_fifo_tdata,
        m20_axis_tvalid => rfdc_to_rx_1_i_fifo_tvalid,
        m20_axis_tready => rfdc_to_rx_1_i_fifo_tready,
        -- Tile_224 ADC1 Q data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        m21_axis_tdata => rfdc_to_rx_1_q_fifo_tdata,
        m21_axis_tvalid => rfdc_to_rx_1_q_fifo_tvalid,
        m21_axis_tready => rfdc_to_rx_1_q_fifo_tready,
        s2_axis_aresetn => tx_0_resetn,
        s2_axis_aclk => tx_0_clk,
        s20_axis_tdata => zeros_32,
        s20_axis_tvalid => zero,
        s20_axis_tready => open,
        s22_axis_tdata => zeros_32,
        s22_axis_tvalid => zero,
        s22_axis_tready => open,
        s3_axis_aresetn => tx_1_resetn,
        s3_axis_aclk => tx_1_clk,
        -- Tile_231 DAC0 data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        s30_axis_tdata => s_axis_0_tdata,
        s30_axis_tvalid => s_axis_0_tvalid,
        s30_axis_tready => s_axis_0_tready,
        -- Tile_231 DAC2 data (Zynq Ulstrascale+ RF Data Converter (2.5) GUI for ZU48DR)
        s32_axis_tdata => s_axis_1_tdata,
        s32_axis_tvalid => s_axis_1_tvalid,
        s32_axis_tready => s_axis_1_tready);

  rx_0_i_fifo : bsv_pkg.SizedFIFO
    generic map(
      p1width      => 16,
      p2depth      => FIFO_DEPTH+1,
      p3cntr_width => integer(log2(real(FIFO_DEPTH))))
    port map(
      CLK     => rx_0_clk,
      RST     => rx_0_reset,
      D_IN    => rfdc_to_rx_0_i_fifo_tdata,
      ENQ     => rfdc_to_rx_0_i_fifo_tvalid,
      FULL_N  => rfdc_to_rx_0_i_fifo_tready,
      D_OUT   => m_axis_0_tdata(16-1 downto 0),
      DEQ     => rx_0_i_fifo_deq,
      EMPTY_N => rx_0_i_fifo_tvalid,
      CLR     => zero);

  rx_0_q_fifo : bsv.bsv.SizedFIFO
    generic map(
      p1width      => 16,
      p2depth      => FIFO_DEPTH+1,
      p3cntr_width => integer(log2(real(FIFO_DEPTH))))
    port map(
      CLK     => rx_0_clk,
      RST     => rx_0_reset,
      D_IN    => rfdc_to_rx_0_q_fifo_tdata,
      ENQ     => rfdc_to_rx_0_q_fifo_tvalid,
      FULL_N  => rfdc_to_rx_0_q_fifo_tready,
      D_OUT   => m_axis_0_tdata(32-1 downto 16),
      DEQ     => rx_0_q_fifo_deq,
      EMPTY_N => rx_0_q_fifo_tvalid,
      CLR     => zero);

  rx_1_i_fifo : bsv.bsv.SizedFIFO
    generic map(
      p1width      => 16,
      p2depth      => FIFO_DEPTH+1,
      p3cntr_width => integer(log2(real(FIFO_DEPTH))))
    port map(
      CLK     => rx_1_clk,
      RST     => rx_1_reset,
      D_IN    => rfdc_to_rx_1_i_fifo_tdata,
      ENQ     => rfdc_to_rx_1_i_fifo_tvalid,
      FULL_N  => rfdc_to_rx_1_i_fifo_tready,
      D_OUT   => m_axis_1_tdata(16-1 downto 0),
      DEQ     => rx_1_i_fifo_deq,
      EMPTY_N => rx_1_i_fifo_tvalid,
      CLR     => zero);

  rx_1_q_fifo : bsv.bsv.SizedFIFO
    generic map(
      p1width      => 16,
      p2depth      => FIFO_DEPTH+1,
      p3cntr_width => integer(log2(real(FIFO_DEPTH))))
    port map(
      CLK     => rx_1_clk,
      RST     => rx_1_reset,
      D_IN    => rfdc_to_rx_1_q_fifo_tdata,
      ENQ     => rfdc_to_rx_1_q_fifo_tvalid,
      FULL_N  => rfdc_to_rx_1_q_fifo_tready,
      D_OUT   => m_axis_1_tdata(32-1 downto 16),
      DEQ     => rx_1_q_fifo_deq,
      EMPTY_N => rx_1_q_fifo_tvalid,
      CLR     => zero);

  rx_0_i_fifo_deq <= m_axis_0_tready and rx_0_i_fifo_tvalid;
  rx_0_q_fifo_deq <= m_axis_0_tready and rx_0_q_fifo_tvalid;
  rx_1_i_fifo_deq <= m_axis_1_tready and rx_1_i_fifo_tvalid;
  rx_1_q_fifo_deq <= m_axis_1_tready and rx_1_q_fifo_tvalid;
  m_axis_0_tvalid <= rx_0_i_fifo_tvalid and rx_0_q_fifo_tvalid;
  m_axis_1_tvalid <= rx_1_i_fifo_tvalid and rx_1_q_fifo_tvalid;

  end generate rx_2_tx_2;

end structural;
