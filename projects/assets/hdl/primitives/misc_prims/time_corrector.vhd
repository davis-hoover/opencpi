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

-- Corrects time_in value by subtracting time_correction. Both the time being
-- correct and the correction amount are unsigned in
-- order to allow UNIX EPOCH format. Note that corrected time may overflow.

library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all;

entity time_corrector is
  -- the DATA PIPE LATENCY CYCLES is currently 0
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    ctrl      : in  time_corrector_ctrl_t;
    status    : out time_corrector_status_t;
    -- INPUT
    idata     : in  data_complex_t;
    imetadata : in  metadata_t;
    ivld      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    odata     : out data_complex_t;
    ometadata : out metadata_t;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end time_corrector;
architecture rtl of time_corrector is
  signal tmp                                 : signed(METADATA_TIME_BIT_WIDTH+1
                                               downto 0) := (others => '0');
  signal tmp_lower_than_min                  : std_logic := '0';
  signal tmp_larger_than_max                 : std_logic := '0';
  signal time_time                           : unsigned(METADATA_TIME_BIT_WIDTH-1
                                               downto 0) := (others => '0');
  signal overflow                            : std_logic := '0';
--  signal overflow_sticky                     : std_logic := '0';
  signal time_correction_latest_reg_dout     : signed(METADATA_TIME_BIT_WIDTH-1
                                               downto 0) := (others => '0');
  signal time_correction_latest_reg_dout_vld : std_logic := '0';

  signal imetadata_slv : std_logic_vector(METADATA_BIT_WIDTH-1 downto 0) :=
                         (others => '0');
  signal metadata      : std_logic_vector(METADATA_BIT_WIDTH-1 downto 0) :=
                         (others => '0');
begin

  time_correction_latest_reg : misc_prims.misc_prims.latest_reg_signed
    generic map(
      BIT_WIDTH => time_correction_latest_reg_dout'length)
    port map(
      clk      => clk,
      rst      => rst,
      din      => ctrl.time_correction,
      din_vld  => ctrl.time_correction_vld,
      dout     => time_correction_latest_reg_dout,
      dout_vld => time_correction_latest_reg_dout_vld);

  tmp <= resize(signed(imetadata.time), tmp'length) -
         resize(signed(ctrl.time_correction), tmp'length);

  tmp_lower_than_min  <= tmp(tmp'left); -- sign bit
  tmp_larger_than_max <= tmp(tmp'left-1); -- largest amplitude bit
  overflow <= tmp_lower_than_min or tmp_larger_than_max;
  status.overflow        <= overflow;
--  status.overflow_sticky <= overflow_sticky;
  time_time <= unsigned(tmp(tmp'left-2 downto 0));

--  overflow_sticky_gen : process(clk)
--  begin
--    if(rising_edge(clk)) then
--      if(rst = '1') then
--        overflow_sticky <= '0';
--      else
--        overflow_sticky <= overflow and overflow_sticky and (not ctrl.clr_overflow_sticky);
--      end if;
--    end if;
--  end process overflow_sticky_gen;

  -- start the DATA PIPE LATENCY CYCLES is currently 0
  odata.i <= idata.i;
  odata.q <= idata.q;

  imetadata_slv <= to_slv(imetadata);

  metadata_gen : process(time_time, imetadata, overflow,
                         time_correction_latest_reg_dout_vld,
                         imetadata_slv)
  begin
    for idx in metadata'range loop
      if((idx <= METADATA_IDX_TIME_L) and (idx >= METADATA_IDX_TIME_R)) then
        metadata(idx) <= time_time(idx-METADATA_IDX_TIME_R);
      elsif(idx = METADATA_IDX_TIME_VLD) then
        metadata(idx) <= imetadata.time_vld and (not overflow) and
                         time_correction_latest_reg_dout_vld;
      else
        metadata(idx) <= imetadata_slv(idx);
      end if;
    end loop;
  end process metadata_gen;

  ometadata <= imetadata when (ctrl.bypass = '1') else from_slv(metadata);

  ovld <= ivld;
  irdy <= ordy;
  -- end the DATA PIPE LATENCY CYCLES is currently 0

end rtl;
