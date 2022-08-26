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

entity eth_frame_generator128 is
  generic (
    DATA_WIDTH : natural := 128;
    KEEP_WIDTH : natural := 16
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

architecture rtl of eth_frame_generator128 is

type state_t is (S_IDLE, S_PAYLOAD, S_PAYLOAD_LAST, S_TLAST);
signal state : state_t;

signal m_tx_eth_tvalid_r  : std_logic;
signal s_tx_axis_tready_r : std_logic;

signal src_mac_raw  : std_logic_vector(47 downto 0);
signal type_raw     : std_logic_vector(15 downto 0);

signal tdata_r      : std_logic_vector(127 downto 0);
signal tkeep_r      : std_logic_vector(15 downto 0);

begin

  -- Ethernet frame inputs in little-endian byte order for convenience
  src_mac_raw <= swap_bytes(s_tx_hdr_src_mac);
  type_raw    <= swap_bytes(s_tx_hdr_type);

  -- output the valid and ready signals
  s_tx_axis_tready <= s_tx_axis_tready_r;
  m_tx_eth_tvalid  <= m_tx_eth_tvalid_r;

  -- indicate we are ready for more data
  with state select s_tx_axis_tready_r <=
      '1' when S_IDLE,
      '0' when S_PAYLOAD_LAST | S_TLAST,
      m_tx_eth_tready or (not m_tx_eth_tvalid_r) when others;

  process(clk)
  begin

    if rising_edge(clk) then
      if reset = '1' then
        state <= S_IDLE;
        tdata_r <= (others => '0');
        tkeep_r <= (others => '0');
        m_tx_eth_tdata <= (others => '0');
        m_tx_eth_tkeep <= (others => '0');
        m_tx_eth_tlast <= '0';
        m_tx_eth_tuser <= '0';
        m_tx_eth_tvalid_r <= '0';

      else

        case state is

          when S_IDLE =>
            if s_tx_axis_tvalid = '1' and s_tx_axis_tready_r = '1' then

              tdata_r <= s_tx_axis_tdata;
              tkeep_r <= s_tx_axis_tkeep;

              m_tx_eth_tdata(47 downto 0)    <= s_tx_axis_tdata(47 downto 0);
              m_tx_eth_tdata(95 downto 48)   <= src_mac_raw;
              m_tx_eth_tdata(111 downto 96)  <= type_raw;
              m_tx_eth_tdata(127 downto 112) <= s_tx_axis_tdata(63 downto 48);

              m_tx_eth_tkeep(13 downto 0)    <= b"11111111111111";
              m_tx_eth_tkeep(15 downto 14)   <= s_tx_axis_tkeep(7 downto 6);

              m_tx_eth_tvalid_r <= '1';

              if s_tx_axis_tlast = '1' and s_tx_axis_tkeep(15 downto 8) = b"00000000" then
                state <= S_TLAST;
                m_tx_eth_tlast <= '1';
              elsif s_tx_axis_tlast = '1' and s_tx_axis_tkeep(15 downto 8) /= b"00000000" then
                state <= S_PAYLOAD_LAST;
                m_tx_eth_tlast <= '0';
              else
                state <= S_PAYLOAD;
                m_tx_eth_tlast <= '0';
              end if;
            end if;

          when S_PAYLOAD =>
            if s_tx_axis_tready_r = '1' then

              m_tx_eth_tdata(63 downto 0)   <= tdata_r(127 downto 64);
              m_tx_eth_tdata(127 downto 64) <= s_tx_axis_tdata(63 downto 0);
              m_tx_eth_tkeep(7  downto 0)   <= tkeep_r(15 downto 8);
              m_tx_eth_tkeep(15 downto 8)   <= s_tx_axis_tkeep(7 downto 0);
              m_tx_eth_tvalid_r             <= s_tx_axis_tvalid;

              if s_tx_axis_tvalid = '1' then
                tdata_r <= s_tx_axis_tdata;
                tkeep_r <= s_tx_axis_tkeep;

                if s_tx_axis_tlast = '1' and s_tx_axis_tkeep(15 downto 8) = b"00000000" then
                  state <= S_TLAST;
                  m_tx_eth_tlast <= '1';
                elsif s_tx_axis_tlast = '1' and s_tx_axis_tkeep(15 downto 8) /= b"00000000" then
                  state <= S_PAYLOAD_LAST;
                  m_tx_eth_tlast <= '0';
                else
                  state <= S_PAYLOAD;
                  m_tx_eth_tlast <= '0';
                end if;
              end if;
            end if;

          when S_PAYLOAD_LAST =>
            -- output the buffered tdata
            -- we don't have to have more input data to do this
            if m_tx_eth_tready= '1' then

              state             <= S_TLAST;
              m_tx_eth_tlast    <= '1';
              m_tx_eth_tvalid_r <= '1';

              m_tx_eth_tdata(63 downto 0)   <= tdata_r(127 downto 64);
              m_tx_eth_tdata(127 downto 64) <= (others => '0');
              m_tx_eth_tkeep(7  downto 0)   <= tkeep_r(15 downto 8);
              m_tx_eth_tkeep(15 downto 8)   <= (others => '0');

            end if;

          when S_TLAST =>
            -- additional state used to drive the last signal low
            -- we don't have to have more input data to do this
            if m_tx_eth_tready= '1' then

              state             <= S_IDLE;
              m_tx_eth_tlast    <= '0';
              m_tx_eth_tvalid_r <= '0';

              m_tx_eth_tdata    <= (others => '0');
              m_tx_eth_tkeep    <= (others => '0');
            end if;

        end case;
      end if;
    end if;

  end process;

end rtl;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------