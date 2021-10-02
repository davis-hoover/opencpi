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

 /*
  * This file contains support for the HDL device in the PL on the Xilinx Zynq platform.
  * On Zynq, the control plane is implemented using the M_AXI_GP0 or M_AXI_GP1 port, which
  * is located at physical address 0x4000000 or 0x80000000.
  * The data plane is implemented with the AXI_HP0-3 and other ports, acting
  * as bus masters only.
  */
#include <stdint.h>
#include <errno.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include "zlib.h"
#include "ocpi-config.h"
#include "OsFileSystem.hh"
#include "HdlZynq.h"
#include "HdlBusDriver.h"
#ifdef OCPI_OS_macos
#define mmap64 mmap
#define off64_t off_t
#endif

 namespace OCPI {
   namespace HDL {
     namespace Zynq {
       namespace OU = OCPI::Util;
       namespace OF = OCPI::OS::FileSystem;
       namespace OM = OCPI::HDL::ZynqMP;
       namespace OH = OCPI::HDL;

       const char
         fpgaMgrState[]  = "/sys/class/fpga_manager/fpga0/state",
       // fpgaMgrFlags[]  = "/sys/class/fpga_manager/fpga0/flags",
#if defined(OCPI_ARCH_aarch64)
       	 fpgaMgrDevice[] = "/pcap", // from /sys/firmware/devicetree/base/...
#else
       	 fpgaMgrDevice[] = "/amba/devcfg@f8007000", // from /sys/firmware/devicetree/base/...
#endif
	 xdevCfgState[]  = "/sys/class/xdevcfg/xdevcfg/device/prog_done",
	 xdevCfgDevice[] = "/dev/xdevcfg";
       class Device
	 : public OCPI::HDL::Device {
	 Driver  &m_driver;
	 uint8_t *m_vaddr;
	 bool     m_fpgaManager;
	 friend class Driver;
	 Device(Driver &driver, std::string &a_name, bool forLoad, const OU::PValue *params,
		std::string &err)
	   : OCPI::HDL::Device(a_name, "ocpi-dma-pio", params),
	     m_driver(driver), m_vaddr(NULL) {
	   m_isAlive = false;
	   m_endpointSize = sizeof(OccpSpace);
	   if (OF::exists(fpgaMgrState)) { // && OF::exists(fpgaMgrFirmware))
	     m_fpgaManager = true;
	     ocpiInfo("HDL Device %s will use the FPGA Manager linux kernel support (no %s)",
		      a_name.c_str(), fpgaMgrState);
	   } else if (OF::exists(xdevCfgState) && !::access(xdevCfgDevice, F_OK)) {
	     // need access() for char device
	     m_fpgaManager = false;
	     ocpiInfo("HDL Device %s will use the /dev/xdevcfg linux kernel support", a_name.c_str());
	   } else {
	     err = "FPGA support not present for Zynq PL, required files are missing";
	     return;
	   }
	   if (isProgrammed(err)) {
	     if (!forLoad)
	       init(err);
	   } else if (err.empty())
	       ocpiInfo("There is no bitstream loaded on this HDL device: %s", a_name.c_str());
	 }
	 ~Device() {
	   std::string ignore;
	   if (m_vaddr)
	     m_driver.unmap(m_vaddr, sizeof(OccpSpace), ignore);
	 }

	 bool
	 configure(ezxml_t config, std::string &err) {
	   // Any delayed setup-before-usage that can be deferred beyond discovery
	  const char *p = ezxml_cattr(config, "platform");
	  m_platform = p ? p : "zed"; // FIXME: is there any other automatic way for this?
	  // since we can't get at the real IDCODE yet
	  if (m_platform == "zcu102")
	    m_part = "xczu9eg";
	  else if (m_platform == "zcu111")
	    m_part = "xczu28dr";
	  else if (m_platform == "zcu104")
	    m_part = "xczu7ev";
	  else
	    m_part = "xczu9eg";
	  return OCPI::HDL::Device::configure(config, err);
	}
	bool
	init(std::string &err) {
	  ocpiDebug("Setting up the Zynq PL");
#if defined(OCPI_ARCH_aarch64) // not a great ultrascale test, but works for now
#if 0 // bus error due to the CSU being "secured"  Maybe we could do it in our kernel driver...
	  volatile OM::CSU *csu;
	  if (!(csu = (volatile OM::CSU*)m_driver.map(sizeof(*csu), OM::CSU_ADDR, err)))
	    return true;
	  uint32_t val = csu->IDCODE;;
	  ocpiDebug("Zynq Ultrascale IDCODE is 0x%x", val);
	  switch (val & ( UINT32_MAX >> 4)) {
	  case 0x4711093: m_part = "ZU3"; break;
	  case 0x4710093: m_part = "ZU4"; break;
	  case 0x4721093: m_part = "ZU5"; break;
	  case 0x4720093: m_part = "ZU6"; break;
	  case 0x4739093: m_part = "ZU7"; break;
	  case 0x4730093: m_part = "ZU9"; break;
	  case 0x4738093: m_part = "ZU11"; break;
	  case 0x4740093: m_part = "ZU15"; break;
	  case 0x4750093: m_part = "ZU17"; break;
	  case 0x4759093: m_part = "ZU19"; break;
	  case 0x4758093: m_part = "ZU21"; break;
	  case 0x47E1093: m_part = "ZU25"; break;
	  case 0x47E5093: m_part = "ZU27"; break;
	  case 0x47E4093: m_part = "ZU28"; break;
	  case 0x47E0093: m_part = "ZU29"; break;
	  default:
	    m_part = "ZUXXX";
	  }
	  m_driver.unmap((uint8_t *)csu, sizeof(*csu), err);
#endif
	  volatile uint32_t *reg;
	  if (!(reg = (volatile uint32_t *)m_driver.map(sizeof(uint32_t), OM::FPD_SLCR_AFI_FS_ADDR, err)))
	    return true;
#if 0
	  *reg = (1<<8) | (1 << 10);  // set gp0/1 to 64bit mode
#else
	  *reg = 0;  // set gp0/1 to 32bit mode
#endif
	  if (m_driver.unmap((uint8_t *)reg, sizeof(*reg), err))
	    return true;
	  volatile OM::ALL_AFIFMS *axi_hp;
	  if (!(axi_hp =
		(volatile OM::ALL_AFIFMS *)m_driver.map(sizeof(OM::ALL_AFIFMS), OM::S_AXI_HPX_FPD_ADDR, err)))
	    return true;
	  for (unsigned n = 0; n <  OM::NUM_S_AXI_HPNCS; n++) {
	    axi_hp->afifm[OM::NUM_S_AXI_HPCS + n].rdctrl = 0xB1; // set 64 bits wide
	    axi_hp->afifm[OM::NUM_S_AXI_HPCS + n].wrctrl = 0xB1;
	  }
	  if (m_driver.unmap((uint8_t *)axi_hp, sizeof(OM::ALL_AFIFMS), err))
	    return true;
#else
	  volatile SLCR *slcr = (volatile SLCR *)m_driver.map(sizeof(SLCR), SLCR_ADDR, err);
	  if (!slcr)
	    return true;
	  // We're not loaded, but fake as much stuff as possible.
	  switch ((slcr->pss_idcode >> 12) & 0x1f) {
	  case 0x02: m_part = "xc7z010"; break;
	  case 0x07: m_part = "xc7z020"; break;
	  case 0x0c: m_part = "xc7z030"; break;
	  case 0x11: m_part = "xc7z045"; break;
	  default:
	    m_part = "xc7zXXX";
	  }
	  ocpiDebug("Zynq SLCR PSS_IDCODE: 0x%x", slcr->pss_idcode);
	  if (m_driver.unmap((uint8_t *)slcr, sizeof(SLCR), err))
	    return true;
#endif
	  uint32_t cpAddr;
#if defined(OCPI_ARCH_aarch64)
	  // Pernaps we could use the ftm.gpi register if we needed to do the gp0/gp1 thing.
	  // Note:  for parts that have the VCU (H.264/5), this is actually wrong.
	  cpAddr = OM::M_HP0_PADDR;
#else
	  volatile FTM *ftm = (volatile FTM *)m_driver.map(sizeof(FTM), FTM_ADDR, err);
	  if (!ftm)
	    return true;
	  ocpiDebug("Debug register 3 from Zynq FTM is 0x%x", ftm->f2pdbg3);
	  // Find out whether the OpenCPI control plane is available at GP0 or GP1, GP0 first
	  bool useGP1 = (ftm->f2pdbg3 & 0x80) != 0;
	  ocpiCheck(!m_driver.unmap((uint8_t *)ftm, sizeof(FTM), err));
	  cpAddr = useGP1 ? GP1_PADDR : GP0_PADDR;
#endif
	  if ((m_vaddr && m_driver.unmap((uint8_t *)m_vaddr, sizeof(OccpSpace), err)) ||
	      !(m_vaddr = m_driver.map(sizeof(OccpSpace), cpAddr, err)))
	    return true;
	  ocpiDebug("Mapping for control plane %p", m_vaddr);
	  cAccess().setAccess(m_vaddr, NULL, OCPI_UTRUNCATE(RegisterOffset, 0));
	  if (OCPI::HDL::Device::init(err))
	    return true;
	  OU::format(m_endpointSpecific,
		     "ocpi-dma-pio:0x%" PRIx32 ".0x%" PRIx32 ".0x%" PRIx32,
		     cpAddr, 0, 0);
	  dAccess().setAccess(NULL, NULL, 0); // the data space will never be accessed by CPU
	  m_isAlive = true;
	  return false;
	}
        // return true if programmed, false if not programmed
        // when false, err may be set or not
        bool
        isProgrammed(std::string &err) {
	  const char *e, *file, *value;
	  if (m_fpgaManager) {
	    file = fpgaMgrState;
	    value = "operating";
	  } else {
	    file = xdevCfgState;
	    value = "1";
	  }
	  bool done = false;
	  std::string val;
	  if ((e = OU::file2String(val, file, '|')))
	    OU::format(err, "Could not retrieve FPGA status from \"%s\": %s", file, e);
	  else
	    done = val == value;
	  ocpiDebug("OCPI::HDL::Zynq::Device::isProgrammed: %s%s",
		    err.empty() ? (done ? "true" : "false") : "error: ", err.empty() ? "" : err.c_str());
	  return done;
        }
	bool
	isLoadedUUID(const std::string &uuid) {
	  static std::string dummy;
	  return isProgrammed(dummy) && OH::Device::isLoadedUUID(uuid);
	}
	bool getMetadata(std::vector<char> &xml, std::string &err) {
	  if (isProgrammed(err))
	    return OCPI::HDL::Device::getMetadata(xml, err);
	  if (err.empty())
	    OU::format(err,
		       "There is no bitstream loaded on this HDL device: %s", name().c_str());
	  return true;
	}
	// The zynq setup does not provide a slave interface to the DMA BRAM,
	// since the SDP is only attached as master to the S_AXI_HP ports.
	// Thus we only allow ActiveMessage since the SDP BRAMs are not memory mapped.
	// (M_AXI_GP0/1 is dedicated to the control plane).
	uint32_t dmaOptions(ezxml_t /*icImplXml*/, ezxml_t /*icInstXml*/, bool isProvider) {
	  return isProvider ?
	    (1 << OCPI::RDT::ActiveMessage) | (1 << OCPI::RDT::FlagIsMeta) :
	    (1 << OCPI::RDT::ActiveMessage) | (1 << OCPI::RDT::FlagIsMetaOptional);
	}

	// Scan the buffer and identify the start of the sync pattern
	// On zynq7000, you need 32 FFs in the preamble, but on zynqmp, you need 64
	static uint8_t *findsync(uint8_t *buf, size_t len) {
	  static uint8_t startup[] = {
#if defined(OCPI_ARCH_aarch64)
	    0xff, 0xff, 0xff, 0xff,
	    0xff, 0xff, 0xff, 0xff, 
	    0xff, 0xff, 0xff, 0xff,
	    0xff, 0xff, 0xff, 0xff, 
	    0xff, 0xff, 0xff, 0xff,
	    0xff, 0xff, 0xff, 0xff, 
	    0xff, 0xff, 0xff, 0xff,
	    0xff, 0xff, 0xff, 0xff, 
#endif
	    0xff, 0xff, 0xff, 0xff,
	    0xff, 0xff, 0xff, 0xff, 
	    0xff, 0xff, 0xff, 0xff,
	    0xff, 0xff, 0xff, 0xff, 
	    0xff, 0xff, 0xff, 0xff,
	    0xff, 0xff, 0xff, 0xff, 
	    0xff, 0xff, 0xff, 0xff,
	    0xff, 0xff, 0xff, 0xff, 
	    0x00, 0x00, 0x00, 0xbb,
	    0x11, 0x22, 0x00, 0x44,
	    0xff, 0xff, 0xff, 0xff, 
	    0xff, 0xff, 0xff, 0xff, 
	    0xaa, 0x99, 0x55, 0x66};
	  uint8_t *p8 = startup;
	  for (uint8_t *u8 = buf; u8 < buf + len; u8++)
	    if (*u8 == *p8++) {
	      if (p8 >= startup+sizeof(startup))
		return u8 + 1 - sizeof(startup);
	    } else {
	      p8 = startup;
	      if (*u8 == *p8) p8++;
	    }
	  return 0;
	}

	// Load a bitstream
	bool
	load(const char *fileName, std::string &error) {
	  ocpiDebug("Loading file \"%s\" on zynq FPGA, with the %s.", fileName,
		    m_fpgaManager ? "fpga manager" : "/dev/xdevcfg driver");
	  struct Xld {
            const size_t IBUFSZ;  // when reading compressed from the stream
            const size_t OBUFSZ; // when filling an in-memory buffer
	    int xfd, bfd;
	    gzFile gz;
	    uint8_t buf[8*1024];
	    int zerror;
	    size_t len;
	    std::string inputFile, outputFile;
	    bool useManager;
	    uint8_t *obase, *optr;  // used to buffer 
	    size_t olength, oleft;

	    void cleanup() { // used for constructor catch cleanup and in destructor
	      if (xfd >= 0) ::close(xfd);
	      if (bfd >= 0) ::close(bfd);
	      if (gz) gzclose(gz);
	      ::free(obase);
	    }

	    Xld(const char *file, bool fpgaManager, std::string &a_error)
	      : IBUFSZ(8*1024), OBUFSZ(64*1024), xfd(-1), bfd(-1), gz(NULL),
                inputFile(file), useManager(fpgaManager), obase(NULL),
                optr(NULL), olength(), oleft(0) {
	      // Open the device LAST since just opening it may do bad things
	      uint8_t *p8;
	      int n;
	      if ((bfd = ::open(file, O_RDONLY)) < 0)
		OU::format(a_error, "Can't open bitstream file '%s' for reading: %s(%d)",
			   file, strerror(errno), errno);
	      else if ((gz = ::gzdopen(bfd, "rb")) == NULL)
		OU::format(a_error, "Can't open compressed bitstream file '%s' for : %s(%u)",
			   file, strerror(errno), errno);
	      // Read up to the sync pattern before byte swapping
	      else if ((n = ::gzread(gz, buf, sizeof(buf))) <= 0)
		OU::format(a_error, "Error reading initial bitstream buffer: %s(%u/%d)",
			   gzerror(gz, &zerror), errno, n);
	      else if (!(p8 = findsync(buf, sizeof(buf)))) // this call is content-specific
		OU::format(a_error, "Can't find sync pattern in compressed bit file");
	      else {
		len = OCPI_SIZE_T_DIFF(buf + sizeof(buf), p8);
		if (p8 != buf)
		  memmove(buf, p8, len);
		// We've done as much as we can before opening the device, which
		// does bad things to the Zynq PL (i.e. causes an "unload")
		if (useManager)
		  outputFile = OCPI_DRIVER_MEM;
		else // use original/old Xilinx loading device driver, pre-fpga manager
		  outputFile = xdevCfgDevice;
		if ((xfd = ::open(outputFile.c_str(), O_RDWR)) < 0)
		  OU::format(a_error, "Can't open %s for bitstream loading: %s(%d)",
			     outputFile.c_str(), strerror(errno), errno);
	      }
	    }
	    ~Xld() {
	      cleanup();
	    }
	    int gzread(uint8_t *&argBuf, std::string &a_error) {
	      int n;
	      if ((n = ::gzread(gz, buf + len, (unsigned)(sizeof(buf) - len))) < 0)
		OU::format(a_error, "Error reading compressed bitstream: %s(%u/%d)",
			   gzerror(gz, &zerror), errno, n);
	      else {
		n += OCPI_UTRUNCATE(int, len);
		len = 0;
		argBuf = buf;
	      }
	      return n;
	    }
	    uint32_t readConfigReg(unsigned /*reg*/) {
	      // write the "read config register" frame.
	      // read back the value
	      return 0;
	    }
	    bool // return true on error
	    copy(std::string &error) {
	      do {
		uint8_t *l_buf;
		int r = gzread(l_buf, error);
		if (r < 0)
		  return true;
		size_t n = (size_t)r;
		if (n & 3)
		  return OU::eformat(error, "Bitstream data in is '%s' not a multiple of 4 bytes",
				     inputFile.c_str());
		if (n == 0)
		  break;
		uint32_t *p32 = (uint32_t*)l_buf;
		for (size_t nn = n; nn; nn -= 4, p32++)
		  *p32 = OU::swap32(*p32); // part of bit-to-bin conversion
		if (useManager) { // fill a contiguous buffer.  ostringstream and vector were worse than this.
		  if (oleft < n) {
		    size_t used = OCPI_SIZE_T_DIFF(optr, obase);
		    obase = (uint8_t *)::realloc(obase, olength += OBUFSZ);
		    oleft += OBUFSZ;
		    optr = obase + used;
		  }
		  memcpy(optr, l_buf, n);
		  optr += n, oleft -= n;
		} else if (::write(xfd, l_buf, n) <= 0)
		  return OU::eformat(error,
				     "Error writing to %s for bitstream loading: %s(%u/%zu)",
				     outputFile.c_str(), strerror(errno), errno, n);
	      } while (1);
	      if (useManager) {
		ocpi_load_fpga_request_t request;
		request.data = obase;
		request.length = OCPI_UTRUNCATE(ocpi_size_t, optr - obase);
		//int fd = creat("bits", 0666); write(fd, obase, request.length); close(fd);
		strncpy(request.device_path, fpgaMgrDevice, sizeof(request.device_path));
		ocpiInfo("Loading using FPGA manager, %u bytes uncompressed from %s",
			 request.length, inputFile.c_str());
		if (ioctl(xfd, OCPI_CMD_LOAD_FPGA, &request))
		  return OU::eformat(error, "Error loading fpga: %s(%u)", strerror(errno), errno);
	      }
	      if (::close(xfd))
		return OU::eformat(error, "Error closing %s: %s(%u)",
				   outputFile.c_str(), strerror(errno), errno);
	      xfd = -1;
	      return false;
	    }
	  };  // end struct Xld

	  Xld xld(fileName, m_fpgaManager, error);
	  if (!error.empty() || xld.copy(error))
	    return true;
	  ocpiDebug("Loading complete, testing for programming done and initialization");
	  return isProgrammed(error) ? init(error) : true;
#if 0
	  // We have written all the data from the file to the device.
	  // Now we can retrieve status registers
	  const uint32_t
	    c_opencpi = 0xdd9fda7a,
	    c_statmask = 0x12345678,
	    c_statvalue = 0x12345678;
	  uint32_t
	    stat = xld.readConfigReg(7),
	    axss = xld.readConfigReg(9);
	  // Check stat for good value
	  if ((stat & c_statmask) != c_statvalue)
	    throw OU::Error("After loading, the configuration status register was 0x%x,"
			    " but should be 0x%x (masked with 0x%x)",
			    stat, c_statvalue, c_statmask);
	  // Check axss for our special value 0xdd9fda7a
	  if (axss != c_opencpi)
	    throw OU::Error("After loading, the USR_ACCESS code was not correct: 0x%x - should be 0x%x",
			    axss, c_opencpi);
#endif
	}
	bool
	unload(std::string &error) {
	  ocpiDebug("Trying to unload Zynq bitstream from %s", m_name.c_str());
	  int xfd;
	  if (m_fpgaManager) {
	    if ((xfd = ::open(OCPI_DRIVER_MEM, O_RDWR)) < 0)
	      return OU::eformat(error, "Can't open %s for bitstream unloading: %s(%d)", OCPI_DRIVER_MEM,
				 strerror(errno), errno);
	    ocpi_load_fpga_request_t request;
	    request.data = (uint8_t*)"bad";
	    request.length = 4;
	    strncpy(request.device_path, fpgaMgrDevice, sizeof(request.device_path));
	    ioctl(xfd, OCPI_CMD_LOAD_FPGA, &request);
	    // could check for wrong state here...
	  } else if ((xfd = ::open("/dev/xdevcfg", O_WRONLY)) < 0)
	    return OU::eformat(error, "Can't open /dev/xdevcfg for bitstream unloading: %s(%d)",
			       strerror(errno), errno);
	  close(xfd);
	  return false;
	}
      }; // end class Device

      Driver::
      Driver()
	: m_memFd(-1) {
      }
      Driver::
      ~Driver() {
	if (m_memFd >= 0)
	  ::close(m_memFd);
      }

      unsigned Driver::
      search(const OU::PValue *params, const char **exclude, bool discoveryOnly,
	     std::string &error) {
	// Opening implies canonicalizing the name, which is needed for excludes
	ocpiInfo("Searching for local Zynq/PL HDL device.");
	OCPI::HDL::Device *dev = open("0", false, params, error);
	return dev && !found(*dev, exclude, discoveryOnly, error) ? 1 : 0;
      }

      OCPI::HDL::Device *Driver::
      open(const char *busName, bool forLoad, const OU::PValue *params, std::string &error) {
	(void)params;
	std::string name("PL:");
	name += busName;
#if defined(OCPI_ARCH_arm) || defined(OCPI_ARCH_arm_cs) || defined(OCPI_ARCH_aarch32) || defined(OCPI_ARCH_aarch64)
	Device *dev = new Device(*this, name, forLoad, params, error);
	if (error.empty())
	  return dev;
	delete dev;
	ocpiInfo("When searching for PL device '%s': %s", busName, error.c_str());
#else
	(void)forLoad;
	error.clear();
#endif
	return NULL;
      }
      uint8_t *Driver::
      map(size_t size, uint32_t offset, std::string &error) {
	void *vaddr;
	off64_t off64 = offset;
	ocpiDebug("Zynq map of offset %" PRIx32 " off64 %" PRIx64 " size %zu",
		  offset, off64, size);
	if (m_memFd < 0 && (m_memFd = ::open("/dev/mem", O_RDWR|O_SYNC)) < 0)
	  error = "Can't open /dev/mem, forgot to load the driver? sudo?";
	else if ((vaddr = mmap64(NULL, size, PROT_READ|PROT_WRITE, MAP_SHARED, m_memFd,
				 off64)) == MAP_FAILED)
	  OU::format(error, "can't mmap /dev/mem: %s(%d)", strerror(errno), errno);
	else {
	  ocpiDebug("Zynq map returns %p", vaddr);
	  return (uint8_t*)vaddr;
	}
	return NULL;
      }
       bool Driver::
       unmap(uint8_t *addr, size_t size, std::string &error) {
	 ocpiDebug("Zynq unmap %p %zu", addr, size);
	 if (m_memFd < 0)
	   error = "Memory device not open for unmap";
	 else if (munmap(static_cast<void*>(addr), size) != 0)
	   OU::format(error, "unmap failure, %s", strerror(errno));
	 else
	   return false;
	 return true;
       }
    } // namespace BUS
  } // namespace HDL
} // namespace OCPI
