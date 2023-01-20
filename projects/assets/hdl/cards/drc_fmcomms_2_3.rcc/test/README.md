# Description
Intended for use with [../../../../applications/drc_test/README.md](../../../../applications/drc_test/README.md)

# Dependencies
For now, this application was designed to be a minimal port of
the FSK application. Accordingly, it has similar dependencies. Additional work
could be done to make it more generic, and specific only to the FMCOMMS2/3
hardware.

- fsk_modem assembly on zed platform
- drc_fmcomms_2_3.rcc worker is built for the desired RCC platform
- file_read.rcc worker is built for the desired RCC platform
- file_write.rcc worker is built for the desired RCC platform
- Baudtracking_simple.rcc worker is built for the desired RCC platform
- real_digitizer.rcc worker is built for the desired RCC platform
