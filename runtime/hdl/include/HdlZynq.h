/*
 * This file is protected by Copyright. Please refer to the COPYRIGHT file
 * distributed with this source distribution.
 *
 * This file is part of OpenCPI <http://www.opencpi.org>
 *
 * OpenCPI is free software: you can redistribute it and/or modify it under the
 * terms of the GNU Lesser General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option) any
 * later version.
 *
 * OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
 * A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
 * details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef HDLZYNQ_H
#define HDLZYNQ_H
#ifdef __cplusplus
namespace OCPI {
  namespace HDL {
    namespace Zynq {
#endif
      const uint32_t GP0_PADDR = 0x40000000;
      const uint32_t GP1_PADDR = 0x80000000;
      const uint32_t FTM_ADDR = 0xF880B000;
      // register map from Appendix B.12 "PL Fabric Trace Monitor" in:
      // https://www.xilinx.com/support/documentation/user_guides/ug585-Zynq-7000-TRM.pdf
      struct FTM {
	uint32_t
	  glbctrl,
	  status,
	  control,
	  p2fdbg0,
	  p2fdbg1,
	  p2fdbg2,
	  p2fdbg3,
	  f2pdbg0,
	  f2pdbg1,
	  f2pdbg2,
	  f2pdbg3,
	  cycountpre,
	  syncreload,
	  synccount,
	  pad0[(0x400-0x34-4)/4],
	  atid,
	  pad1[(0xed0-0x400-4)/4],
	  ittrigoutack,
	  ittrigger,
	  ittracedis,
	  itcyccount,
	  pad2[(0xeec-0xedc-4)/4],
	  itatbdata0,
	  itatbctr2,
	  itatbctr1,
	  itatbctr0,
	  pad3[(0xf00-0xef8-4)/4],	
	  itcr,
	  pad4[(0xfa0-0xf00-4)/4],
	  claimtagset,
	  claimtagclr,
	  pad5[(0xfb0-0xfa4-4)/4],
	  lock_access,
	  lock_status,
	  authstatus,
	  pad6[(0xfc8-0xfb8-4)/4],
	  devid,
	  dev_type,
	  periphid4,
	  periphid5,
	  periphid6,
	  periphid7,
	  periphid0,
	  periphid1,
	  periphid2,
	  periphid3,
	  componid0,
	  componid1,
	  componid2,
	  componid3;
      };
      struct FCLK {
	uint32_t
	clk_ctrl,
	  thr_ctrl,
	  thr_count,
	  thr_sta;
      };
#define NFCLKS 4
      //      const unsigned NFCLKS = 4;
      const uint32_t SLCR_ADDR = 0xf8000000;
      struct SLCR {
	uint32_t
	scl,
	  slcr_lock,
	  slcr_unlock,
	  slcr_locksta,
	  pad0[(0x100 - 0xc - 4)/4],
	  arm_pll_ctrl,
	  ddr_pll_ctrl,
	  io_pll_ctrl,
	  pll_status,
	  arm_pll_cfg,
	  ddr_pll_cfg,
	  io_pll_cfg,
	  pad1,
	  arm_clk_ctrl,
	  ddr_clk_ctrl,
	  dci_clk_ctrl,
	  aper_clk_ctrl,
	  usb0_clk_ctrl,
	  usb1_clk_ctrl,
	  gem0_rclk_ctrl,
	  gem1_rclk_ctrl,
	  gem0_clk_ctrl,
	  gem1_clk_ctrl,
	  smc_clk_ctrl,
	  lqspi_clk_ctrl,
	  sdio_clk_ctrl,
	  uart_clk_ctrl,
	  spi_clk_ctrl,
	  can_clk_ctrl,
	  can_mioclk_ctrl,
	  dbg_clk_ctrl,
	  pcap_clk_ctrl,
	  topsw_clk_ctrl;
	struct FCLK fpga[NFCLKS];
	uint32_t
	  pad2[(0x1c4-0x1ac-4)/4],
	  clk_621_true,
	  pad3[(0x200-0x1c4-4)/4],
	  pss_rst_ctrl,
	  ddr_rst_ctrl,
	  topsw_rst_ctrl,
	  dmac_rst_ctrl,
	  usb_rst_ctrl,
	  gem_rst_ctrl,
	  sdio_rst_ctrl,
	  spi_rst_ctrl,
	  can_rst_ctrl,
	  i2c_rst_ctrl,
	  uart_rst_ctrl,
	  gpio_rst_ctrl,
	  lqspi_rst_ctrl,
	  smc_rst_ctrl,
	  ocm_rst_ctrl,
          pad3a,
	  fpga_rst_ctrl,
	  a9_cpu_rst_ctrl,
	  pad4[(0x24c-0x244-4)/4],
	  rs_awdt_ctrl,
	  pad5[(0x258-0x24c-4)/4],
	  reboot_status,
	  boot_mode,
	  pad6[(0x300-0x25c-4)/4],
	  apu_ctrl,
	  wdt_clk_sel,
	  pad7[(0x440-0x304-4)/4],
	  tz_dma_ns,
	  tz_dma_irq_ns,
	  tz_dma_periph_ns,
	  pad8[(0x530-0x448-4)/4],
	  pss_idcode;
      };
      const uint32_t SPI_ADDR = 0xe0006000;
      struct SPI {
        uint32_t
          cr_offset,
          sr_offset,
          ier_offset,
          idr_offset,
          imr_offset,
          er_offset,
          dr_offset,
          txd_offset,
          rxd_offset,
          sicr_offset,
          txwr_offset,
          rx_thresh_reg0,
          pad0[(0xfc - 0x2c - 4)/4],
          mod_id_reg0,
          pad1[(0x1000 - 0xfc - 4)/4]; // pad between 7 series spi0 last register and 0xE0007000 spi1
      }; // ref ug585-Zynq-7000-TRM.pdf
#define NSPIS 2
#ifdef __cplusplus
    }
    namespace ZynqMP {
#endif
      // All these names and cases come from the TRM and the register table
      // See "Table 10-9: PS System Register Map" in:
      // https://www.xilinx.com/support/documentation/user_guides/ug1085-zynq-ultrascale-trm.pdf
      const uint32_t
	M_HP0_PADDR          = 0xA8000000, // slave address when seen from processor
	M_HP1_PADDR          = 0xB0000000,
	FPD_SLCR_AFI_FS_ADDR = 0xFD615000, // controlplane width register within the FPD_SLCR module
	CSU_ADDR             = 0xFFCA0000, // id code register within the CSU module
	S_AXI_HP0_FPD_ADDR   = 0xFD380000; // address of the first of 4 AFIFMs

      const unsigned NUM_S_AXI_HPS = 4;

      // UltraScale+ "CSU Module" from:
      // https://www.xilinx.com/html_docs/registers/ug1087/ug1087-zynq-ultrascale-registers.html
      struct CSU {
	uint32_t
          csu_status, csu_ctrl, csu_sss_cfg, csu_dma_reset, csu_multiboot, csu_tamper_trig, CSU_FT_STATUS,
	  pad0,
	  csu_isr, csu_imr, csu_ier, csu_idr,
	  pad1,
	  jtag_chain_status, jtag_sec, jtag_dap_cfg, IDCODE, version;
      };

      // UltraScale+ "AFIFM Module" from:
      // https://www.xilinx.com/html_docs/registers/ug1087/ug1087-zynq-ultrascale-registers.html
      struct AFIFM {
        uint8_t
          rdctrl,                   // 0x00000000
          pad0[3];
	uint32_t                    // Relative Address
	  rdissue,                  // 0x00000004
	  rdqos,                    // 0x00000008
	  pad1[(0x010-0x008-4)/4],
	  rddebug;                  // 0x00000010
        uint8_t
	  wrctrl,                   // 0x00000014
          pad2[3];
        uint32_t
	  wrissue,                  // 0x00000018
	  wrqos,                    // 0x0000001C
	  pad3[(0xe00-0x01c-4)/4],
	  i_sts,                    // 0x00000E00
	  i_en,                     // 0x00000E04
	  i_dis,                    // 0x00000E08
	  i_mask,                   // 0x00000E0C
	  pad4[(0xf04-0xe0c-4)/4],
	  control,                  // 0x00000F04
	  pad5[(0xf0c-0xf04-4)/4],
	  safety_chk,               // 0x00000F0C
	  pad6[(0x10000-0x00f0c-4)/4];
      };
#ifdef __cplusplus
    }
  }
}
#endif
#endif
