## N Workers Application 
This is a nontraditional OpenCPI application directory.

Due to a bug within the OpenCPI application matching algorithm (https://gitlab.com/opencpi/opencpi/-/issues/3632) the same component can't be instantiated multiple times within one application.
Therefore, the need arose to have this non standard application directory where components, assembly, and application files are generated via scripts.

### Files
- generate.py: Python file that will generate the the component, assembly, and application files. See script's help for input / output details.
- verify.py: Python file that will verify the number of test bias workers that ran in the application.
- data.input: Binary data used as the input read into the application.

### Prerequisites to Running Test Procedure
Examples listed after each step, commands run from OpenCPI root directory.
1. Install OpenCPI       |  `./scripts/install-opencpi.sh --minimal` 
2. Install RCC Platform  |  `ocpiadmin install platform xilinx19_2_aarch64 --minimal` 
3. Install HDL Platform  |  `ocpiadmin install platform zcu106 --minimal` 
4. Setup Environment     |  `export OCPI_SERVER_ADDRESSES=<platform_ip>:12345 && export OCPI_SOCKET_INTERFACE=<host_interface> && export OCPI_TRANSFER_IP_ADDRESS=<host_ip>`
5. Load Platform         |  `ocpiremote load --rcc-platform xilinx19_2_aarch64 --hdl-platform zcu106`
6. Start Platform        |  `ocpiremote start -b`
7. Verify Container      |  `ocpirun -C`

### Test Procedure
Examples listed after each step, commands run from n_workers_test_app directory.
1. Run the generate.py script  |  `./generate.py -n 123 -o ubuntu20_04`
2. Build generated workers     |  `cd ../../components && ocpidev build --hdl-platform zcu106 && cd -`
3. Build generated assembly    |  `cd ../../hdl/assemblies/<generated_assembly_dir> && ocpidev build --hdl-platform zcu106 && cd -`
4. Run application             |  `OCPI_LIBRARY_PATH=../../artifacts/:../../../core/artifacts/ ocpirun -v n_workers_<number>.xml`
5. Run verify.py script        |  `./verify.py -n 123`

### Special Note:
On Test Procedure step #2, when building the workers, if there are too many components in the directory ocpidev seems to error.
So the following command can be run from the `components` directory to build each of the components for the given platform:
`find . -maxdepth 1 -type d \( ! -name . \) -exec bash -c "cd '{}' && ocpidev build --hdl-platform zcu106" \;`

In addition, the generate and verify scripts do not limit the number of bias_vhdl components created. 
However, the OpenCPI framework currently only handles 127 max workers including the infrastructure workers.
So, 123 is the maximum number of bias_vhdl workers allowed at this time plus 2 file IO workers plus 2 infrastructure workers.