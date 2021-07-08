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
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all;
library cdc;
library protocol;

entity fifo_complex_short_with_metadata is
  generic(
    DEPTH : natural := 2);
  port(
    -- INPUT
    iclk     : in  std_logic;
    irst     : in  std_logic;
    ienq     : in  std_logic;
    iprotocol: in  protocol.complex_short_with_metadata.protocol_t;
    ieof     : in  std_logic;
    ifull_n  : out std_logic;
    -- OUTPUT
    oclk     : in  std_logic;
    odeq     : in  std_logic;
    oprotocol: out protocol.complex_short_with_metadata.protocol_t;
    oeof     : out std_logic;
    oempty_n : out std_logic);
end entity;
architecture rtl of fifo_complex_short_with_metadata is
  signal src_in           : std_logic_vector(
      protocol.complex_short_with_metadata.PROTOCOL_BIT_WIDTH downto 0) :=
      (others => '0');
  signal dst_out          : std_logic_vector(
      protocol.complex_short_with_metadata.PROTOCOL_BIT_WIDTH downto 0) :=
      (others => '0');
  signal dst_out_protocol : std_logic_vector(
      protocol.complex_short_with_metadata.PROTOCOL_BIT_WIDTH-1 downto 0) :=
      (others => '0');
  signal fifo_dst_empty_n : std_logic := '0';
  signal protocol_s       : protocol.complex_short_with_metadata.protocol_t :=
                            protocol.complex_short_with_metadata.PROTOCOL_ZERO;
begin

  src_in <= protocol.complex_short_with_metadata.to_slv(iprotocol) & ieof;

  fifo : cdc.cdc.fifo
    generic map(
      WIDTH       => protocol.complex_short_with_metadata.PROTOCOL_BIT_WIDTH+1,
      DEPTH       => DEPTH)
    port map(
      src_CLK     => iclk,
      src_RST     => irst,
      src_ENQ     => ienq,
      src_in      => src_in,
      src_FULL_N  => ifull_n,
      dst_CLK     => oclk,
      dst_DEQ     => odeq,
      dst_out     => dst_out,
      dst_EMPTY_N => fifo_dst_empty_n);

  oempty_n <= fifo_dst_empty_n;

  dst_out_protocol <= dst_out(
      protocol.complex_short_with_metadata.PROTOCOL_BIT_WIDTH downto 1);
  protocol_s <= protocol.complex_short_with_metadata.from_slv(dst_out_protocol);

  -- FIXME: remote all this qualification with empty_n have downstream qualify use oempty_n properly
  oprotocol.samples        <= protocol_s.samples;
  oprotocol.samples_vld    <= protocol_s.samples_vld and fifo_dst_empty_n;
  oprotocol.time           <= protocol_s.time;
  oprotocol.time_vld       <= protocol_s.time_vld and fifo_dst_empty_n;
  oprotocol.interval       <= protocol_s.interval;
  oprotocol.interval_vld   <= protocol_s.interval_vld and fifo_dst_empty_n;
  oprotocol.flush          <= protocol_s.flush and fifo_dst_empty_n;
  oprotocol.sync           <= protocol_s.sync and fifo_dst_empty_n;
  oprotocol.end_of_samples <= protocol_s.end_of_samples and fifo_dst_empty_n;
  oeof                     <= dst_out(0) and fifo_dst_empty_n;

end rtl;
