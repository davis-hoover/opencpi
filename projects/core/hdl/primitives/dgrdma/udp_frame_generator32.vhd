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

entity udp_frame_generator32 is
  generic (
    DATA_WIDTH : natural := 32;
    KEEP_WIDTH : natural := 4
  );
  port(
    clk              : in std_logic;
    reset            : in std_logic;

    s_tx_axis_tdata  : in std_logic_vector((DATA_WIDTH-1) downto 0);
    s_tx_axis_tkeep  : in std_logic_vector((KEEP_WIDTH-1) downto 0);
    s_tx_axis_tvalid : in std_logic;
    s_tx_axis_tready : out std_logic;
    s_tx_axis_tlast  : in std_logic;

    local_ip_addr    : in std_logic_vector(31 downto 0);
    tx_hdr_type      : in std_logic_vector(15 downto 0);

    m_udp_hdr_valid           : out std_logic;
    m_udp_hdr_ready           : in std_logic;
    m_udp_ip_dscp             : out std_logic_vector(5 downto 0);
    m_udp_ip_ecn              : out std_logic_vector(1 downto 0);
    m_udp_ip_ttl              : out std_logic_vector(7 downto 0);
    m_udp_ip_source_ip        : out std_logic_vector(31 downto 0);
    m_udp_ip_dest_ip          : out std_logic_vector(31 downto 0);
    m_udp_source_port         : out std_logic_vector(15 downto 0);
    m_udp_dest_port           : out std_logic_vector(15 downto 0);
    m_udp_length              : out std_logic_vector(15 downto 0);
    m_udp_checksum            : out std_logic_vector(15 downto 0);
    m_udp_payload_axis_tdata  : out std_logic_vector(DATA_WIDTH-1 downto 0);
    m_udp_payload_axis_tkeep  : out std_logic_vector(KEEP_WIDTH-1 downto 0);
    m_udp_payload_axis_tvalid : out std_logic;
    m_udp_payload_axis_tready : in std_logic;
    m_udp_payload_axis_tlast  : out std_logic;
    m_udp_payload_axis_tuser  : out std_logic
  );
end entity;

architecture rtl of udp_frame_generator32 is

-- FSM state
type state_t is (S_IDLE, S_HEADER_1, S_HEADER_2, S_PAYLOAD, S_TLAST);
signal state : state_t;

-- Internal ready and valid signals
signal s_tx_axis_payload_tready_r    : std_logic;
signal s_tx_axis_tready_r            : std_logic;
signal m_udp_payload_axis_tvalid_r   : std_logic;
signal m_udp_hdr_valid_r             : std_logic;

-- Save the remote IP address and UDP ports
signal remote_ip_addr       : std_logic_vector(31 downto 0);
signal remote_udp_dest_port : std_logic_vector(15 downto 0);

-- Save the last payload tdata and tkeep
signal last_tx_axis_tdata : std_logic_vector(DATA_WIDTH-1 downto 0);
signal last_tx_axis_tkeep : std_logic_vector(KEEP_WIDTH-1 downto 0);
signal last_tx_axis_tlast : std_logic;

begin

  -- IP Header Fields
  m_udp_ip_dscp       <= b"000000";   -- differentiated services code point (standard service - CS0)
  m_udp_ip_ecn        <= b"00";       -- explicit congestion notification (non-ecn capable)
  m_udp_ip_ttl        <= b"01000000"; -- Time-to-live (64)
  m_udp_ip_source_ip  <= local_ip_addr;
  m_udp_ip_dest_ip    <= remote_ip_addr;

  -- UDP Header Fields
  m_udp_source_port   <= tx_hdr_type;
  m_udp_dest_port     <= remote_udp_dest_port;
  m_udp_length        <= (others => '0'); -- udp length is calculate along with the checksum
  m_udp_checksum      <= (others => '0'); -- header checksum is calculated by udp complete component

  -- output ready and valid signals
  s_tx_axis_payload_tready_r <= m_udp_payload_axis_tready or (not m_udp_payload_axis_tvalid_r);  -- Remove bubbles
  s_tx_axis_tready           <= s_tx_axis_tready_r;
  m_udp_hdr_valid            <= m_udp_hdr_valid_r;
  m_udp_payload_axis_tvalid  <= m_udp_payload_axis_tvalid_r;

  -- the condition when we are ready to accept data
  with state select s_tx_axis_tready_r <=
    m_udp_hdr_ready when S_IDLE | S_HEADER_1,
    '0' when S_HEADER_2,
    '0' when S_TLAST,
    s_tx_axis_payload_tready_r when others;

  process(clk)
  begin
    if rising_edge(clk) then

      if reset = '1' then
        state                       <= S_IDLE;
        m_udp_hdr_valid_r           <= '0';

        m_udp_payload_axis_tvalid_r <= '0';        
        m_udp_payload_axis_tdata    <= (others => '0');
        m_udp_payload_axis_tkeep    <= (others => '0');
        m_udp_payload_axis_tlast    <= '0';
        m_udp_payload_axis_tuser    <= '0';

        remote_ip_addr              <= (others => '0');
        remote_udp_dest_port        <= (others => '0');  

        last_tx_axis_tdata <= (others => '0');
        last_tx_axis_tkeep <= (others => '0');
        last_tx_axis_tlast <= '0';    

      else

        case state is

          -- wait for and remove the destination IP address
          -- we need to wait until the udp_hdr ready is asserted
          -- i.e. UDP complete is ready for the next header
          when S_IDLE =>
            m_udp_hdr_valid_r <= '0';

            -- We could test `s_tx_axis_payload_tready_r` as we do in states below.  However,
            -- there is never a bubble when entering this state from one below, so we only
            -- need to test the readiness of the downstream component (`m_udp_payload_axis_tready`).
            if m_udp_payload_axis_tready = '1' then
              m_udp_payload_axis_tvalid_r <= '0';
              m_udp_payload_axis_tdata    <= (others =>'0');
              m_udp_payload_axis_tkeep    <= (others =>'0');
              m_udp_payload_axis_tlast    <= '0';
              m_udp_payload_axis_tuser    <= '0';
            end if;

            if m_udp_hdr_ready = '1' and s_tx_axis_tvalid = '1' then
              -- save the remote IP address
              remote_ip_addr <= s_tx_axis_tdata(31 downto 0);                            
              state <= S_HEADER_1;              
            end if;

          -- wait for the destination UDP PORT
          -- store the accompanying data
          when S_HEADER_1 =>
            m_udp_hdr_valid_r           <= '0';
            m_udp_payload_axis_tvalid_r <= '0';

            m_udp_payload_axis_tdata    <= (others =>'0');
            m_udp_payload_axis_tkeep    <= (others =>'0');
            m_udp_payload_axis_tlast    <= '0';
            m_udp_payload_axis_tuser    <= '0';

            if m_udp_hdr_ready = '1' and s_tx_axis_tvalid = '1' then
              -- save the remote IP Port
              remote_udp_dest_port <= s_tx_axis_tdata(15 downto 0);

              -- the header is now valid
              m_udp_hdr_valid_r <= '1';

              -- save the accompanying data
              last_tx_axis_tdata <= s_tx_axis_tdata;
              last_tx_axis_tkeep <= s_tx_axis_tkeep;
              last_tx_axis_tlast <= s_tx_axis_tlast;

              state <= S_HEADER_2;
            end if; 

          -- Output UDP padding and stored data
          when S_HEADER_2 =>
            if s_tx_axis_payload_tready_r = '1' then
              m_udp_hdr_valid_r           <= '0';
              m_udp_payload_axis_tvalid_r <= '1';

              -- Note the two padding bytes at the start of the packet at bits 15 downto 0.
              m_udp_payload_axis_tdata  <= last_tx_axis_tdata(31 downto 16) & x"0000";
              m_udp_payload_axis_tkeep  <= last_tx_axis_tkeep(3 downto 2) & b"11";
              m_udp_payload_axis_tlast  <= last_tx_axis_tlast;
              m_udp_payload_axis_tuser  <= '0';

              if last_tx_axis_tlast = '1' then
                state <= S_TLAST;
              else
                state <= S_PAYLOAD;
              end if;              
            end if;  

          -- Output Payload   
          when S_PAYLOAD =>  
            if s_tx_axis_payload_tready_r = '1' then
              m_udp_hdr_valid_r           <= '0';
              m_udp_payload_axis_tvalid_r <= s_tx_axis_tvalid;

              m_udp_payload_axis_tdata  <= s_tx_axis_tdata;
              m_udp_payload_axis_tkeep  <= s_tx_axis_tkeep;
              m_udp_payload_axis_tlast  <= s_tx_axis_tlast;
              m_udp_payload_axis_tuser  <= '0';

              if s_tx_axis_tlast = '1' then
                state <= S_TLAST;
              else
                state <= S_PAYLOAD;
              end if;
            end if;   

            -- Wait for the last data to be aaccepted
            when S_TLAST =>
              if s_tx_axis_payload_tready_r = '1' then
                m_udp_hdr_valid_r           <= '0';
                m_udp_payload_axis_tvalid_r <= '0';
                m_udp_payload_axis_tdata    <= (others =>'0');
                m_udp_payload_axis_tkeep    <= (others =>'0');
                m_udp_payload_axis_tlast    <= '0';
                m_udp_payload_axis_tuser    <= '0';
                state <= S_IDLE;
              end if;

        end case;
      end if;
    end if;
  end process;

end rtl;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------
