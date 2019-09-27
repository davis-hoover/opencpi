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
#include "OcpiOsFileSystem.h"
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

       const char
         fpgaMgrState[] =    "/sys/class/fpga_manager/fpga0/state",
	 fpgaMgrFlags[] =    "/sys/class/fpga_manager/fpga0/flags",
       	 fpgaMgrDevice[] =      "/amba/devcfg@f8007000", // from /sys/firmware/devicetree/base/...
       // fpgaMgrDir[] =      "/lib/firmware",
       // fpgaMgrFirmware[] = "/sys/class/fpga_manager/fpga0/firmware",
	 xdevCfgState[] =    "/sys/class/xdevcfg/xdevcfg/device/prog_done",
	 xdevCfgDevice[] =   "/dev/xdevcfg";
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
	   if (OF::exists(fpgaMgrState)) // && OF::exists(fpgaMgrFirmware))
	     m_fpgaManager = true;
	   else if (OF::exists(xdevCfgState) && !::access(xdevCfgDevice, F_OK)) // need access() for char device
	     m_fpgaManager = false;
	   else {
	     err = "FPGA support not present for Zynq PL, required files are missing";
	     return;
	   }
	   if (isProgrammed(err)) {
	     if (init(err)) {
	       if (forLoad)
		 err.clear();
	     }
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
	   if (!m_isAlive) {
	     volatile SLCR *slcr =
	       (volatile SLCR *)m_driver.map(sizeof(SLCR), SLCR_ADDR, err);
	     if (!slcr)
	       return true;
	     // We're not loaded, but fake as much stuff as possible.
	     const char *p = ezxml_cattr(config, "platform");
	     m_platform = p ? p : "zed"; // FIXME: is there any other automatic way for this?
	     switch ((slcr->pss_idcode >> 12) & 0x1f) {
	     case 0x02: m_part = "xc7z010"; break;
	     case 0x07: m_part = "xc7z020"; break;
	     case 0x0c: m_part = "xc7z030"; break;
	     case 0x11: m_part = "xc7z045"; break;
	     default:
	       m_part = "xc7zXXX";
	     }
	     ocpiDebug("Zynq SLCR PSS_IDCODE: 0x%x", slcr->pss_idcode);
	     return m_driver.unmap((uint8_t *)slcr, sizeof(SLCR), err);
	   }
	  return OCPI::HDL::Device::configure(config, err);
	}
	bool
	init(std::string &err) {
	  ocpiDebug("Setting up the Zynq PL");
	  volatile FTM *ftm = (volatile FTM *)m_driver.map(sizeof(FTM), FTM_ADDR, err);
	  if (!ftm)
	    return true;
	  ocpiDebug("Debug register 3 from Zynq FTM is 0x%x", ftm->f2pdbg3);
	  // Find out whether the OpenCPI control plane is available at GP0 or GP1, GP0 first
	  bool useGP1 = (ftm->f2pdbg3 & 0x80) != 0;
	  uint32_t gpAddr = useGP1 ? GP1_PADDR : GP0_PADDR;
	  if (m_driver.unmap((uint8_t *)ftm, sizeof(FTM), err) ||
	      (m_vaddr && m_driver.unmap((uint8_t *)m_vaddr, sizeof(OccpSpace), err)) ||
	      !(m_vaddr = m_driver.map(sizeof(OccpSpace), gpAddr, err)))
	    return true;
	  ocpiDebug("Mapping for GP%c at %p", useGP1 ? '1' : '0', m_vaddr);
	  cAccess().setAccess(m_vaddr, NULL, OCPI_UTRUNCATE(RegisterOffset, 0));
	  if (OCPI::HDL::Device::init(err))
	    return true;
	  OU::format(m_endpointSpecific,
		     "ocpi-dma-pio:0x%" PRIx32 ".0x%" PRIx32 ".0x%" PRIx32,
		     gpAddr, 0, 0);
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
	static uint8_t *findsync(uint8_t *buf, size_t len) {
	  static uint8_t startup[] = {
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
	    const size_t IBUFSZ = 8*1024;  // when reading compressed from the stream
	    const size_t OBUFSZ = 64*1024; // when filling an in-memory buffer
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
	    }
	    Xld(const char *file, bool fpgaManager, std::string &a_error)
	      : xfd(-1), bfd(-1), gz(NULL), inputFile(file), useManager(fpgaManager), obase(NULL), optr(NULL),
		olength(), oleft(0) {
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
		strncpy(request.device_path, fpgaMgrDevice, sizeof(request.device_path));
		if (ioctl(xfd, OCPI_CMD_LOAD_FPGA, &request))
		  return OU::eformat(error, "Error loading fpga: %s(%u)", strerror(errno), errno);
	      }
	      if (::close(xfd))
		return OU::eformat(error, "Error closing %s: %s(%u)",
				   outputFile.c_str(), strerror(errno), errno);
	      xfd = -1;
	      return false;
	    }
	  };
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
	  int xfd;
	  if ((xfd = ::open("/dev/xdevcfg", O_WRONLY)) < 0)
	    return OU::eformat(error, "Can't open /dev/xdevcfg for bitstream unloading: %s(%d)",
			       strerror(errno), errno);
	  close(xfd);
	  return false;
	}
      };

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
	OCPI::HDL::Device *dev = open("0", true, params, error);
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
	ocpiBad("When searching for PL device '%s': %s", busName, error.c_str());
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
	  error = "can't mmap /dev/mem for control space";
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
