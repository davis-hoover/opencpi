# [v1.6.2](https://gitlab.com/opencpi/opencpi/compare/v1.6.1...v1.6.2) (2020-04-05)

One framework related fix, rest are CI/CD related.

### Enhancements
- **devops**: add kicking off of e3xx project pipeline from main opencpi pipeline. (!171)(3dd44849)

### Bug Fixes
- **devops**: Don't use $CI_REGISTRY_IMAGE as it is incorrect for forked projects. (!155)(fe8ac9f8)
- **devops**: Explicitly set default job timeout as forked projects do not inherit the value. (!155)(fe8ac9f8)
- **doc,tools**: Regex pattern used to parse `git branch` output was improved to correctly handle `(detached from XXX)`. (!157)(6126f943)
- **hdl base**: apply fix to sdp_receive_dma. (!166)(3024057a)

# [v1.6.1](https://gitlab.com/opencpi/opencpi/compare/v1.6.0...v1.6.1) (2020-03-02)

This is mainly a documentation + CI/CD improvement release. However, there was
a handful of framework releated bug fixes.

### Enhancements
- **devops**: Speed up CI pipeline by 100%. (!131)(1ba546af)
- **devops**: Trigger pipeline for downstream project opencpi.gitlab.io. (!141)(5a2e7683)
- **devops**: Add support for passing upstream artifacts to downstream projects. (!144)(47da89d0)
- **devops,tools**: Add a "latest" release url. (!125)(ab5ecf67)
- **doc**: rename reference document file names to be friendlier and reflect their content better. (!122)(b9b730ad)
- **tools**: Build and add tutorials to opencpi.gitlab.io. (!117)(674496a1)
- **tools**: Build and add briefings to opencpi.gitlab.io. (!117)(674496a1)
- **tools**: Pages: only build latest release of each version. (!136)(38889eec)
- **tools**: Add CLI and GUI version of tutorials to doc site. **Note**: not all tutorials support this new format and will be made available when converted. (!138)(91922c85)

### Bug Fixes
- **app**: change instances of `data_stream_type` to `direction`. (!142)(6e3e9cb8)
- **tests**: Change `np.nan` to `sys.maxsize` as not all systems support `np.nan`. (!100)(27099092)
- **tools**: install package for Tahoma font. (!102)(8d5ca9a9)
- **tools**: Replace `libreoffice-headless` dependency with `libreoffice-writer` so docs can be built on fresh install of CentOS 7 minimal. (!112)(f5638c53)
- **tools**: ocpidev run now works for xml-only applications created with -X. (!116)(3c3d3fc9)
- **tools**: ocpidev now allows spaces in argument values, equal sign values after --options. (!116)(3c3d3fc9)
- **tools**: Fix OpenCPI version tag sorting for opencpi.gitlab.io. (!124)(bc9cfc14)
- **tools**: Use unoconv to convert libreoffice docs to pdfs. (!126)(7361545e)

### Miscellaneous
- **devops**: Redirect https://opencpi.gitlab.io/opencpi to https://opencpi.gitlab.io/releases/latest/. (!145)(0a5ce1aa)
- **doc**: Change relevant references from GitHub to GitLab. (!100)(27099092)
- **tools**: Install `tree` package since tutorials use it. (!100)(27099092)

# [v1.6.0](https://gitlab.com/opencpi/opencpi/compare/v1.6.0-rc.1...v1.6.0) (2020-02-06)

### Enhancements
- **devops**: Remove use of caching to pass artifacts between stages. Enables use of cloud and local resources. (!87)(72604cb1)

### Bug Fixes
- **tests**: Change `#!/usr/bin/env python3` to `#!/usr/bin/env python3.4`. (!85)(5bf52ee2)

### Documentation
- Updated [Release Notes](https://opencpi.gitlab.io/releases/v1.6.0/doc/Release_Notes.pdf). (!121)(e494630f)
- Version bump documents to `v1.6.0`. (!121)(8e5967c3)

# [v1.6.0-rc.1](https://gitlab.com/opencpi/opencpi/compare/v1.6.0-rc.0...v1.6.0-rc.1) (2020-01-11)

### New Features
- **app,comp**: Builtin Tutorial project. (!92)(db38114a)
- **comp**: Add Phase to amplitude CORDIC RCC work-a-like. (!83)(42c010ea)
- **devops**: add xsim to the ci pipeline. (!50)(ed8bbff4)
- **devops**: Add GitLab Pages static site generator for documentation. (!84)(5748523d)
- **devops**: Add Dockerfile for docker image used to create pdfs and GitLab Pages. (!84)(5748523d)
- **devops**: Use custom docker image in CI pipeline to create pdfs and GitLab Pages. (!84)(5748523d)
- **hdl base**: Add debounce.vhd primitive. (!83)(42c010ea)
- **hdl base**: Add GPI and GPO device workers. (!83)(42c010ea)
- **osp**: Support MacOS Catalina (10.15). (!92)(db38114a)
- **tools**: Add script, `scripts/install-platform.sh`, to install platforms and projects for that platform. (!92)(db38114a)

### Enhancements
- **comp**: Replace matchstiq_z1_gp_out worker with matchstiq_z1_gp_card "virtual card". (!83)(42c010ea)
- **runtime**: data and control clocks split throughout the unit test infrastructure. (!82)(f83770a5)
- **tools**: Simplify installation of AV GUI and reduce user setup after installation. (!92)(db38114a)

### Bug Fixes
- **app**: Fixes fmcomss_2_3_tx artifact build issue for xilinx13_4. (!64)(f9f2791e)
- **app**: Removed extra newline from template.py, added license to model core project. (!88)(86448f87)
- **app,comp**: data_src.hdl: out port ZLM generation failed in some cases. (!73)(a5335922)
- **comp**: Set data_sink_dac on_off port to correct clock domain. (!60)(8fc9e6fe)
- **hdl base**: patches a bug in the fixed_float library seen when using older tools. (!67)(4e77a644)
- **osp**: Fix exporting the zed_ise specific system.xml. (!72)(eaefb073)
- **tools**: updated inode64.c url. (!65)(e54c92ea)
- **tools**: Fix make-hw-deploy.sh to put system.xml in correct place. (!71)(b37f8244)

### Documentation
- **app,comp,runtime**: Add Briefing slides that provide background information about OpenCPI concepts and processes. (!92)(db38114a)
- **app,comp,runtime**: Add Tutorial documents that allow completion of tutorials using an HDL simulator as well as an E310. (!92)(db38114a)
- **app,comp,runtime**: Major update to developer guides. (!92)(db38114a)
- **comp**: Add HDL worker documentation for data_sink_dac.hdl. (!61)(501dab62)
- **devops**: replace github references with gitlab. (!46)(8079eafb)
- **devops**: Refactor CHANGELOG.md. (!75)(5efbc78b)
- **osp**: Update ZedBoard GSG to use new sharing scheme. (!92)(db38114a)
- **osp**: Update Matchstiq GSG to refer to installation guide. (!92)(db38114a)
- **runtime,tools**: New User document geared towards OpenCPI users. (!92)(db38114a)
- **tools**: `scripts/install-opencpi-docs.sh` no longer builds the docs, one must additionally use `make doc`. (!84)(5748523d)
- **tools**: Major update to installation guide. (!92)(db38114a)

# [v1.6.0-rc.0](https://gitlab.com/opencpi/opencpi/compare/v1.5.0...v1.6.0-rc.0) (2019.11.08)

### Feature Preview
- **app**: Timestamping accuracy and characterization. (!27)(499967c3)
- **comp**: Update ADC worker to work with split clocks. (!18)(634ad0cf)
- **comp**: Update ADC worker to no longer timestamp. (!18)(634ad0cf)
- **comp**: Update ADC worker to supply sample clock as an output. (!18)(634ad0cf)
- **comp**: Add HDL worker for timestamping `ComplextShortWithMetadata` protocol data. Supports control, data, input and output clock domains. (!29)(408dfb16)
- **comp**: Update DAC worker to work with split clocks. (!30)(bed4736b)
- **comp**: Update DAC worker to no longer timestamp. (!30)(bed4736b)
- **comp**: Update DAC worker to support end of data/burst and EOF distinct from underrun. (!30)(bed4736b)

### New Features
- **devops**: Init CI/CD starting with CentOS 7 software platform. (!5)(696bcc02)
- **devops**: Utilize docker to test system package installation. (!21)(28805cf9)
- **devops**: Add CentOS 6 software platform. (!25)(e8b67dc6)
- **devops**: Add Xilinx 13.3 and 13.4 software platforms. (!41)(146e2693)
- **tests**: Add CDC library primitives tests. (!38)(35b698a8)
- **tools**: Add gpsd for all software platforms. (!4)(22842b54)
- **tools**: Support remote HW testing, simplfying hardware in the loop testing. (!36, !34)(579e96fc)

### Enhancements
- **comp**: HDL time service worker provides "time is good" signal. (!9)(3aebfece)
- **comp**: HDL time service worker uses booleans instead of bit fields for control and status registers. (!9)(3aebfece)
- **comp**: `time_server.hdl` syncs with framework time service when initializing. (!40)(9a2a670f)
- **runtime**: Support Zynq FPGA loading on linux kernels from 2013 to 2019, including non-Xilinx kernels. (!14)(c0c402dc)
- **runtime**: Standardize on python3.4. (!33)(e2e1eddb)
- **runtime**: Time service initializes time-of-day from gpsd. Falls back to system time-of-day if gpsd not available. (!40)(9a2a670f)
- **tests**: Relax skew constraint for `TestOcpiOsTimer` to reduce false failures when executing in a VM. (!17) (3696eb69)
- **tools**: Xilinx/zynq script updates to better support lots of xilinx software versions, including 2019.1. (!6)(fcf33e2a)
- **tools**: Remove gdb prereq for Xilinx13. (!44)(aea49736)

### Bug Fixes
- **tests**: Do not page help output. Tests desinged to fail were stalling the pipeline. (!11)(155c809c)
- **tools**: Fix make error if `/opt/Xilinx` does not exist. (!11)(155c809c)
- **tools**: Prevent rare git issue when cloning repos that contain CRLF. (!11)(155c809c)
- **tools**: Use tarball for _rsync_ instead of git repo. (!32)(ab3864a5)
- **tools**: Update _inode64_ url to a working location. (!34)(b2ca33ac)
- **tools**: Error cross building `opencpi.ko` for Xilinx13 on CentOS6. (!35)(19d8f474)

### Documentation
- **comp**: Update ADC device worker to reflect enhancements. (!42)(c53385d3)
