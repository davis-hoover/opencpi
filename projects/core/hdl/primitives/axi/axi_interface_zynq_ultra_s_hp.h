// Define the zynq ultrascale series S_AXI_HP AXI interface
#define ADDR_WIDTH 49
#define ID_WIDTH 6
#define DATA_WIDTH 64 // can do 32 or 128 too...
#define CLOCK_FROM_MASTER 1 // The PL get's to clock the interface since it has a hardware CDC
#define RESET_FROM_MASTER 1 // In fact the hardware has no per-interface AXI reset, which is out of AXI spec...
#define AXI4 1
