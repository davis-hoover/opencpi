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

LIBRARY IEEE; USE IEEE.std_logic_1164.ALL; USE ieee.numeric_std.ALL;
LIBRARY platform;
USE platform.ALL;
LIBRARY ocpi; USE ocpi.types.ALL;

ENTITY axis_to_cp8 IS
PORT( clk                :  IN std_logic;
      reset              :  IN std_logic;

      eth0_mac_addr      :  IN std_logic_vector(47 DOWNTO 0); -- register set in soft_ctrl.v

      s_axis_tdata       :  IN std_logic_vector(7 DOWNTO 0);
      s_axis_tvalid      :  IN std_logic;
      s_axis_tlast       :  IN std_logic;
      s_axis_tready      : OUT std_logic;

      m_axis_tdata       : OUT std_logic_vector(7 DOWNTO 0);
      m_axis_tvalid      : OUT std_logic;
      m_axis_tlast       : OUT std_logic;
      m_axis_tready      :  IN std_logic; -- this is not a ready this is an acknowledge TODO: what's going on here???

      cp_in              :  IN platform_pkg.occp_out_t;
      cp_out             : OUT platform_pkg.occp_in_t;

      flag_addr          :  IN std_logic_vector(23 DOWNTO 0);
      flag_data          :  IN std_logic_vector(31 DOWNTO 0);
      flag_valid         :  IN std_logic;
      flag_take          : OUT std_logic;

      debug_select       :  IN std_logic_vector(23 DOWNTO 0);
      debug              : OUT std_logic_vector(31 DOWNTO 0);

      test_points        : OUT std_logic_vector(11 DOWNTO 0) );
END axis_to_cp8;

ARCHITECTURE rtl OF axis_to_cp8 IS

  TYPE slv8_arr_t IS ARRAY (NATURAL RANGE <>) OF std_logic_vector(7 DOWNTO 0);

  FUNCTION convert_mac(mac : std_logic_vector) RETURN slv8_arr_t IS
    VARIABLE v : slv8_arr_t(0 TO 5);
  BEGIN
    FOR i IN 0 TO 5 LOOP
      v(i) := mac(i*8+7 DOWNTO i*8);
    END LOOP;
    RETURN v;
  END;

  SIGNAL target_advert    : slv8_arr_t(0 TO 11) := ( 11 => X"00", 10 => X"00", 9 => X"00", 8 => X"00"                         -- PID
                                                   ,  7 => X"00",  6 => X"00", 5 => X"00", 4 => X"00", 3 => X"00", 2 => X"00" -- MAC Placeholder
                                                   ,  1 => X"40"                                                              -- mbx40
                                                   ,  0 => X"00");                                                            -- mbx0

  CONSTANT tx_type_etc_c      : std_logic_vector(7 DOWNTO 0) := ('0' & '1' & "11" & "0000"); -- rsvd = 0, uncache = 1, dcp_msg_typ = response, cp_resp_code = OK

  SIGNAL response_trigger     : std_logic := '0';
  SIGNAL response_processing  : std_logic := '0';
  SIGNAL rx_metadata          : std_logic_vector(63 DOWNTO 0);
  SIGNAL rx_address           : std_logic_vector(31 DOWNTO 0);
  SIGNAL rx_count             : UNSIGNED(2 DOWNTO 0) := (OTHERS => '0'); -- NATURAL RANGE 0 TO 5  := 0;
  SIGNAL tx_count             : UNSIGNED(4 DOWNTO 0) := (OTHERS => '0'); -- NATURAL RANGE 0 TO 23 := 0;
  SIGNAL rx_dcp_msg_tag       : std_logic_vector(cp_in.tag'LEFT + 2 DOWNTO 0); -- extra bits to indicate no previous and distinguish read and write
  SIGNAL rx_frame_length      : UNSIGNED(15 DOWNTO 0);
  SIGNAL rx_dm_header         : slv8_arr_t(0 TO 1);
  SIGNAL rx_dcp_rsvd          : std_logic_vector(1 DOWNTO 0);
  SIGNAL rx_dcp_msg_typ       : std_logic_vector(1 DOWNTO 0);
  SIGNAL rx_dcp_msg_cde       : std_logic_vector(3 DOWNTO 0);
  SIGNAL rx_duplicate         : boolean := FALSE;
  SIGNAL initiator_advert     : slv8_arr_t(0 TO 3);
  SIGNAL rx_data              : std_logic_vector(31 DOWNTO 0);
  SIGNAL previous_len         : UNSIGNED(4 DOWNTO 0) := (OTHERS => '0'); -- NATURAL RANGE 0 TO 23 := 0;
  SIGNAL tx_previous          : slv8_arr_t(23 DOWNTO 0);
  SIGNAL previous_msg         : slv8_arr_t(23 DOWNTO 0);
  SIGNAL tx_metadata          : std_logic_vector(63 DOWNTO 0);
  SIGNAL tx_rsp_length        : slv8_arr_t(0 TO 1);
  SIGNAL tx_dcp_msg_tag       : std_logic_vector(cp_in.tag'RANGE);
  SIGNAL tx_length            : UNSIGNED(4 DOWNTO 0); -- NATURAL RANGE 0 TO 23;
  SIGNAL tx_data_out          : std_logic_vector(cp_in.data'RANGE);
  SIGNAL rx_timeout_counter   : UNSIGNED(26 DOWNTO 0) := (OTHERS => '1');
  SIGNAL tx_timeout_counter   : UNSIGNED(26 DOWNTO 0) := (OTHERS => '1');
  SIGNAL rx_reset             : std_logic := '0';
  SIGNAL tx_reset             : std_logic := '0';


  TYPE rx_state_t IS ( RX_IDL
                     , RX_FLAG_WRITE
                     , RX_FLAG_WRITE_DONE
                     , RX_SRC
                     , RX_LEN
                     , RX_DMH_1
                     , RX_DMH_2
                     , RX_NOP_1
                     , RX_NOP_WAIT_EOF
                     , RX_NOP_2
                     , RX_NOP_3
                     , RX_WR_ADDR
                     , RX_WR_DATA_1
                     , RX_WR_WAIT_EOF
                     , RX_WR_DATA_2
                     , RX_WR_DATA_3
                     , RX_WR_DATA_4
                     , RX_RD_ADDR
                     , RX_RD_WAIT_EOF
                     , RX_RD_DATA_1
                     , RX_RD_DATA_2
                     , RX_ERROR );

  SIGNAL rx_state      : rx_state_t;
  SIGNAL rx_state_d    : rx_state_t;
  SIGNAL trigger_state : rx_state_t;

  TYPE tx_state_t IS ( TX_IDL
                     , TX_DST
                     , TX_DATA
                     , TX_LEN
                     , TX_DMH
                     , TX_NOP
                     , TX_RD
                     , TX_END
                     , TX_DUPLICATE
                     , TX_ERROR );

  SIGNAL tx_state   : tx_state_t;
  SIGNAL tx_state_d : tx_state_t;

  SIGNAL cp_is_flag_write : boolean;

  SIGNAL test_points_i : std_logic_vector(11 DOWNTO 0);

  SIGNAL rx_state_i : natural;
  SIGNAL tx_state_i : natural;

BEGIN
  rx_state_i <= rx_state_t'pos(rx_state);
  tx_state_i <= tx_state_t'pos(tx_state);

  WITH debug_select SELECT
  debug <= X"02000000" WHEN X"000000"
         , rx_address  WHEN X"000001"
         , X"DEADADDA" WHEN OTHERS;

  proc_test_points : PROCESS(clk) -- Add some registers to ease timing
  BEGIN
    IF rising_edge(clk) THEN
      test_points <= test_points_i;
    END IF;
  END PROCESS;

--  test_points_i(11 DOWNTO 0) <= "000000000001" WHEN rx_state = RX_IDL ELSE
--                                "000000000010" WHEN rx_state = RX_DST ELSE
--                                "000000000100" WHEN rx_state = RX_SRC ELSE
--                                "000000001000" WHEN rx_state = RX_TYP ELSE
--                                "000000010000" WHEN rx_state = RX_LEN ELSE
--                                "000000100000" WHEN rx_state = RX_DMH_1 ELSE
--                                "000001000000" WHEN rx_state = RX_DMH_2 ELSE
--                                "000010000000" WHEN rx_state = RX_NOP_1 ELSE
--                                "000100000000" WHEN rx_state = RX_NOP_2 ELSE
--                                "001000000000" WHEN rx_state = RX_WR_ADDR ELSE
--                                "010000000000" WHEN rx_state = RX_WR_DATA_1 ELSE
--                                "100000000001" WHEN rx_state = RX_WR_DATA_2 ELSE
--                                "100000000010" WHEN rx_state = RX_WR_DATA_3 ELSE
--                                "100000000100" WHEN rx_state = RX_RD_ADDR ELSE
--                                "100000001000" WHEN rx_state = RX_RD_DATA_1 ELSE
--                                "100000010000" WHEN rx_state = RX_RD_DATA_2 ELSE
--                                "100000100000" WHEN rx_state = RX_ERROR ELSE
--                                "111111111111";

  test_points_i(11 DOWNTO 0) <= "000000000001" WHEN tx_state = TX_IDL ELSE
                                "000000000010" WHEN tx_state = TX_DATA ELSE
                                -- "000000000100" WHEN tx_state = TX_DST ELSE
                                -- "000000001000" WHEN tx_state = TX_SRC ELSE
                                -- "000000010000" WHEN tx_state = TX_TYP ELSE
                                "000000100000" WHEN tx_state = TX_LEN ELSE
                                "000001000000" WHEN tx_state = TX_DMH ELSE
                                "000010000000" WHEN tx_state = TX_NOP ELSE
                                "000100000000" WHEN tx_state = TX_RD ELSE
                                "001000000000" WHEN tx_state = TX_DUPLICATE ELSE
                                "010000000000" WHEN tx_state = TX_END ELSE
                                "100000000000" WHEN tx_state = TX_ERROR ELSE
                                "111111111111";


  proc_mac_addr : PROCESS(eth0_mac_addr)
  BEGIN
    target_advert(2 TO 7) <= convert_mac(eth0_mac_addr);
  END PROCESS;

  -- Watchdog timer to ensure the rx state machine does not get stuck
  proc_rx_timeout : PROCESS(clk)
  BEGIN
    IF rising_edge(clk) THEN
      IF reset = '1' THEN
        rx_reset <= '0';
        rx_timeout_counter <= (OTHERS => '1');
      ELSE
        IF rx_state /= RX_IDL THEN
          IF rx_timeout_counter = 0 THEN -- timeout reset the rx statemachine
            rx_reset <= '1';
          ELSIF rx_state_d = rx_state THEN -- state not changing
            rx_timeout_counter <= rx_timeout_counter - 1;
          ELSE -- state changing
            rx_timeout_counter <= (OTHERS => '1');
          END IF;
        ELSE
          rx_reset <= '0';
          rx_timeout_counter <= (OTHERS => '1');
        END IF;
      END IF;
      rx_state_d <= rx_state;
    END IF;
  END PROCESS;


  -- Watchdog timer to ensure the tx state machine does not get stuck
  proc_tx_timeout : PROCESS(clk)
  BEGIN
    IF rising_edge(clk) THEN
      IF reset = '1' THEN
        tx_reset <= '0';
        tx_timeout_counter <= (OTHERS => '1');
      ELSE
        IF tx_state /= TX_IDL THEN
          IF tx_timeout_counter = 0 THEN -- timeout reset the rx statemachine
            tx_reset <= '1';
          ELSIF tx_state_d = tx_state THEN -- state not changing
            tx_timeout_counter <= tx_timeout_counter - 1;
          ELSE -- state changing
            tx_timeout_counter <= (OTHERS => '1');
          END IF;
        ELSE
          tx_reset <= '0';
          tx_timeout_counter <= (OTHERS => '1');
        END IF;
      END IF;
      tx_state_d <= tx_state;
    END IF;
  END PROCESS;

  -- Select response length for transmit
  with trigger_state select tx_rsp_length <=
    (X"00", X"12") when RX_NOP_3,
    (X"00", X"0A") when RX_RD_DATA_2,
    (X"00", X"06") when RX_WR_DATA_4,
    (X"FF", X"FF") when others;

  -- Our state machines, separate for ll8 input and output
  proc_cp : PROCESS(clk)
  BEGIN
    IF rising_edge(clk) THEN
      IF reset = '1' THEN
        rx_dcp_msg_tag       <= (OTHERS => '0');
        rx_state             <= RX_IDL;
        tx_state             <= TX_IDL;
        response_trigger     <= '0';
        response_processing  <= '0';
        cp_out.valid         <= to_bool(FALSE);
        cp_out.is_read       <= to_bool(FALSE);
        cp_out.take          <= to_bool(FALSE);
        cp_is_flag_write     <= FALSE;
        flag_take            <= '0';
        m_axis_tvalid        <= '0';
        m_axis_tlast         <= '0';
        rx_address           <= (OTHERS => '0');
        rx_dcp_msg_cde       <= (OTHERS => '0');
        rx_data              <= (OTHERS => '0');
        tx_data_out          <= (OTHERS => '0');
        s_axis_tready        <= '0';
        m_axis_tdata         <= (OTHERS => '0');
      ELSE

        IF (rx_reset = '1') THEN
          response_trigger <= '0';
          cp_out.valid   <= to_bool(FALSE);
          cp_out.is_read <= to_bool(FALSE);
          rx_state <= RX_IDL;
          s_axis_tready <= '0';
        ELSE
          CASE rx_state IS

            -- tready is '0' on entry to this state
            WHEN RX_IDL =>
              IF s_axis_tvalid = '1' THEN
                -- the first metadata byte is coincident with sof so 5 more to read
                rx_metadata(47 DOWNTO 40) <= s_axis_tdata;
                rx_state <= RX_SRC;
                rx_count <= TO_UNSIGNED(5,rx_count'LENGTH);
                s_axis_tready <= '1';
              ELSIF flag_valid = '1' THEN
                rx_state <= RX_FLAG_WRITE;
                cp_out.valid <= '1';
                cp_out.is_read <= '0';
                cp_is_flag_write <= TRUE;
              END IF;

            WHEN RX_FLAG_WRITE =>
              IF cp_in.take = '1' THEN
                rx_state <= RX_FLAG_WRITE_DONE;
                cp_out.valid <= '0';
                cp_is_flag_write <= FALSE;
                flag_take <= '1';
              END IF;

            WHEN RX_FLAG_WRITE_DONE =>
              flag_take <= '0';
              rx_state <= RX_IDL;

            WHEN RX_SRC =>
              IF s_axis_tvalid = '1' THEN
                FOR i IN 0 TO 5 LOOP
                  IF rx_count = i THEN
                  rx_metadata(i*8+7 DOWNTO i*8) <= s_axis_tdata;
                  END IF;
                END LOOP;
                IF rx_count = 0 THEN
                  rx_count <= TO_UNSIGNED(1,rx_count'LENGTH);
                  rx_state <= RX_LEN;
                ELSE
                  rx_count <= rx_count - 1;
                END IF;
              END IF;

            WHEN RX_LEN => -- DCP length not passed to control plane
              IF s_axis_tvalid = '1' THEN
                FOR i IN 0 TO 1 LOOP
                  IF rx_count = i THEN
                  rx_frame_length(i*8+7 DOWNTO i*8) <= unsigned(s_axis_tdata);
                  END IF;
                END LOOP;
                IF rx_count = 0 THEN
                  rx_count <= TO_UNSIGNED(3,rx_count'LENGTH);
                  rx_state <= RX_DMH_1;
                ELSE
                  rx_count <= rx_count - 1;
                END IF;
              END IF;

            WHEN RX_DMH_1 => -- DMH defines the message type, NOP, Write, Read, Response
              IF s_axis_tvalid = '1' THEN
                rx_dm_header(0) <= s_axis_tdata;
                rx_state <= RX_DMH_2;
                rx_count <= rx_count - 1;
                rx_frame_length <= rx_frame_length - 3; -- frame length received includes the frame length field itself so subtract three
              END IF;

            WHEN RX_DMH_2 => -- DMH
              IF s_axis_tvalid = '1' THEN
                IF rx_count = 2 THEN
                  rx_dm_header(1) <= s_axis_tdata;
                ELSIF rx_count = 1 THEN
                  rx_dcp_rsvd    <= s_axis_tdata(7 DOWNTO 6);
                  rx_dcp_msg_typ <= s_axis_tdata(5 DOWNTO 4);
                  rx_dcp_msg_cde <= s_axis_tdata(3 DOWNTO 0);
                ELSIF rx_count = 0 THEN
                  CASE rx_dcp_msg_typ IS
                    WHEN "00" => -- NOP
                      rx_state <= RX_NOP_1;
                      rx_count <= TO_UNSIGNED(3,rx_count'LENGTH);
                      rx_dcp_msg_tag <= ('1' & '1' & s_axis_tdata); -- save write tag
                    WHEN "01" => -- Write
                      IF rx_dcp_msg_tag = ('1' & '1' & s_axis_tdata) THEN -- test for duplicate write message
                        rx_duplicate <= TRUE;
                      ELSE
                        rx_duplicate <= FALSE;
                        rx_dcp_msg_tag <= ('1' & '1' & s_axis_tdata); -- save write tag
                      END IF;
                      rx_state <= RX_WR_ADDR;
                      rx_count <= TO_UNSIGNED(3,rx_count'LENGTH);
                    WHEN "10" => -- Read
                      IF rx_dcp_msg_tag = ('1' & '0' & s_axis_tdata) THEN -- test for duplicate read message
                        rx_duplicate <= TRUE;
                      ELSE
                        rx_duplicate <= FALSE;
                        rx_dcp_msg_tag <= ('1' & '0' & s_axis_tdata); -- save read tag
                      END IF;
                      rx_state <= RX_RD_ADDR;
                      rx_count <= TO_UNSIGNED(3,rx_count'LENGTH);
                    WHEN "11" => -- Response (I think this is an error from host)
                      rx_state <= RX_ERROR;
                    WHEN OTHERS =>
                  END CASE;
                END IF;
                IF rx_count /= 0 THEN
                  rx_count <= rx_count - 1;
                  rx_frame_length <= rx_frame_length - 1;
                END IF;
              END IF;

            WHEN RX_NOP_1 => -- This does not feed into the control plane and needs to be responded to by this module internally
              IF s_axis_tvalid = '1' THEN
                FOR i IN 0 TO 3 LOOP
                  IF rx_count = i THEN
                    initiator_advert(i) <= s_axis_tdata;
                  END IF;
                END LOOP;
                IF rx_count = 0 THEN
                  IF s_axis_tlast = '1' THEN
                    s_axis_tready <= '0'; -- frame complete pause input
                    rx_state <= RX_NOP_2;
                  ELSE
                    rx_state <= RX_NOP_WAIT_EOF;
                  END IF;
                ELSE
                  rx_count <= rx_count - 1;
                  rx_frame_length <= rx_frame_length - 1;
                END IF;
              END IF;

            WHEN RX_NOP_WAIT_EOF =>
              -- consume padding bytes at end of frame
              -- FIXME: should check length, and handle early TLAST appropriately (currently this will deadlock and
              -- get caught by the watchdog timer, which isn't the end of the world)
              IF s_axis_tlast = '1' THEN
                s_axis_tready <= '0'; -- frame complete pause input
                rx_state <= RX_NOP_2;
              END IF;

            WHEN RX_NOP_2 =>
              IF response_processing = '0' THEN -- Wait for previous response to complete
                response_trigger <= '1';      -- Trigger response
                rx_state <= RX_NOP_3;
              END IF;

            WHEN RX_NOP_3 =>
              IF response_processing = '1' THEN -- Triggered
                response_trigger <= '0';        -- Reset the trigger
                rx_state <= RX_IDL;             -- Return to the idle state
                s_axis_tready <= '0';
              END IF;

            WHEN RX_WR_ADDR => -- Write address feeds into control plane
              IF s_axis_tvalid = '1' THEN
                FOR i IN 0 TO 3 LOOP
                  IF rx_count = i THEN
                    rx_address(i*8+7 DOWNTO i*8) <= s_axis_tdata;
                  END IF;
                END LOOP;
                IF rx_count = 0 THEN
                  rx_count <= TO_UNSIGNED(3,rx_count'LENGTH);
                  rx_state <= RX_WR_DATA_1;
                ELSE
                  rx_count <= rx_count - 1;
                  rx_frame_length <= rx_frame_length - 1;
                END IF;
              END IF;

            WHEN RX_RD_ADDR =>
              IF s_axis_tvalid = '1' THEN
                FOR i IN 0 TO 3 LOOP
                  IF rx_count = i THEN
                    rx_address(i*8+7 DOWNTO i*8) <= s_axis_tdata;
                  END IF;
                END LOOP;
                IF rx_count = 0 THEN
                  rx_data(rx_dcp_msg_tag'LEFT - 2 DOWNTO 0) <= rx_dcp_msg_tag(rx_dcp_msg_tag'LEFT - 2 DOWNTO 0); -- ocscp_rv.vhd expects the data field to contain the dcp message tag on reads. TODO:pad zeros

                  IF s_axis_tlast = '1' THEN
                    IF NOT rx_duplicate THEN
                      cp_out.is_read     <= to_bool(TRUE);
                      cp_out.valid       <= to_bool(TRUE);
                    END IF;
                    s_axis_tready      <= '0';
                    rx_state           <= RX_RD_DATA_1;
                  ELSE
                    rx_state           <= RX_RD_WAIT_EOF;
                  END IF;
                ELSE
                  rx_count <= rx_count - 1;
                  rx_frame_length <= rx_frame_length - 1;
                END IF;
              END IF;

            WHEN RX_RD_WAIT_EOF =>
              IF s_axis_tlast = '1' THEN
                IF NOT rx_duplicate THEN
                  cp_out.is_read     <= to_bool(TRUE);
                  cp_out.valid       <= to_bool(TRUE);
                END IF;
                s_axis_tready      <= '0';
                rx_state           <= RX_RD_DATA_1;
              END IF;

            WHEN RX_RD_DATA_1 =>
              IF response_processing = '0' THEN
                response_trigger <= '1';
                rx_state         <= RX_RD_DATA_2;
              END IF;

            WHEN RX_RD_DATA_2 =>
              IF response_processing = '1' THEN
                response_trigger <= '0';
                IF  NOT rx_duplicate THEN
                  IF its(cp_in.take) THEN              -- read address is "taken" only after returned data is "taken"
                    cp_out.valid   <= to_bool(FALSE);
                    cp_out.is_read <= to_bool(FALSE);
                    rx_state <= RX_IDL;
                    s_axis_tready <= '0';
                  END IF;
                ELSE
                  rx_duplicate <= FALSE;
                  rx_state <= RX_IDL;
                  s_axis_tready <= '0';
                END IF;
              END IF;

            WHEN RX_WR_DATA_1 => -- Write data feeds into control plane
              IF s_axis_tvalid = '1' THEN
                FOR i IN 0 TO 3 LOOP
                  IF rx_count = i THEN
                    rx_data(i*8+7 DOWNTO i*8) <= s_axis_tdata;
                  END IF;
                END LOOP;
                IF rx_count = 0 THEN
                  IF s_axis_tlast = '1' THEN
                    IF NOT rx_duplicate THEN
                      cp_out.valid       <= to_bool(TRUE);
                      rx_state           <= RX_WR_DATA_2;
                    ELSE
                      rx_state <= RX_WR_DATA_3;
                    END IF;
                    s_axis_tready <= '0';
                  ELSE
                    rx_state <= RX_WR_WAIT_EOF;
                  END IF;
                ELSE
                  rx_count <= rx_count - 1;
                  rx_frame_length <= rx_frame_length - 1;
                END IF;
              END IF;

            WHEN RX_WR_WAIT_EOF =>
              IF s_axis_tlast = '1' THEN
                IF  NOT rx_duplicate THEN
                  cp_out.valid       <= to_bool(TRUE);
                  rx_state           <= RX_WR_DATA_2;
                ELSE
                  rx_state           <= RX_WR_DATA_3;
                END IF;
                s_axis_tready <= '0';
              END IF;

            WHEN RX_WR_DATA_2 =>
              IF its(cp_in.take) THEN
                cp_out.valid <= to_bool(FALSE);
                rx_state     <= RX_WR_DATA_3;
              END IF;

            WHEN RX_WR_DATA_3 =>
              IF response_processing = '0' THEN
                response_trigger <= '1';
                rx_state <= RX_WR_DATA_4;
              END IF;

            WHEN RX_WR_DATA_4 =>
              IF response_processing = '1' THEN
                response_trigger <= '0';
                rx_duplicate <= FALSE;
                rx_state <= RX_IDL;
                s_axis_tready <= '0';
              END IF;

            WHEN RX_ERROR =>
              rx_state <= RX_IDL;
              s_axis_tready <= '0';

            WHEN OTHERS =>
              response_trigger <= '0';
              rx_state <= RX_ERROR;

          END CASE;
        END IF;



        IF tx_reset = '1' THEN
          response_processing  <= '0';
          cp_out.take          <= to_bool(FALSE);
          m_axis_tvalid   <= '0';
          m_axis_tlast       <= '0';
          tx_state             <= TX_IDL;
        ELSE

          CASE tx_state IS

            WHEN TX_IDL =>
              IF response_trigger = '1' THEN    -- First capture what we need about the rx message
                IF rx_duplicate THEN
                  tx_count <= previous_len;
                  tx_state <= TX_DUPLICATE;
                ELSE
                  trigger_state <= rx_state;
                  tx_metadata   <= rx_metadata; -- the address to sent the response to.
                  tx_previous   <= (OTHERS => (OTHERS => '0'));
                  IF rx_state = RX_RD_DATA_2 THEN
                    tx_state    <= TX_DATA;
                  ELSE
                    tx_dcp_msg_tag <= rx_dcp_msg_tag(rx_dcp_msg_tag'LEFT - 2 DOWNTO 0); -- strip off the read/write bit
                    tx_state <= TX_DST;
                  END IF;
                  tx_count <= TO_UNSIGNED(5,tx_count'LENGTH);
                END IF;
                response_processing <= '1';
              END IF;

            WHEN TX_DATA =>
              IF cp_in.valid = to_bool(TRUE) THEN
                tx_data_out    <= cp_in.data;
                tx_dcp_msg_tag <= cp_in.tag;
                cp_out.take    <= to_bool(TRUE);
                tx_state       <= TX_DST;
              END IF;

            WHEN TX_DST =>
              cp_out.take      <= to_bool(FALSE);
              IF m_axis_tready = '1' THEN  -- FIXME: this violates the AXI spec - tvalid MUST NOT be dependent on tready
                m_axis_tvalid <= '1';
                FOR i IN 0 TO 5 LOOP
                  IF tx_count = i THEN
                    m_axis_tdata <= tx_metadata(i*8+7 DOWNTO i*8);
                    tx_previous  <= (tx_previous(tx_previous'LEFT - 1 DOWNTO 0) & tx_metadata(i*8+7 DOWNTO i*8));
                  END IF;
                END LOOP;
                IF tx_count = 0 THEN
                  tx_count <= TO_UNSIGNED(1,tx_count'LENGTH);
                  tx_state <= TX_LEN;
                ELSE
                  tx_count <= tx_count - 1;
                END IF;
              END IF;

            WHEN TX_LEN =>
              cp_out.take      <= to_bool(FALSE);
              IF m_axis_tready = '1' THEN
                IF tx_count = 1 THEN
                  m_axis_tdata <= tx_rsp_length(0);
                  tx_previous  <= (tx_previous(tx_previous'LEFT - 1 DOWNTO 0) & tx_rsp_length(0));
                ELSIF tx_count = 0 THEN
                  m_axis_tdata <= tx_rsp_length(1);
                  tx_previous  <= (tx_previous(tx_previous'LEFT - 1 DOWNTO 0) & tx_rsp_length(1));

                  IF trigger_state = RX_NOP_3 THEN
                    tx_length <= previous_len;
                  ELSIF trigger_state = RX_RD_DATA_2 THEN
                    tx_length <= TO_UNSIGNED(15,tx_length'LENGTH); -- length of whole ethernet packet minus one
                  ELSIF trigger_state = RX_WR_DATA_4 THEN
                  tx_length   <= TO_UNSIGNED(11,tx_length'LENGTH); -- length of whole ethernet packet minus one
                  END IF;
                END IF;

                IF tx_count = 0 THEN
                  tx_count <= TO_UNSIGNED(3,tx_count'LENGTH);
                  tx_state <= TX_DMH;
                ELSE
                  tx_count <= tx_count - 1;
                END IF;
              END IF;

            WHEN TX_DMH =>
              IF m_axis_tready = '1' THEN
                CASE TO_INTEGER(tx_count) IS
                  WHEN 3 | 2 =>
                    m_axis_tdata <= X"00";
                    tx_previous <= (tx_previous(tx_previous'LEFT - 1 DOWNTO 0) & X"00");
                  WHEN 1 =>
                    m_axis_tdata <= tx_type_etc_c;
                    tx_previous <= (tx_previous(tx_previous'LEFT - 1 DOWNTO 0) & tx_type_etc_c);
                  WHEN 0 =>
                    m_axis_tdata <= tx_dcp_msg_tag;
                    tx_previous <= (tx_previous(tx_previous'LEFT - 1 DOWNTO 0) & tx_dcp_msg_tag);
                  WHEN OTHERS =>
                END CASE;

                IF tx_count = 0 THEN
                  IF trigger_state = RX_NOP_3 THEN
                    tx_count <= TO_UNSIGNED(11,tx_count'LENGTH);
                    tx_state <= TX_NOP;
                  ELSIF trigger_state = RX_WR_DATA_4 THEN
                    m_axis_tlast <= '1';
                    tx_state <= TX_END;
                  ELSIF trigger_state = RX_RD_DATA_2 THEN
                    tx_count <= TO_UNSIGNED(3,tx_count'LENGTH);
                    tx_state <= TX_RD;
                  END IF;
                ELSE
                  tx_count <= tx_count - 1;
                END IF;
              END IF;

            WHEN TX_NOP =>
              IF m_axis_tready = '1' THEN
                FOR i IN 0 to 11 LOOP
                  IF tx_count = i THEN
                    m_axis_tdata <= target_advert(i); -- target adverisement code 0x40
                  END IF;
                END LOOP;
                IF tx_count = 0 THEN
                  m_axis_tlast <= '1';
                  tx_state       <= TX_END;
                ELSE
                  tx_count <= tx_count - 1;
                END IF;
              END IF;
              tx_previous <= previous_msg; -- don't update the stored previous message on NOP

            WHEN TX_RD  =>
              IF m_axis_tready = '1' THEN
                FOR i IN 0 TO 3 LOOP
                  IF tx_count = i THEN
                    m_axis_tdata <= tx_data_out(i*8+7 DOWNTO i*8);
                    tx_previous <= (tx_previous(tx_previous'LEFT - 1 DOWNTO 0) & tx_data_out(i*8+7 DOWNTO i*8));
                  END IF;
                END LOOP;

                IF tx_count = 0 THEN
                  m_axis_tlast <= '1';
                  tx_state       <= TX_END;
                ELSE
                  tx_count <= tx_count - 1;
                END IF;
              END IF;

            WHEN TX_END  =>
              m_axis_tvalid   <= '0';
              m_axis_tlast       <= '0';
              previous_len         <= tx_length;
              previous_msg         <= tx_previous;
              tx_state             <= TX_IDL;
              response_processing  <= '0';

            WHEN TX_DUPLICATE => -- replay the previous response (only for read and write messages)
              IF m_axis_tready = '1' THEN
                m_axis_tvalid <= '1';

                FOR i IN 0 TO 23 LOOP -- DA + SA + TYP + DCP <= 6 + 6 + 2 + 10 = 24
                  IF tx_count = i THEN
                    m_axis_tdata <= previous_msg(i);
                  END IF;
                END LOOP;

                IF tx_count = 0 THEN
                  m_axis_tlast     <= '1';
                  tx_state           <= TX_END;
                ELSE
                  tx_count <= tx_count - 1;
                END IF;
              END IF;
              tx_previous <= previous_msg; -- as this is a replay keep the original value
              tx_length   <= previous_len; -- as this is a replay keep the original value

            WHEN TX_ERROR =>
              IF m_axis_tready = '1' THEN
                m_axis_tvalid   <= '1';
                m_axis_tlast       <= '1';
                tx_previous          <= previous_msg; -- as this is an error keep the original value
                tx_length            <= previous_len; -- as this is an error keep the original value
                tx_state             <= TX_END;
              END IF;

            WHEN OTHERS =>
              tx_state           <= TX_ERROR;

          END CASE;
        END IF;

      END IF;
    END IF;
  END PROCESS;

  ----------------------------------------------------------------------------
  -- CP Master output signals we drive
  cp_out.clk     <= clk;
  cp_out.reset   <= to_bool(reset);
  cp_out.address <= flag_addr when cp_is_flag_write else rx_address(cp_out.address'LEFT + 2 DOWNTO 2); -- 24bit address adressing 32bit words
  cp_out.byte_en <= "1111"    when cp_is_flag_write else rx_dcp_msg_cde;
  cp_out.data    <= flag_data when cp_is_flag_write else rx_data;


end rtl;
