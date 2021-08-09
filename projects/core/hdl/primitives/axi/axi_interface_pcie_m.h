// Define the generic PCIe master to slave interface
// This is the interface where the PCIE bridge is acting as a PCIE slave and thus an AXI master for the control plane.
#define ADDR_WIDTH 32
#define ID_WIDTH 6
#define DATA_WIDTH 32
#define CLOCK_FROM_MASTER 1
#define RESET_FROM_MASTER 1
#define AXI4 1
