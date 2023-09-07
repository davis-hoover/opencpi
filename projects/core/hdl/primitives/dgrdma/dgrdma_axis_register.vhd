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
-- Register Slice with registered ready signal
-- ---------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all;

entity dgrdma_axis_register is

  generic(
    DATA_WIDTH  : natural := 64;
    KEEP_WIDTH  : natural := 8
  );

  port(
    -- clock and reset
    clk             : in std_logic;
    reset           : in std_logic;

    -- input
    s_axis_tdata    : in std_logic_vector((DATA_WIDTH - 1) downto 0);
    s_axis_tkeep    : in std_logic_vector((KEEP_WIDTH - 1) downto 0);
    s_axis_tvalid   : in std_logic;
    s_axis_tlast    : in std_logic;
    s_axis_tuser    : in std_logic;
    s_axis_tready   : out std_logic;

    -- output 
    m_axis_tdata    : out std_logic_vector((DATA_WIDTH - 1) downto 0);
    m_axis_tkeep    : out std_logic_vector((KEEP_WIDTH - 1) downto 0);
    m_axis_tvalid   : out std_logic;
    m_axis_tlast    : out std_logic;
    m_axis_tuser    : out std_logic;
    m_axis_tready   : in std_logic
  );

end dgrdma_axis_register;


architecture rtl of dgrdma_axis_register is

signal s_axis_tready_r     : std_logic;
signal s_axis_tready_early : std_logic;

signal m_axis_tdata_r     : std_logic_vector((DATA_WIDTH - 1) downto 0);
signal m_axis_tkeep_r     : std_logic_vector((KEEP_WIDTH - 1) downto 0);
signal m_axis_tlast_r     : std_logic;
signal m_axis_tuser_r     : std_logic;
signal m_axis_tvalid_r    : std_logic;
signal m_axis_tvalid_next : std_logic;

signal temp_axis_tdata_r      : std_logic_vector((DATA_WIDTH - 1) downto 0);
signal temp_axis_tkeep_r      : std_logic_vector((KEEP_WIDTH - 1) downto 0);
signal temp_axis_tlast_r      : std_logic;
signal temp_axis_tuser_r      : std_logic;
signal temp_axis_tvalid_r     : std_logic;
signal temp_axis_tvalid_next  : std_logic;

signal store_axis_input_to_output : boolean;
signal store_axis_input_to_temp   : boolean;
signal store_axis_temp_to_output  : boolean;

begin

  s_axis_tready <= s_axis_tready_r;
  m_axis_tdata  <= m_axis_tdata_r;
  m_axis_tkeep  <= m_axis_tkeep_r;
  m_axis_tvalid <= m_axis_tvalid_r;
  m_axis_tlast  <= m_axis_tlast_r;
  m_axis_tuser  <= m_axis_tuser_r;

  -- enable ready for input on next cycle if output is ready
  -- or the temp reg will not be filled on the next cycle
  s_axis_tready_early <= '1' when (m_axis_tready = '1') else
                         '1' when (temp_axis_tvalid_r = '0' and (m_axis_tvalid_r = '0' or s_axis_tvalid = '0')) else
                         '0';

  process(s_axis_tready_r, s_axis_tvalid, m_axis_tready, m_axis_tvalid_r, temp_axis_tvalid_r) is
  begin
    m_axis_tvalid_next    <= m_axis_tvalid_r;
    temp_axis_tvalid_next <= temp_axis_tvalid_r;

    store_axis_input_to_output <= false;
    store_axis_input_to_temp   <= false;
    store_axis_temp_to_output  <= false;

    if s_axis_tready_r = '1' then
      -- input is ready
      if m_axis_tready = '1' or m_axis_tvalid_r = '0' then
        -- output is ready or currently not m_axis_valid_r
        -- transfer data to output
        m_axis_tvalid_next <= s_axis_tvalid;
        store_axis_input_to_output <= true;
      else
        -- output is not ready
        -- store input in temp registers
        temp_axis_tvalid_next <= s_axis_tvalid;
        store_axis_input_to_temp <= true;
      end if;
    else
      if m_axis_tready = '1' then
        -- input is not ready, but output is ready
        m_axis_tvalid_next <= temp_axis_tvalid_r;
        temp_axis_tvalid_next <= '0';
        store_axis_temp_to_output <= true;
      end if;
    end if;
  end process;

  process(clk) is
  begin

    if rising_edge(clk) then
      if reset = '1' then
        m_axis_tdata_r     <= (others => '0');
        m_axis_tkeep_r     <= (others => '0');
        m_axis_tlast_r     <= '0';
        m_axis_tuser_r     <= '0';
        m_axis_tvalid_r    <= '0';
        temp_axis_tdata_r  <= (others => '0');
        temp_axis_tkeep_r  <= (others => '0');
        temp_axis_tlast_r  <= '0';
        temp_axis_tuser_r  <= '0';
        temp_axis_tvalid_r <= '0';
        s_axis_tready_r    <= '0';

      else
        s_axis_tready_r    <= s_axis_tready_early;
        m_axis_tvalid_r    <= m_axis_tvalid_next;
        temp_axis_tvalid_r <= temp_axis_tvalid_next;

        if (store_axis_input_to_output) then
          m_axis_tdata_r <= s_axis_tdata;
          m_axis_tkeep_r <= s_axis_tkeep;
          m_axis_tlast_r <= s_axis_tlast; 
          m_axis_tuser_r <= s_axis_tuser;         
        else
          if (store_axis_temp_to_output) then
            m_axis_tdata_r <= temp_axis_tdata_r;
            m_axis_tkeep_r <= temp_axis_tkeep_r;
            m_axis_tlast_r <= temp_axis_tlast_r;
            m_axis_tuser_r <= temp_axis_tuser_r;
          end if;
        end if;

        if (store_axis_input_to_temp) then
          temp_axis_tdata_r <= s_axis_tdata;
          temp_axis_tkeep_r <= s_axis_tkeep;
          temp_axis_tlast_r <= s_axis_tlast;
          temp_axis_tuser_r <= s_axis_tuser;
        end if; 

      end if;
    end if;

  end process;

end architecture;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------