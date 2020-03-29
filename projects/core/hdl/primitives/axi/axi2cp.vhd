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

-- Adapt the axi_gp master from the PS to a CP master
-- The clock and reset are injected to be supplied to both sides
library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library platform; use platform.all;
library ocpi; use ocpi.types.all, ocpi.util.all;
library work; use work.axi_pkg.all, work.AXI_INTERFACE.all;

entity axi2cp_AXI_INTERFACE is
  port(
    clk     : in std_logic;
    reset   : in bool_t;
    axi_in  : in  axi_m2s_t;
    axi_out : out axi_s2m_t;
    cp_in   : in  platform_pkg.occp_out_t;
    cp_out  : out platform_pkg.occp_in_t
    );
end entity axi2cp_AXI_INTERFACE;
architecture rtl of axi2cp_AXI_INTERFACE is
  signal read_done        : std_logic; -- true in the last cycle of the read
  signal write_done       : std_logic; -- true in the last cycle of the write
  signal address          : std_logic_vector(cp_out.address'range);
  -- state: actually there are 7 states: idle, read/writingn-starting, read/write, read/write-ending
  function read_byte_en(low2addr   : std_logic_vector(1 downto 0);
                        log2nbytes : std_logic_vector(2 downto 0))
    return std_logic_vector is
    variable mask : std_logic_vector(4 downto 0) := log2nbytes & low2addr;
  begin
   case mask is -- log2nbytes & low2addr is
     when "00000" => return "0001";
     when "00001" => return "0010";
     when "00010" => return "0100";
     when "00011" => return "1000";
     when "00100" => return "0011";
     when "00110" => return "1100";
     when "01000" => return "1111";
     when others  => return "0000";
   end case;
  end read_byte_en;
  type address_state_t is (a_idle_e,   -- nothing is happening
                           a_first_e,  -- first address (or two) is being offered to cp
                           a_first_1_e,  -- delay1 - testing
                           a_first_2_e,  -- delay2
                           a_last_e,   -- last address is offered to cp
                           a_taken_e); -- we're done, waiting for AXI to accept the response
  type read_state_t    is (r_idle_e,         -- nothing is happening
                           r_first_wanted_e, -- waiting for first response
                           r_first_valid_e,  -- first data is offered, not accepted
                           r_last_wanted_e,  -- waiting for last response
                           r_last_valid_e);  -- last is offered, not accepted
  signal address_state : address_state_t;
  signal read_state    : read_state_t;     
  signal addr2_r       : std_logic;
  signal RVALID        : std_logic;
begin
  -- Our state machines, separate for address and read-data
  work : process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        address_state <= a_idle_e;
        read_state    <= r_idle_e;
      else
        case address_state is
          when a_idle_e =>
            if axi_in.AW.VALID = '1' and axi_in.W.VALID = '1' then
              if axi_in.AW.LEN = slvn(1, axi_in.AW.LEN'length) then
                address_state <= a_first_e;
                addr2_r       <= '0';
              else
                addr2_r       <= axi_in.AW.ADDR(2);
                address_state <= a_last_e;
              end if;
            elsif axi_in.AR.VALID = '1' then
              if axi_in.AR.LEN = slvn(1, axi_in.AR.LEN'length) then --- BROKEN FOR SCALABLE AXI4 etc.
                addr2_r       <= '0';
                address_state <= a_first_e;
                read_state    <= r_first_wanted_e;
              else
                addr2_r       <= axi_in.AR.ADDR(2);
                address_state <= a_last_e;
                read_state    <= r_last_wanted_e;
              end if;
            end if;
          when a_first_e =>
            -- First of two.  The CP is taking the address and perhaps the write data
            if its(cp_in.take) then
              address_state <= a_first_1_e;
              addr2_r <= '1';
            end if;
          when a_first_1_e =>
            -- Delay slot 1
            address_state <= a_first_2_e;
          when a_first_2_e =>
            -- Delay slot 2
            address_state <= a_last_e;
          when a_last_e =>
            -- last address is offered. When it is taken we must change state.
            if its(cp_in.take) then
              if (read_state = r_idle_e and axi_in.B.READY = '1') or
                  (read_state /= r_idle_e and axi_in.R.READY = '1' and
                   (read_state = r_last_valid_e or
                    (read_state = r_last_wanted_e and cp_in.valid = '1'))) then
                -- if a write, and write response channel is ready, we're done
                -- if a read, and last read data is being accepted, we're done
                address_state <= a_idle_e;
              else
                address_state <= a_taken_e; -- axi master not ready for response
              end if;
            end if;
          when a_taken_e =>
            if (read_state = r_idle_e and axi_in.B.READY = '1') or
                (read_state /= r_idle_e and axi_in.R.READY = '1' and
                 (read_state = r_last_valid_e or
                  (read_state = r_last_wanted_e and cp_in.valid = '1'))) then
              -- if a write, and write response channel is ready, we're done
              -- if a read, and last read data is being accepted, we're done
              address_state <= a_idle_e;
            end if;
        end case;
        case read_state is
          when r_idle_e =>
            -- we exit this state based on address information above
            null;
          when r_first_wanted_e => -- implies 2 word burst
            if cp_in.valid = '1' then
              if axi_in.R.READY = '1' then
                read_state <= r_last_wanted_e;
              else
                read_state <= r_first_valid_e; -- waiting for RREADY
              end if;
            end if;
          when r_first_valid_e =>
            if axi_in.R.READY = '1' then
              read_state <= r_last_wanted_e;
            end if;
          when r_last_wanted_e =>
            if cp_in.valid = '1' then
              if axi_in.R.READY = '1' then
                read_state <= r_idle_e;
              else
                read_state <= r_last_valid_e;
              end if;
            end if;
          when r_last_valid_e =>
            if axi_in.R.READY = '1' then
              read_state <= r_idle_e;
            end if;
        end case;
      end if; -- not reset
    end if; -- rising edge
  end process;
  ------------------------------------------------------------------------------
  -- Combinatorial convenience signals used for various outputs
  read_done  <= to_bool((read_state = r_last_wanted_e and cp_in.valid = '1') or
                       read_state = r_last_valid_e);
  write_done <= to_bool(read_state = r_idle_e and
                        (address_state = a_taken_e or
                         (address_state = a_last_e and cp_in.take = '1')));
  RVALID     <= to_bool((read_state = r_first_wanted_e and cp_in.valid = '1') or
                        read_state = r_first_valid_e or
                        read_done = '1');
  ------------------------------------------------------------------------------
  -- Now we drive external signals based on our state and the combi signals
  -- AXI GP signals we drive from the PL into the PS, ordered per AXI Chapter 2
  -- Global signals
#if !CLOCK_FROM_MASTER
  axi_out.A.CLK    <= clk;       -- we drive the AXI clock as the SDP CLK
#endif
#if !RESET_FROM_MASTER
  axi_out.A.RESETn <= not reset; -- we drive the reset as the SDP reset
#endif
#if AXI4
  axi_out.B.USER <= (others => '0');
  axi_out.R.USER <= (others => '0');
#endif
  -- Write Address Channel: we accept addresses when we don't need them anymore
  --                        note we need the AWID for the all responses
  axi_out.AW.READY <= write_done;
  -- Write Data Channel: we accept the data whenever a write request is taken
  axi_out.W.READY  <= to_bool(read_state = r_idle_e and cp_in.take = '1' and
                             (address_state = a_first_e or address_state = a_last_e));
  -- Write Response Channel: we offer the write response
  axi_out.B.ID     <= axi_in.AW.ID; -- we only do one at a time so we loop back the ID
  axi_out.B.RESP   <= Resp_OKAY;
  axi_out.B.VALID  <= write_done;
  -- Read Address Channel
  axi_out.AR.READY <= read_done;
  -- Read Data Channel
  axi_out.R.ID     <= axi_in.AR.ID;
  axi_out.R.DATA   <= cp_in.data;
  axi_out.R.RESP   <= Resp_OKAY;
  axi_out.R.LAST   <= read_done;
  axi_out.R.VALID  <= RVALID;
  ----------------------------------------------------------------------------
  -- CP Master output signals we drive
  cp_out.clk        <= clk;
  cp_out.reset      <= reset;
  -- Note we need to wait for valid write (WVALID) to arrive when writing and a_last_e
  -- since we enter that state without regard to WVALID and it might not be there then
  cp_out.valid      <= to_bool(address_state = a_first_e or
                               (address_state = a_last_e and
                                (read_state /= r_idle_e or
                                 axi_in.W.VALID = '1')));
  cp_out.is_read    <= to_bool(read_state /= r_idle_e);
  address           <= axi_in.AW.ADDR(cp_out.address'left + 2 downto 2)
                       when read_state = r_idle_e else
                       axi_in.AR.ADDR(cp_out.address'left + 2 downto 2);
  cp_out.address(cp_out.address'left downto 1) <= address(address'left downto 1);
  cp_out.address(0) <= addr2_r;
  cp_out.byte_en    <= axi_in.W.STRB when read_state = r_idle_e else
                       read_byte_en(axi_in.AR.ADDR(1 downto 0),
                                    axi_in.AR.SIZE);
  cp_out.data       <= axi_in.W.DATA;
  cp_out.take       <= RVALID and axi_in.R.READY;
end rtl;
