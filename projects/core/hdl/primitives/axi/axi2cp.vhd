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

-- Adapt an axi slave to a CP master

-- The CP master is driving the control plane clock so this module has two clock modes:
-- 1. The axi master is driving the clock and that clock will drive the CP master
--    and thus the clk port is *ignored*.
-- 2. The axi slave is supposed to drive the clock so the clk port is an input
--    that will drive BOTH the AXI clock (from the slave side) and the CP master
-- So we'll use CPCLK as the process clock for this adapter, which is either the input
-- port clk or the AXI master's clock.
-- We use the CPP to do this (not VHDL), which avoids clock assignments and delta cycles
-- and also keeps all the interface attributes in one place (in the interface header file)
-- We will do the same for reset.

-- The user of this module must be aware of the fact that if the AXI master
-- drives the clock and the slave drives the reset, that the slave (and CP) reset
-- will be the input port "reset", and that reset must be synchronized to the
-- AXI master's clock (i.e. that is not done here).

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library platform; use platform.all;
library ocpi; use ocpi.types.all, ocpi.util.all;
library util;
library work; use work.axi_pkg.all, work.AXI_INTERFACE.all;

entity axi2cp_AXI_INTERFACE is
  port(
    clk     : in std_logic;  -- not used if interface says AXI master drives clock
    reset   : in bool_t;     -- not used if interface says AXI master drives reset
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
  function read_byte_en(low2addr   : std_logic_vector(1 downto 0);
                        log2nbytes : std_logic_vector(2 downto 0))
    return std_logic_vector is
    variable mask : std_logic_vector(4 downto 0) := log2nbytes & low2addr;
  begin
    if unsigned(log2nbytes) >= 2 then
      return "1111";
    end if;
    case mask is -- log2nbytes & low2addr is
      when "00000" => return "0001";
      when "00001" => return "0010";
      when "00010" => return "0100";
      when "00011" => return "1000";
      when "00100" => return "0011";
      when "00110" => return "1100";
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
                           r_first_wanted_e, -- waiting for first of 2 responses
                           r_first_valid_e,  -- first data is offered, not accepted
                           r_last_wanted_e,  -- waiting for last response
                           r_last_valid_e);  -- last is offered, not accepted
  signal address_state : address_state_t;
  signal read_state    : read_state_t;
  signal dwaddr_r      : unsigned(width_for_max(max(axi_in.W.DATA'length/32-1,1))-1 downto 0);
  signal dw_lsb        : natural;
  signal dw_lsb_en     : natural;
  signal size64_r      : bool_t; -- remembering whether the request was 64 bits
  signal RVALID        : std_logic;
  signal cp_reset      : bool_t;
  signal hold_dword_r  : dword_t; -- when the bus is > 32 bits, hold first 32 of 64 here
begin
  --============================================================================================
  -- Clock and reset handling given that clock and reset may be (independently) from either side
  #if CLOCK_FROM_MASTER
    #define CPCLK axi_in.a.clk
  #else
    #define CPCLK clk
    -- delta cycle alert in some tools even though this is a verilog module
    in2out_axi_clk: util.util.in2out port map(in_port => clk, out_port => axi_out.a.clk);
  #endif
// clang 12.0 bug needs this line
  #if RESET_FROM_MASTER
    cp_reset         <= not axi_in.a.resetn;
  #else
    cp_reset         <= reset;
    axi_out.a.resetn <= not reset;
  #endif
  -- delta cycle alert in some tools even though this is a verilog module
  in2out_cp_clk: util.util.in2out port map(in_port => CPCLK, out_port => cp_out.clk);
  cp_out.reset <= cp_reset;
  --============================================================================================

  -- Our state machines, separate for address and read-data
  work : process(CPCLK)
  begin
    if rising_edge(CPCLK) then
      if its(cp_reset) then
        address_state <= a_idle_e;
        read_state    <= r_idle_e;
      else
        case address_state is
          when a_idle_e =>
            if axi_in.AW.VALID = '1' and axi_in.W.VALID = '1' then
              -- We are doing a 64 bit write (in two 32 bit chunks) if either:
              ---- the data path is 32 bits and the burst is 2 words,
              ---- the data path is > 32 bits and the transfer size is 6 (meaning 64 bits)
              dwaddr_r      <= unsigned(axi_in.AW.ADDR(dwaddr_r'left + 2 downto 2));
              if (axi_in.W.DATA'length = 32 and axi_in.AW.LEN = slvn(1, axi_in.AW.LEN'length)) or
                 (axi_in.W.DATA'length > 32 and axi_in.AW.SIZE = slvn(3, axi_in.AW.SIZE'length)) then
                address_state <= a_first_e;
                size64_r      <= btrue;
                -- hold onto the 32 MSBs to use for the second of 2 CP write cycles
                hold_dword_r  <= axi_in.W.DATA(axi_in.W.DATA'left downto axi_in.W.DATA'left-31);
              else
                address_state <= a_last_e;
                size64_r      <= bfalse;
              end if;
            elsif axi_in.AR.VALID = '1' then
              -- We are doing a 64 bit read (in two 32 bit chunks) if either:
              ---- the data path is 32 bits and the burst is 2 words,
              ---- the data path is > 32 bits and the transfer size is 6 (meaning 64 bits)
              dwaddr_r      <= unsigned(axi_in.AR.ADDR(dwaddr_r'left + 2 downto 2));
              if (axi_out.R.DATA'length = 32 and axi_in.AR.LEN = slvn(1, axi_in.AR.LEN'length)) or
                 (axi_out.R.DATA'length > 32 and axi_in.AR.SIZE = slvn(3, axi_in.AR.SIZE'length)) then
                address_state <= a_first_e;
                read_state    <= r_first_wanted_e;
                size64_r      <= btrue;
              else
                address_state <= a_last_e;
                read_state    <= r_last_wanted_e;
                size64_r      <= bfalse;
              end if;
            end if;
          when a_first_e =>
            -- First of two.  The CP is taking the address and perhaps the write data
            if its(cp_in.take) then
              address_state <= a_first_1_e;
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
          when r_first_wanted_e => -- implies 64 bit read
            if cp_in.valid = '1' then
              hold_dword_r <= cp_in.data; -- save LSB dword and wait for second
              if axi_in.R.READY = '1' or axi_out.R.DATA'length > 32 then
                read_state <= r_last_wanted_e;
              else
                read_state <= r_first_valid_e; -- waiting for RREADY
              end if;
            end if;
          when r_first_valid_e => -- only here when data width is 32
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
  RVALID     <= to_bool((axi_out.R.DATA'length = 32 and
                         ((read_state = r_first_wanted_e and cp_in.valid = '1') or
                          read_state = r_first_valid_e)) or
                        read_done = '1');
  ------------------------------------------------------------------------------
  -- Now we drive external signals based on our state and the combi signals
  -- AXI GP signals we drive from the PL into the PS, ordered per AXI Chapter 2
  -- Global signals
#if AXI4
  axi_out.B.USER <= (others => '0');
  axi_out.R.USER <= (others => '0');
#endif
  -- Write Address Channel: we accept addresses when we don't need them anymore
  --                        note we need the AWID for the all responses
  axi_out.AW.READY <= write_done;
  -- Write Data Channel: we accept the data whenever a write request is taken
  axi_out.W.READY  <= to_bool(read_state = r_idle_e and cp_in.take = '1' and
                              ((address_state = a_first_e and axi_in.W.DATA'length = 32)
                               or address_state = a_last_e));
  -- Write Response Channel: we offer the write response
  axi_out.B.ID     <= axi_in.AW.ID; -- we only do one at a time so we loop back the ID
  axi_out.B.RESP   <= Resp_OKAY;
  axi_out.B.VALID  <= write_done;
  -- Read Address Channel
  axi_out.AR.READY <= read_done;
  -- Read Data Channel
  axi_out.R.ID     <= axi_in.AR.ID;
  g0: if axi_out.R.DATA'length = 32 generate
    axi_out.R.DATA <= cp_in.data;
  end generate;
  g1: if axi_out.R.DATA'length > 32 generate
    -- provide the data based on addressing.
    -- either it is a 64 bit word with the last data as MSB or the data
    -- bets routed to log or high based on the address
    g2: for i in 0 to axi_out.R.DATA'length/32-1 generate
      axi_out.R.DATA(i*32+31 downto i*32) <=
        hold_dword_r when size64_r and i = dwaddr_r else cp_in.data;
    end generate;
  end generate;
  axi_out.R.RESP   <= Resp_OKAY;
  axi_out.R.LAST   <= read_done;
  axi_out.R.VALID  <= RVALID;
  ----------------------------------------------------------------------------
  -- CP Master output signals we drive
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
  cp_out.address(0) <= '0' when size64_r and address_state = a_first_e else
                       '1' when size64_r and address_state /= a_first_e else
                       dwaddr_r(0);
  g3: if axi_in.W.DATA'length = 32 generate
    cp_out.data       <= axi_in.W.DATA;
    cp_out.byte_en    <= axi_in.W.STRB(cp_out.byte_en'range) when read_state = r_idle_e else
                         read_byte_en(axi_in.AR.ADDR(1 downto 0), axi_in.AR.SIZE);
  end generate;
  g4: if axi_in.W.DATA'length > 32 generate
    dw_lsb    <= to_integer(dwaddr_r & "00000");
    dw_lsb_en <= to_integer(dwaddr_r & "00");
    cp_out.data    <= axi_in.W.DATA(dw_lsb + 31 downto dw_lsb);
    cp_out.byte_en <= axi_in.W.STRB(dw_lsb_en + 3 downto dw_lsb_en) when read_state = r_idle_e else
                      read_byte_en(axi_in.AR.ADDR(1 downto 0), axi_in.AR.SIZE);
  end generate;
  cp_out.take      <= to_bool(its(cp_in.valid) and 
                              ((axi_out.R.DATA'length > 32 and read_state = r_first_wanted_e) or
                               (RVALID = '1' and axi_in.R.READY = '1')));
end rtl;
