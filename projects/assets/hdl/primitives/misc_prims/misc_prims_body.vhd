library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;

package body misc_prims is

function to_slv(data : in data_complex_t) return std_logic_vector is
begin
  return data.i & data.q;
end to_slv;

function from_slv(slv : in std_logic_vector) return data_complex_t is
  variable ret : data_complex_t;
begin
  ret.i := slv((2*DATA_BIT_WIDTH)-1 downto DATA_BIT_WIDTH);
  ret.q := slv(DATA_BIT_WIDTH-1 downto 0);
  return ret;
end from_slv;

function to_slv(metadata : in metadata_t) return std_logic_vector is
begin
  return metadata.flush &
         metadata.error_samp_drop &
         metadata.data_vld &
         std_logic_vector(metadata.time) &
         metadata.time_vld &
         std_logic_vector(metadata.samp_period) &
         metadata.samp_period_vld;
end to_slv;

function from_slv(slv : in std_logic_vector) return metadata_t is
  variable ret : metadata_t;
begin
  ret.flush             :=          slv(METADATA_IDX_FLUSH);
  ret.error_samp_drop   :=          slv(METADATA_IDX_ERROR_SAMP_DROP);
  ret.data_vld          :=          slv(METADATA_IDX_DATA_VLD);
  ret.time              := unsigned(slv(METADATA_IDX_TIME_L downto
                                        METADATA_IDX_TIME_R));
  ret.time_vld          :=          slv(METADATA_IDX_TIME_VLD);
  ret.samp_period       := unsigned(slv(METADATA_IDX_SAMP_PERIOD_L downto
                                        METADATA_IDX_SAMP_PERIOD_R));
  ret.samp_period_vld   :=          slv(METADATA_IDX_SAMP_PERIOD_VLD);
  return ret;
end from_slv;

function to_slv(info : in info_t) return std_logic_vector is
begin
  return to_slv(info.data) & to_slv(info.metadata);
end to_slv;

function from_slv(slv : in std_logic_vector) return info_t is
  variable ret : info_t;
  variable slv_data     : std_logic_vector(2*DATA_BIT_WIDTH-1 downto 0) := (others => '0');
  variable slv_metadata : std_logic_vector(METADATA_BIT_WIDTH-1 downto 0) := (others => '0');
begin
  slv_data := slv(METADATA_BIT_WIDTH+2*DATA_BIT_WIDTH-1 downto
                  METADATA_BIT_WIDTH);
  slv_metadata := slv(METADATA_BIT_WIDTH-1 downto 0);
  ret.data     := from_slv(slv_data);
  ret.metadata := from_slv(slv_metadata);
  return ret;
end from_slv;

function calc_cdc_bit_dst_fifo_depth (
    constant src_dst_ratio : in real;
    constant num_input_samples : in natural)
    return natural is
    variable result : natural;
  begin

    if (src_dst_ratio >= 1.0) then
        -- For fast to slow, if the signal width is 2x the period of the destination
        -- clock and the input pulses are be separated by 2x src_clk cycles, for one pulse
        -- in the source domain there should expect 2 samples in the destination
        -- domain for each pulse.
        result := 2*(num_input_samples)+2; -- plus offset of 2 for initial data enqeued
    else
        -- For slow to fast should expect about dst_clk/src_clk x number
        -- of samples in the destination domain
        result := natural((ceil((1.0/src_dst_ratio)*real(num_input_samples))))+2; -- plus offset of 2 for initial data enqeued
    end if;
    return result;
end calc_cdc_bit_dst_fifo_depth;


function calc_cdc_fifo_depth (
    constant src_dst_ratio : in real)
    return natural is
    variable result : natural;

  begin
    -- When full, it takes 1 src clk + 3 dst clks + 3 dst clks for the source to know that
    -- that the cdc fifo is no longer empty. Adding up how long that takes in the source domain
    -- the cdc fifo should be at least that deep
    if (src_dst_ratio > 1.0) then
      result := natural(floor(src_dst_ratio) + floor((src_dst_ratio)*2.0)+ 3.0);
    else
      result := natural(1.0 + floor((src_dst_ratio)*3.0) + 3.0);
    end if;
    return result;
end calc_cdc_fifo_depth;

function calc_cdc_pulse_dst_fifo_depth (
    -- The dest pulse latency is 3 src clk and N dst clk delays so adding up how
    -- long that takes on the destination domain, that's
    -- how deep the fifo storing the data should be.
    constant src_dst_ratio : in real;
    constant num_input_samples : in natural)
    return natural is
    variable result : natural;
  begin
    if (src_dst_ratio >= 1.0) then
      result := natural(floor(real(num_input_samples) * (((1.0/src_dst_ratio)*3.0)+2.0))) + 1; -- plus offset of 1 for initial data enqeued
    else
      result := num_input_samples * natural(ceil(3.0*(1.0/src_dst_ratio))+2.0);
    end if;
    return result;
end calc_cdc_pulse_dst_fifo_depth;

function calc_cdc_count_up_dst_fifo_depth (
    -- The dest pulse latency is 3 src clk and N dst clk delays so adding up how
    -- long that takes on the destination domain, that's
    -- how deep the fifo storing the data should be.
    constant src_dst_ratio : in real;
    constant num_input_samples : in natural)
    return natural is
    variable result : natural;
  begin
    if (src_dst_ratio >= 1.0) then
      result := natural(floor(real(num_input_samples) * (((1.0/src_dst_ratio)*3.0)+2.0))) + 1; -- plus offset of 1 for initial data enqeued
    else
      result := num_input_samples * natural(ceil(3.0*(1.0/src_dst_ratio))+2.0) + 1;-- plus offset of 1 extra sample
    end if;
    return result;
end calc_cdc_count_up_dst_fifo_depth;

function src_dst_ratio (
    constant sim_src_clk_hz  : in real;
    constant sim_dst_clk_hz  : in real;
    constant simulation  : in std_logic;
    constant hw_src_dst_clk_ratio : in real)
    return real is
    variable result : real;
  begin
    if (simulation = '1') then
      result := sim_src_clk_hz/sim_dst_clk_hz;
    else
      result := hw_src_dst_clk_ratio;
    end if;
  return result;
end src_dst_ratio;

end misc_prims;
