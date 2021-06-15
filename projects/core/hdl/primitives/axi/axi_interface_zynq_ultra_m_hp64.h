// Define the zynq MP/ultrascale series M_AXI_GP AXI interface
// the OpenCPI VHDL wrapper module zynq_ultra_ps_e:
//   - has the (generated here) record interface
//   - wraps/instantiates the underlying VHDL interface zynq_ultra_ps_e_0
//   - does not change any generic parameters of zynq_ultra_ps_e_0
// the Xilinx VHDL wrapper component/entity zynq_ultra_ps_e_0:
//   - was generated from the GUI or TCL
//   - instantiates the underlying Verilog wrapper zynq_ultra_ps_e_v3_3_0_zynq_ultra_ps_e
//   - overrides the M_AXI_GP* default data wdith (128) to 32 (we only use GP0)
//   - overrides the S_AXI_GP1-6 default data width (128) to 64 (which opencpi does not use)
//   - sets other processor stuff - it represents all the processor options from generation
// We cannot avoid the extra VHDL wrapper in any case?
#define ADDR_WIDTH 40
#define ID_WIDTH 16
#define DATA_WIDTH 64 // The hardware can do up to 128
#define AXI4 1
