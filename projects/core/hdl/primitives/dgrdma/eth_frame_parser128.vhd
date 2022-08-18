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

-- ---------------------------------------------------------------------------
-- This is the 128 bit data width version of the ethernet frame parser
-- It parses incoming Ethernet Frame, stripping out the ether-type, source and
-- destination MAC addresses.
-- The source MAC address is placed in the first 6 bytes of output
-- ---------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
use work.dgrdma_util.all;


entity eth_frame_parser128 is
  generic (
    DATA_WIDTH : natural := 128;
    KEEP_WIDTH : natural := 16
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

architecture rtl of eth_frame_parser128 is

type state_t is (S_IDLE, S_HEADER, S_PAYLOAD, S_PAYLOAD_LAST, S_TLAST);
signal state : state_t;

signal dest_mac_raw       : std_logic_vector(47 downto 0);
signal src_mac_raw        : std_logic_vector(47 downto 0);
signal type_raw           : std_logic_vector(15 downto 0);
signal tdata_r            : std_logic_vector(127 downto 0);
signal tkeep_r            : std_logic_vector(15 downto 0);
signal tlast_r            : std_logic;

-- our output down-stream valid
signal m_rx_axis_tvalid_r : std_logic;

-- our output up-stream ready
signal s_rx_eth_tready_r  : std_logic;

begin

    -- Interpret Ethernet frame outputs in network byte order for convenience
    m_rx_hdr_src_mac  <= swap_bytes(src_mac_raw);
    m_rx_hdr_dest_mac <= swap_bytes(dest_mac_raw);
    m_rx_hdr_type     <= swap_bytes(type_raw);

    -- output the valid and ready signals
    m_rx_axis_tvalid <= m_rx_axis_tvalid_r;
    s_rx_eth_tready <= s_rx_eth_tready_r;

    -- indicate we are ready for more data
    with state select s_rx_eth_tready_r <=
      '1' when S_IDLE | S_HEADER,
      '0' when S_PAYLOAD_LAST | S_TLAST,
      m_rx_axis_tready or (not m_rx_axis_tvalid_r) when others;

    process(clk)
    begin

      if rising_edge(clk) then
        if reset = '1' then
          state <= S_IDLE;
          m_rx_axis_tvalid_r <= '0';
          m_rx_axis_tdata    <= (others => '0');
          m_rx_axis_tkeep    <= (others => '0');
          m_rx_axis_tlast    <= '0';
          dest_mac_raw       <= (others => '0');
          src_mac_raw        <= (others => '0');
          type_raw           <= (others => '0');
          tdata_r            <= (others => '0');
          tkeep_r            <= (others => '0');
          tlast_r            <= '0';

        else

          case state is

            when S_IDLE =>
              -- the first word contains the entire ethernet header
              -- plus 16 bits of data. don't output anything on this
              -- clock cycle as we don't have enough data to make up
              -- a full 128-bit word
              if s_rx_eth_tvalid = '1' and s_rx_eth_tready_r = '1' then

                state <= S_HEADER;
                m_rx_axis_tvalid_r <= '0';

                dest_mac_raw <= s_rx_eth_tdata(47 downto 0);
                src_mac_raw  <= s_rx_eth_tdata(95 downto 48);
                type_raw     <= s_rx_eth_tdata(111 downto 96);

                tdata_r <= s_rx_eth_tdata;
                tkeep_r <= s_rx_eth_tkeep;
                tlast_r <= s_rx_eth_tlast;

              end if;

            when S_HEADER =>
              -- the second word contains enough data to output a
              -- complete word.
              if s_rx_eth_tready_r = '1' then

                m_rx_axis_tvalid_r <= s_rx_eth_tvalid;
                m_rx_axis_tlast    <= tlast_r;

                m_rx_axis_tdata(47 downto 0)   <= src_mac_raw;
                m_rx_axis_tdata(63 downto 48)  <= tdata_r(127 downto 112);
                m_rx_axis_tdata(127 downto 64) <= s_rx_eth_tdata(63 downto 0);

                m_rx_axis_tkeep(5 downto 0)  <= b"111111";
                m_rx_axis_tkeep(7 downto 6)  <= tkeep_r(15 downto 14);
                m_rx_axis_tkeep(15 downto 8) <= s_rx_eth_tkeep(7 downto 0);

                if s_rx_eth_tvalid = '1' then
                  tdata_r <= s_rx_eth_tdata;
                  tkeep_r <= s_rx_eth_tkeep;
                  tlast_r <= s_rx_eth_tlast;
                end if;

                if tlast_r = '1' then
                    state <= S_TLAST;
                    m_rx_axis_tlast <= '1';

                elsif s_rx_eth_tvalid = '1' then

                  if s_rx_eth_tlast = '1' and s_rx_eth_tkeep(15 downto 8) = b"00000000" then
                    state <= S_TLAST;
                    m_rx_axis_tlast <= '1';

                  elsif s_rx_eth_tlast = '1' and s_rx_eth_tkeep(15 downto 8) /= b"00000000" then
                    state <= S_PAYLOAD_LAST;

                  else
                      state <= S_PAYLOAD;
                  end if;
                end if;
              end if;

              when S_PAYLOAD =>
                -- continue to output the payload until the end on the packet
                if s_rx_eth_tready_r = '1' then

                  m_rx_axis_tvalid_r <= s_rx_eth_tvalid;
                  m_rx_axis_tlast    <= tlast_r;

                  m_rx_axis_tdata(63 downto 0)   <= tdata_r(127 downto 64);
                  m_rx_axis_tdata(127 downto 64) <= s_rx_eth_tdata(63 downto 0);

                  m_rx_axis_tkeep(7 downto 0)  <= tkeep_r(15 downto 8);
                  m_rx_axis_tkeep(15 downto 8) <= s_rx_eth_tkeep(7 downto 0);

                  if s_rx_eth_tvalid = '1' then
                    tdata_r <= s_rx_eth_tdata;
                    tkeep_r <= s_rx_eth_tkeep;
                    tlast_r <= s_rx_eth_tlast;

                    if s_rx_eth_tlast = '1' and s_rx_eth_tkeep(15 downto 8) = b"00000000" then
                      state <= S_TLAST;
                      m_rx_axis_tlast <= '1';
                    end if;

                    if s_rx_eth_tlast = '1' and s_rx_eth_tkeep(15 downto 8) /= b"00000000" then
                      state <= S_PAYLOAD_LAST;
                    end if;

                  end if;
                end if;

                when S_PAYLOAD_LAST =>
                  -- output the buffered tdata
                  -- we don't have to have more input data to do this
                  if m_rx_axis_tready = '1' then

                    state              <= S_TLAST;
                    m_rx_axis_tvalid_r <= '1';
                    m_rx_axis_tlast    <= '1';

                    m_rx_axis_tdata(63 downto 0)   <= tdata_r(127 downto 64);
                    m_rx_axis_tdata(127 downto 64) <= (others => '0');

                    m_rx_axis_tkeep(7 downto 0)  <= tkeep_r(15 downto 8);
                    m_rx_axis_tkeep(15 downto 8) <= (others => '0');

                  end if;

                  when S_TLAST =>
                    -- additional state used to drive the last signal low
                    -- we don't have to have more input data to do this
                    if m_rx_axis_tready = '1' then
                      state              <= S_IDLE;
                      m_rx_axis_tvalid_r <= '0';
                      m_rx_axis_tlast    <= '0';
                      m_rx_axis_tdata    <= (others => '0');
                      m_rx_axis_tkeep    <= (others => '0');
                    end if;
          end case;
        end if;
      end if;

    end process;

end rtl;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------