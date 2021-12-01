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
	S_AXI_HPX_FPD_ADDR   = 0xFD360000; // address of the first of all FPD AFIFMs

      const unsigned
	NUM_S_AXI_HPCS = 2,   // total of coherent
	NUM_S_AXI_HPNCS = 4,  // total of non-coherent
	NUM_S_AXI_HPXS = NUM_S_AXI_HPCS + NUM_S_AXI_HPNCS;   // total of all

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
      struct ALL_AFIFMS {
	struct AFIFM afifm[NUM_S_AXI_HPXS];
      };
      const char *afifmNames[] = { "HPC0", "HPC1", "HP0", "HP1", "HP2", "HP3" };

      const uint32_t SIOU_ADDR = 0xFD3D0000;
      struct SIOU {
	uint32_t
	  reg_ctrl, IR_STATUS, IR_MASK, IR_ENABLE,
	  IR_DISABLE,               // 0x10
	  pad0[(0x100-0x10-4)/4],
	  sata_misc_ctrl,           // 0x100
	  pad1[(0x410-0x100-4)/4],
	  crx_ctrl,                 // 0x410
	  pad2[(0x430-0x410-4)/4],
	  dp_stc_clkctrl;           // 0x430
      };
      const uint32_t IOU_SLCR_ADDR = 0xFF180000;
      struct IOU_SLCR_BANK {
	uint32_t ctrl0, ctrl1, ctrl3, ctrl4, ctrl5, ctrl6, status;
      };
      struct IOU_SLCR {
	uint32_t MIO_PIN[78];
	IOU_SLCR_BANK bank[3];
	uint32_t
	  pad0[(0x200 - 0x188 - 4)/4],
	  MIO_LOOPBACK, // 0x200
          MIO_MST_TRI[3],
	  pad1[(0x300 - 0x20C - 4)/4],
	  WDT_CLK_SEL,
	  CAN_MIO_CTRL,
	  GEM_CLK_CTRL,
	  SDIO_CLK_CTRL,
	  CTRL_REG_SD,
	  SD_ITAPDLY,
	  SD_OTAPDLYSEL,
	  SD_CONFIG_REG1,
	  SD_CONFIG_REG2,
	  SD_CONFIG_REG3,
	  SD_INITPRESET,
	  SD_DSPPRESET,
	  SD_HSPDPRESET,
	  SD_SDR12PRESET,
	  SD_SDR25PRESET,
	  SD_SDR50PRSET,
	  SD_SDR104PRST,
	  SD_DDR50PRESET,
	  pad2,
	  SD_MAXCUR1P8, // 0x34C
	  SD_MAXCUR3P0,
	  SD_MAXCUR3P3,
	  SD_DLL_CTRL,
	  SD_CDn_CTRL,
	  GEM_CTRL,
	  pad3[(0x380 - 0x360 - 4)/4],
	  IOU_TTC_APB_CLK, // 0x380
	  pad4[(0x390 - 0x380 - 4)/4],
	  IOU_TAPDLY_BYPASS, // 0x390
	  pad5[(0x400 - 0x390 - 4)/4],
	  IOU_COHERENT_CTRL, // 0x400
	  VIDEO_PSS_CLK_SEL,
	  IOU_INTERCONNECT_ROUTE,
	  pad6[(0x600 - 0x408 - 4)/4],
	  ctrl,
	  pad7[(0x700 - 0x600 - 4)/4],
	  isr,
	  imr,
	  ier,
	  idr,
	  itr; // 0x710
      };
      const uint32_t CRF_APB_ADDR = 0xFD1A0000;
      struct CRF_APB {
	uint32_t
	  ERR_CTRL, IR_STATUS, IR_MASK, IR_ENABLE, IR_DISABLE, pad0[2], CRF_WPROT,
	  APLL_CTRL, APLL_CFG, APLL_FRAC_CFG,
	  DPLL_CTRL, DPLL_CFG, DPLL_FRAC_CFG,
	  VPLL_CTRL, VPLL_CFG, VPLL_FRAC_CFG,
	  PLL_STATUS,
	  APLL_TO_LPD_CTRL,
	  DPLL_TO_LPD_CTRL,
	  VPLL_TO_LPD_CTRL,
	  pad1[(0x60 - 0x50 - 4)/4],
	  ACPU_CTRL, DBG_TRACE_CTRL, DBG_FPD_CTRL,
	  pad2[(0x70 - 0x68 - 4)/4],
	  DP_VIDEO_REF_CTRL, DP_AUDIO_REF_CTRL,
	  pad3[(0x7C - 0x74 - 4)/4],
	  DP_STC_REF_CTRL, DDR_CTRL, GPU_REF_CTRL,
	  pad4[(0xA0 - 0x84 - 4)/4],
	  SATA_REF_CTRL,
	  pad5[(0xB4 - 0xA0 - 4)/4],
	  PCIE_REF_CTRL, FPD_DMA_REF_CTRL, DPDMA_REF_CTRL, TOPSW_MAIN_CTRL, TOPSW_LSBUS_CTRL,
	  pad6[(0xF8 - 0xC4 - 4)/4],
	  DBG_TSTMP_CTRL,
	  pad7[(0x100 - 0xF8 - 4)/4],
	  RST_FPD_TOP, RST_FPD_APU, RST_DDR_SS;
      };
      const uint32_t CRL_APB_ADDR = 0xFF5E0000;
      struct CHKR {
	uint32_t CLKA_UPPER, CLKA_LOWER, CLKB_CNT, CTRL;
      };
      struct CRL_APB {
	uint32_t
	  ERR_CTRL, IR_STATUS, IR_MASK, IR_ENABLE, IR_DISABLE, pad0[2], CRF_WPROT,
	  IOPLL_CTRL, IOPLL_CFG, IOPLL_FRAC_CFG, pad1,
	  RPLL_CTRL, RPLL_CFG, RPLL_FRAC_CFG, pad2,
	  PLL_STATUS,
	  IOPLL_TO_FPD_CTRL,
	  RPLL_TO_FPD_CTRL,
	  USB3_DUAL_REF_CTRL, GEM_REF_CTL[4], USB_BUS_REF_CTRL[2], QSPI_REF_CTRL, SDIO_REF_CTRL[2],
	  UART_REF_CTRL[2], SPI_REF_CTRL[2], CAN_REF_CTRL[2], pad3, CPU_R5_CTRL, pad4[2], IOU_SWITCH_CTRL,
	  CSU_PLL_CTRL, PCAP_CTRL, LPD_SWITCH_CTRL, LPD_LSBUS_CTRL, DBG_LPD_CTRL, NAND_REF_CTRL,
	  LPD_DMA_REF_CTRL, pad5, PL_REF_CTRL[4],
	  PL0_THR_CTRL, PL0_THR_CNT,
	  PL1_THR_CTRL, PL1_THR_CNT,
	  PL2_THR_CTRL, PL2_THR_CNT,
	  PL3_THR_CTRL, PL3_THR_CNT, // PL3_THR_CNt is 0xFC in doc, but it must really be 0xEC...
	  pad6[(0x100 - 0xEC - 4)/4],
	  GEM_TSU_REF_CTRL, DLL_REF_CTRL, PSSYSMON_REF_CTRL,
	  pad7[(0x120 - 0x108 - 4)/4],
	  I2C0_REF_CTRL, I2C1_REF_CTRL, TIMESTAMP_REF_CTRL, pad8,
	  SAFETY_CHK,
	  pad9[(0x140 - 0x130 - 4)/4],
	  CLKMON_STATUS, CLKMON_MASK, CLKMON_ENABLE, CLKMON_DISABLE, CLKMON_TRIGGER,
	  pad10[(0x160 - 0x150 - 4)/4];
	CHKR chkr[8];
	uint32_t
          pad11[(0x200 - 0x1DC - 4)/4],
	  BOOT_MODE_USER, BOOT_MODE_POR,
	  pad12[(0x218 - 0x204 - 4)/4],
	  RESET_CTRL, BLOCKONLY_RST, RESET_REASON,
	  pad13[(0x230 - 0x220 - 4)/4],
	  RST_LPD_IOU0, RST_LPD_IOU1, RST_LPD_IOU2, // RST_LPD_IOU1 missing in doc?
 	  RST_LPD_TOP, RST_LPD_DBG,
	  pad14[(0x270 - 0x240 - 4)/4],
	  BANK3_CTRL[6],
	  BANK3_STATUS; // 0x288
      };
      const uint32_t
        APM_CCI_INTC_ADDR = 0xFD490000,
        APM_INTC_OCM_ADDR = 0xFFA00000,
        APM_LPD_FPD_ADDR  = 0xFFA10000;
      struct MCL {
	uint32_t pad, IR, RR, MCLER;
      };
      struct SMC {
	uint32_t SMCR, SIR, pad[2];
      };
      struct APM {
	uint32_t GCCR_H, GCCR_L,
	  pad0[(0x24 - 0x4 - 4)/4],
	  SIR, SICR, SISR, GIER, IER, ISR,
	  pad1[(0x44 - 0x38 - 4)/4],
	  MSR[2],
	  pad2[(0x100 - 0x48 - 4)/4];
	MCL mcl[8]; // starts at 0x100 including initial pad
	uint32_t pad3[(0x200 - 0x17c - 4)/4];
	SMC smc[8];
	uint32_t
	  pad4[(0x300 - 0x27c - 4)/4],
	  CR, WIDR, WIDMR, RIDR, RIDMR,
	  pad5[(0x400 - 0x310 - 4)/4],
	  FECR; // 0x400
      };
#ifdef __cplusplus
    }
  }
}
#endif
#endif
