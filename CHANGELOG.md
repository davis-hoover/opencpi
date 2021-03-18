# [v2.1.0](https://gitlab.com/opencpi/opencpi/-/compare/v2.1.0-rc.2...v2.1.0) (2021-03-17)

Changes/additions since [OpenCPI Release v2.1.0-rc.2](https://gitlab.com/opencpi/opencpi/-/releases/v2.1.0-rc.2)

### Enhancements
- **comp,hdl base**: add properties to the data_sink_qdac device worker for number of samples before the first underrun and number of underruns. (!510)(2238c355)
- **doc**: rename `Acronyms and Definitions` to `OpenCPI Glossary`, update, and append to reference documents. (!508)(07aeb463)
- **hdl base**: replace bsv primitive with a reset compatible with xilinx2020.1. (!486)(cccad883)
- **hdl base**: allow timestamper_scdcd to insert sampling intervals. (!506)(c1a3059d)
- **tools**: add optimization options to ocpiremote, and make its options consistent with ocpidev and others. (!505)(6c9e8bc6)

### Bug Fixes
- **comp,hdl base**: fix extra cycles for dev_out.valid signal when data valid goes low. (!510)(2238c355)
- **devops**: fix `build-pages.py` to handle OSP default branch that isn't `develop`. (!501)(aa1199e0)
- **devops,tests**: disable `gpi.test` until proper fix implemented. (!503)(8e4af08d)
- **hdl base**: change timestamper_scdcd and associated protocol marshaller to avoid idle cycles in output. (!506)(c1a3059d)
- **hdl base**: set HDL device timeservice with system time when GPS time is not available. (!506)(c1a3059d)
- **hdl base,runtime**: fix bug in `HdlDevice.cxx` that set `enable_time_now_updates_from_PPS_written` to `true` when not even using PPS. (!502)(da2a10a4)
- **runtime**: disable compilation of event tracing. (!505)(6c9e8bc6)
- **runtime,tools**: clean up compilation warnings that are errors in centos7 under optimization only. (!513)(bc347d5d)

### Miscellaneous
- **doc**: remove obsolete `Acronyms and Definitions` document. (!512)(63c1c7ac)
- **osp**: hdl configuration file update. (!500)(55823787)

# [v2.1.0-rc.2](https://gitlab.com/opencpi/opencpi/-/compare/v2.1.0-rc.1...v2.1.0-rc.2) (2021-03-04)

Changes/additions since [OpenCPI Release v2.1.0-rc.1](https://gitlab.com/opencpi/opencpi/-/releases/v2.1.0-rc.1)

### New Features
- **runtime**: add `OCPI_ROOT_DIR` environment variable to setup scripts. (!471)(f4b25449)

### Enhancements
- **devops,tools**: allow `gen-cg-pdfs.sh` to work with recent LibreOffice versions. (!482)(3405e888)
- **hdl base**: make `capture_v2` a split clock worker. (!492)(a8098c74)
- **runtime**: enable drc stop_config. (!483)(904f12ff)
- **runtime,tools**: add `--optimize` option to `opencpi-setup.sh`. (!495)(dcf1e54c)
- **tools**: building sw framework/rcc/aci for optimization is now fully enabled, but not in the UI yet. (!490)(c16a8374)

### Bug Fixes
- **comp**: fix bug in drc worker implementation. (!497)(2dad9b19)
- **hdl base**: increase data path cdc fifo depth from 2 to 16 within `timestamper_scdcd` for better throughput. (!496)(6295897e)
- **osp**: zcu104: fix a typo and a symlink. (!491)(ae8386a8)
- **runtime**: DtDmaXfer.cxx: fix log-level for messages to/from FPGA. (!498)(d5164abd)
- **tools**: ocpidev.sh: fix broken test statements. (!498)(d5164abd)

### Miscellaneous
- **doc**: update DRC briefing for LibreOffice 5.3 compatibility. (!487)(8c300713)
- **osp**: zcu104: fix regression, thereby allowing `data_sink_test_app` and `fsk_dig_radio_ctrl` to run. (!491)(ae8386a8)
- **tests**: temporarily disable `capture_v2` test. (!499)(9595345e)

# [v2.1.0-rc.1](https://gitlab.com/opencpi/opencpi/-/compare/v2.1.0-beta.1...v2.1.0-rc.1) (2021-02-08)

Changes/additions since [OpenCPI Release v2.1.0-beta.1](https://gitlab.com/opencpi/opencpi/-/releases/v2.1.0-beta.1)

### New Features
- **doc**: add DRC documentation to Application Development Guide and Platform Development Guide, and create new briefing. (!480)(1b9693a3)
- **tests,tools**: create iperf3 install script that is called by install-prerequisites script. (!445)(a6f9aa0f)

### Enhancements
- **app**: ocpiremote: use less memory on the target embedded system when creating the sandbox, allow setting dma memory side on start. (!457)(46f1aff7)
- **comp**: allow workers to get the current time, and C workers to have log messages. (!457)(46f1aff7)
- **comp**: add in fsk_modem assembly and drc for zcu104. (!469)(a78f78e6)
- **comp,hdl base**: updated data_src_qadc_ad9631_sub for one clock per sample and added properties for data_src_qadc. (!449)(3c2ace47)
- **devops**: fix downstream pipelines failing due to environment variables not being set correctly. (!437)(72adeca8)
- **hdl base**: update cnt_zed_fmcomms_2_3_scdcd.xdc and cnt_zcu104_fmcomms_2_3_scdcd.xdc to properly constrain things for the ADC one clock per sample. (!451)(064d6479)
- **hdl base**: enable SDP send and receive to support lots of cpu-side buffers (255). (!457)(46f1aff7)
- **hdl base**: increase maximum message size between HDL workers to 64k-4. (!457)(46f1aff7)
- **hdl base**: add timegate worker to support timed transmission. (!466)(344f26db)
- **hdl base**: allow zynq platforms to use the ACP port (partial). (!470)(69121c36)
- **hdl base**: add ACP handling for zynq on zed at least. (!475)(f2577630)
- **hdl base**: updated ad9361 data sink txen logic. (!479)(a7dbf4fa)
- **osp**: add macos11_1 support. (!457)(46f1aff7)
- **osp**: move zcu104 platform where it should be in the platform project. (!457)(46f1aff7)
- **runtime**: support delegating array ports in proxies, with individual port connections in slave assemblies. (!436)(4be9ec46)
- **runtime**: make cpu-side buffering much more scalable to easily support lots of buffers. (!457)(46f1aff7)
- **runtime**: use "gather" APIs to improve TCP throughput. (!470)(69121c36)
- **tests**: add simple performance test workers, and update file_write to report throughput and check test data correctness. (!457)(46f1aff7)
- **tests,tools**: convert old advanced_pattern unit test into current framework. (!435)(fbde6289)
- **tests,tools**: unit under test is done worker. (!460)(66d68419)
- **tools**: build hdl xmls to satisfy proxy dependencies. (!438)(5c313de0)
- **tools**: fix code generation for parameterized SDP ports. (!457)(46f1aff7)

### Bug Fixes
- **app,runtime**: fix external connections on slave assemblies. (!456)(5fce8148)
- **devops,tests**: fix potential resource exhaustion issue on runners due to broken tests. (!474)(6e01a7d6)
- **doc**: fix ocpiadmin man page typo (`-url` --> `--url`). (!462)(e9180617)
- **hdl base**: fix sdp_send to eliminate the single cycle of backpressure on input, build sdp for 32/64/128 widths. (!457)(46f1aff7)
- **hdl base,tools**: clean up the hdl primitives folders. (!430)(7ae9105e)
- **runtime**: make the DRC "stop_config" method required. (!457)(46f1aff7)
- **runtime**: fix cases where buffer-counts and sizes were not being set by ocpirun options. (!457)(46f1aff7)
- **runtime**: datagram: fix 32/64-bit issue when sides are different. (!457)(46f1aff7)
- **runtime**: add missing zynq setup script to exported files. (!458)(48d37a8e)
- **runtime**: remove rcc worker error for buffer size and protocol mismatch. (!461)(fa2287ce)
- **runtime**: comment out second channel of drc. (!463)(8d158bd2)
- **runtime**: add "guard" in configure_gps_if_enabled() function. (!465)(85a0a442)
- **runtime**: fix setting gain_mode manual on rx channel using DRC. (!478)(10c11830)
- **tools**: fix bad exports list for some Xilinx platforms when deploying to ZedBoard. (!446)(a7bf321b)
- **tools**: fix handling of single-element array properties by RPROP_ARRAY_16 and WPROP_ARRAY_16. (!459)(e7f0be4c)
- **tools**: fix help message in "ocpiadmin" script. (!462)(e9180617)

# [v2.1.0-beta.1](https://gitlab.com/opencpi/opencpi/-/compare/v2.0.1...v2.1.0-beta.1) (2020-12-18)

Changes/additions since [OpenCPI Release v2.0.1](https://gitlab.com/opencpi/opencpi/-/releases/v2.0.1)

### New Features
- **runtime**: slaves are not automatically included in the application without mentioning them. (!428)(22c9956b)
- **tools**: add convenience script (scripts/install-gnuradio.sh) to install OpenCPI's modified version of GNU Radio 3.7. (!283)(8ad0cd5f)

### Enhancements
- **app**: enable bbloopback mode for FSK application on matchstiq z1. (!422)(2c2ebb0d)
- **devops**: add OSP support to yaml-generator.py. (!382)(bf7a9c77)
- **devops**: implement child pipelines for cross-platform builds/tests. (!382)(bf7a9c77)
- **devops**: implement grandchild pipelines so that more jobs can be dynamically generated. (!431)(c249580e)
- **devops**: fix downstream pipelines failing due to environment variables not being set correctly. (!437)(72adeca8)
- **osp**: add support for zcu102. (!407)(444d760c)
- **protocols**: update ComplexShortWithMetadata-prot.xml to use a sequence length of 4096 instead of 4092 for the iq argument of the samples operation. (!427)(34d0d193)
- **runtime**: port delegation from proxies to slaves is now implemented. (!421)(b718ff61)
- **runtime**: generic DRC helper class established in an API header OcpiDrcProxyApi.hh. (!421)(b718ff61)
- **runtime**: update zed/fmcomms2 platform with new drc. (!433)(d494dad9)
- **tools**: install-gnuradio.sh: add GNU Radio 3.8 support. (!401)(4c92ed80)
- **tools**: add missing fields to the opencpi GRC blocks. (!425)(a40d1a90)
- **tools**: ocpigen: add XML parsing for project assets. (!434)(30acd3d2)

### Bug Fixes
- **runtime**: fix ocpiremote deploy not deploying boot files to correct remote directory. (!416)(56b316af)
- **tools**: include bitstream argument in "ocpiremote restart" to prevent errors being thrown. (!371)(83566d76)
- **tools**: improve gnuradio 3.8 install. (!405)(a18a710c)

### Miscellaneous
- **doc,runtime,tests,tools**: remove remaining CentOS 6 references and supporting code. (!403)(3b9c943b)
- **comp**: make "socket_write.rcc" portable. (!418)(4755f36a)
- **hdl base**: add ADI "mykonos" library as a prerequisite. (!385)(f2ec19c5)
- **tools**: remove remaining BSV references and code from ocpigen. (!414)(8f73efd2)

# [v2.0.1](https://gitlab.com/opencpi/opencpi/-/compare/v2.0.0...v2.0.1) (2020-11-18)

Changes/additions since [OpenCPI Release v2.0.0](https://gitlab.com/opencpi/opencpi/-/releases/v2.0.0)

### Enhancements
- **osp**: update/refactor the DRC support libraries to be sharable among proxies, and make pluto an example of using them. (!393)(df56b22b)
- **tools**: doc site: include OSP documentation starting with version 1.7.1. (!402)(73a409c4)
- **tools**: doc site: add man page link to a release's index page if man pages exist. (!402)(73a409c4)

### Bug Fixes
- **doc,tools**: prevent libreoffice tracked changes from showing up in rendered pdfs. (!392)(a7cb3110)
- **hdl base**: add IDLE state to state machine. (!404)(477404a2)
- **hdl base**: fix bug with statemachine. (!406)(d7fca60c)
- **runtime**: add new way of calling no-os ad9361 library. (!420)(01e79568)
- **tools**: fix bugs for clock adapter insertion. (!383)(2632c226)
- **tools**: fix ubuntu check scripts to not error on non-ubuntu platforms. (!398)(044e4db1)
- **tools**: fix bugs for clock adapter insertion. (!399)(99e89a32)
- **tools**: doc site: fix incorrect "latest" release labeling. (!402)(73a409c4)
- **tools**: fix "ocpigen" processing of 64-bit initial values for 64-bit HDL worker parameters. (!417)(977c228e)

### Miscellaneous
- **comp**: move "zero_padding" component to "inactive" project. (!419)(64f4f058)
- **doc,runtime,tests,tools**: remove remaining CentOS 6 references and supporting code. (!403)(3b9c943b)

# [v2.0.0](https://gitlab.com/opencpi/opencpi/-/compare/v2.0.0-rc.2...v2.0.0) (2020-10-06)

Changes/additions since [OpenCPI Release v2.0.0-rc.2](https://gitlab.com/opencpi/opencpi/-/releases/v2.0.0-rc.2)

### New Features
- **tools**: add dockerfile for docker image used during GRCon20 workshops. (!386)(94e17772)

### Enhancements
- **app**: include the demo app from tutorial 1 in the tutorial project for completeness. (!373)(1566b9e9)
- **comp**: Add timed sample protocols. (!370)(90c31833)
- **comp**: add rcc and hdl workers for the tutorial 1 workers so we have both rcc and hdl of all of them. (!373)(1566b9e9)
- **comp**: cleanup another tutorial worker, `peak_detector.rcc`, for tutorial 2. (!373)(1566b9e9)
- **doc**: add files for the `timestamper_scdcd` datasheet to be compiled. (!357)(37931d3b)
- **runtime**: to be more consistent, enable "worker" attribute in app instances to include the authoring model suffix. (!373)(1566b9e9)
- **runtime**: allow "worker" variable in selection expressions. (!373)(1566b9e9)
- **runtime**: when there are no slaves indicated for a proxy instance (like from GRC), find slaves automatically if such a thing can be unambiguous.  This is still not fully inferred slaves, it is inferred slaves when they are already present, but not indicated as slaves. (!373)(1566b9e9)
- **runtime**: enable `OCPI_APPLICATION_PARAMS` to work better and for more options like `dump` and `verbose` (still not documented). (!373)(1566b9e9)
- **runtime**: have our hdl sim drivers kill sims on `SIGTERM` as well as `SIGINT`. (!373)(1566b9e9)
- **tools**: `ocpigen`: make `ocpi_debug` a hidden property. (!373)(1566b9e9)
- **tools**: `ocpigr37`: make `ocpi_container` a pseudo-property for GRC to be "partly hidden". (!373)(1566b9e9)
- **tools**: add platform, worker, model, and "done" pseudo-properties to the `ocpigr37` output, and put them last after normal properties. (!373)(1566b9e9)
- **tools**: `ocpigen`: make `ocpi_endian` a hidden property. (!373)(1566b9e9)
- **tools**: add env var `OCPI_DISTRO_BUILD` to enable generic x86_64 distro build feature. (!380)(e849452b)
- **tools**: build generic x86_64 GMP library when `OCPI_DISTRO_BUILD` env var is set. (!380)(e849452b)
- **tools**: add non-positional parameter handling to `ocpiadmin`. (!384)(cb1209c6)

### Bug Fixes
- **comp**: fix bug in `cdc_clk_gen.vhd`. (!378)(3ac9aac6)
- **hdl base**: fix an ancient bug in VHDL delta cycles that we previously blamed on being an isim-only bug. (!373)(1566b9e9)
- **runtime**: don't end up busy-waiting when the container has no applications to run at all. (!373)(1566b9e9)
- **tests**: fix typo in `ocpidev_directory_test.sh` relating to `ocpishow.py`. (!377)(0723c9aa)
- **tools**: fix an ancient bug in modelsim building that could report an error which then "disappeared" on rebuild. (!373)(1566b9e9)
- **tools**: make the tutorial project depend on platform so it can build for pluto and other OSPs. (!373)(1566b9e9)
- **tools**: fix `centos8-check.sh` script. (!375)(03a04a91)
- **tools**: fix `ocpishow.py` to have better error handling. (!377)(0723c9aa)
- **tools**: fix `project.py` (in `tools/python/_opencpi`) to have better error handling. (!377)(0723c9aa)

# [v2.0.0-rc.2](https://gitlab.com/opencpi/opencpi/-/compare/v2.0.0-rc.1...v2.0.0-rc.2) (2020-09-22)

Changes/additions since [OpenCPI Release v2.0.0-rc.1](https://gitlab.com/opencpi/opencpi/-/releases/v2.0.0-rc.1)

### New Features
- **tools**: add ability to specify host only prereqs. (!361)(3ac81b61)

### Enhancements
- **devops**: add script to automate creation of gitlab CI pipeline jobs for opencpi projects/platforms. (!351)(5b068b89)
- **doc**: add more man pages:  ocpihdl, ocpirun, opencpi, and some other updates. (!366)(207870c0)
- **tools**: add yaml-cpp v0.6.x as prereq (x86_64 only), removing weak dependency on boost. (!356)(be3e4cfa)

### Miscellaneous
- **comp**: add fifo_depth_p of 2048 to fifo.hdl build configuration. (!358)(fcd0e217)
- **tests**: suppress plutosdr from fir_complex_sse_ts.test due to lack of dsp resources. (!359)(387938a8)

# [v2.0.0-rc.1](https://gitlab.com/opencpi/opencpi/-/compare/v2.0.0-beta.1...v2.0.0-rc.1) (2020-08-28)

Changes/additions since OpenCPI Release v2.0.0-beta.1

### Enhancements
- **comp**: improve dc_offset_filter doc by adding transfer function. (!333)(364bb72e)
- **comp**: build socket_write.rcc for ubuntu18_04 platform. (!353)(7ef32634)
- **devops,tests**: remove obsolete ".bitz" files from git repo. (!337)(3d801f21)
- **doc**: add more man pages for OpenCPI commands. (!347)(6b7e41eb)
- **doc,tools**: add doc RPM to existing packaging machinery. (!329)(62cc8e74)
- **hdl base**: all hdl platforms have a standard test bitstream exported in a standard place. (!338)(e19fc095)
- **runtime,tools**: a proxy can have optional slaves so apps can have subsets, and the proxy can test or presence. (!338)(e19fc095)
- **tools**: enable python2 ACI in addition to python3 ACI. (!334)(3ea0db4d)
- **tools**: implement "-v" (verbose) option in "deploy-platform.sh" script. (!345)(5d7c5383)
- **tools**: add VERSION file that defines the version of OpenCPI. (!346)(b1e80c4d)
- **tools**: refactor `scripts/update-release.sh` to use new VERSION file. (!346)(b1e80c4d)

### Bug Fixes
- **comp**: `timestamper_scdcd.vhd`: add logic to confirm that EOF is valid. (!314)(b4918d13)
- **hdl base**: `complex_short_with_metadata_demarshaller.vhd`: add reset for EOF. (!314)(b4918d13)
- **hdl base**: `time_downsampler.vhd`: add reset for EOF. (!314)(b4918d13)
- **hdl base**: the ml605 now builds everything including the inactive and tutorial projects. (!338)(e19fc095)
- **runtime**: some property setting patterns, especially for remote device slaves, were broken and now fixed. (!344)(fb8e6c12)
- **tools**: fix export logic so as not to create broken symlinks. (!329)(62cc8e74)
- **tools**: build regressions on lesser used platforms not in normal pipeline. (!331)(a7f7cdd2)
- **tools**: fix "ocpigr" error exceptions caused by obsolete bitstream files. (!337)(3d801f21)
- **tools**: ocpigen: check status code returned by `finalizeHdlDataPort()` instead of ignoring it. (!339)(33f94239)
- **tools**: fix building an ubuntu docker container with a non ubuntu host by preventing kernel related items from being built. (!343)(29a8c490)
- **tools**: fix OSP HDL platform export mechanism. (!345)(5d7c5383)
- **tools**: fix/restore usable of project-level componentlibrary settings in proxies in hdl/cards. (!350)(1584caf7)

### Miscellaneous
- **tools**: remove support for CentOS 6 as a development host platform. (!354)(3dc24ee0)

# [v2.0.0-beta.1](https://gitlab.com/opencpi/opencpi/-/compare/v1.7.0...v2.0.0-beta.1) (2020-07-24)

Changes/additions since OpenCPI Release v1.7.0

### New Features
- **devops**: upload entire OpenCPI tree to AWS S3 when a job fails. (!297)(6708dc22)
- **osp**: add support for additional xilinx software platforms: xilinx13_4_aarch32, xilinx19_2_aarch{32,64}. (!173)(5e034a9a)
- **tools**: add AV GUI to ubuntu18_04 platform. (!294)(d74f201c)
- **tools**: add centos8 RCC development platform. (!312)(c85641a3)
- **tools**: initial add of "ubuntu18_04" development platform. (!278)(e053aac5)

### Enhancements
- **devops**: add ability for opencpi pipeline to launch downstream plutosdr pipeline. (!303)(ddb5b49e)
- **devops**: add weekly scheduled CI pipeline to lessen load on MR pipelines. (!287)(c47409e0)
- **devops**: move CI artifact hosting from gitlab to AWS. (!325)(8c28c710)
- **doc**: add generation of html man pages. (!327)(196ab92e)
- **doc**: add man pages for ocpidev nouns (previous ones are for verbs). (!327)(196ab92e)
- **doc,tools**: export PDFs so they can more easily be packaged in an RPM. (!311)(fb4c4f4c)
- **hdl base**: allow bitstream loading in linux 4.10, and avoid probing a bitstream when unloading or loading. (!316)(d3dabaf9)
- **hdl base,tools**: component library searching is now all-libs-in-project, per project, not each-lib-in-all-projects. (!316)(d3dabaf9)
- **hdl base,tools**: primitive libraries can be qualified by the project's package id. (!316)(d3dabaf9)
- **hdl base,tools**: workers chosen for an assembly are not affected by what is built as long as anything is built. (!316)(d3dabaf9)
- **osp**: add initial support of ad9361 fmcomms transceiver for zcu104 platform. (!302)(bfe43f20)
- **tools**: `ocpigr`: emit yaml instead of xml to support grc 3.8. (!306)(b2b8617d)
- **tools**: refactor ocpiadmin.sh and relocate to `tools/scripts/`. (!319)(f37f3732)

### Bug Fixes
- **devops**: fix hdl platforms building in pipelines when they shouldn't. (!317)(2c557552)
- **hdl base**: check for hdl target before building zynq primitive wrapper. (!326)(308f360e)
- **tools**: fix MANPATH and PYTHONPATH settings in "opencpi-setup.sh". (!323)(3312352c)
- **tools**: fix centos7 platform installation error when swig3 package not available. (!328)(8bf294e7)
- **tools**: fix incorrect package-ids in artifacts using top-level specs (not specs in libraries). (!321)(380f6c63)
- **tools**: fix ocpigr build issues. (!324)(543ab821)
- **tools**: suppress cross-compilation for items in `build/places` that use the `-t` flag. (!307)(894f6e81)

### Miscellaneous
- **devops**: remove CentOS 6 from CI pipeline. (!308)(5006cbc1)
- **devops,tools**: revamp OpenCPI RPM package production process. (!304)(2b62a34a)
- **doc**: update ubuntu* and centos8 platform README files. (!315)(77e3a53c)
- **osp**: exclude plutosdr in assets assemblies not capable of building. (!295)(a2c8fb98)

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
