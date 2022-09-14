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

-- THIS FILE WAS ORIGINALLY GENERATED ON Thu Jun 16 23:55:16 2016 EDT
-- BASED ON THE FILE: sdp_pipeline.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: sdp_pipeline
-- Note THIS IS THE OUTER skeleton, since the 'outer' attribute was set.

-- header
-- sdp_header_width:
-- op 2
-- xid 3
-- lead 2
-- trail 2
-- node 4
-- count 12
-- addr 10 + 14
-- extaddr 10: total is 61 + 32 + 1 is 0 to 93

library IEEE, ocpi, sdp, util, sync;
use IEEE.std_logic_1164.all, ieee.numeric_std.all, ocpi.types.all, sdp.sdp.all;
architecture rtl of sdp_pipeline_worker is
  constant sdp_width_c : positive := to_integer(sdp_width);
  constant width_c : positive := sdp_width_c * dword_size + sdp_header_ndws*32 + 1;
  subtype data_t is std_logic_vector(width_c-1 downto 0); -- values in up and down fifos
  signal up_enq, up_deq, up_full, up_empty : bool_t;
  signal down_enq, down_deq, down_full, down_empty : bool_t;
  signal down_in_slv, up_out_slv, up_in_slv, down_out_slv : data_t;
  signal up_full_n, up_empty_n, down_full_n, down_empty_n : bool_t; -- for sync.fifo modules - ick
  function sdp2slv(dws : dword_array_t; sdp : sdp_t) return data_t is
    variable v : data_t;
  begin
    for i in 0 to sdp_width_c-1 loop
      v(i*32+31 downto i*32) := dws(i);
    end loop;
    for i in 0 to sdp_header_ndws-1 loop
      v((i+sdp_width_c)*32+31 downto (i+sdp_width_c)*32) := header2dws(sdp.header)(i);
    end loop;
    v(v'left) := sdp.eop;
    return v;
  end sdp2slv;
  function slv2sdp_data(slv : data_t) return dword_array_t is
    variable v : dword_array_t(0 to sdp_width_c-1);
  begin
    for i in 0 to sdp_width_c-1 loop
      v(i) := slv(i*32+31 downto i*32);
    end loop;
    return v;
  end slv2sdp_data;
  function slv2sdp(slv : data_t; empty : bool_t; enq : bool_t) return sdp_t is
    variable v : dword_array_t(0 to sdp_header_ndws-1);
    variable sdp : sdp_t;
  begin
    for i in 0 to sdp_header_ndws-1 loop
      v(i) := slv((i+sdp_width_c)*32+31 downto (i+sdp_width_c)*32);
    end loop;
    sdp.header := dws2header(v);
    sdp.eop := slv(slv'left);
    sdp.valid := not empty;
    sdp.ready := enq;
    return sdp;
  end slv2sdp;
begin
  -- data path conversions between slv bits (for fifo) and sdp records and data

  -- flowing from down_in to up_out
  down_in_slv <= sdp2slv(down_in_data, down_in.sdp);
  up_out_data <= slv2sdp_data(up_out_slv);
  up_out.sdp  <= slv2sdp(up_out_slv, up_empty, down_enq);

  -- flowing from up_in to down_out
  up_in_slv  <= sdp2slv(up_in_data, up_in.sdp);
  down_out_data <= slv2sdp_data(down_out_slv);
  down_out.sdp  <= slv2sdp(down_out_slv, down_empty, up_enq);

  -- the unfortunate part of this is that we can't assign whole records because
  -- the take/ready signals are in the opposite directions for other reasons

  -- The flow-through signals not subject to pipelining
  down_out.id         <= up_in.id;           -- totally static value
  up_out.dropCount    <= down_in.dropCount;  -- nearly static value for debug
  up_out.isNode       <= down_in.isNode;     -- totally static value
  up_out.metadata     <= down_in.metadata;   -- dynamic value changing when fifo is not

  up_full             <= not up_full_n; -- FIXED when these fifos move to util
  up_empty            <= not up_empty_n; -- FIXED when these fifos move to util
  up_enq              <= down_in.sdp.valid and not up_full;
  up: component sync.sync.sync_fifo_1xn
    generic map(width  => width_c)
    port map   (clk    => sdp_clk,
                rst    => sdp_reset,
                clr    => '0',
                enq    => up_enq,
                deq    => up_in.sdp.ready,
                d_in   => down_in_slv,
                full_n => up_full_n,
                empty_n=> up_empty_n,
                d_out  => up_out_slv);

  down_full             <= not down_full_n;  -- FIXED when these fifos move to util
  down_empty            <= not down_empty_n;  -- FIXED when these fifos move to util
  down_enq           <= up_in.sdp.valid and not down_full;
  down: component sync.sync.sync_fifo_1xn
    generic map(width  => width_c)
    port map   (clk    => sdp_clk,
                rst    => sdp_reset,
                clr    => '0',
                enq    => down_enq,
                deq    => down_in.sdp.ready,
                d_in   => up_in_slv,
                full_n => down_full_n,
                empty_n=> down_empty_n,
                d_out  => down_out_slv);

end rtl;
