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
  port(
    -- rfdc AXI-Lite
    rfdc_axi_in      : in  axi.lite32.axi_m2s_t;
    rfdc_axi_out     : out axi.lite32.axi_s2m_t;
    -- rfdc_adc AXI-Lite
    rfdc_adc_axi_in  : in  axi.lite32.axi_m2s_t;
    rfdc_adc_axi_out : out axi.lite32.axi_s2m_t;
    -- rfdc_dac AXI-Lite
    rfdc_dac_axi_in  : in  axi.lite32.axi_m2s_t;
    rfdc_dac_axi_out : out axi.lite32.axi_s2m_t;
    -- RX path clock inputs
    rx_clks_p       : in  std_logic_vector(2-1 downto 0);
    rx_clks_n       : in  std_logic_vector(2-1 downto 0);
    -- TX path clock inputs
    tx_clks_p       : in  std_logic_vector(1-1 downto 0);
    tx_clks_n       : in  std_logic_vector(1-1 downto 0);
    -- sysref clock input pair
    sysref_p        : in  std_logic;
    sysref_n        : in  std_logic;
    -- RF inputs
    rf_rxs_p        : in  std_logic_vector(2-1 downto 0);
    rf_rxs_n        : in  std_logic_vector(2-1 downto 0);
    rf_txs_p        : out std_logic_vector(4-1 downto 0);
    rf_txs_n        : out std_logic_vector(4-1 downto 0);
    -- AXI-Stream ports for complex TX paths, TDATA is Q [31:16], I [15:0]
    tx_aclks        : out std_logic_vector(1-1 downto 0); -- associated with all s_axis
    s_axis_0_tdata  : in  std_logic_vector(32-1 downto 0);
    s_axis_0_tvalid : in  std_logic;
    s_axis_0_tready : out std_logic;
    s_axis_1_tdata  : in  std_logic_vector(32-1 downto 0);
    s_axis_1_tvalid : in  std_logic;
    s_axis_1_tready : out std_logic;
    -- AXI-Stream ports for complex RX paths, TDATA is Q [31:16], I [15:0]
    rx_aclks        : out std_logic_vector(2-1 downto 0); -- associated with all m_axis
    rx_aresets      : out std_logic_vector(2-1 downto 0); -- active-high, associated with all m_axis
    m_axis_0_tdata  : out std_logic_vector(32-1 downto 0);
    m_axis_0_tvalid : out std_logic;
    m_axis_0_tready : in  std_logic;
    m_axis_1_tdata  : out std_logic_vector(32-1 downto 0);
    m_axis_1_tvalid : out std_logic;
    m_axis_1_tready : in  std_logic);
end entity rfdc;
architecture structural of rfdc is

  COMPONENT usp_rf_data_converter_0
    PORT (
      adc0_clk_p : IN STD_LOGIC;
      adc0_clk_n : IN STD_LOGIC;
      clk_adc0 : OUT STD_LOGIC;
      adc2_clk_p : IN STD_LOGIC;
      adc2_clk_n : IN STD_LOGIC;
      clk_adc2 : OUT STD_LOGIC;
      dac2_clk_p : IN STD_LOGIC;
      dac2_clk_n : IN STD_LOGIC;
      clk_dac2 : OUT STD_LOGIC;
      clk_dac3 : OUT STD_LOGIC;
      s_axi_aclk : IN STD_LOGIC;
      s_axi_aresetn : IN STD_LOGIC;
      s_axi_awaddr : IN STD_LOGIC_VECTOR(17 DOWNTO 0);
      s_axi_awvalid : IN STD_LOGIC;
      s_axi_awready : OUT STD_LOGIC;
      s_axi_wdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
      s_axi_wstrb : IN STD_LOGIC_VECTOR(3 DOWNTO 0);
      s_axi_wvalid : IN STD_LOGIC;
      s_axi_wready : OUT STD_LOGIC;
      s_axi_bresp : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
      s_axi_bvalid : OUT STD_LOGIC;
      s_axi_bready : IN STD_LOGIC;
      s_axi_araddr : IN STD_LOGIC_VECTOR(17 DOWNTO 0);
      s_axi_arvalid : IN STD_LOGIC;
      s_axi_arready : OUT STD_LOGIC;
      s_axi_rdata : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
      s_axi_rresp : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
      s_axi_rvalid : OUT STD_LOGIC;
      s_axi_rready : IN STD_LOGIC;
      irq : OUT STD_LOGIC;
      sysref_in_p : IN STD_LOGIC;
      sysref_in_n : IN STD_LOGIC;
      vin0_01_p : IN STD_LOGIC;
      vin0_01_n : IN STD_LOGIC;
      vin2_01_p : IN STD_LOGIC;
      vin2_01_n : IN STD_LOGIC;
      vout20_p : OUT STD_LOGIC;
      vout20_n : OUT STD_LOGIC;
      vout22_p : OUT STD_LOGIC;
      vout22_n : OUT STD_LOGIC;
      vout30_p : OUT STD_LOGIC;
      vout30_n : OUT STD_LOGIC;
      vout32_p : OUT STD_LOGIC;
      vout32_n : OUT STD_LOGIC;
      m0_axis_aresetn : IN STD_LOGIC;
      m0_axis_aclk : IN STD_LOGIC;
      m00_axis_tdata : OUT STD_LOGIC_VECTOR(15 DOWNTO 0);
      m00_axis_tvalid : OUT STD_LOGIC;
      m00_axis_tready : IN STD_LOGIC;
      m01_axis_tdata : OUT STD_LOGIC_VECTOR(15 DOWNTO 0);
      m01_axis_tvalid : OUT STD_LOGIC;
      m01_axis_tready : IN STD_LOGIC;
      m2_axis_aresetn : IN STD_LOGIC;
      m2_axis_aclk : IN STD_LOGIC;
      m20_axis_tdata : OUT STD_LOGIC_VECTOR(15 DOWNTO 0);
      m20_axis_tvalid : OUT STD_LOGIC;
      m20_axis_tready : IN STD_LOGIC;
      m21_axis_tdata : OUT STD_LOGIC_VECTOR(15 DOWNTO 0);
      m21_axis_tvalid : OUT STD_LOGIC;
      m21_axis_tready : IN STD_LOGIC;
      s2_axis_aresetn : IN STD_LOGIC;
      s2_axis_aclk : IN STD_LOGIC;
      s20_axis_tdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
      s20_axis_tvalid : IN STD_LOGIC;
      s20_axis_tready : OUT STD_LOGIC;
      s22_axis_tdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
      s22_axis_tvalid : IN STD_LOGIC;
      s22_axis_tready : OUT STD_LOGIC;
      s3_axis_aresetn : IN STD_LOGIC;
      s3_axis_aclk : IN STD_LOGIC;
      s30_axis_tdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
      s30_axis_tvalid : IN STD_LOGIC;
      s30_axis_tready : OUT STD_LOGIC;
      s32_axis_tdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
      s32_axis_tvalid : IN STD_LOGIC;
      s32_axis_tready : OUT STD_LOGIC
    );
  END COMPONENT;

  component axi_interconnect is
    port(
      rfdc_axi_in      : in  axi.lite32.axi_m2s_t;
      rfdc_axi_out     : out axi.lite32.axi_s2m_t;
      rfdc_adc_axi_in  : in  axi.lite32.axi_m2s_t;
      rfdc_adc_axi_out : out axi.lite32.axi_s2m_t;
      rfdc_dac_axi_in  : in  axi.lite32.axi_m2s_t;
      rfdc_dac_axi_out : out axi.lite32.axi_s2m_t;
      axi_in           : in  axi.lite32.axi_s2m_t;
      axi_out          : out axi.lite32.axi_m2s_t);
  end component axi_interconnect;

  constant FIFO_DEPTH : positive := 16;
  signal zeros_32 : std_logic_vector(32-1 downto 0)
                  := (others => '0');
  signal zero     : std_logic := '0';
  -- raw clk domain
  signal interconnect_to_xilinx_rfdc_ip_axi_in : axi.lite32.axi_s2m_t := (
      aw => (READY => '0'),
      ar => (READY => '0'),
      w => (READY => '0'),
      r => (DATA => (others => '0'), RESP => (others => '0'), VALID => '0'),
      b => (RESP => (others => '0'), VALID => '0'));
  signal interconnect_to_xilinx_rfdc_ip_axi_out : axi.lite32.axi_m2s_t := (
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
begin

  interconnect : axi_interconnect
    port map(
      rfdc_axi_in      => rfdc_axi_in,
      rfdc_axi_out     => rfdc_axi_out,
      rfdc_adc_axi_in  => rfdc_adc_axi_in,
      rfdc_adc_axi_out => rfdc_adc_axi_out,
      rfdc_dac_axi_in  => rfdc_dac_axi_in,
      rfdc_dac_axi_out => rfdc_dac_axi_out,
      axi_in           => interconnect_to_xilinx_rfdc_ip_axi_in,
      axi_out          => interconnect_to_xilinx_rfdc_ip_axi_out);

  tx_aclks(0)   <= tx_0_clk;
  rx_aclks(0)   <= rx_0_clk;
  rx_aclks(1)   <= rx_1_clk;
  rx_aresets(0) <= rx_0_reset;
  rx_aresets(1) <= rx_1_reset;

  rx_0_reset_synchronizer : cdc.cdc.reset
    generic map(
      SRC_RST_VALUE => '0')
    port map(
      src_rst   => rfdc_axi_in.a.resetn,
      dst_clk   => rx_0_clk,
      dst_rst   => rx_0_reset,
      dst_rst_n => rx_0_resetn);

  rx_1_reset_synchronizer : cdc.cdc.reset
    generic map(
      SRC_RST_VALUE => '0')
    port map(
      src_rst   => rfdc_axi_in.a.resetn,
      dst_clk   => rx_1_clk,
      dst_rst   => rx_1_reset,
      dst_rst_n => rx_1_resetn);

  tx_0_reset_synchronizer : cdc.cdc.reset
    generic map(
      SRC_RST_VALUE => '0')
    port map(
      src_rst   => rfdc_axi_in.a.resetn,
      dst_clk   => tx_0_clk,
      dst_rst   => tx_0_reset,
      dst_rst_n => tx_0_resetn);

  xilinx_rfdc_ip : usp_rf_data_converter_0
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
      clk_dac3 => open,
      s_axi_aclk => rfdc_axi_in.a.clk,
      s_axi_aresetn => rfdc_axi_in.a.resetn,
      s_axi_awaddr  => interconnect_to_xilinx_rfdc_ip_axi_out.aw.ADDR(18-1 downto 0),
      s_axi_awvalid => interconnect_to_xilinx_rfdc_ip_axi_out.aw.VALID,
      s_axi_awready => interconnect_to_xilinx_rfdc_ip_axi_in.aw.READY,
      s_axi_wdata   => interconnect_to_xilinx_rfdc_ip_axi_out.w.DATA,
      s_axi_wstrb   => interconnect_to_xilinx_rfdc_ip_axi_out.w.STRB,
      s_axi_wvalid  => interconnect_to_xilinx_rfdc_ip_axi_out.w.VALID,
      s_axi_wready  => interconnect_to_xilinx_rfdc_ip_axi_in.w.READY,
      s_axi_bresp   => interconnect_to_xilinx_rfdc_ip_axi_in.b.RESP,
      s_axi_bvalid  => interconnect_to_xilinx_rfdc_ip_axi_in.b.VALID,
      s_axi_bready  => interconnect_to_xilinx_rfdc_ip_axi_out.b.READY,
      s_axi_araddr  => interconnect_to_xilinx_rfdc_ip_axi_out.ar.ADDR(18-1 downto 0),
      s_axi_arvalid => interconnect_to_xilinx_rfdc_ip_axi_out.ar.VALID,
      s_axi_arready => interconnect_to_xilinx_rfdc_ip_axi_in.ar.READY,
      s_axi_rdata   => interconnect_to_xilinx_rfdc_ip_axi_in.r.DATA,
      s_axi_rresp   => interconnect_to_xilinx_rfdc_ip_axi_in.r.RESP,
      s_axi_rvalid  => interconnect_to_xilinx_rfdc_ip_axi_in.r.VALID,
      s_axi_rready  => interconnect_to_xilinx_rfdc_ip_axi_out.r.READY,
      irq => open,
      sysref_in_p => sysref_p,
      sysref_in_n => sysref_n,
      vin0_01_p => rf_rxs_p(0),
      vin0_01_n => rf_rxs_n(0),
      vin2_01_p => rf_rxs_p(1),
      vin2_01_n => rf_rxs_n(1),
      vout20_p => rf_txs_p(2),
      vout20_n => rf_txs_n(2),
      vout22_p => rf_txs_p(3),
      vout22_n => rf_txs_n(3),
      vout30_p => rf_txs_p(0),
      vout30_n => rf_txs_n(0),
      vout32_p => rf_txs_p(1),
      vout32_n => rf_txs_n(1),
      m0_axis_aresetn => rx_0_resetn,
      m0_axis_aclk => rx_0_clk,
      m00_axis_tdata  => rfdc_to_rx_0_i_fifo_tdata,
      m00_axis_tvalid => rfdc_to_rx_0_i_fifo_tvalid,
      m00_axis_tready => rfdc_to_rx_0_i_fifo_tready,
      m01_axis_tdata  => rfdc_to_rx_0_q_fifo_tdata,
      m01_axis_tvalid => rfdc_to_rx_0_q_fifo_tvalid,
      m01_axis_tready => rfdc_to_rx_0_q_fifo_tready,
      m2_axis_aresetn => rx_1_resetn,
      m2_axis_aclk => rx_1_clk,
      m20_axis_tdata => rfdc_to_rx_1_i_fifo_tdata,
      m20_axis_tvalid => rfdc_to_rx_1_i_fifo_tvalid,
      m20_axis_tready => rfdc_to_rx_1_i_fifo_tready,
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
      s3_axis_aresetn => tx_0_resetn,
      s3_axis_aclk => tx_0_clk,
      s30_axis_tdata => s_axis_0_tdata,
      s30_axis_tvalid => s_axis_0_tvalid,
      s30_axis_tready => s_axis_0_tready,
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

end structural;
