# Description
This application performs hardware-in-the-loop testing for any
DRC worker. A radio-specific OAS XML is used by passing its path as an argument.
A radio-specific CSV file with test cases is used by passing its path as an
additional argument. This application is intended to perform basic tests to
ensure that the ranges of allowable values are properly enforced for sampling
rate, analog RF bandwidth, tuning frequency, gain, and gain modes (AGC/manual).

# Maturity
This application has been successfully tested with the Zed/FMCOMMS3 hardware
using assets/hdl/card/drc_fmcomms_2_3.rcc (which is single-configuration only).
It has NOT been robustly tested against CSV files, and it is easy to
malform the CSV - please take care in constructing the file and rely
on examples/spreadsheet software as needed.

# Portability
This application is portable to any RCC/HDL container. The OCPI_LIBRARY_PATH
environment variable is intended to be used to enforce use of a particular
DRC worker. The test values in the CSV file fed
in the ACI are specific to the FMCOMMS3 transceiver card.

# Dependencies
The dependencies are specific to whatever OAS XML is used. Refer to the
documentation associated with the OAS XML. For example, if using
[../../hdl/cards/drc_fmcomms_2_3.rcc/test/drc_fmcomms_2_3_test.xml](../../hdl/cards/drc_fmcomms_2_3.rcc/test/drc_fmcomms_2_3_test.xml), see 
[../../hdl/cards/drc_fmcomms_2_3.rcc/test/README.md](../../hdl/cards/drc_fmcomms_2_3.rcc/test/README.md)

# Synopsis
```console
drc_test <path/to/oas.xml> <path/to/test_cases.csv>
```
An example usage for the FMCOMMS2/3 when run from this application directory:
```console
export OCPI_LIBRARY_PATH=../../hdl/cards/drc_fmcomms_2_3.rcc/:$OCPI_LIBRARY_PATH
export OAS_PATH=../../hdl/cards/drc_fmcomms_2_3.rcc/test/drc_fmcomms_2_3_test.xml
export TEST_CASES_PATH=../../hdl/cards/drc_fmcomms_2_3.rcc/test/drc_fmcomms_2_3_test.csv
drc_test -o $OAS_PATH -t $TEST_CASES_PATH
```

# Success Criteria
Application runs and exits with a status of 0.

# CSV Test Case File Format
The explicit CSV test file requirements are as follows. Note that example CSVs are also a good starting point [../../hdl/cards/drc_fmcomms_2_3_rx.rcc/test/drc_fmcomms_2_3_test.csv](../../hdl/cards/drc_fmcomms_2_3.rcc/test/drc_fmcomms_2_3_test.csv). All fields within the CSV file are concepts that originate from the DRC briefing and component specification.
   - The file must contain comma-separated columns
   - The file must include a header line
   - The order of the column values must correspond to the order of the following fields: transition,configuration,channel,rx,tuning_freq_MHz,bandwidth_3dB_MHz,sampling_rate_Msps,samples_are_complex,gain_mode,gain_dB,tolerance_tuning_freq_MHz,tolerance_bandwidth_3dB_MHz,tolerance_sampling_rate_Msps,tolerance_gain_dB,rf_port_name,fatal,comment
   - Each row's transition column (after the header row, i.e. second row or later) must be one of: "" (empty string), "start", "stop", "prepare", or "release"
   - Each row's configuration column (second row or later) must always include a value in the unsigned integer format
   - Each row's channel columns (second row or later) must be of an unsigned integer format, if the transition column is non-empty
   - Each row's rx, samples_are_complex, and fatal columns (second row or later) must be one of: "" (empty string), "true", or "false", if the transition column is non-empty
   - Each row's tuning_freq_MHz, bandwidth_3dB_MHz, sampling_rate_Msps, and tolerance... columns (second row or later) must contain either "" (empty string) or a double-precision floating point value, if the transition column is non-empty

Additional application handling behavior to note:
   - If a row's transition column (second row or later) is non-empty, the following values for that row are all ignored: channel, rx, tuning_freq_MHz, bandwidth_3dB_MHz, sampling_rate_Msps, samples_are_complex, gain_mode, gain_dB, and all tolerance... columns
   - The rows of the file are applied in row order (the order of DRC state transitions matter, and must be tested!!)
   - It is typical to apply a configuration first (row has "" transition), and apply subsequent transitions for the already supplied configuration
   - The comment column is for convenience and its value is not used by the application

The following CSV contents exemplify a single test case with a
single configuration (0),
single channel (0),
tuning frequency of 1,000 MHz,
analog bandwidth of 10 MHz,
sampling rate of 20 Msps,
using complex samples,
with manual gain set to 0 dB.
The configuration is applied first via a write to the configuration property,
then the start transition is issued.
This test case/configuration is expected to succeed in entering the operating
state (since fatal=false).
It requests a channel by direction only (rx=true) as it does not specify a
specific RF port (rf_port_name empty).
```console
transition,configuration,channel,rx,tuning_freq_MHz,bandwidth_3dB_MHz,sampling_rate_Msps,samples_are_complex,gain_mode,gain_dB,tolerance_tuning_freq_MHz,tolerance_bandwidth_3dB_MHz,tolerance_samplng_rate_Msps,tolerance_gain_dB,rf_port_name,fatal,comment
,0,0,true,1000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,,,request by direction=rx
start,0,,,,,,,,,,,,,,false,start with no fatal error
release,0,,,,,,,,,,,,,,,
```

The following contents exemplify a similar test case but also constraining the
configuration to a particular RF port named Rx0.
```console
transition,configuration,channel,rx,tuning_freq_MHz,bandwidth_3dB_MHz,sampling_rate_Msps,samples_are_complex,gain_mode,gain_dB,tolerance_tuning_freq_MHz,tolerance_bandwidth_3dB_MHz,tolerance_samplng_rate_Msps,tolerance_gain_dB,rf_port_name,fatal,comment
,0,0,true,1000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,Rx0,,request by rf_port_name=Rx0
start,0,,,,,,,,,,,,,,true,start with fatal error
release,0,,,,,,,,,,,,,,,
```

The following contents exemplify a similar test case but with a tuning frequency
that is outside of the known valid ranges of the underlying hardware
(10,000 MHz) and is therefore expecting a fatal program error (fatal=true)
resulting in the DRC entering the error state instead of operating.
```console
transition,configuration,channel,rx,tuning_freq_MHz,bandwidth_3dB_MHz,sampling_rate_Msps,samples_are_complex,gain_mode,gain_dB,tolerance_tuning_freq_MHz,tolerance_bandwidth_3dB_MHz,tolerance_samplng_rate_Msps,tolerance_gain_dB,rf_port_name,fatal,comment
,0,0,true,10000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,Rx0,,request by rf_port_name=Rx0
start,0,,,,,,,,,,,,,,true,start with fatal error
release,0,,,,,,,,,,,,,,,
```

Single configuration, multi-channel test cases are formed using an empty transition field for multiple subsequent rows with increase channel indices, and then issuing a start.
```console
transition,configuration,channel,rx,tuning_freq_MHz,bandwidth_3dB_MHz,sampling_rate_Msps,samples_are_complex,gain_mode,gain_dB,tolerance_tuning_freq_MHz,tolerance_bandwidth_3dB_MHz,tolerance_samplng_rate_Msps,tolerance_gain_dB,rf_port_name,fatal,comment
,0,0,true,1000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,Rx0,,request by rf_port_name=Rx0
,0,1,true,1000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,Rx0,,request by rf_port_name=Rx1
,0,2,true,1000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,Tx0,,request by rf_port_name=Tx0
,0,3,true,1000,10,20,true,manual,0,1E-06,0.000001,0.000001,0.000001,Tx1,,request by rf_port_name=Tx1
start,0,,,,,,,,,,,,,,false,now actually start all channels 0-3 for configuration 0
release,0,,,,,,,,,,,,,,,
```

# Log Output
The following exemplifies what the first test case should look like for a
single config, single channel; that is, a single config/channel followed by the
start transition.
The fatal=0 indicates that the configuration was expected to succeed; that is,
no fatal error
was expected to occur. The PASS indicates that the expected, or tested-for
behavior occured, therefore the test case passed. Note that the corresponding
line numbers for the original CSV file provided to the application are
included for convenience.
```console
[INFO]     : csv_line 2:      cfg=0,ch=0,rx=0,fc=2450,bw=2.50062,fs=0.9375,sc=1,gm=man,gn=0,fct=1e-06,bwt=1e-06,fst=1e-06,gnt=1e-06,rf=
[INFO] PASS: csv_line 3: start: cfg=0,fatal=0
```

The following exemplifies a second test case. A release transition is issued
first, in order to release the previously operating configuration 0
from the aforementioned csv_line 3. This case tests a slightly different
tuning frequency (fc).
```console
[INFO]     : csv_line 4: start: cfg=0,fatal=0
[INFO]     : csv_line 5:      cfg=0,ch=0,rx=0,fc=2451,bw=2.50062,fs=0.9375,sc=1,gm=man,gn=0,fct=1e-06,bwt=1e-06,fst=1e-06,gnt=1e-06,rf=
[INFO] PASS: csv_line 6: start: cfg=0,fatal=0
```

The following exemplifies a new CSV file which does not behave as expected,
indicating a potential bug in the underlying DRC worker.
It has a single test case which is expected to be fatal (fatal=1, i.e.
not expected to succesfully move into the operating state), but it suceeds
anyway. This is displayed by the unexpected FAIL indicated. This
type of behavior is often indicative of an incorrectly written
Configurator/CSPSolver. Turning up the log info is expected to
provide useful debugging info.
```console
[INFO]     : csv_line 2:      cfg=0,ch=0,rx=0,fc=6000,bw=2.50062,fs=0.9375,sc=1,gm=man,gn=0,fct=1e-06,bwt=1e-06,fst=1e-06,gnt=1e-06,rf=
[INFO] FAIL: csv_line 3: start: cfg=0,fatal=1
[INFO] FAIL
```
