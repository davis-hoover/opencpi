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

-- THIS FILE WAS ORIGINALLY GENERATED ON Sun Apr  5 09:03:54 2015 EDT
-- BASED ON THE FILE: sdp_node.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: sdp_node
-- Note THIS IS THE OUTER skeleton, since the 'outer' attribute was set.

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions

architecture rtl of sdp_node_worker is

  -- Combinatorial state for splitting downstream messages to "client" or "down"
  signal for_client       : bool_t; -- the message coming from up_in is for the client

  -- State for joining upstream messsages from "client" or "down".
  signal up_starting      : bool_t;
  signal up_ending        : bool_t;
  signal up_from_client   : bool_t;
  signal up_active_r      : bool_t; -- We are sending a message to up_out, not the first cycle
  signal up_from_client_r : bool_t; -- The current (or last) message is from client.

begin
  -------------------------------------------------------------------------
  -- The first function is to route messages arriving on the up_in channel
  -- to either the client_out channel or the down_out channel.
  -- Since the header is stable for the length of the message, its easy.
  -- The "ready" signal is routed back to the "up" channel from the recipient.
  for_client <= to_bool(up_in.sdp.header.node = up_in.id);

  -- Copy the incoming upstream info to the client, qualifying the valid signal
  client_out.id <= up_in.id;
  client_out.sdp.header <= up_in.sdp.header;
  client_out.sdp.eop <= up_in.sdp.eop;
  client_out_data <= up_in_data;
  client_out.sdp.valid <= up_in.sdp.valid and for_client;

  -- Copy the incoming upstream info downstream, qualifying the valid signal
  down_out.id <= up_in.id + 1;
  down_out.sdp.header <= up_in.sdp.header;
  down_out.sdp.eop <= up_in.sdp.eop;
  down_out_data <= up_in_data;
  down_out.sdp.valid <= up_in.sdp.valid and not for_client;

  -- Accept the incoming frame from the recipient
  up_out.sdp.ready <= client_in.sdp.ready when its(for_client) else down_in.sdp.ready;

  -- The drop count comes from the sdp_term at the end of the bus
  up_out.dropCount <= down_in.dropCount;

  -------------------------------------------------------------------------
  -- The "joining" function, from down and/or client to upstream
  -- This needs memory to implement fairness so it has some state
  -- It also must keep the routing stable within a message.

  -- Are we starting an upstream message in THIS cycle?
  up_starting <= not up_active_r and (client_in.sdp.valid or down_in.sdp.valid);

  -- Are we ending a message in this cycle?
  up_ending <= client_in.sdp.valid and client_in.sdp.eop and up_in.sdp.ready
               when its(up_from_client) else
               down_in.sdp.valid and down_in.sdp.eop and up_in.sdp.ready;

  -- mux into up_out channel
  up_out.sdp.header    <= client_in.sdp.header when its(up_from_client) else down_in.sdp.header;
  up_out.sdp.eop       <= client_in.sdp.eop    when its(up_from_client) else down_in.sdp.eop;
  up_out.sdp.valid     <= client_in.sdp.valid  when its(up_from_client) else down_in.sdp.valid;
  up_out_data          <= client_in_data       when its(up_from_client) else down_in_data;
  up_out.isNode        <= btrue;

  down_out.sdp.ready   <= up_in.sdp.ready and down_in.sdp.valid and not up_from_client;
  client_out.sdp.ready <= up_in.sdp.ready and client_in.sdp.valid and up_from_client;

  -------------------------------------------------------------------------
  -- Arbitration interface least-recently used

  arbitrate_lru: if unsigned(sdp_arb) = 0 generate

  begin
    -- implement least-recently-used arbitration when deciding to take data
    -- from the client or down interface
    -- 1) hold the previous decision whilst the transfer is active
    -- 2) select the client when it has something to send AND there is nothing on the
    -- down interface
    -- 3) select the client when it has something to send AND the client wasn't
    -- used for the last transfer
    up_from_client <= up_from_client_r when its(up_active_r) else
                    client_in.sdp.valid and (not down_in.sdp.valid or not up_from_client_r);

     -- pass the metadata through from the selected interface
    up_out.metaData <= client_in.metaData  when its(up_from_client) else down_in.metaData;

  end generate arbitrate_lru;

  -------------------------------------------------------------------------
  -- Arbitration interface longest waiting

  arbitrate_full: if unsigned(sdp_arb) > 0 generate

      -- implement which interface has been waiting longest scheme
      -- the number of clock cycles that out client has been wait is calculated
      -- and the maximum of this count or the count passed up from the sdp-node
      -- down-stream of us is passed upwards. each node can then see if anything
      -- downstream has been waiting longer than our client and if so prioritise it
      constant c_waiting_prio_width   : integer := up_out.metaData'length;
      constant c_waiting_count_width  : integer := to_integer(unsigned(sdp_arb));
      constant c_waiting_count_max    : integer := (2**c_waiting_count_width)-1;

      signal client_waiting_count_r   : unsigned(c_waiting_count_width-1 downto 0);
      signal client_waiting           : unsigned(c_waiting_prio_width-1 downto 0);
      signal client_waiting_prio      : unsigned(c_waiting_prio_width-1 downto 0);

      signal down_waiting_count_r     : unsigned(c_waiting_count_width-1 downto 0);
      signal down_waiting             : unsigned(c_waiting_prio_width-1 downto 0);
      signal down_waiting_prio        : unsigned(c_waiting_prio_width-1 downto 0);

      signal client_has_prio          : bool_t;

  begin

    -- 1) hold the previous decision whilst the transfer is active
    -- 2) select the client when it has something to send AND there is nothing on the down interface
    -- 3) select the client when it has something to send AND our client has been waiting the longest
      up_from_client <= up_from_client_r when its(up_active_r)
          else client_in.sdp.valid and (not down_in.sdp.valid or client_has_prio);

      -- convert the width of the wait count to match the metaData signal width
      client_waiting <= client_waiting_count_r((c_waiting_count_width-1) downto (c_waiting_count_width-c_waiting_prio_width)) when (c_waiting_prio_width < c_waiting_count_width)
          else resize(client_waiting_count_r, c_waiting_prio_width);

      client_waiting_prio <= client_waiting;

      -- convert the width of the wait count to match the metaData signal width
      down_waiting <= down_waiting_count_r((c_waiting_count_width-1) downto (c_waiting_count_width-c_waiting_prio_width)) when (c_waiting_prio_width < c_waiting_count_width)
          else resize(down_waiting_count_r, c_waiting_prio_width);

      -- if the down interface is connected to another sdp-node we can use
      -- the waiting count directly from it. if it is connected to a client
      -- then use our own count
      down_waiting_prio <= down_in.metaData when its(down_in.isnode)
          else down_waiting;

      arb_work_client : process(sdp_clk)
      begin

        if rising_edge(sdp_clk) then

          -- reset the client waiting counter
          if its(sdp_reset) then
            client_waiting_count_r <= (others => '0');
            up_out.metaData <= (others => '0');
            client_has_prio <= bfalse;

          else

            -- our client has been waiting the longest
            client_has_prio <= to_bool(client_waiting_prio >= down_waiting_prio);

            -- if client has been selected reset the wait counter
            if (its(up_in.sdp.ready) and its(client_in.sdp.valid) and its(up_from_client)) then
              client_waiting_count_r <= (others => '0');
                up_out.metaData <= (others => '0');

            -- hold the waiting count if client doesn't have any data
            elsif (not client_in.sdp.valid) then
              client_waiting_count_r <= client_waiting_count_r;

              if (client_waiting_prio > down_waiting_prio) then
                up_out.metaData <= client_waiting_prio;
              else
                up_out.metaData <= down_waiting_prio;
              end if;

            -- saturate the client wait counter
            elsif (client_waiting_count_r = to_unsigned(c_waiting_count_max, c_waiting_count_width)) then
              client_waiting_count_r <= client_waiting_count_r;

              if (client_waiting_prio > down_waiting_prio) then
                up_out.metaData <= client_waiting_prio;
              else
                up_out.metaData <= down_waiting_prio;
              end if;

            -- increment the waiting count
            else
              client_waiting_count_r <= client_waiting_count_r + 1;

              if ((client_waiting_prio + 1) > down_waiting_prio) then
                up_out.metaData <= (client_waiting_prio + 1);
              else
                up_out.metaData <= down_waiting_prio;
              end if;
            end if;
          end if;
        end if;
      end process;

      -- if the down interface is not connected to another sdp-node
      -- (i.e. it is at the end of the chain and is connected directly
      -- to a client then we need to count how long the client has been waiting
      arb_work_down : process(sdp_clk)
      begin

        if rising_edge(sdp_clk) then

          -- reset the down interface waiting counter
          if its(sdp_reset) then
            down_waiting_count_r <= (others => '0');

          -- if down has been selected reset the wait counter
          elsif (its(up_in.sdp.ready) and its(down_in.sdp.valid) and not its(up_from_client)) then
            down_waiting_count_r <= (others => '0');

          -- hold the waiting count if there isn't any data
          elsif (not down_in.sdp.valid) then
            down_waiting_count_r <= down_waiting_count_r;

          -- saturate the waiting counter
          elsif (down_waiting_count_r = to_unsigned(c_waiting_count_max, c_waiting_count_width)) then
            down_waiting_count_r <= down_waiting_count_r;

          -- increment the waiting count
          else
            down_waiting_count_r <= down_waiting_count_r + 1;

          end if;

        end if;
      end process;

  end generate arbitrate_full;

  -------------------------------------------------------------------------
  -- Our state machine for upstream messages - keep track of 2 FFs.
  work : process(sdp_clk)
  begin

    if rising_edge(sdp_clk) then

      if its(sdp_reset) then
        up_active_r      <= bfalse;
        up_from_client_r <= bfalse;

      else

        if up_starting and not its(up_ending) then
          up_from_client_r <= up_from_client; -- make this sticky through a message
          if not up_ending then
            up_active_r <= btrue;
          end if;
        end if;

        if its(up_ending) then
          up_active_r <= bfalse;
        end if;

      end if; -- end not reset
    end if; -- end rising edge
  end process;

end rtl;
