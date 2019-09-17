library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;

package body misc_prims is

function to_slv(metadata : in metadata_t) return std_logic_vector is
begin
  return metadata.error_samp_drop &
         metadata.data_vld &
         std_logic_vector(metadata.time) &
         metadata.time_vld;
end to_slv;

function from_slv(slv : in std_logic_vector) return metadata_t is
  variable ret : metadata_t;
begin
  ret.error_samp_drop :=          slv(METADATA_IDX_ERROR_SAMP_DROP);
  ret.data_vld        :=          slv(METADATA_IDX_DATA_VLD);
  ret.time            := unsigned(slv(METADATA_IDX_TIME_L downto
                                      METADATA_IDX_TIME_R));
  ret.time_vld        :=          slv(METADATA_IDX_TIME_VLD);
  return ret;
end from_slv;

end misc_prims;
