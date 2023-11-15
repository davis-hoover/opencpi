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
-- Parse incoming UDP Frame
-- The incoming UDP frame (from the UDP Complete component) has been separated
-- out into header information and payload. The source IPaddress and source
-- UDP Port are stored and prepended to the payload (48 bits in total).
-- The destination UDP Port is also stored and output as udp_dest_port
-- The destination UDP Port is used later to route control and data traffic
-- back to the sender.
-- DG-RDMA specifies that the first 2 bytes of the UDP payload are unused
-- padding so these are discarded.
-- The output axis bus of this component is 32-bit wide.
-- ---------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
use work.dgrdma_util.all;

entity udp_frame_parser32 is
  generic (
    DATA_WIDTH : natural := 32;
    KEEP_WIDTH : natural := 4
  );
  port(
    clk   : in std_logic;
    reset : in std_logic;

    local_mac_addr            : in std_logic_vector(47 downto 0);
    local_ip_addr             : in std_logic_vector(31 downto 0);

    s_udp_hdr_valid           : in std_logic;
    s_udp_hdr_ready           : out std_logic;
    s_udp_eth_dest_mac        : in std_logic_vector(47 downto 0);
    s_udp_eth_src_mac         : in std_logic_vector(47 downto 0);
    s_udp_eth_type            : in std_logic_vector(15 downto 0);
    s_udp_ip_version          : in std_logic_vector(3 downto 0);
    s_udp_ip_ihl              : in std_logic_vector(3 downto 0);
    s_udp_ip_dscp             : in std_logic_vector(5 downto 0);
    s_udp_ip_ecn              : in std_logic_vector(1 downto 0);
    s_udp_ip_length           : in std_logic_vector(15 downto 0);
    s_udp_ip_identification   : in std_logic_vector(15 downto 0);
    s_udp_ip_flags            : in std_logic_vector(2 downto 0);
    s_udp_ip_fragment_offset  : in std_logic_vector(12 downto 0);
    s_udp_ip_ttl              : in std_logic_vector(7 downto 0);
    s_udp_ip_protocol         : in std_logic_vector(7 downto 0);
    s_udp_ip_header_checksum  : in std_logic_vector(15 downto 0);
    s_udp_ip_source_ip        : in std_logic_vector(31 downto 0);
    s_udp_ip_dest_ip          : in std_logic_vector(31 downto 0);
    s_udp_source_port         : in std_logic_vector(15 downto 0);
    s_udp_dest_port           : in std_logic_vector(15 downto 0);
    s_udp_length              : in std_logic_vector(15 downto 0);
    s_udp_checksum            : in std_logic_vector(15 downto 0);

    s_udp_payload_axis_tdata  : in std_logic_vector(DATA_WIDTH-1 downto 0);
    s_udp_payload_axis_tkeep  : in std_logic_vector(KEEP_WIDTH-1 downto 0);
    s_udp_payload_axis_tvalid : in std_logic;
    s_udp_payload_axis_tready : out std_logic;
    s_udp_payload_axis_tlast  : in std_logic;
    s_udp_payload_axis_tuser  : in std_logic;

    m_rx_axis_tdata   : out std_logic_vector((DATA_WIDTH-1) downto 0);
    m_rx_axis_tkeep   : out std_logic_vector((KEEP_WIDTH-1) downto 0);
    m_rx_axis_tvalid  : out std_logic;
    m_rx_axis_tready  : in std_logic;
    m_rx_axis_tlast   : out std_logic;

    udp_dest_port     : out std_logic_vector(15 downto 0)
  );
end entity;

architecture rtl of udp_frame_parser32 is

-- FSM state
type state_t is (S_IDLE, S_HEADER_1, S_HEADER_2, S_PAYLOAD);
signal state : state_t;

-- Internal ready and valid signals
signal m_rx_axis_tvalid_r          : std_logic;
signal s_udp_hdr_ready_r           : std_logic;
signal s_udp_payload_axis_tready_r : std_logic;
signal s_axis_tready_r             : std_logic;

-- Save the remote IP address and UDP ports
signal remote_ip_addr       : std_logic_vector(31 downto 0);
signal remote_udp_src_port  : std_logic_vector(15 downto 0);
signal remote_udp_dest_port : std_logic_vector(15 downto 0);

-- MAC and IP Address Match signals
signal rx_mac_addr_match    : boolean;
signal rx_ip_addr_match     : boolean;
signal rx_match             : boolean;

begin

  -- down stream ready (we can move forward)
  s_axis_tready_r <= m_rx_axis_tready or (not m_rx_axis_tvalid_r);

  -- we are ready for the UDP header when in IDLE state
  with state select s_udp_hdr_ready_r <=
    '1' when S_IDLE,
    '0' when others;

  -- we are ready for more UDP payload (data) in states
  -- other than IDLE, HEADER
  with state select s_udp_payload_axis_tready_r <=
    '0' when S_IDLE | S_HEADER_1,
     s_axis_tready_r when others;

  -- output ready and valid signals
  s_udp_hdr_ready           <= s_udp_hdr_ready_r;
  s_udp_payload_axis_tready <= s_udp_payload_axis_tready_r;
  m_rx_axis_tvalid          <= '0' when not(rx_match) else m_rx_axis_tvalid_r;

  -- only consider packets that match our mac and ip address
  -- MAC address matching includes local_mac, the broadcast mac (all fs) and multicast MAC (IPv4) 
  -- IP matching include local IP address and IPv4 mulicast addresses
  -- UDP port matching occurs later by the frame router
  rx_mac_addr_match <= (s_udp_eth_dest_mac = local_mac_addr) or (s_udp_eth_dest_mac = X"ffffffffffff") or ((s_udp_eth_dest_mac and X"ffffff800000") = X"01005e000000");
  rx_ip_addr_match  <= (s_udp_ip_dest_ip = local_ip_addr)    or ((s_udp_ip_dest_ip and X"f0000000") = X"e0000000");

  process(clk)
  begin
    if rising_edge(clk) then

      if reset = '1' then
        state                <= S_IDLE;
        remote_ip_addr       <= (others => '0');
        remote_udp_src_port  <= (others => '0');
        remote_udp_dest_port <= (others => '0');
        rx_match             <= false;

        m_rx_axis_tvalid_r <= '0';
        m_rx_axis_tlast    <= '0';
        m_rx_axis_tdata    <= (others => '0');
        m_rx_axis_tkeep    <= (others => '0');

      else

        case state is

          -- in IDLE state wait for the UDP header
          when S_IDLE =>
            if s_axis_tready_r = '1' then
              m_rx_axis_tdata    <= (others => '0');
              m_rx_axis_tkeep    <= (others => '0');
              m_rx_axis_tlast    <= '0';
              m_rx_axis_tvalid_r <= '0';

              if s_udp_hdr_valid = '1' then
                remote_ip_addr        <= s_udp_ip_source_ip;
                remote_udp_src_port   <= s_udp_source_port;
                remote_udp_dest_port  <= s_udp_dest_port;
                rx_match              <= rx_mac_addr_match and rx_ip_addr_match;
                state <= S_HEADER_1;
              end if;
            end if;

          -- Output the REMOTE IP 32-bit address
          when S_HEADER_1 =>
            if s_axis_tready_r = '1' then
              udp_dest_port      <= remote_udp_dest_port;
              m_rx_axis_tdata    <= remote_ip_addr;
              m_rx_axis_tkeep    <= b"1111";
              m_rx_axis_tlast    <= '0';
              m_rx_axis_tvalid_r <= '1';
              state <= S_HEADER_2;
            end if;

          -- Output the REMOTE (source) PORT
          -- Discard the first 2 bytes of payload data (this is padding)
          when S_HEADER_2 =>
            if s_axis_tready_r = '1' then
              m_rx_axis_tdata    <= s_udp_payload_axis_tdata(31 downto 16) & remote_udp_src_port;
              m_rx_axis_tkeep    <= s_udp_payload_axis_tkeep(3 downto 2) & b"11";
              m_rx_axis_tlast    <= s_udp_payload_axis_tlast;
              m_rx_axis_tvalid_r <= s_udp_payload_axis_tvalid;

              if s_udp_payload_axis_tvalid = '1' then
                if s_udp_payload_axis_tlast = '1' then
                  state <= S_IDLE;
                else
                  state <= S_PAYLOAD;
                end if;
              end if;
            end if;

            -- output the payload
            when S_PAYLOAD =>
            if s_axis_tready_r = '1' then
              m_rx_axis_tdata    <= s_udp_payload_axis_tdata;
              m_rx_axis_tkeep    <= s_udp_payload_axis_tkeep;
              m_rx_axis_tlast    <= s_udp_payload_axis_tlast;
              m_rx_axis_tvalid_r <= s_udp_payload_axis_tvalid;

              if s_udp_payload_axis_tvalid = '1' then
                if s_udp_payload_axis_tlast = '1' then
                  state <= S_IDLE;
                end if;
              end if;
            end if;

        end case;
      end if;
    end if;
  end process;

end rtl;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------