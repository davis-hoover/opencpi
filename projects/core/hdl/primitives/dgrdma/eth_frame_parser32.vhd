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

library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
use work.dgrdma_util.all;

-- strip Ethernet frame and place source MAC address on first 6 bytes of output
entity eth_frame_parser32 is
  generic (
    DATA_WIDTH : natural := 32;
    KEEP_WIDTH : natural := 4
  );
  port(
    clk               : in std_logic;
    reset             : in std_logic;

    s_rx_eth_tdata    : in std_logic_vector((DATA_WIDTH-1) downto 0);
    s_rx_eth_tkeep    : in std_logic_vector((KEEP_WIDTH-1) downto 0);
    s_rx_eth_tvalid   : in std_logic;
    s_rx_eth_tready   : out std_logic;
    s_rx_eth_tlast    : in std_logic;
    s_rx_eth_tuser    : in std_logic;

    m_rx_axis_tdata   : out std_logic_vector((DATA_WIDTH-1) downto 0);
    m_rx_axis_tkeep   : out std_logic_vector((KEEP_WIDTH-1) downto 0);
    m_rx_axis_tvalid  : out std_logic;
    m_rx_axis_tready  : in std_logic;
    m_rx_axis_tlast   : out std_logic;

    m_rx_hdr_src_mac  : out std_logic_vector(47 downto 0);
    m_rx_hdr_dest_mac : out std_logic_vector(47 downto 0);
    m_rx_hdr_type     : out std_logic_vector(15 downto 0)
  );
end entity;

architecture rtl of eth_frame_parser32 is
  type state_t is (S_IDLE, S_HEADER1, S_HEADER2, S_MAC, S_HEADER3, S_PAYLOAD1, S_PAYLOAD, S_TLAST);
  signal state : state_t;

  signal m_rx_axis_tvalid_r : std_logic;
  signal s_rx_eth_tready_r : std_logic;

  -- Wide fields appear on 64-bit AXIS interface in little-endian byte order
  signal src_mac_raw : std_logic_vector(47 downto 0);
  signal dest_mac_raw : std_logic_vector(47 downto 0);
  signal type_raw : std_logic_vector(15 downto 0);

  -- First 2 bytes of payload
  signal saved_payload : std_logic_vector(15 downto 0);

  signal state_i : natural;
begin
  state_i <= state_t'pos(state);

  -- Interpret Ethernet frame outputs in network byte order for convenience
  m_rx_hdr_src_mac <= swap_bytes(src_mac_raw);
  m_rx_hdr_dest_mac <= swap_bytes(dest_mac_raw);
  m_rx_hdr_type <= swap_bytes(type_raw);

  -- always ready if we're waiting for header
  -- otherwise ready if we are about to clock out data from pipeline register, or if it's empty
  with state select s_rx_eth_tready_r <=
    '1' when S_IDLE | S_HEADER1 | S_HEADER2 | S_HEADER3,
    '0' when S_TLAST | S_MAC,
    m_rx_axis_tready or (not m_rx_axis_tvalid_r) when others;

  s_rx_eth_tready <= s_rx_eth_tready_r;
  m_rx_axis_tvalid <= m_rx_axis_tvalid_r;

  process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        state <= S_IDLE;
        m_rx_axis_tvalid_r <= '0';
        m_rx_axis_tlast <= '0';
        m_rx_axis_tdata <= (others => '0');
        m_rx_axis_tkeep <= (others => '0');

        src_mac_raw <= (others => '0');
        dest_mac_raw <= (others => '0');
        type_raw <= (others => '0');
      else
        case state is
          when S_IDLE =>
            -- We are asserting s_rx_eth_tready. Wait for first beat of Ethernet frame
            if s_rx_eth_tvalid = '1' then
              dest_mac_raw(31 downto 0) <= s_rx_eth_tdata(31 downto 0);
              state <= S_HEADER1;
            end if;

          when S_HEADER1 =>
            if s_rx_eth_tvalid = '1' then
              dest_mac_raw(47 downto 32) <= s_rx_eth_tdata(15 downto 0);
              src_mac_raw(15 downto 0) <= s_rx_eth_tdata(31 downto 16);
              state <= S_HEADER2;
            end if;

          when S_HEADER2 =>
            if s_rx_eth_tvalid = '1' then
              src_mac_raw(47 downto 16) <= s_rx_eth_tdata(31 downto 0);
              state <= S_HEADER3;
            end if;

          when S_HEADER3 =>
            if s_rx_eth_tvalid = '1' then
              type_raw <= s_rx_eth_tdata(15 downto 0);
              saved_payload <= s_rx_eth_tdata(31 downto 16);

              -- First 32 bits of MAC
              m_rx_axis_tdata <= src_mac_raw(31 downto 0);
              m_rx_axis_tkeep <= X"f";

              m_rx_axis_tvalid_r <= '1';
              state <= S_MAC;
            end if;

          when S_MAC =>
            if m_rx_axis_tready = '1' then
              -- Rest of MAC and saved first 2 bytes of payload data
              m_rx_axis_tdata <= saved_payload & src_mac_raw(47 downto 32);
              state <= S_PAYLOAD1;
            end if;

          when S_PAYLOAD1 =>
            -- We are asserting m_rx_axis_tvalid. Wait for slave to accept first beat of frame,
            -- then pass through signals from master with one cycle delay
            if m_rx_axis_tready = '1' then
              m_rx_axis_tvalid_r <= s_rx_eth_tvalid;
              m_rx_axis_tdata <= s_rx_eth_tdata;
              m_rx_axis_tkeep <= s_rx_eth_tkeep;
              m_rx_axis_tlast <= s_rx_eth_tlast;

              if s_rx_eth_tlast = '1' then
                state <= S_TLAST;
              else
                state <= S_PAYLOAD;
              end if;
            end if;

          when S_PAYLOAD =>
            if s_rx_eth_tready_r = '1' then
              m_rx_axis_tdata <= s_rx_eth_tdata;
              m_rx_axis_tkeep <= s_rx_eth_tkeep;
              m_rx_axis_tvalid_r <= s_rx_eth_tvalid;
              m_rx_axis_tlast <= s_rx_eth_tlast;
              if s_rx_eth_tvalid = '1' and s_rx_eth_tlast = '1' then
                state <= S_TLAST;
              end if;
            end if;

          when S_TLAST =>
            if m_rx_axis_tready = '1' then
              m_rx_axis_tvalid_r <= '0';
              m_rx_axis_tlast <= '0';
              state <= S_IDLE;
            end if;
        end case;
      end if;
    end if;
  end process;

end rtl;
