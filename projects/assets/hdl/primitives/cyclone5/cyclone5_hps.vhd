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
  port    (hps_in        : in  hps_in_t;
           hps_out       : out hps_out_t;
           -- master
           h2f_axi_in    : in  axi.cyclone5_h2f.axi_s2m_array_t(0 to C_H2F_AXI_COUNT-1);
           h2f_axi_out   : out axi.cyclone5_h2f.axi_m2s_array_t(0 to C_H2F_AXI_COUNT-1);
           -- slave
           f2h_axi_in    : in  axi.cyclone5_f2h.axi_m2s_array_t(0 to C_F2H_AXI_COUNT-1);
           f2h_axi_out   : out axi.cyclone5_f2h.axi_s2m_array_t(0 to C_F2H_AXI_COUNT-1)
           );
end entity cyclone5_hps;
architecture rtl of cyclone5_hps is

  component soc_system_hps_0 is
		generic (
			F2S_Width : integer := 2;
			S2F_Width : integer := 2
		);
		port (
			h2f_cold_rst_n : out   std_logic;                                        -- reset_n
			h2f_user0_clk  : out   std_logic;                                        -- clk
			mem_a          : out   std_logic_vector(12 downto 0);                    -- mem_a
			mem_ba         : out   std_logic_vector(2 downto 0);                     -- mem_ba
			mem_ck         : out   std_logic;                                        -- mem_ck
			mem_ck_n       : out   std_logic;                                        -- mem_ck_n
			mem_cke        : out   std_logic;                                        -- mem_cke
			mem_cs_n       : out   std_logic;                                        -- mem_cs_n
			mem_ras_n      : out   std_logic;                                        -- mem_ras_n
			mem_cas_n      : out   std_logic;                                        -- mem_cas_n
			mem_we_n       : out   std_logic;                                        -- mem_we_n
			mem_reset_n    : out   std_logic;                                        -- mem_reset_n
			mem_dq         : inout std_logic_vector(7 downto 0)  := (others => 'X'); -- mem_dq
			mem_dqs        : inout std_logic                     := 'X';             -- mem_dqs
			mem_dqs_n      : inout std_logic                     := 'X';             -- mem_dqs_n
			mem_odt        : out   std_logic;                                        -- mem_odt
			mem_dm         : out   std_logic;                                        -- mem_dm
			oct_rzqin      : in    std_logic                     := 'X';             -- oct_rzqin
			h2f_rst_n      : out   std_logic;                                        -- reset_n
			h2f_axi_clk    : in    std_logic                     := 'X';             -- clk
			h2f_AWID       : out   std_logic_vector(11 downto 0);                    -- awid
			h2f_AWADDR     : out   std_logic_vector(29 downto 0);                    -- awaddr
			h2f_AWLEN      : out   std_logic_vector(3 downto 0);                     -- awlen
			h2f_AWSIZE     : out   std_logic_vector(2 downto 0);                     -- awsize
			h2f_AWBURST    : out   std_logic_vector(1 downto 0);                     -- awburst
			h2f_AWLOCK     : out   std_logic_vector(1 downto 0);                     -- awlock
			h2f_AWCACHE    : out   std_logic_vector(3 downto 0);                     -- awcache
			h2f_AWPROT     : out   std_logic_vector(2 downto 0);                     -- awprot
			h2f_AWVALID    : out   std_logic;                                        -- awvalid
			h2f_AWREADY    : in    std_logic                     := 'X';             -- awready
			h2f_WID        : out   std_logic_vector(11 downto 0);                    -- wid
			h2f_WDATA      : out   std_logic_vector(63 downto 0);                    -- wdata
			h2f_WSTRB      : out   std_logic_vector(7 downto 0);                     -- wstrb
			h2f_WLAST      : out   std_logic;                                        -- wlast
			h2f_WVALID     : out   std_logic;                                        -- wvalid
			h2f_WREADY     : in    std_logic                     := 'X';             -- wready
			h2f_BID        : in    std_logic_vector(11 downto 0) := (others => 'X'); -- bid
			h2f_BRESP      : in    std_logic_vector(1 downto 0)  := (others => 'X'); -- bresp
			h2f_BVALID     : in    std_logic                     := 'X';             -- bvalid
			h2f_BREADY     : out   std_logic;                                        -- bready
			h2f_ARID       : out   std_logic_vector(11 downto 0);                    -- arid
			h2f_ARADDR     : out   std_logic_vector(29 downto 0);                    -- araddr
			h2f_ARLEN      : out   std_logic_vector(3 downto 0);                     -- arlen
			h2f_ARSIZE     : out   std_logic_vector(2 downto 0);                     -- arsize
			h2f_ARBURST    : out   std_logic_vector(1 downto 0);                     -- arburst
			h2f_ARLOCK     : out   std_logic_vector(1 downto 0);                     -- arlock
			h2f_ARCACHE    : out   std_logic_vector(3 downto 0);                     -- arcache
			h2f_ARPROT     : out   std_logic_vector(2 downto 0);                     -- arprot
			h2f_ARVALID    : out   std_logic;                                        -- arvalid
			h2f_ARREADY    : in    std_logic                     := 'X';             -- arready
			h2f_RID        : in    std_logic_vector(11 downto 0) := (others => 'X'); -- rid
			h2f_RDATA      : in    std_logic_vector(63 downto 0) := (others => 'X'); -- rdata
			h2f_RRESP      : in    std_logic_vector(1 downto 0)  := (others => 'X'); -- rresp
			h2f_RLAST      : in    std_logic                     := 'X';             -- rlast
			h2f_RVALID     : in    std_logic                     := 'X';             -- rvalid
			h2f_RREADY     : out   std_logic;                                        -- rready
			f2h_axi_clk    : in    std_logic                     := 'X';             -- clk
			f2h_AWID       : in    std_logic_vector(7 downto 0)  := (others => 'X'); -- awid
			f2h_AWADDR     : in    std_logic_vector(31 downto 0) := (others => 'X'); -- awaddr
			f2h_AWLEN      : in    std_logic_vector(3 downto 0)  := (others => 'X'); -- awlen
			f2h_AWSIZE     : in    std_logic_vector(2 downto 0)  := (others => 'X'); -- awsize
			f2h_AWBURST    : in    std_logic_vector(1 downto 0)  := (others => 'X'); -- awburst
			f2h_AWLOCK     : in    std_logic_vector(1 downto 0)  := (others => 'X'); -- awlock
			f2h_AWCACHE    : in    std_logic_vector(3 downto 0)  := (others => 'X'); -- awcache
			f2h_AWPROT     : in    std_logic_vector(2 downto 0)  := (others => 'X'); -- awprot
			f2h_AWVALID    : in    std_logic                     := 'X';             -- awvalid
			f2h_AWREADY    : out   std_logic;                                        -- awready
			f2h_AWUSER     : in    std_logic_vector(4 downto 0)  := (others => 'X'); -- awuser
			f2h_WID        : in    std_logic_vector(7 downto 0)  := (others => 'X'); -- wid
			f2h_WDATA      : in    std_logic_vector(31 downto 0) := (others => 'X'); -- wdata
			f2h_WSTRB      : in    std_logic_vector(3 downto 0)  := (others => 'X'); -- wstrb
			f2h_WLAST      : in    std_logic                     := 'X';             -- wlast
			f2h_WVALID     : in    std_logic                     := 'X';             -- wvalid
			f2h_WREADY     : out   std_logic;                                        -- wready
			f2h_BID        : out   std_logic_vector(7 downto 0);                     -- bid
			f2h_BRESP      : out   std_logic_vector(1 downto 0);                     -- bresp
			f2h_BVALID     : out   std_logic;                                        -- bvalid
			f2h_BREADY     : in    std_logic                     := 'X';             -- bready
			f2h_ARID       : in    std_logic_vector(7 downto 0)  := (others => 'X'); -- arid
			f2h_ARADDR     : in    std_logic_vector(31 downto 0) := (others => 'X'); -- araddr
			f2h_ARLEN      : in    std_logic_vector(3 downto 0)  := (others => 'X'); -- arlen
			f2h_ARSIZE     : in    std_logic_vector(2 downto 0)  := (others => 'X'); -- arsize
			f2h_ARBURST    : in    std_logic_vector(1 downto 0)  := (others => 'X'); -- arburst
			f2h_ARLOCK     : in    std_logic_vector(1 downto 0)  := (others => 'X'); -- arlock
			f2h_ARCACHE    : in    std_logic_vector(3 downto 0)  := (others => 'X'); -- arcache
			f2h_ARPROT     : in    std_logic_vector(2 downto 0)  := (others => 'X'); -- arprot
			f2h_ARVALID    : in    std_logic                     := 'X';             -- arvalid
			f2h_ARREADY    : out   std_logic;                                        -- arready
			f2h_ARUSER     : in    std_logic_vector(4 downto 0)  := (others => 'X'); -- aruser
			f2h_RID        : out   std_logic_vector(7 downto 0);                     -- rid
			f2h_RDATA      : out   std_logic_vector(31 downto 0);                    -- rdata
			f2h_RRESP      : out   std_logic_vector(1 downto 0);                     -- rresp
			f2h_RLAST      : out   std_logic;                                        -- rlast
			f2h_RVALID     : out   std_logic;                                        -- rvalid
			f2h_RREADY     : in    std_logic                     := 'X'              -- rready
		);
	end component soc_system_hps_0;

  signal        h2f_rst_n  : std_logic;
begin

  h2f_axi_out(0).A.RESETN <= h2f_rst_n;
  hps_out.h2f_rst_n <= h2f_rst_n;

  hps_0 : soc_system_hps_0
    generic map (
      F2S_Width => 1, -- "0:Unused" "1:32-bit" "2:64-bit" "3:128-bit"
      S2F_Width => 2  -- "0:Unused" "1:32-bit" "2:64-bit" "3:128-bit"
    )
    port map (
      h2f_cold_rst_n           => hps_out.h2f_cold_rst_n ,                             --  h2f_cold_reset.reset_n
      h2f_user0_clk            => hps_out.h2f_user0_clk,                               -- h2f_user0_clock.clk
      mem_a                    => open,                                                --              memory.mem_a
      mem_ba                   => open,                                                --                    .mem_ba
      mem_ck                   => open,                                                --                    .mem_ck
      mem_ck_n                 => open,                                                --                    .mem_ck_n
      mem_cke                  => open,                                                --                    .mem_cke
      mem_cs_n                 => open,                                                --                    .mem_cs_n
      mem_ras_n                => open,                                                --                    .mem_ras_n
      mem_cas_n                => open,                                                --                    .mem_cas_n
      mem_we_n                 => open,                                                --                    .mem_we_n
      mem_reset_n              => open,                                                --                    .mem_reset_n
      mem_dq                   => open,                                                --                    .mem_dq
      mem_dqs                  => open,                                                --                    .mem_dqs
      mem_dqs_n                => open,                                                --                    .mem_dqs_n
      mem_odt                  => open,                                                --                    .mem_odt
      mem_dm                   => open,                                                --                    .mem_dm
      oct_rzqin                => '0',                                                 --                    .oct_rzqin
      h2f_rst_n                => h2f_rst_n,                                           --           h2f_reset.reset_n
      h2f_axi_clk              => h2f_axi_in(0).A.CLK,                                 --       h2f_axi_clock.clk
      h2f_AWID                 => h2f_axi_out(0).AW.ID,                                --      h2f_axi_master.awid
      h2f_AWADDR               => h2f_axi_out(0).AW.ADDR,                              --                    .awaddr
      h2f_AWLEN                => h2f_axi_out(0).AW.LEN,                               --                    .awlen
      h2f_AWSIZE               => h2f_axi_out(0).AW.SIZE,                              --                    .awsize
      h2f_AWBURST              => h2f_axi_out(0).AW.BURST,                             --                    .awburst
      h2f_AWLOCK               => h2f_axi_out(0).AW.LOCK,                              --                    .awlock
      h2f_AWCACHE              => h2f_axi_out(0).AW.CACHE,                             --                    .awcache
      h2f_AWPROT               => h2f_axi_out(0).AW.PROT,                              --                    .awprot
      h2f_AWVALID              => h2f_axi_out(0).AW.VALID,                             --                    .awvalid
      h2f_AWREADY              => h2f_axi_in(0).AW.READY,                              --                    .awready
      h2f_WID                  => h2f_axi_out(0).W.ID,                                 --                    .wid
      h2f_WDATA                => h2f_axi_out(0).W.DATA,                               --                    .wdata
      h2f_WSTRB                => h2f_axi_out(0).W.STRB,                               --                    .wstrb
      h2f_WLAST                => h2f_axi_out(0).W.LAST,                               --                    .wlast
      h2f_WVALID               => h2f_axi_out(0).W.VALID,                              --                    .wvalid
      h2f_WREADY               => h2f_axi_in(0).W.READY,                               --                    .wready
      h2f_BID                  => h2f_axi_in(0).B.ID,                                  --                    .bid
      h2f_BRESP                => h2f_axi_in(0).B.RESP,                                --                    .bresp
      h2f_BVALID               => h2f_axi_in(0).B.VALID,                               --                    .bvalid
      h2f_BREADY               => h2f_axi_out(0).B.READY,                              --                    .bready
      h2f_ARID                 => h2f_axi_out(0).AR.ID,                                --                    .arid
      h2f_ARADDR               => h2f_axi_out(0).AR.ADDR,                              --                    .araddr
      h2f_ARLEN                => h2f_axi_out(0).AR.LEN,                               --                    .arlen
      h2f_ARSIZE               => h2f_axi_out(0).AR.SIZE,                              --                    .arsize
      h2f_ARBURST              => h2f_axi_out(0).AR.BURST,                             --                      .arburst
      h2f_ARLOCK               => h2f_axi_out(0).AR.LOCK,                              --                      .arlock
      h2f_ARCACHE              => h2f_axi_out(0).AR.CACHE,                             --                    .arcache
      h2f_ARPROT               => h2f_axi_out(0).AR.PROT,                              --                    .arprot
      h2f_ARVALID              => h2f_axi_out(0).AR.VALID,                             --                    .arvalid
      h2f_ARREADY              => h2f_axi_in(0).AR.READY,                              --                    .arready
      h2f_RID                  => h2f_axi_in(0).R.ID,                                  --                    .rid
      h2f_RDATA                => h2f_axi_in(0).R.DATA,                                --                    .rdata
      h2f_RRESP                => h2f_axi_in(0).R.RESP,                                --                    .rresp
      h2f_RLAST                => h2f_axi_in(0).R.LAST,                                --                    .rlast
      h2f_RVALID               => h2f_axi_in(0).R.VALID,                               --                    .rvalid
      h2f_RREADY               => h2f_axi_out(0).R.READY,                              --                    .rready
      f2h_axi_clk              => f2h_axi_in(0).A.CLK,                                 --       f2h_axi_clock.clk
      f2h_AWID                 => f2h_axi_in(0).AW.ID,                                 --       f2h_axi_slave.awid
      f2h_AWADDR               => f2h_axi_in(0).AW.ADDR,                               --                    .awaddr
      f2h_AWLEN                => f2h_axi_in(0).AW.LEN,                                --                    .awlen
      f2h_AWSIZE               => f2h_axi_in(0).AW.SIZE,                               --                    .awsize
      f2h_AWBURST              => f2h_axi_in(0).AW.BURST,                              --                    .awburst
      f2h_AWLOCK               => f2h_axi_in(0).AW.LOCK,                               --                    .awlock
      f2h_AWCACHE              => f2h_axi_in(0).AW.CACHE,                              --                    .awcache
      f2h_AWPROT               => f2h_axi_in(0).AW.PROT,                               --                    .awprot
      f2h_AWVALID              => f2h_axi_in(0).AW.VALID,                              --                    .awvalid
      f2h_AWREADY              => f2h_axi_out(0).AW.READY,                             --                    .awready
      -- f2h_AWUSER               => f2h_axi_in(0).AW.USER,                               --                    .awuser
      f2h_WID                  => f2h_axi_in(0).W.ID,                                  --                    .wid
      f2h_WDATA                => f2h_axi_in(0).W.DATA,                                --                    .wdata
      f2h_WSTRB                => f2h_axi_in(0).W.STRB,                                --                    .wstrb
      f2h_WLAST                => f2h_axi_in(0).W.LAST,                                --                    .wlast
      f2h_WVALID               => f2h_axi_in(0).W.VALID,                               --                    .wvalid
      f2h_WREADY               => f2h_axi_out(0).W.READY,                              --                    .wready
      f2h_BID                  => f2h_axi_out(0).B.ID,                                 --                    .bid
      f2h_BRESP                => f2h_axi_out(0).B.RESP,                               --                    .bresp
      f2h_BVALID               => f2h_axi_out(0).B.VALID,                              --                    .bvalid
      f2h_BREADY               => f2h_axi_in(0).B.READY,                               --                    .bready
      f2h_ARID                 => f2h_axi_in(0).AR.ID,                                 --                    .arid
      f2h_ARADDR               => f2h_axi_in(0).AR.ADDR,                               --                    .araddr
      f2h_ARLEN                => f2h_axi_in(0).AR.LEN,                                --                    .arlen
      f2h_ARSIZE               => f2h_axi_in(0).AR.SIZE,                               --                    .arsize
      f2h_ARBURST              => f2h_axi_in(0).AR.BURST,                              --                    .arburst
      f2h_ARLOCK               => f2h_axi_in(0).AR.LOCK,                               --                    .arlock
      f2h_ARCACHE              => f2h_axi_in(0).AR.CACHE,                              --                    .arcache
      f2h_ARPROT               => f2h_axi_in(0).AR.PROT,                               --                    .arprot
      f2h_ARVALID              => f2h_axi_in(0).AR.VALID,                              --                    .arvalid
      f2h_ARREADY              => f2h_axi_out(0).AR.READY,                             --                    .arready
      -- f2h_ARUSER               => f2h_axi_in(0).AR.USER,                               --                    .aruser
      f2h_RID                  => f2h_axi_out(0).R.ID,                                 --                    .rid
      f2h_RDATA                => f2h_axi_out(0).R.DATA,                               --                    .rdata
      f2h_RRESP                => f2h_axi_out(0).R.RESP,                               --                    .rresp
      f2h_RLAST                => f2h_axi_out(0).R.LAST,                               --                    .rlast
      f2h_RVALID               => f2h_axi_out(0).R.VALID,                              --                    .rvalid
      f2h_RREADY               => f2h_axi_in(0).R.READY                                --                    .rready
    );

end rtl;
