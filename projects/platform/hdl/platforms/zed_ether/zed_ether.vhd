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

-- THIS FILE WAS ORIGINALLY GENERATED ON Fri Feb 12 20:38:03 2021 UTC
-- BASED ON THE FILE: zed_ether.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: zed_ether

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library dgrdma; use dgrdma.dgrdma.all;
library unisim; use unisim.vcomponents.all;

architecture rtl of zed_ether_worker is
  signal clk        : std_logic;  -- 125MHz - general system clock
  signal clk_mac    : std_logic;  -- 125MHz - MAC clock
  signal clk_mac_90 : std_logic;  -- 125MHz at 90 degrees - used for Ethernet MAC

  signal reset      : std_logic;
  signal led_int    : std_logic_vector(7 downto 0);

  signal heartbeat : std_logic;
  subtype heartbeat_ctr_t is natural range 0 to (62500000 - 1); -- 1Hz flash at 125MHz
  signal heartbeat_ctr : heartbeat_ctr_t;

  signal local_mac_addr : std_logic_vector(47 downto 0);
  signal eth_speed_1    : std_logic_vector(1 downto 0);
  signal eth_speed_2    : std_logic_vector(1 downto 0);

  signal mac_addr_valid : std_logic;
  signal mac_addr_error : std_logic;

  signal sdp_reset : std_logic;
  signal reset_mac : std_logic;

begin

  -- Drive metadata interface - boiler plate
  metadata_out.clk     <= clk;
  metadata_out.romAddr <= props_in.romAddr;
  metadata_out.romEn   <= props_in.romData_read;

  -- Drive timekeeping interface - depends on which clock, and whether there is a PPS input
  timebase_out.clk      <= clk;
  timebase_out.usingPPS <= '0';
  timebase_out.pps      <= '0';

  props_out.dna             <= (others => '0');
  props_out.nSwitches       <= (others => '0');
  props_out.switches        <= (others => '0');
  props_out.memories_length <= to_ulong(1);
  props_out.memories        <= (others => to_ulong(0));
  props_out.nLEDs           <= to_ulong(0); --led'length);
  props_out.UUID            <= metadata_in.UUID;
  props_out.romData         <= metadata_in.romData;
  props_out.slotCardIsPresent <= (others => '0');

  -- Clock generation
  clk_125mhz_en <= '1';
  clkgen_inst : entity work.clock_gen
    port map (
        clkin_125mhz_p => clk_125mhz_p,
        clkin_125mhz_n => clk_125mhz_n,
        reset_in => '0',

        clk => clk,
        reset => reset,

        clk_mac => clk_mac,
        clk_mac_90 => clk_mac_90,
        reset_mac => reset_mac
      );

  -- Read MAC address from EEPROM (Microchip 24AA025E48) on reset
  read_macaddr_inst : entity work.i2c_macaddr_eeprom
    generic map(
      -- Note that the device address printed on the schematic and the user guide
      -- (0xA0) is incorrect: the default resistor straps set the address to 0xA2
      DEVICE_ADDR => "1010001",
      REG_ADDR => X"fa"
    )
    port map (
      clk => clk,
      reset => reset or btnd,

      eui48 => local_mac_addr,
      eui_valid => mac_addr_valid,
      eui_error => mac_addr_error,

      scl => mac_eeprom_scl,
      sda => mac_eeprom_sda
    );

  sdp_reset <= ctl_in.reset or btnc or dev_in(0).RESET;

  dgrdma_if : dual_rgmii_to_ocpi
    generic map (
      sdp_width => to_integer(sdp_width),
      ACK_TRACKER_BITFIELD_WIDTH => to_integer(ack_tracker_bitfield_width),
      ACK_TRACKER_MAX_ACK_COUNT  => to_integer(ack_tracker_max_ack_count)
    )
    port map (
      clk           => clk,
      clk_mac       => clk_mac,
      clk_mac_90    => clk_mac_90,
      reset         => reset,
      reset_mac     => reset_mac,
      sdp_reset     => sdp_reset,

      -- Configuration
      local_mac_addr        => local_mac_addr,
      remote_mac_addr       => dev_in(0).REMOTE_MAC_ADDR(47 downto 0),
      remote_dst_id         => dev_in(0).REMOTE_DST_ID,
      local_src_id          => dev_in(0).LOCAL_SRC_ID,
      interface_mtu         => unsigned(dev_in(0).INTERFACE_MTU),
      ack_wait              => unsigned(dev_in(0).ACK_WAIT),
      max_acks_outstanding  => unsigned(dev_in(0).MAX_ACKS_OUTSTANDING),
      coalesce_wait         => unsigned(dev_in(0).COALESCE_WAIT),
      dual_ethernet         => dev_in(0).DUAL_ETHERNET,
      ifg_delay             => unsigned'(X"0c"), -- 12 bytes = 96 bit times (minimum interframe gap)
      eth_speed_1           => eth_speed_1,
      eth_speed_2           => eth_speed_2,

      -- Control plane master
      cp_in => cp_in,
      cp_out => cp_out,

      -- SDP master
      sdp_in => ether_in,
      sdp_out => ether_out,
      sdp_in_data => ether_in_data,
      sdp_out_data => ether_out_data,

      -- RGMII interface 1
      phy_reset_n_1 => phy_reset_n_1,
      phy_int_n_1 => '1',
      phy_rx_clk_1 => phy_rx_clk_1,
      phy_rxd_1 => phy_rxd_1,
      phy_rx_ctl_1 => phy_rx_ctl_1,
      phy_tx_clk_1 => phy_tx_clk_1,
      phy_txd_1 => phy_txd_1,
      phy_tx_ctl_1 => phy_tx_ctl_1,

      -- RGMII interface 2
      phy_reset_n_2 => phy_reset_n_2,
      phy_int_n_2 => '1',
      phy_rx_clk_2 => phy_rx_clk_2,
      phy_rxd_2 => phy_rxd_2,
      phy_rx_ctl_2 => phy_rx_ctl_2,
      phy_tx_clk_2 => phy_tx_clk_2,
      phy_txd_2 => phy_txd_2,
      phy_tx_ctl_2 => phy_tx_ctl_2,

      -- Ack Tracker
      ack_tracker_rej_ack               => dev_out(0).ACK_TRACKER_REJ_ACK,
      ack_tracker_bitfield              => dev_out(0).ACK_TRACKER_BITFIELD,
      ack_tracker_base_seqno            => dev_out(0).ACK_TRACKER_BASE_SEQNO,
      ack_tracker_rej_seqno             => dev_out(0).ACK_TRACKER_REJ_SEQNO,
      ack_tracker_total_acks_sent       => dev_out(0).ACK_TRACKER_TOTAL_ACKS_SENT,
      ack_tracker_tx_acks_sent          => dev_out(0).ACK_TRACKER_TX_ACKS_SENT,
      ack_tracker_pkts_enqueued         => dev_out(0).ACK_TRACKER_PKTS_ENQUEUED,
      ack_tracker_reject_out_of_range   => dev_out(0).ACK_TRACKER_REJECT_OUT_OF_RANGE,
      ack_tracker_reject_already_set    => dev_out(0).ACK_TRACKER_REJECT_ALREADY_SET,
      ack_tracker_accepted_by_peek      => dev_out(0).ACK_TRACKER_ACCEPTED_BY_PEEK,
      ack_tracker_high_watermark        => dev_out(0).ACK_TRACKER_HIGH_WATERMARK,
      frame_parser_reject               => dev_out(0).FRAME_PARSER_REJECT
    );

  -- Display MAC address / status on Zedboard LEDs based on switch settings
  with sw(2 downto 0) select led <=
    led_int                      when "000",
    local_mac_addr(47 downto 40) when "001",
    local_mac_addr(39 downto 32) when "010",
    local_mac_addr(31 downto 24) when "011",
    local_mac_addr(23 downto 16) when "100",
    local_mac_addr(15 downto 8)  when "101",
    local_mac_addr(7 downto 0)   when "110",
    X"aa"                        when "111";

  led_int(0) <= heartbeat;
  led_int(1) <= mac_addr_valid;
  led_int(2) <= mac_addr_error;
  led_int(4 downto 3) <= eth_speed_1; -- "10" = 1000Mb/s
                                      -- "01" = 100Mb/s
                                      -- "00" = 10Mb/s
  led_int(6 downto 5) <= eth_speed_2;
  led_int(7) <= '1';

  -- Heartbeat LED
  process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        heartbeat_ctr <= 0;
        heartbeat <= '0';
      else
        if heartbeat_ctr = heartbeat_ctr_t'high then
          heartbeat_ctr <= 0;
          heartbeat <= not heartbeat;
        else
          heartbeat_ctr <= heartbeat_ctr + 1;
        end if;
      end if;
    end if;
  end process;

end rtl;
