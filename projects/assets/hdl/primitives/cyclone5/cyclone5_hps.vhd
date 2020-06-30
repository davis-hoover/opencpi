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

library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library platform;
library cyclone5; use cyclone5.cyclone5_pkg.all;
library axi;

entity cyclone5_hps is
  port    (hps_in        : in  pl2hps_t;
           hps_out       : out hps2pl_t;
           hps_inout     : inout hps_io_t;
           m_h2f_axi_in  : in  axi.cyclone5_m.axi_s2m_array_t(0 to C_M_AXI_COUNT-1);
           m_h2f_axi_out : out axi.cyclone5_m.axi_m2s_array_t(0 to C_M_AXI_COUNT-1);
           s_f2h_axi_in  : in  axi.cyclone5_s.axi_m2s_array_t(0 to C_S_AXI_COUNT-1);
           s_f2h_axi_out : out axi.cyclone5_s.axi_s2m_array_t(0 to C_S_AXI_COUNT-1)
           );
end entity cyclone5_hps;
architecture rtl of cyclone5_hps is
  -- component soc_system is
  --   port (
  --     button_pio_external_connection_export : in    std_logic_vector(1 downto 0);   --    button_pio_external_connection.export
  --     clk_clk                               : in    std_logic;                      --    clk.clk
  --     dipsw_pio_external_connection_export  : in    std_logic_vector(3 downto 0)    --    dipsw_pio_external_connection.export
  --     hps_0_f2h_cold_reset_req_reset_n      : in    std_logic;                      --    hps_0_f2h_cold_reset_req.reset_n
  --     hps_0_f2h_debug_reset_req_reset_n     : in    std_logic;                      --    hps_0_f2h_debug_reset_req.reset_n
  --     hps_0_f2h_stm_hw_events_stm_hwevents  : in    std_logic_vector(27 downto 0)   --    hps_0_f2h_stm_hw_events.stm_hwevents
  --     hps_0_f2h_warm_reset_req_reset_n      : in    std_logic;                      --    hps_0_f2h_warm_reset_req.reset_n
  --     hps_0_h2f_reset_reset_n               : out   std_logic;                      --    hps_0_h2f_reset.reset_n
  --     hps_0_hps_io_hps_io_emac1_inst_TX_CLK : out   std_logic;                      --    hps_0_hps_io.hps_io_emac1_inst_TX_CLK
  --     hps_0_hps_io_hps_io_emac1_inst_TXD0   : out   std_logic;                      --    .hps_io_emac1_inst_TXD0
  --     hps_0_hps_io_hps_io_emac1_inst_TXD1   : out   std_logic;                      --    .hps_io_emac1_inst_TXD1
  --     hps_0_hps_io_hps_io_emac1_inst_TXD2   : out   std_logic;                      --    .hps_io_emac1_inst_TXD2
  --     hps_0_hps_io_hps_io_emac1_inst_TXD3   : out   std_logic;                      --    .hps_io_emac1_inst_TXD3
  --     hps_0_hps_io_hps_io_emac1_inst_RXD0   : in    std_logic;                      --    .hps_io_emac1_inst_RXD0
  --     hps_0_hps_io_hps_io_emac1_inst_MDIO   : inout std_logic;                      --    .hps_io_emac1_inst_MDIO
  --     hps_0_hps_io_hps_io_emac1_inst_MDC    : out   std_logic;                      --    .hps_io_emac1_inst_MDC
  --     hps_0_hps_io_hps_io_emac1_inst_RX_CTL : in    std_logic;                      --    .hps_io_emac1_inst_RX_CTL
  --     hps_0_hps_io_hps_io_emac1_inst_TX_CTL : out   std_logic;                      --    .hps_io_emac1_inst_TX_CTL
  --     hps_0_hps_io_hps_io_emac1_inst_RX_CLK : in    std_logic;                      --    .hps_io_emac1_inst_RX_CLK
  --     hps_0_hps_io_hps_io_emac1_inst_RXD1   : in    std_logic;                      --    .hps_io_emac1_inst_RXD1
  --     hps_0_hps_io_hps_io_emac1_inst_RXD2   : in    std_logic;                      --    .hps_io_emac1_inst_RXD2
  --     hps_0_hps_io_hps_io_emac1_inst_RXD3   : in    std_logic;                      --    .hps_io_emac1_inst_RXD3
  --     hps_0_hps_io_hps_io_qspi_inst_IO0     : inout std_logic;                      --    .hps_io_qspi_inst_IO0
  --     hps_0_hps_io_hps_io_qspi_inst_IO1     : inout std_logic;                      --    .hps_io_qspi_inst_IO1
  --     hps_0_hps_io_hps_io_qspi_inst_IO2     : inout std_logic;                      --    .hps_io_qspi_inst_IO2
  --     hps_0_hps_io_hps_io_qspi_inst_IO3     : inout std_logic;                      --    .hps_io_qspi_inst_IO3
  --     hps_0_hps_io_hps_io_qspi_inst_SS0     : out   std_logic;                      --    .hps_io_qspi_inst_SS0
  --     hps_0_hps_io_hps_io_qspi_inst_CLK     : out   std_logic;                      --    .hps_io_qspi_inst_CLK
  --     hps_0_hps_io_hps_io_sdio_inst_CMD     : inout std_logic;                      --    .hps_io_sdio_inst_CMD
  --     hps_0_hps_io_hps_io_sdio_inst_D0      : inout std_logic;                      --    .hps_io_sdio_inst_D0
  --     hps_0_hps_io_hps_io_sdio_inst_D1      : inout std_logic;                      --    .hps_io_sdio_inst_D1
  --     hps_0_hps_io_hps_io_sdio_inst_CLK     : out   std_logic;                      --    .hps_io_sdio_inst_CLK
  --     hps_0_hps_io_hps_io_sdio_inst_D2      : inout std_logic;                      --    .hps_io_sdio_inst_D2
  --     hps_0_hps_io_hps_io_sdio_inst_D3      : inout std_logic;                      --    .hps_io_sdio_inst_D3
  --     hps_0_hps_io_hps_io_usb1_inst_D0      : inout std_logic;                      --    .hps_io_usb1_inst_D0
  --     hps_0_hps_io_hps_io_usb1_inst_D1      : inout std_logic;                      --    .hps_io_usb1_inst_D1
  --     hps_0_hps_io_hps_io_usb1_inst_D2      : inout std_logic;                      --    .hps_io_usb1_inst_D2
  --     hps_0_hps_io_hps_io_usb1_inst_D3      : inout std_logic;                      --    .hps_io_usb1_inst_D3
  --     hps_0_hps_io_hps_io_usb1_inst_D4      : inout std_logic;                      --    .hps_io_usb1_inst_D4
  --     hps_0_hps_io_hps_io_usb1_inst_D5      : inout std_logic;                      --    .hps_io_usb1_inst_D5
  --     hps_0_hps_io_hps_io_usb1_inst_D6      : inout std_logic;                      --    .hps_io_usb1_inst_D6
  --     hps_0_hps_io_hps_io_usb1_inst_D7      : inout std_logic;                      --    .hps_io_usb1_inst_D7
  --     hps_0_hps_io_hps_io_usb1_inst_CLK     : in    std_logic;                      --    .hps_io_usb1_inst_CLK
  --     hps_0_hps_io_hps_io_usb1_inst_STP     : out   std_logic;                      --    .hps_io_usb1_inst_STP
  --     hps_0_hps_io_hps_io_usb1_inst_DIR     : in    std_logic;                      --    .hps_io_usb1_inst_DIR
  --     hps_0_hps_io_hps_io_usb1_inst_NXT     : in    std_logic;                      --    .hps_io_usb1_inst_NXT
  --     hps_0_hps_io_hps_io_spim0_inst_CLK    : out   std_logic;                      --    .hps_io_spim0_inst_CLK
  --     hps_0_hps_io_hps_io_spim0_inst_MOSI   : out   std_logic;                      --    .hps_io_spim0_inst_MOSI
  --     hps_0_hps_io_hps_io_spim0_inst_MISO   : in    std_logic;                      --    .hps_io_spim0_inst_MISO
  --     hps_0_hps_io_hps_io_spim0_inst_SS0    : out   std_logic;                      --    .hps_io_spim0_inst_SS0
  --     hps_0_hps_io_hps_io_uart0_inst_RX     : in    std_logic;                      --    .hps_io_uart0_inst_RX
  --     hps_0_hps_io_hps_io_uart0_inst_TX     : out   std_logic;                      --    .hps_io_uart0_inst_TX
  --     hps_0_hps_io_hps_io_i2c0_inst_SDA     : inout std_logic;                      --    .hps_io_i2c0_inst_SDA
  --     hps_0_hps_io_hps_io_i2c0_inst_SCL     : inout std_logic;                      --    .hps_io_i2c0_inst_SCL
  --     hps_0_hps_io_hps_io_can0_inst_RX      : in    std_logic;                      --    .hps_io_can0_inst_RX
  --     hps_0_hps_io_hps_io_can0_inst_TX      : out   std_logic;                      --    .hps_io_can0_inst_TX
  --     hps_0_hps_io_hps_io_trace_inst_CLK    : out   std_logic;                      --    .hps_io_trace_inst_CLK
  --     hps_0_hps_io_hps_io_trace_inst_D0     : out   std_logic;                      --    .hps_io_trace_inst_D0
  --     hps_0_hps_io_hps_io_trace_inst_D1     : out   std_logic;                      --    .hps_io_trace_inst_D1
  --     hps_0_hps_io_hps_io_trace_inst_D2     : out   std_logic;                      --    .hps_io_trace_inst_D2
  --     hps_0_hps_io_hps_io_trace_inst_D3     : out   std_logic;                      --    .hps_io_trace_inst_D3
  --     hps_0_hps_io_hps_io_trace_inst_D4     : out   std_logic;                      --    .hps_io_trace_inst_D4
  --     hps_0_hps_io_hps_io_trace_inst_D5     : out   std_logic;                      --    .hps_io_trace_inst_D5
  --     hps_0_hps_io_hps_io_trace_inst_D6     : out   std_logic;                      --    .hps_io_trace_inst_D6
  --     hps_0_hps_io_hps_io_trace_inst_D7     : out   std_logic;                      --    .hps_io_trace_inst_D7
  --     hps_0_hps_io_hps_io_gpio_inst_GPIO09  : inout std_logic;                      --    .hps_io_gpio_inst_GPIO09
  --     hps_0_hps_io_hps_io_gpio_inst_GPIO35  : inout std_logic;                      --    .hps_io_gpio_inst_GPIO35
  --     hps_0_hps_io_hps_io_gpio_inst_GPIO41  : inout std_logic;                      --    .hps_io_gpio_inst_GPIO41
  --     hps_0_hps_io_hps_io_gpio_inst_GPIO42  : inout std_logic;                      --    .hps_io_gpio_inst_GPIO42
  --     hps_0_hps_io_hps_io_gpio_inst_GPIO43  : inout std_logic;                      --    .hps_io_gpio_inst_GPIO43
  --     hps_0_hps_io_hps_io_gpio_inst_GPIO44  : inout std_logic;                      --    .hps_io_gpio_inst_GPIO44
  --     issp_hps_resets_source                : out   std_logic_vector(2 downto 0);   --    issp_hps_resets.source
  --     led_pio_external_connection_in_port   : in    std_logic_vector(3 downto 0);   --    led_pio_external_connection.in_port
  --     led_pio_external_connection_out_port  : out   std_logic_vector(3 downto 0);   --    .out_port
  --     memory_mem_a                          : out   std_logic_vector(14 downto 0);  --    memory.mem_a
  --     memory_mem_ba                         : out   std_logic_vector(2 downto 0);   --    .mem_ba
  --     memory_mem_ck                         : out   std_logic;                      --    .mem_ck
  --     memory_mem_ck_n                       : out   std_logic;                      --    .mem_ck_n
  --     memory_mem_cke                        : out   std_logic;                      --    .mem_cke
  --     memory_mem_cs_n                       : out   std_logic;                      --    .mem_cs_n
  --     memory_mem_ras_n                      : out   std_logic;                      --    .mem_ras_n
  --     memory_mem_cas_n                      : out   std_logic;                      --    .mem_cas_n
  --     memory_mem_we_n                       : out   std_logic;                      --    .mem_we_n
  --     memory_mem_reset_n                    : out   std_logic;                      --    .mem_reset_n
  --     memory_mem_dq                         : inout std_logic_vector(39 downto 0);  --    .mem_dq
  --     memory_mem_dqs                        : inout std_logic_vector(4 downto 0);   --    .mem_dqs
  --     memory_mem_dqs_n                      : inout std_logic_vector(4 downto 0);   --    .mem_dqs_n
  --     memory_mem_odt                        : out   std_logic;                      --    .mem_odt
  --     memory_mem_dm                         : out   std_logic_vector(4 downto 0);   --    .mem_dm
  --     memory_oct_rzqin                      : in    std_logic;                      --    .oct_rzqin
  --     reset_reset_n                         : in    std_logic                       --     reset.reset_n
  --     );
  -- end component;
  component soc_system_hps_0 is
		generic (
			F2S_Width : integer := 2;
			S2F_Width : integer := 2
		);
		port (
			f2h_cold_rst_req_n       : in    std_logic                      := 'X';             -- reset_n
			f2h_dbg_rst_req_n        : in    std_logic                      := 'X';             -- reset_n
			f2h_warm_rst_req_n       : in    std_logic                      := 'X';             -- reset_n
			f2h_stm_hwevents         : in    std_logic_vector(27 downto 0)  := (others => 'X'); -- stm_hwevents
			mem_a                    : out   std_logic_vector(14 downto 0);                     -- mem_a
			mem_ba                   : out   std_logic_vector(2 downto 0);                      -- mem_ba
			mem_ck                   : out   std_logic;                                         -- mem_ck
			mem_ck_n                 : out   std_logic;                                         -- mem_ck_n
			mem_cke                  : out   std_logic;                                         -- mem_cke
			mem_cs_n                 : out   std_logic;                                         -- mem_cs_n
			mem_ras_n                : out   std_logic;                                         -- mem_ras_n
			mem_cas_n                : out   std_logic;                                         -- mem_cas_n
			mem_we_n                 : out   std_logic;                                         -- mem_we_n
			mem_reset_n              : out   std_logic;                                         -- mem_reset_n
			mem_dq                   : inout std_logic_vector(39 downto 0)  := (others => 'X'); -- mem_dq
			mem_dqs                  : inout std_logic_vector(4 downto 0)   := (others => 'X'); -- mem_dqs
			mem_dqs_n                : inout std_logic_vector(4 downto 0)   := (others => 'X'); -- mem_dqs_n
			mem_odt                  : out   std_logic;                                         -- mem_odt
			mem_dm                   : out   std_logic_vector(4 downto 0);                      -- mem_dm
			oct_rzqin                : in    std_logic                      := 'X';             -- oct_rzqin
			hps_io_emac1_inst_TX_CLK : out   std_logic;                                         -- hps_io_emac1_inst_TX_CLK
			hps_io_emac1_inst_TXD0   : out   std_logic;                                         -- hps_io_emac1_inst_TXD0
			hps_io_emac1_inst_TXD1   : out   std_logic;                                         -- hps_io_emac1_inst_TXD1
			hps_io_emac1_inst_TXD2   : out   std_logic;                                         -- hps_io_emac1_inst_TXD2
			hps_io_emac1_inst_TXD3   : out   std_logic;                                         -- hps_io_emac1_inst_TXD3
			hps_io_emac1_inst_RXD0   : in    std_logic                      := 'X';             -- hps_io_emac1_inst_RXD0
			hps_io_emac1_inst_MDIO   : inout std_logic                      := 'X';             -- hps_io_emac1_inst_MDIO
			hps_io_emac1_inst_MDC    : out   std_logic;                                         -- hps_io_emac1_inst_MDC
			hps_io_emac1_inst_RX_CTL : in    std_logic                      := 'X';             -- hps_io_emac1_inst_RX_CTL
			hps_io_emac1_inst_TX_CTL : out   std_logic;                                         -- hps_io_emac1_inst_TX_CTL
			hps_io_emac1_inst_RX_CLK : in    std_logic                      := 'X';             -- hps_io_emac1_inst_RX_CLK
			hps_io_emac1_inst_RXD1   : in    std_logic                      := 'X';             -- hps_io_emac1_inst_RXD1
			hps_io_emac1_inst_RXD2   : in    std_logic                      := 'X';             -- hps_io_emac1_inst_RXD2
			hps_io_emac1_inst_RXD3   : in    std_logic                      := 'X';             -- hps_io_emac1_inst_RXD3
			hps_io_qspi_inst_IO0     : inout std_logic                      := 'X';             -- hps_io_qspi_inst_IO0
			hps_io_qspi_inst_IO1     : inout std_logic                      := 'X';             -- hps_io_qspi_inst_IO1
			hps_io_qspi_inst_IO2     : inout std_logic                      := 'X';             -- hps_io_qspi_inst_IO2
			hps_io_qspi_inst_IO3     : inout std_logic                      := 'X';             -- hps_io_qspi_inst_IO3
			hps_io_qspi_inst_SS0     : out   std_logic;                                         -- hps_io_qspi_inst_SS0
			hps_io_qspi_inst_CLK     : out   std_logic;                                         -- hps_io_qspi_inst_CLK
			hps_io_sdio_inst_CMD     : inout std_logic                      := 'X';             -- hps_io_sdio_inst_CMD
			hps_io_sdio_inst_D0      : inout std_logic                      := 'X';             -- hps_io_sdio_inst_D0
			hps_io_sdio_inst_D1      : inout std_logic                      := 'X';             -- hps_io_sdio_inst_D1
			hps_io_sdio_inst_CLK     : out   std_logic;                                         -- hps_io_sdio_inst_CLK
			hps_io_sdio_inst_D2      : inout std_logic                      := 'X';             -- hps_io_sdio_inst_D2
			hps_io_sdio_inst_D3      : inout std_logic                      := 'X';             -- hps_io_sdio_inst_D3
			hps_io_usb1_inst_D0      : inout std_logic                      := 'X';             -- hps_io_usb1_inst_D0
			hps_io_usb1_inst_D1      : inout std_logic                      := 'X';             -- hps_io_usb1_inst_D1
			hps_io_usb1_inst_D2      : inout std_logic                      := 'X';             -- hps_io_usb1_inst_D2
			hps_io_usb1_inst_D3      : inout std_logic                      := 'X';             -- hps_io_usb1_inst_D3
			hps_io_usb1_inst_D4      : inout std_logic                      := 'X';             -- hps_io_usb1_inst_D4
			hps_io_usb1_inst_D5      : inout std_logic                      := 'X';             -- hps_io_usb1_inst_D5
			hps_io_usb1_inst_D6      : inout std_logic                      := 'X';             -- hps_io_usb1_inst_D6
			hps_io_usb1_inst_D7      : inout std_logic                      := 'X';             -- hps_io_usb1_inst_D7
			hps_io_usb1_inst_CLK     : in    std_logic                      := 'X';             -- hps_io_usb1_inst_CLK
			hps_io_usb1_inst_STP     : out   std_logic;                                         -- hps_io_usb1_inst_STP
			hps_io_usb1_inst_DIR     : in    std_logic                      := 'X';             -- hps_io_usb1_inst_DIR
			hps_io_usb1_inst_NXT     : in    std_logic                      := 'X';             -- hps_io_usb1_inst_NXT
			hps_io_spim0_inst_CLK    : out   std_logic;                                         -- hps_io_spim0_inst_CLK
			hps_io_spim0_inst_MOSI   : out   std_logic;                                         -- hps_io_spim0_inst_MOSI
			hps_io_spim0_inst_MISO   : in    std_logic                      := 'X';             -- hps_io_spim0_inst_MISO
			hps_io_spim0_inst_SS0    : out   std_logic;                                         -- hps_io_spim0_inst_SS0
			hps_io_uart0_inst_RX     : in    std_logic                      := 'X';             -- hps_io_uart0_inst_RX
			hps_io_uart0_inst_TX     : out   std_logic;                                         -- hps_io_uart0_inst_TX
			hps_io_i2c0_inst_SDA     : inout std_logic                      := 'X';             -- hps_io_i2c0_inst_SDA
			hps_io_i2c0_inst_SCL     : inout std_logic                      := 'X';             -- hps_io_i2c0_inst_SCL
			hps_io_can0_inst_RX      : in    std_logic                      := 'X';             -- hps_io_can0_inst_RX
			hps_io_can0_inst_TX      : out   std_logic;                                         -- hps_io_can0_inst_TX
			hps_io_trace_inst_CLK    : out   std_logic;                                         -- hps_io_trace_inst_CLK
			hps_io_trace_inst_D0     : out   std_logic;                                         -- hps_io_trace_inst_D0
			hps_io_trace_inst_D1     : out   std_logic;                                         -- hps_io_trace_inst_D1
			hps_io_trace_inst_D2     : out   std_logic;                                         -- hps_io_trace_inst_D2
			hps_io_trace_inst_D3     : out   std_logic;                                         -- hps_io_trace_inst_D3
			hps_io_trace_inst_D4     : out   std_logic;                                         -- hps_io_trace_inst_D4
			hps_io_trace_inst_D5     : out   std_logic;                                         -- hps_io_trace_inst_D5
			hps_io_trace_inst_D6     : out   std_logic;                                         -- hps_io_trace_inst_D6
			hps_io_trace_inst_D7     : out   std_logic;                                         -- hps_io_trace_inst_D7
			hps_io_gpio_inst_GPIO09  : inout std_logic                      := 'X';             -- hps_io_gpio_inst_GPIO09
			hps_io_gpio_inst_GPIO35  : inout std_logic                      := 'X';             -- hps_io_gpio_inst_GPIO35
			hps_io_gpio_inst_GPIO41  : inout std_logic                      := 'X';             -- hps_io_gpio_inst_GPIO41
			hps_io_gpio_inst_GPIO42  : inout std_logic                      := 'X';             -- hps_io_gpio_inst_GPIO42
			hps_io_gpio_inst_GPIO43  : inout std_logic                      := 'X';             -- hps_io_gpio_inst_GPIO43
			hps_io_gpio_inst_GPIO44  : inout std_logic                      := 'X';             -- hps_io_gpio_inst_GPIO44
			h2f_rst_n                : out   std_logic;                                         -- reset_n
			f2h_sdram0_clk           : in    std_logic                      := 'X';             -- clk
			f2h_sdram0_ADDRESS       : in    std_logic_vector(26 downto 0)  := (others => 'X'); -- address
			f2h_sdram0_BURSTCOUNT    : in    std_logic_vector(7 downto 0)   := (others => 'X'); -- burstcount
			f2h_sdram0_WAITREQUEST   : out   std_logic;                                         -- waitrequest
			f2h_sdram0_READDATA      : out   std_logic_vector(255 downto 0);                    -- readdata
			f2h_sdram0_READDATAVALID : out   std_logic;                                         -- readdatavalid
			f2h_sdram0_READ          : in    std_logic                      := 'X';             -- read
			f2h_sdram0_WRITEDATA     : in    std_logic_vector(255 downto 0) := (others => 'X'); -- writedata
			f2h_sdram0_BYTEENABLE    : in    std_logic_vector(31 downto 0)  := (others => 'X'); -- byteenable
			f2h_sdram0_WRITE         : in    std_logic                      := 'X';             -- write
			h2f_axi_clk              : in    std_logic                      := 'X';             -- clk
			h2f_AWID                 : out   std_logic_vector(11 downto 0);                     -- awid
			h2f_AWADDR               : out   std_logic_vector(29 downto 0);                     -- awaddr
			h2f_AWLEN                : out   std_logic_vector(3 downto 0);                      -- awlen
			h2f_AWSIZE               : out   std_logic_vector(2 downto 0);                      -- awsize
			h2f_AWBURST              : out   std_logic_vector(1 downto 0);                      -- awburst
			h2f_AWLOCK               : out   std_logic_vector(1 downto 0);                      -- awlock
			h2f_AWCACHE              : out   std_logic_vector(3 downto 0);                      -- awcache
			h2f_AWPROT               : out   std_logic_vector(2 downto 0);                      -- awprot
			h2f_AWVALID              : out   std_logic;                                         -- awvalid
			h2f_AWREADY              : in    std_logic                      := 'X';             -- awready
			h2f_WID                  : out   std_logic_vector(11 downto 0);                     -- wid
			h2f_WDATA                : out   std_logic_vector(63 downto 0);                     -- wdata
			h2f_WSTRB                : out   std_logic_vector(7 downto 0);                      -- wstrb
			h2f_WLAST                : out   std_logic;                                         -- wlast
			h2f_WVALID               : out   std_logic;                                         -- wvalid
			h2f_WREADY               : in    std_logic                      := 'X';             -- wready
			h2f_BID                  : in    std_logic_vector(11 downto 0)  := (others => 'X'); -- bid
			h2f_BRESP                : in    std_logic_vector(1 downto 0)   := (others => 'X'); -- bresp
			h2f_BVALID               : in    std_logic                      := 'X';             -- bvalid
			h2f_BREADY               : out   std_logic;                                         -- bready
			h2f_ARID                 : out   std_logic_vector(11 downto 0);                     -- arid
			h2f_ARADDR               : out   std_logic_vector(29 downto 0);                     -- araddr
			h2f_ARLEN                : out   std_logic_vector(3 downto 0);                      -- arlen
			h2f_ARSIZE               : out   std_logic_vector(2 downto 0);                      -- arsize
			h2f_ARBURST              : out   std_logic_vector(1 downto 0);                      -- arburst
			h2f_ARLOCK               : out   std_logic_vector(1 downto 0);                      -- arlock
			h2f_ARCACHE              : out   std_logic_vector(3 downto 0);                      -- arcache
			h2f_ARPROT               : out   std_logic_vector(2 downto 0);                      -- arprot
			h2f_ARVALID              : out   std_logic;                                         -- arvalid
			h2f_ARREADY              : in    std_logic                      := 'X';             -- arready
			h2f_RID                  : in    std_logic_vector(11 downto 0)  := (others => 'X'); -- rid
			h2f_RDATA                : in    std_logic_vector(63 downto 0)  := (others => 'X'); -- rdata
			h2f_RRESP                : in    std_logic_vector(1 downto 0)   := (others => 'X'); -- rresp
			h2f_RLAST                : in    std_logic                      := 'X';             -- rlast
			h2f_RVALID               : in    std_logic                      := 'X';             -- rvalid
			h2f_RREADY               : out   std_logic;                                         -- rready
			f2h_axi_clk              : in    std_logic                      := 'X';             -- clk
			f2h_AWID                 : in    std_logic_vector(7 downto 0)   := (others => 'X'); -- awid
			f2h_AWADDR               : in    std_logic_vector(31 downto 0)  := (others => 'X'); -- awaddr
			f2h_AWLEN                : in    std_logic_vector(3 downto 0)   := (others => 'X'); -- awlen
			f2h_AWSIZE               : in    std_logic_vector(2 downto 0)   := (others => 'X'); -- awsize
			f2h_AWBURST              : in    std_logic_vector(1 downto 0)   := (others => 'X'); -- awburst
			f2h_AWLOCK               : in    std_logic_vector(1 downto 0)   := (others => 'X'); -- awlock
			f2h_AWCACHE              : in    std_logic_vector(3 downto 0)   := (others => 'X'); -- awcache
			f2h_AWPROT               : in    std_logic_vector(2 downto 0)   := (others => 'X'); -- awprot
			f2h_AWVALID              : in    std_logic                      := 'X';             -- awvalid
			f2h_AWREADY              : out   std_logic;                                         -- awready
			f2h_AWUSER               : in    std_logic_vector(4 downto 0)   := (others => 'X'); -- awuser
			f2h_WID                  : in    std_logic_vector(7 downto 0)   := (others => 'X'); -- wid
			f2h_WDATA                : in    std_logic_vector(63 downto 0)  := (others => 'X'); -- wdata
			f2h_WSTRB                : in    std_logic_vector(7 downto 0)   := (others => 'X'); -- wstrb
			f2h_WLAST                : in    std_logic                      := 'X';             -- wlast
			f2h_WVALID               : in    std_logic                      := 'X';             -- wvalid
			f2h_WREADY               : out   std_logic;                                         -- wready
			f2h_BID                  : out   std_logic_vector(7 downto 0);                      -- bid
			f2h_BRESP                : out   std_logic_vector(1 downto 0);                      -- bresp
			f2h_BVALID               : out   std_logic;                                         -- bvalid
			f2h_BREADY               : in    std_logic                      := 'X';             -- bready
			f2h_ARID                 : in    std_logic_vector(7 downto 0)   := (others => 'X'); -- arid
			f2h_ARADDR               : in    std_logic_vector(31 downto 0)  := (others => 'X'); -- araddr
			f2h_ARLEN                : in    std_logic_vector(3 downto 0)   := (others => 'X'); -- arlen
			f2h_ARSIZE               : in    std_logic_vector(2 downto 0)   := (others => 'X'); -- arsize
			f2h_ARBURST              : in    std_logic_vector(1 downto 0)   := (others => 'X'); -- arburst
			f2h_ARLOCK               : in    std_logic_vector(1 downto 0)   := (others => 'X'); -- arlock
			f2h_ARCACHE              : in    std_logic_vector(3 downto 0)   := (others => 'X'); -- arcache
			f2h_ARPROT               : in    std_logic_vector(2 downto 0)   := (others => 'X'); -- arprot
			f2h_ARVALID              : in    std_logic                      := 'X';             -- arvalid
			f2h_ARREADY              : out   std_logic;                                         -- arready
			f2h_ARUSER               : in    std_logic_vector(4 downto 0)   := (others => 'X'); -- aruser
			f2h_RID                  : out   std_logic_vector(7 downto 0);                      -- rid
			f2h_RDATA                : out   std_logic_vector(63 downto 0);                     -- rdata
			f2h_RRESP                : out   std_logic_vector(1 downto 0);                      -- rresp
			f2h_RLAST                : out   std_logic;                                         -- rlast
			f2h_RVALID               : out   std_logic;                                         -- rvalid
			f2h_RREADY               : in    std_logic                      := 'X';             -- rready
			h2f_lw_axi_clk           : in    std_logic                      := 'X';             -- clk
			h2f_lw_AWID              : out   std_logic_vector(11 downto 0);                     -- awid
			h2f_lw_AWADDR            : out   std_logic_vector(20 downto 0);                     -- awaddr
			h2f_lw_AWLEN             : out   std_logic_vector(3 downto 0);                      -- awlen
			h2f_lw_AWSIZE            : out   std_logic_vector(2 downto 0);                      -- awsize
			h2f_lw_AWBURST           : out   std_logic_vector(1 downto 0);                      -- awburst
			h2f_lw_AWLOCK            : out   std_logic_vector(1 downto 0);                      -- awlock
			h2f_lw_AWCACHE           : out   std_logic_vector(3 downto 0);                      -- awcache
			h2f_lw_AWPROT            : out   std_logic_vector(2 downto 0);                      -- awprot
			h2f_lw_AWVALID           : out   std_logic;                                         -- awvalid
			h2f_lw_AWREADY           : in    std_logic                      := 'X';             -- awready
			h2f_lw_WID               : out   std_logic_vector(11 downto 0);                     -- wid
			h2f_lw_WDATA             : out   std_logic_vector(31 downto 0);                     -- wdata
			h2f_lw_WSTRB             : out   std_logic_vector(3 downto 0);                      -- wstrb
			h2f_lw_WLAST             : out   std_logic;                                         -- wlast
			h2f_lw_WVALID            : out   std_logic;                                         -- wvalid
			h2f_lw_WREADY            : in    std_logic                      := 'X';             -- wready
			h2f_lw_BID               : in    std_logic_vector(11 downto 0)  := (others => 'X'); -- bid
			h2f_lw_BRESP             : in    std_logic_vector(1 downto 0)   := (others => 'X'); -- bresp
			h2f_lw_BVALID            : in    std_logic                      := 'X';             -- bvalid
			h2f_lw_BREADY            : out   std_logic;                                         -- bready
			h2f_lw_ARID              : out   std_logic_vector(11 downto 0);                     -- arid
			h2f_lw_ARADDR            : out   std_logic_vector(20 downto 0);                     -- araddr
			h2f_lw_ARLEN             : out   std_logic_vector(3 downto 0);                      -- arlen
			h2f_lw_ARSIZE            : out   std_logic_vector(2 downto 0);                      -- arsize
			h2f_lw_ARBURST           : out   std_logic_vector(1 downto 0);                      -- arburst
			h2f_lw_ARLOCK            : out   std_logic_vector(1 downto 0);                      -- arlock
			h2f_lw_ARCACHE           : out   std_logic_vector(3 downto 0);                      -- arcache
			h2f_lw_ARPROT            : out   std_logic_vector(2 downto 0);                      -- arprot
			h2f_lw_ARVALID           : out   std_logic;                                         -- arvalid
			h2f_lw_ARREADY           : in    std_logic                      := 'X';             -- arready
			h2f_lw_RID               : in    std_logic_vector(11 downto 0)  := (others => 'X'); -- rid
			h2f_lw_RDATA             : in    std_logic_vector(31 downto 0)  := (others => 'X'); -- rdata
			h2f_lw_RRESP             : in    std_logic_vector(1 downto 0)   := (others => 'X'); -- rresp
			h2f_lw_RLAST             : in    std_logic                      := 'X';             -- rlast
			h2f_lw_RVALID            : in    std_logic                      := 'X';             -- rvalid
			h2f_lw_RREADY            : out   std_logic;                                         -- rready
			f2h_irq_p0               : in    std_logic_vector(31 downto 0)  := (others => 'X'); -- irq
			f2h_irq_p1               : in    std_logic_vector(31 downto 0)  := (others => 'X')  -- irq
		);
	end component soc_system_hps_0;

  component altsource_probe_top is
		generic (
			sld_auto_instance_index : string  := "YES";
			sld_instance_index      : integer := 0;
			instance_id             : string  := "NONE";
			probe_width             : integer := 1;
			source_width            : integer := 1;
			source_initial_value    : string  := "0";
			enable_metastability    : string  := "NO"
		);
		port (
			source     : out std_logic_vector(2 downto 0);        -- source
			source_clk : in  std_logic                    := 'X'; -- clk
			source_ena : in  std_logic                    := 'X'  -- source_ena
		);
	end component altsource_probe_top;

  component altera_edge_detector
    generic (
      PULSE_EXT             : integer := 32;
      EDGE_TYPE             : integer := 0;
      IGNORE_RST_WHILE_BUSY : integer := 0
      );
    port (
      clk       : in  std_logic;
      rst_n     : in  std_logic;
      signal_in : in  std_logic;
      pulse_out : out std_logic
      );
  end component;
  -- constant      ID_WIDTH          : natural := 6;
  signal        hps_fpga_reset_n  : std_logic;
  signal        hps_reset_req     : std_logic_vector(2 downto 0);
  signal        hps_cold_reset    : std_logic;
  signal        hps_cold_reset_n  : std_logic;
  signal        hps_warm_reset    : std_logic;
  signal        hps_warm_reset_n  : std_logic;
  signal        hps_debug_reset   : std_logic;
  signal        hps_debug_reset_n : std_logic;
  -- signal        s_f2h_ARID        : std_logic_vector(7 downto 0);
  -- signal        s_f2h_AWID        : std_logic_vector(7 downto 0);
  -- signal        s_f2h_WID         : std_logic_vector(7 downto 0);
  -- signal        s_f2h_BID         : std_logic_vector(7 downto 0);
  -- signal        s_f2h_RID         : std_logic_vector(7 downto 0);
  signal        stm_hw_events     : std_logic_vector(27 downto 0);
begin

  m_h2f_axi_out(0).A.RESETN <= hps_fpga_reset_n;
  hps_cold_reset_n <= not hps_cold_reset;
  hps_warm_reset_n <= not hps_warm_reset;
  hps_debug_reset_n <= not hps_debug_reset;
  hps_out.RESET_N <= hps_fpga_reset_n;
  hps_out.COLD_RST <= hps_cold_reset;
  hps_out.DBG_RST <= hps_debug_reset_n;
  hps_out.WARM_RST <= hps_warm_reset_n;
  -- s_f2h_ARID <= "00" & s_f2h_axi_in(0).AR.ID;
  -- s_f2h_AWID <= "00" & s_f2h_axi_in(0).AW.ID;
  -- s_f2h_WID  <= "00" & s_f2h_axi_in(0).W.ID;
  -- s_f2h_axi_out(0).B.ID <= s_f2h_BID(ID_WIDTH-1 downto 0);
  -- s_f2h_axi_out(0).R.ID <= s_f2h_RID(ID_WIDTH-1 downto 0);


  in_system_sources_probes_0 : altsource_probe_top
 	 generic map (
   		sld_auto_instance_index => "YES",
   		sld_instance_index      => 0,
   		instance_id             => "RST",
   		probe_width             => 0,
   		source_width            => 3,
   		source_initial_value    => "0",
   		enable_metastability    => "YES")
 	 port map (
 		  source     => hps_reset_req, --    sources.source
 		  source_clk => hps_in.CLK,    -- source_clk.clk
 		  source_ena => '1'            -- (terminated)
 	 );

  pulse_cold_reset : altera_edge_detector
    generic map (
      PULSE_EXT             => 6,
      EDGE_TYPE             => 1,
      IGNORE_RST_WHILE_BUSY => 1)
    port map (
      clk       => hps_in.CLK,
      rst_n     => hps_fpga_reset_n,
      signal_in => hps_reset_req(0),
      pulse_out => hps_cold_reset);

  pulse_warm_reset : altera_edge_detector
    generic map (
      PULSE_EXT             => 2,
      EDGE_TYPE             => 1,
      IGNORE_RST_WHILE_BUSY => 1)
    port map (
      clk       => hps_in.CLK,
      rst_n     => hps_fpga_reset_n,
      signal_in => hps_reset_req(1),
      pulse_out => hps_warm_reset);

  pulse_debug_reset : altera_edge_detector
    generic map (
      PULSE_EXT             => 32,
      EDGE_TYPE             => 1,
      IGNORE_RST_WHILE_BUSY => 1)
    port map (
      clk       => hps_in.CLK,
      rst_n     => hps_fpga_reset_n,
      signal_in => hps_reset_req(2),
      pulse_out => hps_debug_reset);

  hps_0 : soc_system_hps_0
    generic map (
      F2S_Width => 2, -- "0:Unused" "1:32-bit" "2:64-bit" "3:128-bit"
      S2F_Width => 2  -- "0:Unused" "1:32-bit" "2:64-bit" "3:128-bit"
    )
    port map (
      f2h_cold_rst_req_n       => hps_cold_reset_n,                                      --  f2h_cold_reset_req.reset_n
      f2h_dbg_rst_req_n        => hps_debug_reset_n,                                     -- f2h_debug_reset_req.reset_n
      f2h_warm_rst_req_n       => hps_warm_reset_n,                                      --  f2h_warm_reset_req.reset_n
      f2h_stm_hwevents         => (others => '0'),                                       --   f2h_stm_hw_events.stm_hwevents
      mem_a                    => open,                                                  --              memory.mem_a
      mem_ba                   => open,                                                  --                    .mem_ba
      mem_ck                   => open,                                                  --                    .mem_ck
      mem_ck_n                 => open,                                                  --                    .mem_ck_n
      mem_cke                  => open,                                                  --                    .mem_cke
      mem_cs_n                 => open,                                                  --                    .mem_cs_n
      mem_ras_n                => open,                                                  --                    .mem_ras_n
      mem_cas_n                => open,                                                  --                    .mem_cas_n
      mem_we_n                 => open,                                                  --                    .mem_we_n
      mem_reset_n              => open,                                                  --                    .mem_reset_n
      mem_dq                   => open,                                                  --                    .mem_dq
      mem_dqs                  => open,                                                  --                    .mem_dqs
      mem_dqs_n                => open,                                                  --                    .mem_dqs_n
      mem_odt                  => open,                                                  --                    .mem_odt
      mem_dm                   => open,                                                  --                    .mem_dm
      oct_rzqin                => hps_in.oct_rzqin,                                      --                    .oct_rzqin
      hps_io_emac1_inst_TX_CLK => open,                                                  --              hps_io.hps_io_emac1_inst_TX_CLK
      hps_io_emac1_inst_TXD0   => open,                                                  --                    .hps_io_emac1_inst_TXD0
      hps_io_emac1_inst_TXD1   => open,                                                  --                    .hps_io_emac1_inst_TXD1
      hps_io_emac1_inst_TXD2   => open,                                                  --                    .hps_io_emac1_inst_TXD2
      hps_io_emac1_inst_TXD3   => open,                                                  --                    .hps_io_emac1_inst_TXD3
      hps_io_emac1_inst_RXD0   => '0',                                                   --                    .hps_io_emac1_inst_RXD0
      hps_io_emac1_inst_MDIO   => hps_inout.hps_io_emac1_inst_MDIO,                      --                    .hps_io_emac1_inst_MDIO
      hps_io_emac1_inst_MDC    => open,                                                  --                    .hps_io_emac1_inst_MDC
      hps_io_emac1_inst_RX_CTL => '0',                                                   --                    .hps_io_emac1_inst_RX_CTL
      hps_io_emac1_inst_TX_CTL => open,                                                  --                    .hps_io_emac1_inst_TX_CTL
      hps_io_emac1_inst_RX_CLK => '0',                                                   --                    .hps_io_emac1_inst_RX_CLK
      hps_io_emac1_inst_RXD1   => '0',                                                   --                    .hps_io_emac1_inst_RXD1
      hps_io_emac1_inst_RXD2   => '0',                                                   --                    .hps_io_emac1_inst_RXD2
      hps_io_emac1_inst_RXD3   => '0',                                                   --                    .hps_io_emac1_inst_RXD3
      hps_io_qspi_inst_IO0     => hps_inout.hps_io_qspi_inst_IO0,                        --                    .hps_io_qspi_inst_IO0
      hps_io_qspi_inst_IO1     => hps_inout.hps_io_qspi_inst_IO1,                        --                    .hps_io_qspi_inst_IO1
      hps_io_qspi_inst_IO2     => hps_inout.hps_io_qspi_inst_IO2,                        --                    .hps_io_qspi_inst_IO2
      hps_io_qspi_inst_IO3     => hps_inout.hps_io_qspi_inst_IO3,                        --                    .hps_io_qspi_inst_IO3
      hps_io_qspi_inst_SS0     => open,                                                  --                    .hps_io_qspi_inst_SS0
      hps_io_qspi_inst_CLK     => open,                                                  --                    .hps_io_qspi_inst_CLK
      hps_io_sdio_inst_CMD     => hps_inout.hps_io_sdio_inst_CMD,                        --                    .hps_io_sdio_inst_CMD
      hps_io_sdio_inst_D0      => hps_inout.hps_io_sdio_inst_D0,                         --                    .hps_io_sdio_inst_D0
      hps_io_sdio_inst_D1      => hps_inout.hps_io_sdio_inst_D1,                         --                    .hps_io_sdio_inst_D1
      hps_io_sdio_inst_CLK     => open,                                                  --                    .hps_io_sdio_inst_CLK
      hps_io_sdio_inst_D2      => hps_inout.hps_io_sdio_inst_D2,                         --                    .hps_io_sdio_inst_D2
      hps_io_sdio_inst_D3      => hps_inout.hps_io_sdio_inst_D3,                         --                    .hps_io_sdio_inst_D3
      hps_io_usb1_inst_D0      => hps_inout.hps_io_usb1_inst_D0,                         --                    .hps_io_usb1_inst_D0
      hps_io_usb1_inst_D1      => hps_inout.hps_io_usb1_inst_D1,                         --                    .hps_io_usb1_inst_D1
      hps_io_usb1_inst_D2      => hps_inout.hps_io_usb1_inst_D2,                         --                    .hps_io_usb1_inst_D2
      hps_io_usb1_inst_D3      => hps_inout.hps_io_usb1_inst_D3,                         --                    .hps_io_usb1_inst_D3
      hps_io_usb1_inst_D4      => hps_inout.hps_io_usb1_inst_D4,                         --                    .hps_io_usb1_inst_D4
      hps_io_usb1_inst_D5      => hps_inout.hps_io_usb1_inst_D5,                         --                    .hps_io_usb1_inst_D5
      hps_io_usb1_inst_D6      => hps_inout.hps_io_usb1_inst_D6,                         --                    .hps_io_usb1_inst_D6
      hps_io_usb1_inst_D7      => hps_inout.hps_io_usb1_inst_D7,                         --                    .hps_io_usb1_inst_D7
      hps_io_usb1_inst_CLK     => '0',                                                   --                    .hps_io_usb1_inst_CLK
      hps_io_usb1_inst_STP     => open,                                                  --                    .hps_io_usb1_inst_STP
      hps_io_usb1_inst_DIR     => '0',                                                   --                    .hps_io_usb1_inst_DIR
      hps_io_usb1_inst_NXT     => '0',                                                   --                    .hps_io_usb1_inst_NXT
      hps_io_spim0_inst_CLK    => open,                                                  --                    .hps_io_spim0_inst_CLK
      hps_io_spim0_inst_MOSI   => open,                                                  --                    .hps_io_spim0_inst_MOSI
      hps_io_spim0_inst_MISO   => '0',                                                   --                    .hps_io_spim0_inst_MISO
      hps_io_spim0_inst_SS0    => open,                                                  --                    .hps_io_spim0_inst_SS0
      hps_io_uart0_inst_RX     => '0',                                                   --                    .hps_io_uart0_inst_RX
      hps_io_uart0_inst_TX     => open,                                                  --                    .hps_io_uart0_inst_TX
      hps_io_i2c0_inst_SDA     => open,                                                  --                    .hps_io_i2c0_inst_SDA
      hps_io_i2c0_inst_SCL     => open,                                                  --                    .hps_io_i2c0_inst_SCL
      hps_io_can0_inst_RX      => '0',                                                   --                    .hps_io_can0_inst_RX
      hps_io_can0_inst_TX      => open,                                                  --                    .hps_io_can0_inst_TX
      hps_io_trace_inst_CLK    => open,                                                  --                    .hps_io_trace_inst_CLK
      hps_io_trace_inst_D0     => open,                                                  --                    .hps_io_trace_inst_D0
      hps_io_trace_inst_D1     => open,                                                  --                    .hps_io_trace_inst_D1
      hps_io_trace_inst_D2     => open,                                                  --                    .hps_io_trace_inst_D2
      hps_io_trace_inst_D3     => open,                                                  --                    .hps_io_trace_inst_D3
      hps_io_trace_inst_D4     => open,                                                  --                    .hps_io_trace_inst_D4
      hps_io_trace_inst_D5     => open,                                                  --                    .hps_io_trace_inst_D5
      hps_io_trace_inst_D6     => open,                                                  --                    .hps_io_trace_inst_D6
      hps_io_trace_inst_D7     => open,                                                  --                    .hps_io_trace_inst_D7
      hps_io_gpio_inst_GPIO09  => hps_inout.hps_io_gpio_inst_GPIO09,                     --                    .hps_io_gpio_inst_GPIO09
      hps_io_gpio_inst_GPIO35  => hps_inout.hps_io_gpio_inst_GPIO35,                     --                    .hps_io_gpio_inst_GPIO35
      hps_io_gpio_inst_GPIO41  => hps_inout.hps_io_gpio_inst_GPIO41,                     --                    .hps_io_gpio_inst_GPIO41
      hps_io_gpio_inst_GPIO42  => hps_inout.hps_io_gpio_inst_GPIO42,                     --                    .hps_io_gpio_inst_GPIO42
      hps_io_gpio_inst_GPIO43  => hps_inout.hps_io_gpio_inst_GPIO43,                     --                    .hps_io_gpio_inst_GPIO43
      hps_io_gpio_inst_GPIO44  => hps_inout.hps_io_gpio_inst_GPIO44,                     --                    .hps_io_gpio_inst_GPIO44
      h2f_rst_n                => hps_fpga_reset_n,                                      --           h2f_reset.reset_n
      f2h_sdram0_clk           => '0',                                                   --    f2h_sdram0_clock.clk
      f2h_sdram0_ADDRESS       => (others => '0'),                                       --     f2h_sdram0_data.address
      f2h_sdram0_BURSTCOUNT    => (others => '0'),                                       --                    .burstcount
      f2h_sdram0_WAITREQUEST   => open,                                                  --                    .waitrequest
      f2h_sdram0_READDATA      => open,                                                  --                    .readdata
      f2h_sdram0_READDATAVALID => open,                                                  --                    .readdatavalid
      f2h_sdram0_READ          => '0',                                                   --                    .read
      f2h_sdram0_WRITEDATA     => (others => '0'),                                       --                    .writedata
      f2h_sdram0_BYTEENABLE    => (others => '0'),                                       --                    .byteenable
      f2h_sdram0_WRITE         => '0',                                                   --                    .write
      h2f_axi_clk              => m_h2f_axi_in(0).A.CLK,                                 --       h2f_axi_clock.clk
      h2f_AWID                 => m_h2f_axi_out(0).AW.ID,                                --      h2f_axi_master.awid
      h2f_AWADDR               => m_h2f_axi_out(0).AW.ADDR,                              --                    .awaddr
      h2f_AWLEN                => m_h2f_axi_out(0).AW.LEN,                               --                    .awlen
      h2f_AWSIZE               => m_h2f_axi_out(0).AW.SIZE,                              --                    .awsize
      h2f_AWBURST              => m_h2f_axi_out(0).AW.BURST,                             --                    .awburst
      h2f_AWLOCK               => m_h2f_axi_out(0).AW.LOCK,                              --                    .awlock
      h2f_AWCACHE              => m_h2f_axi_out(0).AW.CACHE,                             --                    .awcache
      h2f_AWPROT               => m_h2f_axi_out(0).AW.PROT,                              --                    .awprot
      h2f_AWVALID              => m_h2f_axi_out(0).AW.VALID,                             --                    .awvalid
      h2f_AWREADY              => m_h2f_axi_in(0).AW.READY,                              --                    .awready
      h2f_WID                  => m_h2f_axi_out(0).W.ID,                                 --                    .wid
      h2f_WDATA                => m_h2f_axi_out(0).W.DATA,                               --                    .wdata
      h2f_WSTRB                => m_h2f_axi_out(0).W.STRB,                               --                    .wstrb
      h2f_WLAST                => m_h2f_axi_out(0).W.LAST,                               --                    .wlast
      h2f_WVALID               => m_h2f_axi_out(0).W.VALID,                              --                    .wvalid
      h2f_WREADY               => m_h2f_axi_in(0).W.READY,                               --                    .wready
      h2f_BID                  => m_h2f_axi_in(0).B.ID,                                  --                    .bid
      h2f_BRESP                => m_h2f_axi_in(0).B.RESP,                                --                    .bresp
      h2f_BVALID               => m_h2f_axi_in(0).B.VALID,                               --                    .bvalid
      h2f_BREADY               => m_h2f_axi_out(0).B.READY,                              --                    .bready
      h2f_ARID                 => m_h2f_axi_out(0).AR.ID,                                --                    .arid
      h2f_ARADDR               => m_h2f_axi_out(0).AR.ADDR,                              --                    .araddr
      h2f_ARLEN                => m_h2f_axi_out(0).AR.LEN,                               --                    .arlen
      h2f_ARSIZE               => m_h2f_axi_out(0).AR.SIZE,                              --                    .arsize
      h2f_ARBURST              => m_h2f_axi_out(0).AR.BURST,                             --                      .arburst
      h2f_ARLOCK               => m_h2f_axi_out(0).AR.LOCK,                              --                      .arlock
      h2f_ARCACHE              => m_h2f_axi_out(0).AR.CACHE,                             --                    .arcache
      h2f_ARPROT               => m_h2f_axi_out(0).AR.PROT,                              --                    .arprot
      h2f_ARVALID              => m_h2f_axi_out(0).AR.VALID,                             --                    .arvalid
      h2f_ARREADY              => m_h2f_axi_in(0).AR.READY,                              --                    .arready
      h2f_RID                  => m_h2f_axi_in(0).R.ID,                                  --                    .rid
      h2f_RDATA                => m_h2f_axi_in(0).R.DATA,                                --                    .rdata
      h2f_RRESP                => m_h2f_axi_in(0).R.RESP,                                --                    .rresp
      h2f_RLAST                => m_h2f_axi_in(0).R.LAST,                                --                    .rlast
      h2f_RVALID               => m_h2f_axi_in(0).R.VALID,                               --                    .rvalid
      h2f_RREADY               => m_h2f_axi_out(0).R.READY,                              --                    .rready
      f2h_axi_clk              => s_f2h_axi_in(0).A.CLK,                                 --       f2h_axi_clock.clk
      f2h_AWID                 => s_f2h_axi_in(0).AW.ID,                                 --       f2h_axi_slave.awid
      f2h_AWADDR               => s_f2h_axi_in(0).AW.ADDR,                               --                    .awaddr
      f2h_AWLEN                => s_f2h_axi_in(0).AW.LEN,                                --                    .awlen
      f2h_AWSIZE               => s_f2h_axi_in(0).AW.SIZE,                               --                    .awsize
      f2h_AWBURST              => s_f2h_axi_in(0).AW.BURST,                              --                    .awburst
      f2h_AWLOCK               => s_f2h_axi_in(0).AW.LOCK,                               --                    .awlock
      f2h_AWCACHE              => s_f2h_axi_in(0).AW.CACHE,                              --                    .awcache
      f2h_AWPROT               => s_f2h_axi_in(0).AW.PROT,                               --                    .awprot
      f2h_AWVALID              => s_f2h_axi_in(0).AW.VALID,                              --                    .awvalid
      f2h_AWREADY              => s_f2h_axi_out(0).AW.READY,                             --                    .awready
      -- f2h_AWUSER               => s_f2h_axi_in(0).AW.USER,                               --                    .awuser
      f2h_WID                  => s_f2h_axi_in(0).W.ID,                                  --                    .wid
      f2h_WDATA                => s_f2h_axi_in(0).W.DATA,                                --                    .wdata
      f2h_WSTRB                => s_f2h_axi_in(0).W.STRB,                                --                    .wstrb
      f2h_WLAST                => s_f2h_axi_in(0).W.LAST,                                --                    .wlast
      f2h_WVALID               => s_f2h_axi_in(0).W.VALID,                               --                    .wvalid
      f2h_WREADY               => s_f2h_axi_out(0).W.READY,                              --                    .wready
      f2h_BID                  => s_f2h_axi_out(0).B.ID,                                 --                    .bid
      f2h_BRESP                => s_f2h_axi_out(0).B.RESP,                               --                    .bresp
      f2h_BVALID               => s_f2h_axi_out(0).B.VALID,                              --                    .bvalid
      f2h_BREADY               => s_f2h_axi_in(0).B.READY,                               --                    .bready
      f2h_ARID                 => s_f2h_axi_in(0).AR.ID,                                 --                    .arid
      f2h_ARADDR               => s_f2h_axi_in(0).AR.ADDR,                               --                    .araddr
      f2h_ARLEN                => s_f2h_axi_in(0).AR.LEN,                                --                    .arlen
      f2h_ARSIZE               => s_f2h_axi_in(0).AR.SIZE,                               --                    .arsize
      f2h_ARBURST              => s_f2h_axi_in(0).AR.BURST,                              --                    .arburst
      f2h_ARLOCK               => s_f2h_axi_in(0).AR.LOCK,                               --                    .arlock
      f2h_ARCACHE              => s_f2h_axi_in(0).AR.CACHE,                              --                    .arcache
      f2h_ARPROT               => s_f2h_axi_in(0).AR.PROT,                               --                    .arprot
      f2h_ARVALID              => s_f2h_axi_in(0).AR.VALID,                              --                    .arvalid
      f2h_ARREADY              => s_f2h_axi_out(0).AR.READY,                             --                    .arready
      -- f2h_ARUSER               => s_f2h_axi_in(0).AR.USER,                               --                    .aruser
      f2h_RID                  => s_f2h_axi_out(0).R.ID,                                 --                    .rid
      f2h_RDATA                => s_f2h_axi_out(0).R.DATA,                               --                    .rdata
      f2h_RRESP                => s_f2h_axi_out(0).R.RESP,                               --                    .rresp
      f2h_RLAST                => s_f2h_axi_out(0).R.LAST,                               --                    .rlast
      f2h_RVALID               => s_f2h_axi_out(0).R.VALID,                              --                    .rvalid
      f2h_RREADY               => s_f2h_axi_in(0).R.READY,                               --                    .rready
      -- h2f_lw_axi_clk           => hps_in.CLK,                                            --    h2f_lw_axi_clock.clk
      -- h2f_lw_AWID              => hps_0_h2f_lw_axi_master_awid,                          --   h2f_lw_axi_master.awid
      -- h2f_lw_AWADDR            => hps_0_h2f_lw_axi_master_awaddr,                        --                    .awaddr
      -- h2f_lw_AWLEN             => hps_0_h2f_lw_axi_master_awlen,                         --                    .awlen
      -- h2f_lw_AWSIZE            => hps_0_h2f_lw_axi_master_awsize,                        --                    .awsize
      -- h2f_lw_AWBURST           => hps_0_h2f_lw_axi_master_awburst,                       --                    .awburst
      -- h2f_lw_AWLOCK            => hps_0_h2f_lw_axi_master_awlock,                        --                    .awlock
      -- h2f_lw_AWCACHE           => hps_0_h2f_lw_axi_master_awcache,                       --                    .awcache
      -- h2f_lw_AWPROT            => hps_0_h2f_lw_axi_master_awprot,                        --                    .awprot
      -- h2f_lw_AWVALID           => hps_0_h2f_lw_axi_master_awvalid,                       --                    .awvalid
      -- h2f_lw_AWREADY           => hps_0_h2f_lw_axi_master_awready,                       --                    .awready
      -- h2f_lw_WID               => hps_0_h2f_lw_axi_master_wid,                           --                    .wid
      -- h2f_lw_WDATA             => hps_0_h2f_lw_axi_master_wdata,                         --                    .wdata
      -- h2f_lw_WSTRB             => hps_0_h2f_lw_axi_master_wstrb,                         --                    .wstrb
      -- h2f_lw_WLAST             => hps_0_h2f_lw_axi_master_wlast,                         --                    .wlast
      -- h2f_lw_WVALID            => hps_0_h2f_lw_axi_master_wvalid,                        --                    .wvalid
      -- h2f_lw_WREADY            => hps_0_h2f_lw_axi_master_wready,                        --                    .wready
      -- h2f_lw_BID               => hps_0_h2f_lw_axi_master_bid,                           --                    .bid
      -- h2f_lw_BRESP             => hps_0_h2f_lw_axi_master_bresp,                         --                    .bresp
      -- h2f_lw_BVALID            => hps_0_h2f_lw_axi_master_bvalid,                        --                    .bvalid
      -- h2f_lw_BREADY            => hps_0_h2f_lw_axi_master_bready,                        --                    .bready
      -- h2f_lw_ARID              => hps_0_h2f_lw_axi_master_arid,                          --                    .arid
      -- h2f_lw_ARADDR            => hps_0_h2f_lw_axi_master_araddr,                        --                    .araddr
      -- h2f_lw_ARLEN             => hps_0_h2f_lw_axi_master_arlen,                         --                    .arlen
      -- h2f_lw_ARSIZE            => hps_0_h2f_lw_axi_master_arsize,                        --                    .arsize
      -- h2f_lw_ARBURST           => hps_0_h2f_lw_axi_master_arburst,                       --                    .arburst
      -- h2f_lw_ARLOCK            => hps_0_h2f_lw_axi_master_arlock,                        --                    .arlock
      -- h2f_lw_ARCACHE           => hps_0_h2f_lw_axi_master_arcache,                       --                    .arcache
      -- h2f_lw_ARPROT            => hps_0_h2f_lw_axi_master_arprot,                        --                    .arprot
      -- h2f_lw_ARVALID           => hps_0_h2f_lw_axi_master_arvalid,                       --                    .arvalid
      -- h2f_lw_ARREADY           => hps_0_h2f_lw_axi_master_arready,                       --                    .arready
      -- h2f_lw_RID               => hps_0_h2f_lw_axi_master_rid,                           --                    .rid
      -- h2f_lw_RDATA             => hps_0_h2f_lw_axi_master_rdata,                         --                    .rdata
      -- h2f_lw_RRESP             => hps_0_h2f_lw_axi_master_rresp,                         --                    .rresp
      -- h2f_lw_RLAST             => hps_0_h2f_lw_axi_master_rlast,                         --                    .rlast
      -- h2f_lw_RVALID            => hps_0_h2f_lw_axi_master_rvalid,                        --                    .rvalid
      -- h2f_lw_RREADY            => hps_0_h2f_lw_axi_master_rready,                        --                    .rready
      f2h_irq_p0               => (others => '0'),                                       --            f2h_irq0.irq
      f2h_irq_p1               => (others => '0')                                        --            f2h_irq1.irq
    );

  -- hps : soc_system
  -- component soc_system is
  --   port (
  --     button_pio_external_connection_export =>(others => '0'),
  --     clk_clk                               =>hps_in.CLK,
  --     dipsw_pio_external_connection_export  =>'0',
  --     hps_0_f2h_cold_reset_req_reset_n      =>hps_cold_reset_n,
  --     hps_0_f2h_debug_reset_req_reset_n     =>hps_debug_reset_n,
  --     hps_0_f2h_stm_hw_events_stm_hwevents  =>(others => '0'),
  --     hps_0_f2h_warm_reset_req_reset_n      =>hps_warm_reset_n,
  --     hps_0_h2f_reset_reset_n               =>hps_fpga_reset_n,
  --     hps_0_hps_io_hps_io_emac1_inst_TX_CLK =>open,
  --     hps_0_hps_io_hps_io_emac1_inst_TXD0   =>open,
  --     hps_0_hps_io_hps_io_emac1_inst_TXD1   =>open,
  --     hps_0_hps_io_hps_io_emac1_inst_TXD2   =>open,
  --     hps_0_hps_io_hps_io_emac1_inst_TXD3   =>open,
  --     hps_0_hps_io_hps_io_emac1_inst_RXD0   =>'0',
  --     hps_0_hps_io_hps_io_emac1_inst_MDIO   =>open,
  --     hps_0_hps_io_hps_io_emac1_inst_MDC    =>open,
  --     hps_0_hps_io_hps_io_emac1_inst_RX_CTL =>'0',
  --     hps_0_hps_io_hps_io_emac1_inst_TX_CTL =>open,
  --     hps_0_hps_io_hps_io_emac1_inst_RX_CLK =>'0',
  --     hps_0_hps_io_hps_io_emac1_inst_RXD1   =>'0',
  --     hps_0_hps_io_hps_io_emac1_inst_RXD2   =>'0',
  --     hps_0_hps_io_hps_io_emac1_inst_RXD3   =>'0',
  --     hps_0_hps_io_hps_io_qspi_inst_IO0     =>open,
  --     hps_0_hps_io_hps_io_qspi_inst_IO1     =>open,
  --     hps_0_hps_io_hps_io_qspi_inst_IO2     =>open,
  --     hps_0_hps_io_hps_io_qspi_inst_IO3     =>open,
  --     hps_0_hps_io_hps_io_qspi_inst_SS0     =>open,
  --     hps_0_hps_io_hps_io_qspi_inst_CLK     =>open,
  --     hps_0_hps_io_hps_io_sdio_inst_CMD     =>open,
  --     hps_0_hps_io_hps_io_sdio_inst_D0      =>open,
  --     hps_0_hps_io_hps_io_sdio_inst_D1      =>open,
  --     hps_0_hps_io_hps_io_sdio_inst_CLK     =>open,
  --     hps_0_hps_io_hps_io_sdio_inst_D2      =>open,
  --     hps_0_hps_io_hps_io_sdio_inst_D3      =>open,
  --     hps_0_hps_io_hps_io_usb1_inst_D0      =>open,
  --     hps_0_hps_io_hps_io_usb1_inst_D1      =>open,
  --     hps_0_hps_io_hps_io_usb1_inst_D2      =>open,
  --     hps_0_hps_io_hps_io_usb1_inst_D3      =>open,
  --     hps_0_hps_io_hps_io_usb1_inst_D4      =>open,
  --     hps_0_hps_io_hps_io_usb1_inst_D5      =>open,
  --     hps_0_hps_io_hps_io_usb1_inst_D6      =>open,
  --     hps_0_hps_io_hps_io_usb1_inst_D7      =>open,
  --     hps_0_hps_io_hps_io_usb1_inst_CLK     =>'0',
  --     hps_0_hps_io_hps_io_usb1_inst_STP     =>open,
  --     hps_0_hps_io_hps_io_usb1_inst_DIR     =>'0',
  --     hps_0_hps_io_hps_io_usb1_inst_NXT     =>'0',
  --     hps_0_hps_io_hps_io_spim0_inst_CLK    =>open,
  --     hps_0_hps_io_hps_io_spim0_inst_MOSI   =>open,
  --     hps_0_hps_io_hps_io_spim0_inst_MISO   =>'0',
  --     hps_0_hps_io_hps_io_spim0_inst_SS0    =>open,
  --     hps_0_hps_io_hps_io_uart0_inst_RX     =>'0',
  --     hps_0_hps_io_hps_io_uart0_inst_TX     =>open,
  --     hps_0_hps_io_hps_io_i2c0_inst_SDA     =>open,
  --     hps_0_hps_io_hps_io_i2c0_inst_SCL     =>open,
  --     hps_0_hps_io_hps_io_can0_inst_RX      =>'0',
  --     hps_0_hps_io_hps_io_can0_inst_TX      =>open,
  --     hps_0_hps_io_hps_io_trace_inst_CLK    =>open,
  --     hps_0_hps_io_hps_io_trace_inst_D0     =>open,
  --     hps_0_hps_io_hps_io_trace_inst_D1     =>open,
  --     hps_0_hps_io_hps_io_trace_inst_D2     =>open,
  --     hps_0_hps_io_hps_io_trace_inst_D3     =>open,
  --     hps_0_hps_io_hps_io_trace_inst_D4     =>open,
  --     hps_0_hps_io_hps_io_trace_inst_D5     =>open,
  --     hps_0_hps_io_hps_io_trace_inst_D6     =>open,
  --     hps_0_hps_io_hps_io_trace_inst_D7     =>open,
  --     hps_0_hps_io_hps_io_gpio_inst_GPIO09  =>open,
  --     hps_0_hps_io_hps_io_gpio_inst_GPIO35  =>open,
  --     hps_0_hps_io_hps_io_gpio_inst_GPIO41  =>open,
  --     hps_0_hps_io_hps_io_gpio_inst_GPIO42  =>open,
  --     hps_0_hps_io_hps_io_gpio_inst_GPIO43  =>open,
  --     hps_0_hps_io_hps_io_gpio_inst_GPIO44  =>open,
  --     issp_hps_resets_source                =>hps_reset_req,
  --     led_pio_external_connection_in_port   =>'0',
  --     led_pio_external_connection_out_port  =>open,
  --     memory_mem_a                          =>open,
  --     memory_mem_ba                         =>open,
  --     memory_mem_ck                         =>open,
  --     memory_mem_ck_n                       =>open,
  --     memory_mem_cke                        =>open,
  --     memory_mem_cs_n                       =>open,
  --     memory_mem_ras_n                      =>open,
  --     memory_mem_cas_n                      =>open,
  --     memory_mem_we_n                       =>open,
  --     memory_mem_reset_n                    =>open,
  --     memory_mem_dq                         =>open,
  --     memory_mem_dqs                        =>open,
  --     memory_mem_dqs_n                      =>open,
  --     memory_mem_odt                        =>open,
  --     memory_mem_dm                         =>open,
  --     memory_oct_rzqin                      =>'0',
  --     reset_reset_n                         =>hps_fpga_reset_n
  --     );
end rtl;
