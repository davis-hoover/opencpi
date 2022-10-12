-- This file is protected by Copyright. Please refer to the COPYRIGHT file
-- distributed with this source distribution.
--
-- This file is part of OpenCPI <http://www.opencpi.org>
--
-- OpenCPI is free software: you can redistribute it and/or modify it under the
-- terms of the GNU Lesser General Public License as published by the Free
-- Software Foundation, either version 3 of the License, or (at your option) any
-- later version.
--
-- OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
-- WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
-- A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
-- details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.

library ieee; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library i2c, platform;

entity i2c_macaddr_eeprom is
  generic (
    -- Defaults correct for Microchip 28AA02E48 on Avnet FMC Network card
    -- Note that the device address printed on the schematic and the user guide
    -- (0xA0) is incorrect: the default resistor straps set the address to 0xA2
    DEVICE_ADDR : std_logic_vector(6 downto 0) := "1010001";
    REG_ADDR : unsigned(7 downto 0) := X"fa";
    PRESCALE : unsigned(15 downto 0) := to_unsigned(312, 16)  -- 400kHz from 125MHz clock
  );
  port (
    clk : in std_logic;
    reset : in std_logic;

    eui48 : buffer std_logic_vector(47 downto 0);
    eui_valid : out std_logic;
    eui_error : out std_logic;

    scl : inout std_logic;
    sda : inout std_logic
  );
end i2c_macaddr_eeprom;

architecture rtl of i2c_macaddr_eeprom is
  type state_t is (IDLE, READ1, READ2, FINISHED, ERR);
  signal state : state_t;

  signal read_en : std_logic;
  signal rdata : std_logic_vector(31 downto 0);
  signal addr : std_logic_vector(7 downto 0);
  signal number_of_bytes : std_logic_vector(2 downto 0);
  signal done : std_logic;
  signal error : std_logic;

  signal scl_i : std_logic;
  signal scl_o : std_logic;
  signal scl_oen : std_logic;

  signal sda_i : std_logic;
  signal sda_o : std_logic;
  signal sda_oen : std_logic;
begin
  with state select eui_valid <=
    '1' when FINISHED,
    '0' when others;
  with state select eui_error <=
    '1' when ERR,
    '0' when others;

  -- open-drain drivers for SCL and SDA
  scl_iobuf : platform.platform_pkg.TSINOUT_1
    port map(
      I => '0',
      O => scl_i,
      OE => not (scl_o or scl_oen),
      IO => scl
    );

  sda_iobuf : platform.platform_pkg.TSINOUT_1
    port map(
      I => '0',
      O => sda_i,
      OE => not (sda_o or sda_oen),
      IO => sda
    );

  process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        eui48 <= (others => '0');
        state <= IDLE;
      else
        case state is
          when IDLE =>
            read_en <= '1';
            addr <= std_logic_vector(REG_ADDR);
            number_of_bytes <= "010";
            state <= READ1;

          when READ1 =>
            if error = '1' then
              state <= ERR;
            elsif done = '1' then
              addr <= std_logic_vector(REG_ADDR + 2);
              number_of_bytes <= "100";
              eui48(47 downto 40) <= rdata(23 downto 16);
              eui48(39 downto 32) <= rdata(31 downto 24);
              state <= READ2;
            end if;

          when READ2 =>
            if error = '1' then
              state <= ERR;
            elsif done = '1' then
              read_en <= '0';
              eui48(31 downto 24) <= rdata(7 downto 0);
              eui48(23 downto 16) <= rdata(15 downto 8);
              eui48(15 downto 8) <= rdata(23 downto 16);
              eui48(7 downto 0) <= rdata(31 downto 24);
              state <= FINISHED;
            end if;

          when others =>
            read_en <= '0';
        end case;
      end if;
    end if;
  end process;

  i2c_inst : i2c.i2c.i2c_opencores_ctrl
    generic map(
      CLK_CNT => PRESCALE
    )
    port map(
      wci_clk => clk,
      wci_reset => reset,

      number_of_bytes => number_of_bytes,
      addr => addr,
      is_read => read_en,
      is_write => '0',
      slave_addr => DEVICE_ADDR,

      wdata => (others => '0'),
      rdata => rdata,
      done => done,
      error => error,
      scl_i => scl_i,
      scl_o => scl_o,
      scl_oen => scl_oen,
      sda_i => sda_i,
      sda_o => sda_o,
      sda_oen => sda_oen
    );

end rtl;
