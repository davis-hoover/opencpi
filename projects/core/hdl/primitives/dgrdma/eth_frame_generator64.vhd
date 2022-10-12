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
entity eth_frame_generator64 is
  generic (
    DATA_WIDTH : natural := 64;
    KEEP_WIDTH : natural := 8
  );
  port(
    clk              : in std_logic;
    reset            : in std_logic;

    s_tx_axis_tdata  : in std_logic_vector((DATA_WIDTH-1) downto 0);
    s_tx_axis_tkeep  : in std_logic_vector((KEEP_WIDTH-1) downto 0);
    s_tx_axis_tvalid : in std_logic;
    s_tx_axis_tready : out std_logic;
    s_tx_axis_tlast  : in std_logic;

    s_tx_hdr_src_mac : in std_logic_vector(47 downto 0);
    s_tx_hdr_type    : in std_logic_vector(15 downto 0);

    m_tx_eth_tdata   : out std_logic_vector((DATA_WIDTH-1) downto 0);
    m_tx_eth_tkeep   : out std_logic_vector((KEEP_WIDTH-1) downto 0);
    m_tx_eth_tvalid  : out std_logic;
    m_tx_eth_tready  : in std_logic;
    m_tx_eth_tlast   : out std_logic;
    m_tx_eth_tuser   : out std_logic
  );
end entity;

architecture rtl of eth_frame_generator64 is
  type state_t is (S_IDLE, S_HEADER, S_PAYLOAD1, S_PAYLOAD, S_TLAST);
  signal state : state_t;

  signal m_tx_eth_tvalid_r : std_logic;
  signal s_tx_axis_tready_r : std_logic;

  signal src_mac_raw : std_logic_vector(47 downto 0);
  signal dest_mac_raw : std_logic_vector(47 downto 0);
  signal type_raw : std_logic_vector(15 downto 0);

  signal save_first_payload_beat : std_logic_vector(15 downto 0);

  signal state_i : natural;
begin
  state_i <= state_t'pos(state);

  -- Ethernet frame inputs in little-endian byte order for convenience
  src_mac_raw <= swap_bytes(s_tx_hdr_src_mac);
  type_raw <= swap_bytes(s_tx_hdr_type);

  -- always ready if we're waiting for first beat
  -- not ready while waiting for slave to accept Ethernet header
  -- otherwise ready if we are about to clock out data from pipeline register, or if it's empty
  with state select s_tx_axis_tready_r <=
    '1' when S_IDLE,
    '0' when S_HEADER | S_TLAST,
    m_tx_eth_tready or (not m_tx_eth_tvalid_r) when others;

  s_tx_axis_tready <= s_tx_axis_tready_r;
  m_tx_eth_tvalid <= m_tx_eth_tvalid_r;

  process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        state <= S_IDLE;
        m_tx_eth_tdata <= (others => '0');
        m_tx_eth_tkeep <= (others => '0');
        m_tx_eth_tlast <= '0';
        m_tx_eth_tuser <= '0';
        m_tx_eth_tvalid_r <= '0';
      else
        case state is
          when S_IDLE =>
            if s_tx_axis_tvalid = '1' then
              dest_mac_raw <= s_tx_axis_tdata(47 downto 0);
              save_first_payload_beat <= s_tx_axis_tdata(63 downto 48);
              m_tx_eth_tdata <= src_mac_raw(15 downto 0) & s_tx_axis_tdata(47 downto 0);
              m_tx_eth_tkeep <= X"ff";
              m_tx_eth_tvalid_r <= '1';
              state <= S_HEADER;
            end if;

          when S_HEADER =>
            if m_tx_eth_tready = '1' then
              m_tx_eth_tdata <= save_first_payload_beat & type_raw & src_mac_raw(47 downto 16);
              m_tx_eth_tkeep <= X"ff";
              state <= S_PAYLOAD1;
            end if;

          when S_PAYLOAD1 =>
            -- We are asserting m_tx_eth_tvalid. Wait for slave to accept first beat of frame,
            -- then pass through signals from master with one cycle delay
            if m_tx_eth_tready = '1' then
              m_tx_eth_tdata <= s_tx_axis_tdata;
              m_tx_eth_tkeep <= s_tx_axis_tkeep;
              m_tx_eth_tvalid_r <= s_tx_axis_tvalid;
              m_tx_eth_tlast <= s_tx_axis_tlast;
              if s_tx_axis_tlast = '1' then
                state <= S_TLAST;
              else
                state <= S_PAYLOAD;
              end if;
            end if;

          when S_PAYLOAD =>
            if s_tx_axis_tready_r = '1' then
              m_tx_eth_tdata <= s_tx_axis_tdata;
              m_tx_eth_tkeep <= s_tx_axis_tkeep;
              m_tx_eth_tvalid_r <= s_tx_axis_tvalid;
              m_tx_eth_tlast <= s_tx_axis_tlast;
              if s_tx_axis_tvalid = '1' and s_tx_axis_tlast = '1' then
                state <= S_TLAST;
              end if;
            end if;

          when S_TLAST =>
            if m_tx_eth_tready = '1' then
              m_tx_eth_tvalid_r <= '0';
              m_tx_eth_tlast <= '0';
              state <= S_IDLE;
            end if;
        end case;
      end if;
    end if;
  end process;

end rtl;
