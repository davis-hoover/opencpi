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

entity dgrdma_axis_pipeline is

  generic(
    DATA_WIDTH  : natural := 64;
    KEEP_WIDTH  : natural := 8;
    LENGTH      : natural := 2
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

end dgrdma_axis_pipeline;

architecture rtl of dgrdma_axis_pipeline is

type tdata_array_t  is array (LENGTH downto 0) of std_logic_vector((DATA_WIDTH - 1) downto 0);
type tkeep_array_t  is array (LENGTH downto 0) of std_logic_vector((KEEP_WIDTH - 1) downto 0);
type tvalid_array_t is array (LENGTH downto 0) of std_logic;
type tlast_array_t  is array (LENGTH downto 0) of std_logic;
type tuser_array_t  is array (LENGTH downto 0) of std_logic;
type tready_array_t is array (LENGTH downto 0) of std_logic;

signal axis_tdata  : tdata_array_t;
signal axis_tkeep  : tkeep_array_t;
signal axis_tvalid : tvalid_array_t;
signal axis_tlast  : tlast_array_t;
signal axis_tuser  : tuser_array_t;
signal axis_tready : tready_array_t;

component dgrdma_axis_register
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
end component dgrdma_axis_register;

begin

  axis_tdata(0)       <= s_axis_tdata;
  axis_tkeep(0)       <= s_axis_tkeep;
  axis_tvalid(0)      <= s_axis_tvalid;
  axis_tlast(0)       <= s_axis_tlast;
  axis_tuser(0)       <= s_axis_tuser;
  s_axis_tready       <= axis_tready(0);

  m_axis_tdata        <= axis_tdata(LENGTH);
  m_axis_tkeep        <= axis_tkeep(LENGTH);
  m_axis_tvalid       <= axis_tvalid(LENGTH);
  m_axis_tlast        <= axis_tlast(LENGTH);
  m_axis_tuser        <= axis_tuser(LENGTH);
  axis_tready(LENGTH) <= m_axis_tready;

  axis_register_gen : for ii in 0 to LENGTH-1 generate

    axis_register_inst : dgrdma_axis_register
      generic map (
        DATA_WIDTH  => DATA_WIDTH,
        KEEP_WIDTH  => KEEP_WIDTH
      )
      port map (
        clk             => clk,
        reset           => reset,

        -- AXI input
        s_axis_tdata    => axis_tdata(ii),
        s_axis_tkeep    => axis_tkeep(ii),
        s_axis_tvalid   => axis_tvalid(ii),
        s_axis_tready   => axis_tready(ii),
        s_axis_tlast    => axis_tlast(ii),
        s_axis_tuser    => axis_tuser(ii),

        -- AXI output
        m_axis_tdata    => axis_tdata(ii+1),
        m_axis_tkeep    => axis_tkeep(ii+1),
        m_axis_tvalid   => axis_tvalid(ii+1),
        m_axis_tready   => axis_tready(ii+1),
        m_axis_tlast    => axis_tlast(ii+1),
        m_axis_tuser    => axis_tuser(ii+1)
    );

  end generate;

end architecture;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------