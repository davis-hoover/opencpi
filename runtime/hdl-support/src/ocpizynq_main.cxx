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

#define OCPI_OPTIONS_HELP \
  "Usage syntax is: ocpizynq [options] <command>\n" \
  "  Commands are:\n" \
  "    clocks  - print how the clocks are configured\n" \
  "    axi_hp   - print how the axi_hp interfaces are configured\n" \
  "    spi      - print how the spi interfaces are configured\n"

//          name      abbrev  type    value description
#define OCPI_OPTIONS \
  CMD_OPTION  (psclk,     p,    Double,   "33.3333e6", "Frequency of the PS_CLK clock into the Zync SoC") \

#include <stddef.h>
#include <stdint.h>
#include <stddef.h>
#include <unistd.h>
#include <sys/mman.h>
#include <time.h>
#include "ocpi-config.h"
#include "OcpiUtilMisc.h"
#include "CmdOption.hh"
#include "HdlZynq.h"

namespace OU = OCPI::Util;
namespace OM = OCPI::HDL::ZynqMP;
using namespace OCPI::HDL::Zynq;

struct PLL {
  const char *name;
  uint32_t ctrl, cfg, fdiv;
  PLL(const char *a_name, uint32_t a_ctrl, uint32_t a_cfg)
    : name(a_name), ctrl(a_ctrl), cfg(a_cfg), fdiv((ctrl >> 12) & 0x7f) {
    bool bpmode = ((ctrl >> 3) & 1) != 0;
    printf("%3s PLL: FDIV: %u, bypass mode: %s, bypass status: %s,"
	   " power: %s, reset: %s\n",
	   name, fdiv,  bpmode ? "pin" : "reg",
	   (ctrl >> 4)&1 ? "bypassed" : (bpmode ? "pin" : "enabled"),
	   ctrl & 2 ? "off" : "on", ctrl & 1 ? "asserted" : "deasserted");
  }
  double freq(double psclk) { return psclk * fdiv; }
};

static uint8_t *
map(size_t addr, size_t arg_size) {
  static int fd = -1;
  if (fd < 0 &&
      (fd = open("/dev/mem", O_RDWR|O_SYNC)) < 0) {
    perror("opening /dev/mem") ;
    return NULL ;
  }
  size_t
    pagesize = (size_t)getpagesize(),
    base = addr & ~(pagesize - 1),
    size = OU::roundUp(addr + arg_size - base, pagesize);
  void *ptr = mmap(NULL, size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, (off_t)base);
  if (ptr == MAP_FAILED) {
    perror("mapping /dev/mem");
    return NULL;
  }
  return ((uint8_t*)ptr) + (addr - base);
}

void
print_spi_idx_msg(unsigned idx, const char* msg, ...) {
  va_list arg;
  va_start(arg, msg);
  printf("SPI%u: ", idx);
  vfprintf(stdout, msg, arg);
  va_end(arg);
}


static void
doPLL(const char *name, uint32_t control) {
  const char *clks[] = { "PS", "PS", "PS", "PS", "VIDEO", "ALT", "AUX", "GT" };
  printf("For PLL %s control 0x%x pre clk is %s_REF_CLK and post clk is %s_REF_CLK\n",
	 name, control, clks[(control >> 20) & 7], clks[(control >> 24) & 7]);
  printf("    div2 %u feedback %u bypass %u reset %u\n",
	 (control >> 16) & 1, (control >> 8) & 0x7f, (control >> 3) & 1, control & 1);
}
static void
doFclk(unsigned n, uint32_t control) {
  const char *plls[] = { "IOPLL", "Unexpected==1", "RPLL", "DPLL_CLK_TO_LPD" };
  printf("For FCLK%u enable %u div1 %u div0 %u src %s\n", n,
	 (control >> 24) & 1, (control >> 16) & 0x3f, (control >> 8) & 0x3f,
	 plls[control & 3]);
}
int
mymain(const char **argv) {
#if !defined(OCPI_ARCH_arm) && !defined(OCPI_ARCH_arm_cs) && !defined(OCPI_ARCH_aarch32) && !defined(OCPI_ARCH_aarch64)
  options.bad("This program is only functional on Zynq/Arm platforms");
#endif
  std::string cmd = argv[0]; // ensured valid by caller
  if (cmd == "test")
    printf("testing\n");
  else if (cmd == "clocks") {
#if defined(OCPI_ARCH_aarch64)
    // Clocking sources (10):
    // 4 Periperal input clocks: PCIe/USB, DIsplayPort, SATA, SGMII
    // 1 Internal AUX_REF_CLK from PL
    // 5 Input pins: are PS_REF_CLK, and MIO 28/51/27/50
    // Muxed down to 5 inputs outside the PLLs, to each of the 5 System PLLs, so the 5 clocks to all PLLs are:
    // 1 of the peripheral cocks (SIOU.CRX_CTRL/REFCLK_SEL)
    // 1 Internal AUX_REF_CLK
    // 1 PS_REF_CLK
    // 1 Choose between MIO28 and MIO 51 (PSS_ALT_CLK)
    // 1 Choose between MIO27 and MIO 50 (VIDEO_PSS_CLK_SEL)
    // Each system PLL can choose among 5 a bypass clock and a through-the-pll clk and then select which is output
    // Called: RPLL, IOPL, APLL, DPLL, VPLL
    auto siou = (volatile OM::SIOU *)map(OM::SIOU_ADDR, sizeof(OM::SIOU));
    if (!siou)
      options.bad("cannot map SIOU");
    printf("Dumping SIOU:\n");
    printf("SIOU: reg_ctrl 0x%x IR_STATUS 0x%x IR_MASK 0x%x IR_ENABLE 0x%x IR_DISABLE 0x%x\n",
	   siou->reg_ctrl, siou->IR_STATUS, siou->IR_MASK, siou->IR_ENABLE, siou->IR_DISABLE);
    printf("SIOU: sata_misc_ctrl 0x%x crx_ctrl 0x%x dp_stc_clkctrl 0x%x\n",
	   siou->sata_misc_ctrl, siou->crx_ctrl, siou->dp_stc_clkctrl);
    const char *gtr_sources[] = { "PCIe/USB", "DisplayPort", "SATA", "SGMII" };
    printf("SIOU: GTR_REF_CLK source is %s\n", gtr_sources[siou->crx_ctrl & 3]);
    printf("SIOU: check %zx\n", offsetof(OM::SIOU, dp_stc_clkctrl));
    auto iou_slcr = (volatile OM::IOU_SLCR *)map(OM::IOU_SLCR_ADDR, sizeof(OM::IOU_SLCR));
    uint32_t vpcs = iou_slcr->VIDEO_PSS_CLK_SEL;
    printf("IOU_SLCR: VIDEO_PSS_CLK_SEL 0x%x MIO[27] 0x%x MIO[28] 0x%x MIO[50] 0x%x MIO[15] 0x%x\n",
	   vpcs, iou_slcr->MIO_PIN[27], iou_slcr->MIO_PIN[28], iou_slcr->MIO_PIN[50], iou_slcr->MIO_PIN[51]);
	   printf("IOU_SLCR: VIDEO_CLK source is: %s\n", vpcs & 1 ? "MIO[50]" : "MIO[27]");
    printf("IOU_SLCR: PSS_ALT_CLK source is: %s\n", vpcs & 2 ? "MIO[51]" : "MIO[28]");
    printf("IOU_SLCR: check %zx\n", offsetof(OM::IOU_SLCR, itr));
    auto crf_apb = (volatile OM::CRF_APB *)map(OM::CRF_APB_ADDR, sizeof(OM::CRF_APB));
    printf("CRF_APB: check %zx\n", offsetof(OM::CRF_APB, RST_DDR_SS));
    doPLL("APLL", crf_apb->APLL_CTRL);
    doPLL("DPLL", crf_apb->DPLL_CTRL);
    doPLL("VPLL", crf_apb->VPLL_CTRL);
    auto crl_apb = (volatile OM::CRL_APB *)map(OM::CRL_APB_ADDR, sizeof(OM::CRL_APB));
    doPLL("IOPLL", crl_apb->IOPLL_CTRL);
    doPLL("RPLL", crl_apb->RPLL_CTRL);
    printf("CRL_APB: check %zx\n", offsetof(OM::CRL_APB, BANK3_STATUS));
    uint32_t acpu_ctrl = crf_apb->ACPU_CTRL;
    const char *aclks[] = { "APLL", "Unexpected==1", "DPLL", "VPLL" };
    printf("ACPU Clock: half %u full %u divisor %u source is %s\n",
	   (acpu_ctrl >> 25) & 1, (acpu_ctrl >> 24) & 1, (acpu_ctrl >> 8) & 0x3f,
	   aclks[acpu_ctrl & 3]);
    for (unsigned n = 0; n < 4; n++)
      doFclk(0, crl_apb->PL_REF_CTRL[n]);
    auto cci_intc = (volatile OM::APM *)map(OM::APM_INTC_OCM_ADDR, sizeof(OM::APM));
    printf("CCI_INTC_APM: check %zx\n", offsetof(OM::APM, FECR));
    uint32_t 
      l0 = *(volatile uint32_t *)cci_intc->GCCR_L,
      h0 = *(volatile uint32_t *)cci_intc->GCCR_H;
    sleep(1);
    uint32_t 
      l1 = *(volatile uint32_t *)cci_intc->GCCR_L,
      h1 = *(volatile uint32_t *)cci_intc->GCCR_H;
    printf("TIME 0x%08x%08x 0x%08x%08x\n", h0, l0, h1, l0);
    options.bad("clocks command not implemented on zynq ultrascale");
#endif
    volatile FTM *ftm = (volatile FTM *)map(FTM_ADDR, sizeof(FTM));
    if (!ftm)
      return 1;
    volatile SLCR *slcr = (volatile SLCR *)map(SLCR_ADDR, sizeof(SLCR));
    if (!slcr)
      return 1;
    printf("ftm: glbctrl 0x%x status 0x%x control 0x%x cycountpre 0x%x synccount 0x%x "
	   "itcyccount 0x%x lock_status 0x%x lock_access 0x%x\n",
	   ftm->glbctrl, ftm->status, ftm->control, ftm->cycountpre, ftm->synccount,
	   ftm->itcyccount, ftm->lock_status, ftm->lock_access);
    ftm->lock_access = 0xc5acce55; // unlock the FTM
    ftm->glbctrl = 1;              // enable the FTM
    ftm->control = 4;              // enable cycle count packets, no trace packets
    ftm->lock_access = 0;          // relock
#ifdef OCPI_OS_macos
    uint32_t t0 = 0;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    ts.tv_sec++;
    uint32_t t0 = ftm->itcyccount;  // capture t0
    clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts, NULL);
#endif
    uint32_t t1 = ftm->itcyccount;  // capture t1
    double freq = (t1 - t0)/2.;
    freq *= slcr->clk_621_true & 1 ? 6 : 4;
    uint32_t ctrl = slcr->arm_clk_ctrl;
    PLL
      arm("ARM", slcr->arm_pll_ctrl, slcr->arm_pll_cfg),
      ddr("DDR", slcr->ddr_pll_ctrl, slcr->ddr_pll_cfg),
      io("IO", slcr->io_pll_ctrl, slcr->io_pll_cfg),
      &pll = ((ctrl & 0x30) >> 4) == 2 ? ddr :
             ((ctrl & 0x30) >> 4) == 3 ? io : arm;
    uint32_t divisor = (ctrl >> 8) & 0x3f;
    double pssclk = (freq * divisor) / pll.fdiv;
    printf("Apparent CPU frequency is:~ %4.2f\n", (freq + 5000.)/1000000.);
    printf("Apparent PSCLK frequency is: %4.2f\n", (pssclk + 5000.)/1000000.);
    printf("Apparent PLL frequencies are: ARM: %4.2f, DDR: %4.2f, IO: %4.2f\n",
	   (arm.freq(pssclk) + 5000.)/1000000.,
	   (ddr.freq(pssclk) + 5000.)/1000000.,
	   (io.freq(pssclk) + 5000.)/1000000.);
    bool x6 = (slcr->clk_621_true & 1) != 0;
    double topfreq = pll.freq(pssclk) / divisor;
    double
      x1 = topfreq / (x6 ? 6 : 4),
      x2 = x1 * 2,
      x3x2 = x1 * (x6 ? 3 : 2);
    printf("ARM CPU Clocks: source: %s, mode: %s, divisor: %u, freq: %4.2f MHz\n",
	   pll.name, x6 ? "6:3:2:1" : "4:2:2:1", divisor,
	   (topfreq + 5000.) / 1000000);
    printf("  Enabled: peri: %s, 1x: %s %4.2f, 2x: %s %4.2f, 3x2x: %s %4.2f, 6x4x: %s %4.2f\n",
	   (ctrl & (1 << 28)) ? "on" : "off",
	   (ctrl & (1 << 27)) ? "on" : "off",
	   (x1 + 5000.)/1000000.,
	   (ctrl & (1 << 26)) ? "on" : "off",
	   (x2 + 5000.)/1000000.,
	   (ctrl & (1 << 25)) ? "on" : "off",
	   (x3x2 + 5000.)/1000000.,
	   (ctrl & (1 << 24)) ? "on" : "off",
	   (topfreq + 5000.)/1000000.);
    volatile FCLK *fp = slcr->fpga;
    for (unsigned n = 0; n < NFCLKS; n++, fp++) {
      volatile FCLK f = *(FCLK*)fp;
      //    printf("%u %p %08x %08x %08x %08x\n", n, fp,
      //	   f.clk_ctrl, fp->thr_ctrl, fp->thr_count, fp->thr_sta);
      PLL &fpll =
	((f.clk_ctrl & 0x30) >> 4) == 2 ? arm :
	((f.clk_ctrl & 0x30) >> 4) == 3 ? ddr : io;
      uint32_t
	divisor0 = (f.clk_ctrl >> 8) & 0x3f,
	divisor1 = (f.clk_ctrl >> 20) & 0x3f;

      printf("FCLK %u: source: %s PLL, divisor0: %2u, divisor1: %2u",
	     n, fpll.name, divisor0, divisor1);
      printf(", throttling %sreset, throttling %sstarted",
	     f.thr_ctrl & 2 ? "is " : "not ", f.thr_ctrl & 1 ? "is " : "not ");
      if (f.thr_count & 0xffff)
	printf(", last count: %u", f.thr_count & 0xffff);
      printf(", mode: %s", f.thr_sta & 0x10000 ? "debug/static" : "stopped/normal");
      if (f.thr_sta & 0xffff)
	printf(", current count: %u", f.thr_sta & 0xffff);
      printf(", frequency: %4.2f MHz\n",
	     ((((options.psclk() * fpll.fdiv) / divisor0 ) / divisor1) + 5000) / 1000000.);
    }
  } else if (cmd == "axi_hp") {
#if defined(OCPI_ARCH_aarch64)
    volatile uint32_t *reg = (volatile uint32_t *)map(OM::FPD_SLCR_AFI_FS_ADDR, sizeof(uint32_t));
    printf("SLCR: 0x%x\n", *reg);
    volatile OM::ALL_AFIFMS *axi_hp =
      (volatile OM::ALL_AFIFMS *)map(OM::S_AXI_HPX_FPD_ADDR, sizeof(OM::ALL_AFIFMS));
    volatile OM::AFIFM *afifm = axi_hp->afifm;
    for (unsigned n = 0; n < OM::NUM_S_AXI_HPXS; n++, afifm++) {
      printf("%.10s: rdctrl: 0x%x rdissue: 0x%x rdqos: 0x%x rddebug: 0x%x\n",
	     OM::afifmNames[n], afifm->rdctrl, afifm->rdissue, afifm->rdqos, afifm->rddebug);
      printf("        : wrctrl: 0x%x wrissue: 0x%x wrqos: 0x%x\n",
	     afifm->wrctrl, afifm->wrissue, afifm->wrqos);
      printf("        :  i_sts: 0x%x i_en: 0x%x i_dis: 0x%x i_mask: 0x%x control: 0x%x safety_chk 0x%x\n",
	     afifm->i_sts, afifm->i_en, afifm->i_dis, afifm->i_mask, afifm->control, afifm->safety_chk);
    }
#else
    struct AFI {
      uint32_t
        rdchan_ctrl,
        rdchan_issuingcap,
        rdqos,
        rddatafifo_level,
        rddebug,
        wrchan_ctrl,
        wrchan_issuingcap,
        wrqos,
        wrdatafifo_level,
        wrdebug,
        pad[(0x1000 - 0x24 - 4)/4];
    };
    const unsigned NAXI_HPS = 4;
    struct AXI_HP {
      AFI afi[NAXI_HPS];
    };
    const uint32_t AXI_HP_ADDR = 0xf8008000;
    volatile AXI_HP *axi_hp = (volatile AXI_HP *)map(AXI_HP_ADDR, sizeof(AXI_HP));
    if (!axi_hp)
      return 1;
    volatile AFI *afi = axi_hp->afi;
    printf("AXI_HP_ADDR 0x%x axi_hp 0x%p afi 0x%p\n", AXI_HP_ADDR, axi_hp, afi);
    sleep(10);
    for (unsigned n = 0; n < NAXI_HPS; n++, afi++) {
#if 1
      printf("AXI_HP %u: rdctrl: 0x%x rdissue: 0x%x rdqos: 0x%x rdfifo: <unread> rddebug: 0x%x\n",
	     n, afi->rdchan_ctrl, afi->rdchan_issuingcap, afi->rdqos,
	     /*afi->rddatafifo_level,*/ afi->rddebug);
      printf("        : wrctrl: 0x%x wrissue: 0x%x wrqos: 0x%x wrfifo: <unread> wrdebug: 0x%x\n",
	     afi->wrchan_ctrl, afi->wrchan_issuingcap, afi->wrqos, /*afi->wrdatafifo_level,*/
	     afi->wrdebug);
#else
      printf("AXI_HP %u: rdctrl: 0x%x rdissue: 0x%x rdqos: 0x%x rdfifo: 0x%x rddebug: 0x%x\n",
	     n, afi->rdchan_ctrl, afi->rdchan_issuingcap, afi->rdqos, afi->rddatafifo_level, 0);
#endif
      sleep(1);
    }
#endif
  } else if (cmd == "devcfg") {
    const uint32_t DEVCFG_ADDR = 0xF8007000;
    struct DEVCFG {
      uint32_t
        ctrl,
	lock,
	cfg,
	int_sts,
	int_mask,
	status,
	dma_src_addr,
	dma_dst_addr,
	dma_src_len,
	dma_dest_len,
	rom_shadow,
	multiboot_addr,
	sw_id,
	unlock,
	mctrl,
	xadcif_cfg,
	xadcif_int_sts,
	xadcif_int_mask,
	xadcif_msts,
	xadcif_cmdfifo,
	xadcif_rdfifo,
	xadcif_mctl;
    };
    volatile DEVCFG *devcfg = (volatile DEVCFG *)map(DEVCFG_ADDR, sizeof(DEVCFG));
    printf("ctrl 0x%x lock 0x%x cfg 0x%x int_sts 0x%x int_mask 0x%x status 0x%x\n",
	   devcfg->ctrl, devcfg->lock, devcfg->cfg, devcfg->int_sts, devcfg->int_mask, devcfg->status);
  } else if (cmd == "spi") {
    struct SPI_ARRAY {
      SPI spi[NSPIS];
    };
    volatile SPI_ARRAY *spi_array= (volatile SPI_ARRAY *)map(SPI_ADDR, sizeof(SPI_ARRAY));
    volatile SPI *spi = spi_array->spi;
    for (unsigned n = 0; n < NSPIS; n++, spi++) {
      print_spi_idx_msg(n, "SPI Configuration: 0x%x\n", spi->cr_offset);
      print_spi_idx_msg(n, "SPI Interrupt Status: 0x%x\n", spi->sr_offset);
      print_spi_idx_msg(n, "Interrupt Enable: 0x%x\n", spi->ier_offset);
      print_spi_idx_msg(n, "Interrupt disable: 0x%x\n", spi->idr_offset);
      print_spi_idx_msg(n, "Interrupt mask: 0x%x\n", spi->imr_offset);
      print_spi_idx_msg(n, "SPI Controller Enable: 0x%x\n", spi->er_offset);
      print_spi_idx_msg(n, "Delay Control: 0x%x\n", spi->dr_offset);
      print_spi_idx_msg(n, "Slave Idle Count: 0x%x\n", spi->sicr_offset);
      print_spi_idx_msg(n, "TX_FIFO Threshold: 0x%x\n", spi->txwr_offset);
      print_spi_idx_msg(n, "RX_FIFO Threshold: 0x%x\n", spi->rx_thresh_reg0);
      print_spi_idx_msg(n, "Module ID: 0x%x\n", spi->mod_id_reg0);
    }
  }
  return 0;
}
