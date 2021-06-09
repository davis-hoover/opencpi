// Define the zynq 7 series S_AXI_HP AXI interface
#define ADDR_WIDTH 32
#define ID_WIDTH 6
#define DATA_WIDTH 64
#define CLOCK_FROM_MASTER 1
// Even though this signal is present on the Zynq PS primitive module, it is not asserted on bitstream load
// So we instead rely on the FCLK_RESET signal instead.
#define RESET_FROM_MASTER 1
