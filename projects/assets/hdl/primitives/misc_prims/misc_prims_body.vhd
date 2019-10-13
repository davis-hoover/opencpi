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

end misc_prims;
