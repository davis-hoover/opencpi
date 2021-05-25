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

----------------------------------------------------------------------------------------------------
-- This module in inserted between an SDP slave and an AXI slave and thus itself acts as
-- an SDP master and AXI master.
--   Note:  In AXI terminology, master is who issues reads and writes.
--          In SDP terminology, master is who asserts clock/reset, and either side can read or write.
--   The AXI side, as a master, can issue AXI read and write requests.
--   It supports the OpenCPI data plane when the SDP is reading and writing to the interconnect
--   as a "DMA master".
--   So this adapter receives read/write requests as an SDP master and issues read/write request
--   as an AXI master.
--   This module will not issue any read or write requests to SDP as an SDP master
--   because it does not act as an AXI slave and so has no reason to issue reads or writes to SDP.
--   When a read request comes from SDP, the response (when it comes back from AXI)
--   will be returned to the SDP slave that initiated the read request.
-- It is parameterized (CPP-style) by the AXI interface parameters (see README).

-- Clocking - determined by the AXI interface parameters

-- The SDP interface is driving the SDP clock so this module has two clock modes:
-- 1. The axi master is driving the clock and that clock will drive the SDP clock (as SDP master)
--    and thus the clk input port is *ignored*.
-- 2. The axi slave is supposed to drive the clock so the clk port is an input
--    that will drive BOTH the AXI clock (from the slave side) and the SDP master's clock
-- So we'll use SDPCLK as the process clock for this adapter, which is either the input
-- port clk or the AXI master's clock.
-- We use the CPP to do this (not VHDL), which avoids clock assignments and delta cycles
-- and also keeps all the interface attributes in one place (in the interface header file)
-- We will do the same for reset.

-- The user of this module must be aware of the fact that if the AXI master
-- drives the clock and the AXI slave drives the reset, that the slave (and SDP) reset
-- will be the input port "reset", and that reset must be synchronized to the
-- AXI master's clock (i.e. that is not done here).

-- OPTIMIZING FOR FMAX:  when going to 100MHZ on zynq, we introduced a pipeline
-- to compute all the values derived from incoming SDP headers.
-- The variables with the _p suffix are those that were promoted from combinatorial
-- values on a (slower) functional version to be registered for pipeline purposes.
-- Combinatorial values used in the first pipeline stage (to capture in the _p), have _0 suffix

library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library platform; use platform.platform_pkg.all;
library ocpi; use ocpi.types.all, ocpi.util.all;
library axi; use axi.axi_pkg.all;
library sdp; use sdp.sdp.all;
library util;
library work; use work.axi_pkg.all, work.AXI_INTERFACE.all;

entity sdp2axi_AXI_INTERFACE is
  generic(
    ocpi_debug   : boolean;
    sdp_width    : natural);
  port(
    clk          : in  std_logic;   -- not used if interface says AXI slave drives the clock
    reset        : in  bool_t;      -- not used if interface says AXI master drives reset
    sdp_in       : in  s2m_t;
    sdp_in_data  : in  dword_array_t(0 to sdp_width-1);
    sdp_out      : out m2s_t;
    sdp_out_data : out dword_array_t(0 to sdp_width-1);
    axi_in       : in  axi_s2m_t;
    axi_out      : out axi_m2s_t;
    axi_error    : out bool_t;
    dbg_state    : out ulonglong_t;
    dbg_state1   : out ulonglong_t;
    dbg_state2   : out ulonglong_t
    );
end entity sdp2axi_AXI_INTERFACE;
architecture rtl of sdp2axi_AXI_INTERFACE is
  --------------------------------------------------------------------------------
  -- Terminology:
  -- xf     the beat of a data path - a "transfer"
  -- sxf    the "beat" of the sdp data path when valid
  -- pkt    the 1-or-more sxf sdp packet w/ request/address and (if a write) write data
  -- axf    the "beat" of the axi data path (fixed at 64 bits wide here)
  -- burst  the burst (of axfs) of data over AXI to a single requested address
  -- dw:    32 bit word (Microsoft's and PCI's anachronistic DWORD)
  -- sw:    sdp word (payload of sdp transfer sdp_width*32)
  -- aw:    axi word (currently 64b)
  --------------------------------------------------------------------------------
  constant axi_width           : natural := axi_out.w.data'length/dword_size;
  constant aw_bytes_c          : natural := axi_width * dword_bytes;
  constant axi_max_burst_c     : natural := 2**axi_out.aw.len'length;
  subtype pkt_naxf_t           is unsigned(width_for_max(max_pkt_dws/axi_width)-1 downto 0);
  -- SDP request decoding and internal outputs
  signal pkt_dw_addr_0         : whole_addr_t;
  signal pkt_ndws_0            : pkt_ndw_t; -- count of dws in an SDP pkt
  signal pkt_writing_0         : bool_t;
  signal sdp_take              : bool_t;    -- we are taking from SDP in this cycle

  -- States of the address FSM
  type address_state_t is (sop_next_e, -- next sdp_in.sdp.valid is start of packet
                           in_pkt_e,   -- generating burst requests for packet
                           waiting_e); -- waiting for eop from write channel
  -- The address of the axi transfer in units of the axi width
  subtype axi_xfr_addr_t is unsigned(axi_out.AW.ADDR'left - width_for_max(aw_bytes_c-1)
                                    downto 0);
  signal addr_state_r          : address_state_t;
  signal axf_initial_dw_offset_0 : unsigned(width_for_max(axi_width-1)-1 downto 0);
  signal axi_addr              : axi_xfr_addr_t;
  signal axi_addr_r            : axi_xfr_addr_t;
  signal axi_error_r           : bool_t; -- sticky error for internal use
  signal axi_len               : unsigned(width_for_max(axi_max_burst_c-1)-1 downto 0);
  signal pkt_naxf_0            : pkt_naxf_t;
  signal pkt_naxf_left         : pkt_naxf_t;
  signal pkt_naxf_left_r       : pkt_naxf_t;
  signal axi_requesting_addr   : bool_t;
  signal axi_accepting_addr    : bool_t;
  -- Write data output indication
  signal taking_data           : bool_t; -- write channel is taking data
  signal addressing_done       : bool_t;
  signal writing_done          : bool_t;
  signal accepting_last        : bool_t;
  -- pipeline versions of combinatorial values
  signal pipeline              : bool_t; -- are we capturing to the pipeline this cycle?
  signal sdp_p                 : sdp_t; -- ready is not used in the pipeline version
  signal pkt_writing_p         : bool_t;
  signal pkt_naxf_p            : pkt_naxf_t;
  signal pkt_dw_addr_p         : whole_addr_t;
  signal sdp_reset             : bool_t;

  component sdp2axi_wd_AXI_INTERFACE is
    generic(ocpi_debug      : boolean;
            axi_width       : natural;
            sdp_width       : natural);
    port(   clk             : in  std_logic;
            reset           : in  bool_t;
            addressing_done : in  bool_t;           -- addressing is done in/before this cycle
            pipeline        : in  bool_t;           -- our pipeline state is full
            sdp             : in  sdp_t;
            sdp_in_data     : in  dword_array_t(0 to sdp_width-1);
            sdp_p           : in  sdp_t;
            axi_in          : in  w_s2m_t;          -- write data channel in to here
            axi_out         : out w_m2s_t;          -- write data channel out from here
            taking_data     : out bool_t;           -- indicate data is being used.
            writing_done    : out bool_t;           -- indicate all data taken.
            debug           : out ulonglong_t);
  end component;

  component sdp2axi_rd_AXI_INTERFACE is
    generic(ocpi_debug   : boolean;
            axi_width    : natural;
            sdp_width    : natural);
    port(   clk          : in  std_logic;
            reset        : in  bool_t;
            sdp_take     : in  bool_t;
            sdp_in       : in  s2m_t;
            sdp_out      : out m2s_t;
            sdp_out_data : out dword_array_t(0 to sdp_width-1);
            axi_in       : in  r_s2m_t;   -- read data channel in to here
            axi_out      : out r_m2s_t;   -- read data channel out from here
            debug        : out ulonglong_t);
  end component;
begin
  --============================================================================================
  -- Clock and reset handling given that clock and reset may be (independently) from either side
  -- We are the AXI master
  #if CLOCK_FROM_MASTER
    #define SDPCLK clk
    -- delta cycle alert in some tools even though this is a verilog module
    in2out_axi_clk: util.util.in2out port map(in_port => clk, out_port => axi_out.a.clk);
  #else
    #define SDPCLK axi_in.a.clk
  #endif
  #if RESET_FROM_MASTER
    sdp_reset <= reset;
    axi_out.a.resetn <= not reset;
  #else
    sdp_reset <= not axi_in.a.resetn;
  #endif
  -- delta cycle alert in some tools even though this is a verilog module
  in2out_cp_clk: util.util.in2out port map(in_port => SDPCLK, out_port => sdp_out.clk);
  sdp_out.reset <= sdp_reset;
  --============================================================================================

  pkt_dw_addr_0         <= sdp_in.sdp.header.extaddr & sdp_in.sdp.header.addr;
  pkt_ndws_0            <= count_in_dws(sdp_in.sdp.header);
  pkt_naxf_0            <= resize((pkt_ndws_0 + axf_initial_dw_offset_0 + axi_width - 1) /
                                  axi_width, pkt_naxf_0'length);
  pkt_naxf_left         <= pkt_naxf_p when addr_state_r = sop_next_e else pkt_naxf_left_r;
  pkt_writing_0         <= to_bool(sdp_in.sdp.header.op = write_e);
  axf_initial_dw_offset_0 <= pkt_dw_addr_0(width_for_max(axi_width-1)-1 downto 0);
  axi_len               <= resize(ocpi.util.min(pkt_naxf_left, axi_max_burst_c) - 1,
                                  axi_len'length);
  axi_accepting_addr    <= to_bool(((its(pkt_writing_p) and axi_in.AW.READY = '1') or
                                 (not its(pkt_writing_p) and axi_in.AR.READY = '1')));
  axi_requesting_addr   <= to_bool(sdp_p.valid and addr_state_r /= waiting_e);
  axi_addr              <= resize(pkt_dw_addr_p(pkt_dw_addr_p'left downto
                                                width_for_max(axi_width-1)), axi_addr'length)
                           when addr_state_r = sop_next_e else
                           axi_addr_r;
  axi_error             <= axi_error_r;
  accepting_last        <= to_bool(axi_accepting_addr and
                                   (pkt_naxf_p <= axi_max_burst_c or
                                    pkt_naxf_left <= axi_max_burst_c));
  -- Tell other modules that the addressing is done previously or is done this cycle
  addressing_done       <= to_bool(accepting_last or addr_state_r = waiting_e);
  -- take from SDP when
  sdp_take <= to_bool(sdp_p.valid and
                      -- For reads, take when AXI accepts the addr for the last burst in pkt
                      ((not its(pkt_writing_p) and accepting_last) or
                       -- For writes, take when write data is taken and addr bursts are done
                       (pkt_writing_p and
                        ((taking_data and (not its(sdp_p.eop) or addressing_done)) or
                         (its(writing_done) and accepting_last)))));

  --------------------------------------------------------------------------------
  -- Clocked processing for addressing and breaking addressed packets into bursts
  -- Since the SDP header is stable for the life of the packet, we can issue all the
  -- address channel bursts based on that, independent of read and write data channels
  -- States for this FSM:
  --   sop_next_e : between packets.  Any sdp_in.valid starts packet
  --   in_pkt_e   : working on bursts for a pkt
  --   waiting_e  : waiting for EOP after all bursts done.
  --------------------------------------------------------------------------------
  doclk : process(SDPCLK)
  begin
    if rising_edge(SDPCLK) then
      if its(sdp_reset) then
        addr_state_r <= sop_next_e;  -- we are initially waiting for SOP
        axi_error_r  <= bfalse;
      else
        case addr_state_r is
          when sop_next_e =>
            if sdp_p.valid and not its(axi_error_r) then -- SDP is offering something.  capture address
              if its(axi_accepting_addr) then
                pkt_naxf_left_r    <= pkt_naxf_p - ocpi.util.min(pkt_naxf_p, axi_max_burst_c);
                axi_addr_r         <= axi_addr + axi_max_burst_c;
                -- first burst if being accepted.
                if pkt_naxf_p > axi_max_burst_c then -- more bursts after this
                  addr_state_r <= in_pkt_e;
                elsif not its(sdp_take and sdp_p.eop) then
                  addr_state_r <= waiting_e;
                end if;
              end if;
            end if;
          when in_pkt_e =>
            if its(axi_accepting_addr) then
              pkt_naxf_left_r    <= pkt_naxf_left_r -
                                    ocpi.util.min(pkt_naxf_left_r, axi_max_burst_c);
              axi_addr_r         <= axi_addr + axi_max_burst_c;
              if pkt_naxf_left_r <= axi_max_burst_c then
                if sdp_p.eop and sdp_take then
                  addr_state_r <= sop_next_e;
                else
                  addr_state_r <= waiting_e;
                end if;
              end if;
            end if;
          when waiting_e =>
            if sdp_p.eop and sdp_take then
              addr_state_r <= sop_next_e;
            end if;
        end case;
        -- Capture errors from write responses.  Write data submodule doesn't look
        if axi_in.B.VALID = '1' and axi_in.B.RESP /= Resp_OKAY then
          axi_error_r <= '1';
        end if;
      end if; -- not reset
    end if;     -- rising edge
  end process;

  -----------------------------------------------------------------
  -- Process added for pipelining/fmax
  -----------------------------------------------------------------
  pipeline <= sdp_in.sdp.valid and (not sdp_p.valid or sdp_take);
  dopipe : process(SDPCLK)
  begin
    if rising_edge(SDPCLK) then
      if its(sdp_reset) then
        sdp_p.valid   <= bfalse;
        pkt_writing_p <= bfalse;
        pkt_naxf_p    <= (others => '0');
        pkt_dw_addr_p <= (others => '0');
      elsif its(pipeline) then
        sdp_p         <= sdp_in.sdp;
        pkt_writing_p <= pkt_writing_0;
        pkt_naxf_p    <= pkt_naxf_0;
        pkt_dw_addr_p <= pkt_dw_addr_0;
      elsif its(sdp_take) then
        sdp_p.valid   <= bfalse;
      end if;
    end if;
  end process;

  ----------------------------------------------
  -- Interface outputs to the S_AXI_HP interface
  ----------------------------------------------
#if AXI4
  axi_out.AW.REGION            <= (others => '0');
  axi_out.AW.QOS               <= (others => '0');
  axi_out.AR.QOS               <= (others => '0');
#endif  
  -- Write address channel
  axi_out.AW.ID                <= (others => '0');  -- spec says same id means in-order
  axi_out.AW.ADDR              <= std_logic_vector(axi_addr) &
                                  slv0(width_for_max(axi_out.W.DATA'length/8-1));
  axi_out.AW.LEN               <= std_logic_vector(axi_len);
  axi_out.AW.SIZE              <= std_logic_vector(to_unsigned(width_for_max(axi_out.W.DATA'length/8)-1,
                                                               axi_out.AW.SIZE'length));
  axi_out.AW.BURST             <= "01";         -- we are always doing incrementing bursts
  axi_out.AW.LOCK              <= "00";         -- normal access, no locking or exclusion
  axi_out.AW.CACHE             <= (others => '0');
  axi_out.AW.PROT              <= (others => '0');
  axi_out.AW.VALID             <= axi_requesting_addr and pkt_writing_p;

  -- Write data channel
  -- wired directly to sdp2axi_wd

  -- Write response channel
  axi_out.B.READY              <= '1';              -- we are always ready for responses

  -- Read address channel
  axi_out.AR.ID                <= std_logic_vector(sdp_p.header.node(2 downto 0)) &
                                  std_logic_vector(sdp_p.header.xid);
  axi_out.AR.ADDR              <= std_logic_vector(axi_addr) &
                                  slv0(width_for_max(axi_in.R.DATA'length/8-1));
  axi_out.AR.LEN               <= std_logic_vector(axi_len);
  axi_out.AR.SIZE              <= std_logic_vector(to_unsigned(width_for_max(axi_out.W.DATA'length/8)-1,
                                                               axi_out.AR.SIZE'length));
  axi_out.AR.BURST             <= "01";  -- we are always doing incrementing bursts
  axi_out.AR.LOCK              <= "00";  -- normal access, no locking or exclusion
  axi_out.AR.CACHE             <= (others => '0');
  axi_out.AR.PROT              <= (others => '0');
  axi_out.AR.VALID             <= axi_requesting_addr and not pkt_writing_p;

  -- These are AXI4 sigals, but this interface is not AXI4
  -- axi_out.AR.QOS               <= (others => '0');
  -- axi_out.AW.QOS               <= (others => '0');
  -- These are not AMBA/AXI
  -- axi_out.AR.ISSUECAP1_EN      <= '0';
  -- axi_out.AW.ISSUECAP1_EN      <= '0';

  ----------------------------------------------
  -- debug output - very poor man's ILA
  ----------------------------------------------
  dbg_state <= to_ulonglong(0
    -- std_logic_vector(axi_addr_r(31 downto 0)) & "000" &
    -- slv(pkt_writing_p) & --31
    -- slv(taking_data) & --30
    -- slv(sdp_in.sdp.eop) & --29
    -- slv(addressing_done) & --28
    -- slv(axi_accepting_addr) & --27
    -- slv(accepting_last) & --26
    -- slv(sdp_in.sdp.valid) & --25
    -- "00000000000" & -- 24 - 14
    -- slv(to_unsigned(address_state_t'pos(addr_state_r),2)) & -- 13-12
    -- std_logic_vector(pkt_naxf_left(11 to 0)) -- 11 to 0
    );
    
  ----------------------------------------------
  -- Instantiate the write data channel module
  wd : sdp2axi_wd_AXI_INTERFACE
    generic map (ocpi_debug      => ocpi_debug,
                 axi_width       => axi_width,
                 sdp_width       => sdp_width)
    port map (   clk             => SDPCLK,
                 reset           => sdp_reset,
                 addressing_done => addressing_done,
                 pipeline        => pipeline,
                 sdp             => sdp_in.sdp,  -- not pipelined
                 sdp_in_data     => sdp_in_data, -- not pipelined
                 sdp_p           => sdp_p, -- pipelined
                 axi_in          => axi_in.w,
                 axi_out         => axi_out.w,
                 taking_data     => taking_data,
                 writing_done    => writing_done,
                 debug           => dbg_state1);

  ----------------------------------------------
  -- Instantiate the read data channel module
  rd : sdp2axi_rd_AXI_INTERFACE
    generic map (ocpi_debug   => ocpi_debug,
                 axi_width    => axi_width,
                 sdp_width    => sdp_width)
    port map (   clk          => SDPCLK,
                 reset        => sdp_reset,
                 sdp_take     => pipeline,
                 sdp_in       => sdp_in,
                 sdp_out      => sdp_out,
                 sdp_out_data => sdp_out_data,
                 axi_in       => axi_in.r,
                 axi_out      => axi_out.r,
                 debug        => dbg_state2);

end rtl;
