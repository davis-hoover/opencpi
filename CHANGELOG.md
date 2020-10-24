# [v1.7.1](https://gitlab.com/opencpi/opencpi/-/compare/v1.7.0...v1.7.1) (2020-10-24)

Changes/additions since [OpenCPI Release v1.7.0](https://gitlab.com/opencpi/opencpi/-/releases/v1.7.0)

### Bug Fixes
- **tools**: `genDocumentation.sh`: Fix parsing of OSP name that is used to determine output prefix for OSP pdfs. (!396)(f52ca9c8)
- **tools**: fix rare bug when `ubuntu16_04-check.sh` runs on a CentOS 6 os. (!397)(bcff9e47)

# [v1.7.0](https://gitlab.com/opencpi/opencpi/compare/v1.7.0-rc.1...v1.7.0) (2020-07-09)

Changes/additions since OpenCPI Release v1.7.0-rc.1

[Consolidated changelog](https://gitlab.com/opencpi/opencpi/-/releases/v1.7.0)  
Full [diff](https://gitlab.com/opencpi/opencpi/compare/v1.6.2...v1.7.0) between v1.6.2 and v1.7.0

### Enhancements
- **doc**: tex documents are more consistent in terms of layout. (!286)(98c0cafb)
- **tools**: revamp export script modularity to support RPM installs. (!299)(f66e7180)

### Bug Fixes
- **hdl base**: fix fractional and integer second misalignment in time_server.hdl. (!296)(9b9dc17a)

# [v1.7.0-rc.1](https://gitlab.com/opencpi/opencpi/compare/v1.7.0-beta.1...v1.7.0-rc.1) (2020-06-25)

Changes/additions since OpenCPI Release v1.7.0-beta.1

### Enhancements
- **comp**: add new complex_short_samples protocol. (!250)(d4a95651)
- **devops,tests**: add specifying hdl platforms to run in pipeline using gitlab web UI. (!255)(f01d9a71)
- **doc**: clarify that `RCCPort::send()` does not advance a worker's output port buffer, and `RCC_OK` should be returned. (!285)(8468d7cc)
- **doc**: clarify that git clone of Xilinx repos are automatic. (!285)(8468d7cc)
- **doc**: clarify that minBufferCount in RCC workers refers to how many buffers exist and not how many need to be full of data. (!285)(8468d7cc)
- **runtime**: update ocpiremote tar command. (!263)(7a0f0f14)

### Bug Fixes
- **comp**: fix cdc tester workers cosim issue. (!176)(6945a2af)
- **doc**: fix opencpi.gitlab.io urls in various "develop" version docs. (!257)(b1ebfed1)
- **hdl base**: bypass build for fir_real_sse_for_xilinx.hdl on rcc-platform builds. (!260)(d80c30a0)
- **hdl base**: fix issue with generating clock generator primitive when using Vivado 2019.2. (!261)(ded238b4)
- **hdl base**: fix verify script. (!273)(22d72ca5)
- **hdl base**: only build zynq ultra primitives for xsim or zync_ultra. (!282)(25842f25)
- **hdl base,tools**: clocking of split clock output ports propagating clocks from input ports was fixed. (!277)(869c4408)
- **osp**: update xilinx13_3 exports for sd card generation. (!241)(1b2c2fb0)
- **runtime**: fix EOF on output when the output port is not in the run condition. (!284)(752fea83)
- **runtime,tests**: fix macos10_14/Mojave installations, mostly due to python2->python3 transition. (!262)(1ab35078)
- **tools**: add missing CentOS 6 dependencies for ISE. (!282)(25842f25)
- **tools**: ensure i386 repo is enabled for Ubuntu 16.04, some vendor tools require 32-bit libraries still. (!271)(1aabe590)
- **tools**: fix HDL primitive search algorithm in `tools/include/hdl/hdl-search.mk`. (!266)(bdd9c797)
- **tools**: fix altera  build issue for part numbers. (!281)(bbbc0a18)
- **tools**: fix macos catalina install. (!281)(bbbc0a18)
- **tools**: install-platform script enhancements. (!268)(1ca453a1)
- **tools**: remove clocking library from hdl-pre.mk. (!270)(c75b93ca)

### Miscellaneous
- **doc**: remove utilization.inc and configurations.inc from repo. (!251)(86b45477)
- **osp,tests**: exclude plutosdr from fifo, fir_real_sse, fir_complex_sse unit tests. (!249)(981440b5)
- **tools**: add openssl-devel to centos7 packages. (!254)(7e7e6d82)

# [v1.7.0-beta.1](https://gitlab.com/opencpi/opencpi/compare/v1.6.2...v1.7.0-beta.1) (2020-05-31)

### Summary
- Support for [ADALM-PLUTO](https://www.analog.com/en/design-center/evaluation-hardware-and-software/evaluation-boards-kits/adalm-pluto.html) via the new [PLUTO SDR](https://gitlab.com/opencpi/osp/ocpi.osp.plutosdr) OSP.
- Support for [Zynq-UltraScale](https://www.xilinx.com/products/technology/ultrascale-mpsoc.html) via the new built-in assets `zcu104` HDL platform.
- New built-in `platform` project moved a lot existing support for platforms out of the`assets` project.
- Ubuntu 16.04 development host support
- Vivado 2019.2 support
- Plus many more enhancements and bug fixes! See sections below for full list of new features and improvements.

### New Features
- **comp**: add RCC work-a-like for HDL cic_dec. (!111)(d5c54a72)
- **comp**: xilinx FIR compiler based fir_Real_sse worker. (!229)(2649bf6d)
- **comp,hdl base**: create platform project and move zed platform, zed_ise platform, zynq primitive, data_src_adc component spec and data_src_dac component spec to platform project. (!182)(84aa3af6)
- **devops**: developers can specify hdl platform to run in CI pipeline via their [commit message](https://gitlab.com/opencpi/opencpi/-/wikis/gitlab-ci-cd). (!202)(b51e43c9)
- **doc**: add component best practice guide. (!221)(fe014ed6)
- **doc**: add ocpidev man pages. (!256)(47be5371)
- **hdl base**: add new primitive library "clocking" for Xilinx MMCM and PLL. (!109)(b4a449ce)
- **osp**: add zcu104 support, as well as the zynq-ultrascale infrastructure for any zynq-ultrascale platform. (!168)(466184ae)
- **tools**: add support for Vivado 2019.2 xsim on ubuntu16_04 platform. (!180)(4fe483ce)
- **tools**: add ubuntu16_04 software platform. (!170)(1b0f685e)

### Enhancements
- **app**: convert timing accuracy test procedures to exclusively use OpenCPI applications. (!79)(be7dc0af)
- **comp**: add HDL worker for converting ComplexShortWithMetadata protocol to iqstream protocol. (!120)(8bd3d458)
- **comp**: add HDL worker for converting iqstream protocol to ComplexShortWithMetadata protocol. (!165)(dd6d22e7)
- **comp**: add enhancement of using BRAM to HDL pattern_v2 component. (!123)(bcc28387)
- **comp,doc**: add component datasheet for iqstream_to_cswm.hdl. (!252)(dc821ec8)
- **devops**: add building for matchstiq_z1 to the CI pipeline. (!161)(54d8c358)
- **devops**: add building modelsim and tests for modelsim to CI pipeline. (!208)(723a71fa)
- **devops**: add building of opencpi and building of tests for the zed platform to the CI pipeline. (!156)(fa188146)
- **devops**: add isim building and testing to CI pipeline. (!190)(cbd5041e)
- **devops**: downstream e3xx pipelines use branch with name matching upstream if one exists; otherwise develop. (!210)(de77a0e4)
- **devops**: set xsim as default HDL platform tested by CI for non merge request pipelines. (!201)(adf29dc6)
- **doc**: add preliminary documentation for adding HDL tool support. (!119)(4a68f932)
- **doc**: document OCPI_SOCKET_INTERFACE env var when using remote containers on multi-homed systems. (!199)(ac023eef)
- **doc**: document top level attributes for containers and pf configs:  platform, config, constraints, onlyplatform etc. (!199)(ac023eef)
- **doc**: explain how one protocol can xi:include another. (!199)(ac023eef)
- **doc**: fix known defects, expand test coverage, and add support for HdlWorker StreamInterface attributes in `docGen.py`. (!118)(50ebe553)
- **doc**: update cic_dec documentation to reflect the new tests. (!86)(db706821)
- **doc**: update install/user/tutorial docs based on trainee feedback. (!220)(b4551467)
- **doc**: update software platform and adc/dac sections of platform development guide. (!256)(47be5371)
- **doc,tools**: automate document table generation for select component datasheets. (!163)(fb3edb44)
- **hdl base**: add zynq 7010 support (generics added to asset's project's zynq_ps primitve). (!103)(451edd39)
- **hdl base**: update hdl worker shell code for cdc best practices. (!172)(1d0c8f8e)
- **osp**: add new configuration for ad9361-data-sub. (!237)(f3a85f72)
- **osp**: add three new configurations for gpi. (!237)(f3a85f72)
- **osp**: mint19 now works as a development platform with no FPGA tools tested. (!167)(4a8629c1)
- **osp**: simplified and more robust export model for platforms and SD cards. (!158)(22f40996)
- **runtime**: add loading boot files to device with `ocpiremote.py`. (!244)(2569d725)
- **runtime**: expand ocpizynq utility to print out 7 series PS SPI registers. (!143)(27997461)
- **tests**: update python test files from python 2 to python 3.4. Later changes removed the explicit python minor version. (!108)(b6929b1f)
- **tests,tools**: add ability to use OpenCPI ACI with python3. (!209)(3247ecfc)
- **tests,tools**: refactor kernel module build process. (!230)(08e8132f)
- **tests,tools**: remove python2-related packages from `<platform>-packages.sh` scripts. (!218)(6371471c)
- **tools**: add support for optional HDL ports with `clockdirection=in`. (!245)(30a645dd)
- **tools**: automate how we create new Xilinx-based RCC software platforms, from 2013 to the present. (!135)(e0a92be8)
- **tools**: change all "python34" references to "python3". (!169)(eee26b03)
- **tools**: convert `ocpiremote.sh` to `ocpiremote.py`. (!114)(0891c554)
- **tools**: eliminate the tools/cdk from the source tree (not user-visible). (!203)(892a8e51)

### Bug Fixes
- **app**: fix cic_dec `view.sh` bug that failed to generate plots. (!86)(db706821)
- **comp**: fix bug where data_sink_dac.hdl assigns Q from I value. (!120)(8bd3d458)
- **comp**: fix pattern_v2 unit test bug. (!177)(8d0c0f6d)
- **comp,tests**: fix test_tx_event unit test hanging on zed. (!187)(84a32435)
- **hdl base**: fix bug when building assemblies for zed_ise. (!219)(ff39bcb2)
- **runtime**: fix bug when trying to use remote containers with zed_ise. (!219)(ff39bcb2)
- **runtime**: return correct value when getting scalar values from parameter properties with `getPropertyValue<type>()` API call. (!184)(1fabe14d)
- **tests**: fix a socket test that fails when computer's hostname is not resolvable. (!235)(4af69dd7)
- **tests**: test-timer.cxx allowed duration increased from 5% to 15% of expected duration to account for VM sleep/wake overhead. (!205)(51ba070f)
- **tests,tools**: fix matplotlib for python3.4 unavailable. (!209)(3247ecfc)
- **tools**: fix codegen bug when multiple ports use the same protocol. (!246)(40698dca)
- **tools**: fix gpsd build for "DBUS development package installed" case. (!243)(6cdcb044)
- **tools**: fix sed expression in `makeExportLinks.sh` related to `user-env.sh`. (!198)(fbc9badb)
- **tools**: improve ocpiav usage/help message. (!191)(e0abd684)

### Miscellaneous
- **comp**: change ComplexShortWithMetadata protocol. (!115)(5333a8a9)
- **comp**: modify data_src_adc component/worker to match intended design. (!140)(1008e082)
- **doc**: add plutosdr platform to OpenCPI Installation Guide. (!128)(981ebd35)
- **doc**: update plutosdr platform in OpenCPI Installation Guide. (!216)(59318d87)
- **hdl base**: move zynq_ultra primitive to new platform project. (!225)(e0e20753)
- **osp**: add additional build configurations to components needed by the plutosdr platform. (!107)(2696ad7d)
- **osp**: add dev system packages in support of plutosdr. (!242)(2afaf517)
- **runtime**: remove bash-isms in ocpiremote scripts. (!148)(e5bfa8db)
- **tools**: add shebangs to python scripts missing them. (!238)(d3600eb2)
- **tools**: fix improper directory structure generation for `genDocumentation.sh`. (!183)(a14e6fe5)
- **tools**: fix ocpigen error message for cards. (!226)(90d1425a)
- **tools**: remove explicit uses of python to execute python scripts, relying on shebangs instead. (!238)(d3600eb2)
- **tools**: use python3 version of doc packages instead of python34. (!232)(0cd230ad)


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
