// Define the generic PCIe slave to master interface
// This is the interface where the PCIE bridge is acting as a PCIE master, and this is an AXI slave for the data plane.
#define ADDR_WIDTH 32
#define ID_WIDTH 6
#define DATA_WIDTH 64
#define CLOCK_FROM_MASTER 1
#define RESET_FROM_MASTER 1  
#define AXI4 1
