# Description
This application performs hardware-in-the-loop testing for any
drc worker. A radio-specific OAS XML is used by passing its path as an argument.
A radio-specific CSV file with test cases is used by pass its path as an
additional argument. This application is intended to perform basic tests to
ensure that the ranges of allowable values are properly enforced for sampling
rate, analog RF bandwidth, tuning frequency, gain, and gain modes (AGC/manual).

# Maturity
This application has been successfully tested with the Zed/FMCOMMS3 hardware
using assets/hdl/card/drc_fmcomms_2_3.rcc (which is single-configuration only).

# CSV Test Case File Format
The explicit CSV test file requirements are as follows, but example CSVs are also a good starting point (../../hdl/cards/drc_fmcomms_2_3_rx.rcc/test/drc_fmcomms_2_3_rx_test.csv). All fields within the CSV file are concepts that originate from the DRC briefing and component specification.
   - Must contain comma-separated columns
   - There must be a header line
   - The order of the column values must correspond to the following order: transition,configuration,channel,rx,tuning_freq_MHz,bandwidth_3dB_MHz,sampling_rate_Msps,samples_are_complex,gain_mode,gain_dB,tolerance_tuning_freq_MHz,tolerance_bandwidth_3dB_MHz,tolerance_samplng_rate_Msps,tolerance_gain_dB,rf_port_name,fatal,comment
   - The transition column (second row or later) must be one of: "" (empty string, writes configuration property but does not issue a transition) "start", "stop", "prepare", or "release"
   - If the configuration row (second row or later) is non-empty, the application first writes the row's configuration (via the drc configuration property) and then issues any specified transition if the transition is non-empty
   - If the "start", "stop", "prepare", and "release" transitions are specified, it causes the application to issue that particular transition (as a write to the corresponding property) for the specified configuration
   - The rows of the CSV are applied in order (DRC state matters, and must be tested!!)
   - If "stop", or "release" transitions are used in a row, the following values for that row are all ignored: configuration, channel, rx, tuning_freq_MHz, bandwidth_3dB_MHz, sampling_rate_Msps, samples_are_complex, gain_mode, gain_dB, and all tolerance fields
   - The configuration and channel columns (second row or later) must be of an unsigned format
   - The rx, samples_are_complex, and fatal columns (second row or later) must contain either 1) nothing, 2) the string "true", or 3) the string "false".
   - The tuning_freq_MHz, bandwidth_3dB_MHz, sampling_rate_Msps, rx and fatal lines must contain either 1) nothing, 2) the string "true", or 3) the string "false".
   - The comment column is for convenience and its value is not used anywhere
The following CSV contents exemplify a single test case with a
single configuration (0),
single channel (0),
tuning frequency of 1,000 MHz,
analog bandwidth of 10 MHz,
samping rate of 20 Msps,
using complex samples,
with manual gain set to 0 dB.
The configuration is applied first via a write to the configuration property,
then the start transition is issued.
This test case/configuration is expected to suceed in entering the operating
state (since fatal=false).
It requests a channel by direction only (rx=true) as it does not specify a
specific RF port (rf_port_name empty).
```console
transition,configuration,channel,rx,tuning_freq_MHz,bandwidth_3dB_MHz,sampling_rate_Msps,samples_are_complex,gain_mode,gain_dB,tolerance_tuning_freq_MHz,tolerance_bandwidth_3dB_MHz,tolerance_samplng_rate_Msps,tolerance_gain_dB,rf_port_name,fatal,comment
start,0,0,true,1000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,,false,request by direction=rx
```console

The following contents exemplify a similar test case but also contraining the
configuration to a particular RF port named Rx0.
```console
transition,configuration,channel,rx,tuning_freq_MHz,bandwidth_3dB_MHz,sampling_rate_Msps,samples_are_complex,gain_mode,gain_dB,tolerance_tuning_freq_MHz,tolerance_bandwidth_3dB_MHz,tolerance_samplng_rate_Msps,tolerance_gain_dB,rf_port_name,fatal,comment
start,0,0,true,1000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,Rx0,false,request by rf_port_name=Rx0
```console

The following contents exemplify a similar test case but with a tuning frequency
that is outside of the known valid ranges of the underlying hardware
(10,000 MHz) and is therefore expecting a fatal program error (fatal=true)
resulting in the drc entering the error state instead of operating.
```console
transition,configuration,channel,rx,tuning_freq_MHz,bandwidth_3dB_MHz,sampling_rate_Msps,samples_are_complex,gain_mode,gain_dB,tolerance_tuning_freq_MHz,tolerance_bandwidth_3dB_MHz,tolerance_samplng_rate_Msps,tolerance_gain_dB,rf_port_name,fatal,comment
start,0,0,true,10000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,Rx0,true,request by rf_port_name=Rx0
```console

Single configuration, multi-channel configurations are issued by using an empty transition field for multiple subsequent rows with increase channel indices, and then issuing a start.
```console
transition,configuration,channel,rx,tuning_freq_MHz,bandwidth_3dB_MHz,sampling_rate_Msps,samples_are_complex,gain_mode,gain_dB,tolerance_tuning_freq_MHz,tolerance_bandwidth_3dB_MHz,tolerance_samplng_rate_Msps,tolerance_gain_dB,rf_port_name,fatal,comment
,0,0,true,1000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,Rx0,false,request by rf_port_name=Rx0
,0,1,true,1000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,Rx0,false,request by rf_port_name=Rx1
,0,2,true,1000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,Tx0,false,request by rf_port_name=Tx0
,0,3,true,1000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,Tx1,false,request by rf_port_name=Tx1
start,0,,,,,,,,,,,,,,true,now actually start 
```console

# Portability
This application is portable to any RCC/HDL container. The OCPI_LIBRARY_PATH
environment variable is intended to be used to enforce use of a particular
DRC worker. The test values in the CSV file fed
in the ACI are specific to the FMCOMMS3 transceiver card.

# Synopsis
```console
drc_test <drc_oas.xml> <hardware_test_cases.csv>
```
An example usage for the FMCOMMS2/3 when run from this application directory:
```console
export OCPI_LIBRARY_PATH=../../hdl/cards/drc_fmcomms_2_3.rcc/:$OCPI_LIBRARY_PATH
export APP_OAS=../../hdl/cards/drc_fmcomms_2_3.rcc/test/drc_fmcomms_2_3_test.xml
export APP_CSV=../../hdl/cards/drc_fmcomms_2_3.rcc/test/drc_fmcomms_2_3_test.csv
drc_test $APP_OAS $APP_CSV
```

# Maturity
Runs and passes on Zed/FMCOMMS3 hardware (tested using xilinx19_2_aarch32 RCC
platform) using the example synopsis described above.

# Dependencies
The dependencies are specific to whatever OAS XML is used. Refer to the
documentation associated with the OAS XML. For example, if using
../../hdl/cards/drc_fmcomms_2_3.rcc/test/drc_2_3_test.xml, see 
../../hdl/cards/drc_fmcomms_2_3.rcc/test/README.md

# Success Criteria
Application runs and exits with a status of 0.

# Example Output
```console
[INFO]      set:        cfg=0,ch=0,rx=1,fc=2450,bw=0.9375,fs=0.9375,sc=1,gm=man,gn=0,fct=1e-06,bwt=1e-06,fst=1e-06,gnt=1e-06,rf=,fatal=0
ad9361_init : AD936x Rev 2 successfully initialized
[INFO] PASS start:      cfg=0
[INFO]      release:    cfg=0
[INFO]      set:        cfg=0,ch=0,rx=1,fc=69.99,bw=0.9375,fs=0.9375,sc=1,gm=man,gn=0,fct=1e-06,bwt=1e-06,fst=1e-06,gnt=1e-06,rf=,fatal=1
[INFO] PASS start:      cfg=0
[INFO]      release:    cfg=0
...
[INFO]      set:        cfg=0,ch=0,rx=1,fc=70,bw=0.9375,fs=0.9375,sc=1,gm=man,gn=0,fct=1e-06,bwt=1e-06,fst=1e-06,gnt=1e-06,rf=Rx0,fatal=0
[INFO] PASS start:      cfg=0                                                                                        
[INFO] PASS     
```
