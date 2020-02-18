library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;

package body misc_prims is

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

end misc_prims;
