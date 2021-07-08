library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library platform; use platform.platform_pkg.all;
library unisim; use unisim.vcomponents.all;
--library bsv;
library axi; --use axi.axi_pkg.all;
library sdp; use sdp.sdp.all; --, sdp.sdp_axi.all;
library generic_pcie; use generic_pcie.generic_pcie_pkg.all;
             
architecture rtl of worker is
  signal sys_rst_n         : std_logic; --
  signal sys_clk_n         : std_logic; --125Mhz clock input
  signal sys_clk_p         : std_logic; --

  --
  signal global_in         : global_in_t;
  signal global_out        : global_out_t;
  signal msi_in            : msi_in_t;
  signal msi_out           : msi_out_t;
  signal pcie_in           : pcie_in_t;
  signal pcie_out          : pcie_out_t;
  
  -- AXI interfaces
  -- Master
  signal m_axi_in          : axi.pcie_m.axi_s2m_t;  -- Control plane
  signal m_axi_out         : axi.pcie_m.axi_m2s_t;  -- COntrol plane
  -- Slave
  signal s_axi_in          : axi.pcie_s.axi_m2s_t;  -- Data plane
  signal s_axi_out         : axi.pcie_s.axi_s2m_t;  -- Data plane

  -- General IO/Debug signals
  signal led_count         : unsigned(26 downto 0);
  signal one_hz            : std_logic;

  --signal leds              : std_logic_vector(2 downto 0);

  component generic_pcie is
    port (
      pcie_in     : in  pcie_in_t;
      pcie_out    : out pcie_out_t;

      global_in   : in  global_in_t;
      global_out  : out global_out_t;

      msi_in      : in  msi_in_t;
      msi_out     : out msi_out_t;

      -- Master (x1)
      m_axi_in    : in  axi.pcie_m.axi_s2m_t;
      m_axi_out   : out axi.pcie_m.axi_m2s_t;
      -- Slave (x1)
      s_axi_in    : in  axi.pcie_s.axi_m2s_t;
      s_axi_out   : out axi.pcie_s.axi_s2m_t
    );
  end component generic_pcie;

begin

bridge_pcie_axi : generic_pcie
  port map(

    pcie_in     => pcie_in,
    pcie_out    => pcie_out,

    global_in   => global_in,
    global_out  => global_out,

    msi_in      => msi_in,
    msi_out     => msi_out,

    -- Master (x1)
    m_axi_in    => m_axi_in,
    m_axi_out   => m_axi_out,
    -- Slave (x1)
    s_axi_in    => s_axi_in,
    s_axi_out   => s_axi_out
  );

  -- -- PCIe connections from generic_pcie module
  -- pcie_in.pcie_rxp    <= pcie_rxp;
  -- pcie_in.pcie_rxn    <= pcie_rxn;
  -- pcie_txp            <= pcie_out.pcie_txp;
  -- pcie_txn            <= pcie_out.pcie_txn;

  -- -- Differential system clock input 
  -- sys_clk_ibufds : BUFFER_IN_1
  --   generic map (
  --     IOSTANDARD   => UNSPECIFIED,
  --     DIFFERENTIAL => true,
  --     GLOBAL_CLOCK => true);
  --   port map (
  --     I    => sys_clk_p,
  --     IBAR => sys_clk_n,
  --     O    => sys_clk
  --     );

  -- -- Counter for blinking LED
  -- watchdog_count : process(sys_clk)
  --   variable count_var : unsigned (26 downto 0);
  --   variable one_hz_var : std_logic;
  -- begin
  --   if rising_edge(sys_clk) then
  --     if sys_rst_n = '0' then
  --       count_var  := d'625000000;
  --       one_hz_var := 0;
  --     else
  --       if count_var = d'0 then
  --         count_var  := d'625000000;
  --         one_hz_var := not watchdog_var;
  --       else 
  --         count_var  := count_var - 1;
  --         one_hz_var := watchdog_var;
  --       end if;
  --     end if;
  --   end if;
  -- led_count <= count_var; 
  -- one_hz    <= watchdog_var
  -- end process;

leds(0) <= one_hz;
leds(1) <= '0';
leds(2) <= '1';

end rtl;
