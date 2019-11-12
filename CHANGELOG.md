## [1.6.0-rc.0](https://gitlab.com/opencpi/opencpi/compare/v1.5.0...v1.6.0-rc.0) (2019.11.08)

### Feature Preview
- **app**: Timestamping accuracy and characterization. (!27)(499967c3)
- **worker**: Update ADC worker to work with split clocks. (!18)(634ad0cf)
- **worker**: Update ADC worker to no longer timestamp. (!18)(634ad0cf)
- **worker**: Update ADC worker to supply sample clock as an output.
    (!18)(634ad0cf)
- **worker**: Add HDL worker for timestamping `ComplextShortWithMetadata`
    protocol data. Supports control, data, input and output clock domains.
    (!29)(408dfb16)
- **worker**: Update DAC worker to work with split clocks. (!30)(bed4736b)
- **worker**: Update DAC worker to no longer timestamp. (!30)(bed4736b)
- **worker**: Update DAC worker to support end of data/burst and EOF distinct
    from underrun. (!30)(bed4736b)

### Features
- **ci**: Init CI/CD starting with CentOS 7 software platform. (!5)(696bcc02)
- **ci**: Utilize docker to test system package installation. (!21)(28805cf9)
- **ci**: Add CentOS 6 software platform. (!25)(e8b67dc6)
- **ci**: Add Xilinx 13.3 and 13.4 software platforms. (!41)(146e2693)
- **prereq**: Add gpsd for all software platforms. (!4)(22842b54)
- **tests**: Add CDC library primitives tests. (!38)(35b698a8)
- **tools**: Support remote HW testing, simplfying hardware in the loop
    testing. (!36, !34)(579e96fc)

### Enhancements
- **framework**: Support Zynq FPGA loading on linux kernels from 2013 to 2019,
    including non-Xilinx kernels. (!14)(c0c402dc)
- **framework**: Standardize on python3.4. (!33)(e2e1eddb)
- **framework**: Time service initializes time-of-day from gpsd. Falls back to
    system time-of-day if gpsd not available. (!40)(9a2a670f)
- **platform**: Xilinx/zynq script updates to better support lots of xilinx
    software versions, including 2019.1. (!6)(fcf33e2a)
- **prereq**: Remove gdb prereq for Xilinx13. (!44)(aea49736)
- **worker**: HDL time service worker provides "time is good" signal.
    (!9)(3aebfece)
- **worker**: HDL time service worker uses booleans instead of bit fields for
    control and status registers. (!9)(3aebfece)
- **worker**: `time_server.hdl` syncs with framework time service when
    initializing. (!40)(9a2a670f)
- **tests**: Relax skew constraint for `TestOcpiOsTimer` to reduce false
    failures when executing in a VM. (!17) (3696eb69)

### Bug Fixes
- **build**: Fix make error if `/opt/Xilinx` does not exist. (!11)(155c809c)
- **build**: Error cross building `opencpi.ko` for Xilinx13 on CentOS6. (!35)(19d8f474)
- **prereq**: Prevent rare git issue when cloning repos that contain CRLF.
    (!11)(155c809c)
- **prereq**: Use tarball for _rsync_ instead of git repo. (!32)(ab3864a5)
- **prereq**: Update _inode64_ url to a working location. (!34)(b2ca33ac)
- **tests**: Do not page help output. Tests desinged to fail were stalling the
    pipeline. (!11)(155c809c)

### Documentation
- **Worker**: Update ADC device worker to reflect enhancements. (!42)(c53385d3)
