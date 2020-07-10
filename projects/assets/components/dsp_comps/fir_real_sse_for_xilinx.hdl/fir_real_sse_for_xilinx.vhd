-- THIS FILE WAS ORIGINALLY GENERATED ON Mon Jan  6 13:41:08 2020 CST
-- BASED ON THE FILE: pluto_fsk_tx_fir.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: fir_real_sse_for_xilinx

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library util; use util.util.all;

architecture rtl of worker is
  
  constant c_COEFF_PADDING	: integer := to_integer(COEFF_PADDING_p);
  constant c_COEFF_WIDTH	: integer := to_integer(COEFF_WIDTH_p);
  constant c_NUM_TAPS           : integer := to_integer(NUM_TAPS_p); 

  signal s_enable		: std_logic;
  signal s_reset_n_i    	: std_logic; 

  signal s_fir_vld_o    	: std_logic;
  signal s_fir_tready 		: std_logic;
  signal s_fir_d_o 		: std_logic_vector(39 downto 0) := (others => '0'); 

  signal s_peak_rst_i   	: std_logic;
  signal s_peak_o       	: std_logic_vector(15 downto 0);
  signal s_peak_a_i     	: std_logic_vector(15 downto 0);

  signal s_clk_cnt 		: unsigned(15 downto 0);
  signal s_take			: std_logic;
  signal s_doit_out     	: bool_t;

  signal s_raw_byte_enable 	: std_logic_vector(3 downto 0);
  signal s_raw_addr 	   	: std_logic_vector(7 downto 0);
  signal s_raw_data    		: std_logic_vector(15 downto 0);

  ----------------------------------------------------------------------------
  -- Reload state machine signals
  ----------------------------------------------------------------------------
  signal s_init_coef_reload : std_logic;
  
  type reload_state_type is (idle, rom_dly, bram_ld, bram_dly1, bram_dly2, load, rom_adv, config);
  signal reload_state : reload_state_type := idle; 
  
  signal s_rom_addr 		: std_logic_vector(6 downto 0) := "0000000"; 
  signal s_rom_o    		: std_logic_vector(7 downto 0);

  signal s_config_valid 	: std_logic := '0'; 

  signal cr_cntr 		: unsigned(15 downto 0); -- TODO size it based on coeff 
  signal s_bram_en 		: std_logic;
  signal s_bram_addr 		: std_logic_vector(7 downto 0);
  signal cr_bram_out  		: std_logic_vector(15 downto 0);

  signal s_reload_data 		: std_logic_vector(15 downto 0); 
  signal s_reload_valid 	: std_logic; 
  signal s_reload_last 		: std_logic;
  
  signal s_reload_ready 	: std_logic;

  signal s_fir_clk_en 		: std_logic;
  signal s_reload_active 	: std_logic;

  signal s_cur_coeff 		: unsigned(7 downto 0); 

begin

  -- enable core when processing samples or reloading coefficients 
  s_fir_clk_en <= s_doit_out or s_reload_active;
  
  -----------------------------------------------------------------------------
  -- handle coefficient resizing and byte enables
  -----------------------------------------------------------------------------
  be_16_gen : if c_COEFF_WIDTH <= 16 generate
    --Input byte enable decode
    s_raw_data <= props_in.raw.data(c_COEFF_WIDTH-1 downto 0) when (s_raw_byte_enable = "0011") else
                   props_in.raw.data(c_COEFF_WIDTH-1+16 downto 16) when (s_raw_byte_enable = "1100") else (others => '0');
  end generate be_16_gen;

  s_raw_byte_enable <= props_in.raw.byte_enable;
  s_raw_addr        <= '0' & std_logic_vector(props_in.raw.address(7 downto 1)); 
  props_out.raw.done <= '1';
  props_out.raw.error <= '0';

  s_peak_rst_i <= ctl_in.reset or std_logic(props_in.peak_read);
  s_peak_a_i <= std_logic_vector(signed(s_fir_d_o(30 downto 15)));

  s_doit_out <= ctl_in.is_operating and out_in.ready;

  ----------------------------------------------------------------------------
  -- WSI Port assignments
  ----------------------------------------------------------------------------
  in_out.take <= s_take;  
  s_take <= s_enable and s_fir_tready;

  out_out.valid <= s_fir_vld_o;
  out_out.give <= s_fir_vld_o;
  out_out.data <= s_fir_d_o(30 downto 15);

  ----------------------------------------------------------------------------
  -- Enable circuitry when Control State is_operating and up/downstream Workers ready 
  ----------------------------------------------------------------------------
  s_enable <= ctl_in.is_operating and in_in.ready and out_in.ready; 
  
  -- 's_reset_n_i' is the negation of 'ctl_in.reset' for use with Vivado cores
  s_reset_n_i <= not(ctl_in.reset); 


  ----------------------------------------------------------------------------
  -- REORDER ROM 
  ----------------------------------------------------------------------------
  inst_reorder_rom : entity work.fir_real_sse_for_xilinx_reload_order_rom
  port map ( clk  => ctl_in.clk, 
             addr => s_rom_addr, 
             dout => s_rom_o);

  ----------------------------------------------------------------------------
  -- COEF BRAM
  ----------------------------------------------------------------------------
  inst_coef_bram : component util.util.BRAM2
  generic map (
    PIPELINED 	=> 0,
    ADDR_WIDTH 	=> s_rom_o'length,
    DATA_WIDTH  => c_COEFF_WIDTH, 
    MEMSIZE     => c_NUM_TAPS)
    port map  (CLKA	=> ctl_in.clk,
               ENA      => s_bram_en,
               WEA      => '0', 
               ADDRA    => s_bram_addr,
               DIA      => x"0000",
               DOA      => cr_bram_out,
               CLKB     => ctl_in.clk,
               ENB      => '1', 
               WEB      => props_in.raw.is_write,
               ADDRB    => s_raw_addr,
               DIB      => s_raw_data,
               DOB      => open);  
  
  ----------------------------------------------------------------------------
  -- Coefficent Reload FSM 
  ---------------------------------------------------------------------------- 
  s_init_coef_reload <= to_bool(props_in.raw.is_write) and to_bool(to_integer(unsigned(s_raw_addr))=c_NUM_TAPS-1); 
  s_cur_coeff <= unsigned(s_rom_o); 
 
  reload_fsm : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then

      case reload_state is
        when idle => 
          s_config_valid <= '0'; 
          s_reload_data <= (others=>'0');
          s_reload_valid <= '0';
          s_reload_last <= '0'; 
          s_rom_addr <= (others=>'0');        
	  s_bram_en <= '0';
          s_bram_addr <= (others=>'0');
          s_reload_active <= '0';
          if s_init_coef_reload='1' then
            reload_state <= bram_ld; 
            s_reload_active <= '1';
	  end if;

	when rom_dly =>
          reload_state <= bram_ld;
      
        when bram_ld =>  	  
          s_bram_en<='1';
          if s_cur_coeff > c_COEFF_PADDING-1 then
	    s_bram_addr <= std_logic_vector(s_cur_coeff-c_COEFF_PADDING);
          end if;
          reload_state <= bram_dly1; 
 
        when bram_dly1 => 
          s_bram_en<='0';
          reload_state <= bram_dly2;

        when bram_dly2 =>
          reload_state <= load;
        
        when load => 
          if s_cur_coeff < c_COEFF_PADDING then 
            s_reload_data <= (others=>'0');
	  else
            s_reload_data <= cr_bram_out;
          end if; 
          s_reload_valid <= '1';
          if unsigned(s_rom_addr)=(c_NUM_TAPS+c_COEFF_PADDING)-1 then
            s_reload_last<= '1';
          end if;
          reload_state <= rom_adv;
  
        when rom_adv => 
           s_reload_last <= '0'; 
           s_reload_valid <= '0'; 
           if s_reload_last = '1' then
             reload_state <= config; 
           else 
             s_rom_addr <= std_logic_vector(unsigned(s_rom_addr) + 1);
             reload_state <= rom_dly;
           end if;

        when config =>
             s_config_valid <= '1'; 
             s_reload_active <= '0';
             reload_state <= idle; 
        when others => 
          reload_state <= idle;
      end case;
    end if; 
  end process; 

  ----------------------------------------------------------------------------
  -- Xilinx Vivado IP: FIR Filter instance 
  ----------------------------------------------------------------------------

  inst_fir_for_fsk : entity work.fir_compiler_0
    port map (
	aclk			=> ctl_in.clk, 	 
        aclken 			=> s_fir_clk_en,   		
        aresetn			=> s_reset_n_i, 	
        s_axis_data_tvalid 	=> s_take,
        s_axis_data_tdata 	=> in_in.data, 
	s_axis_data_tready	=> s_fir_tready, 
        m_axis_data_tvalid 	=> s_fir_vld_o, 
	m_axis_data_tdata	=> s_fir_d_o,
        s_axis_config_tvalid    => s_config_valid, 
        s_axis_config_tready    => open,
        s_axis_config_tdata     => x"00", 
        s_axis_reload_tvalid    => s_reload_valid,
        s_axis_reload_tlast     => s_reload_last,
        s_axis_reload_tready    => s_reload_ready,
        s_axis_reload_tdata     => s_reload_data                
      );
  
  ----------------------------------------------------------------------------
  -- Peak Detection primitive. Value is cleared when read 
  ----------------------------------------------------------------------------
  pm_gen : if its(PEAK_MONITOR) generate
    inst_pd : util_prims.util_prims.peakDetect
      port map (
        CLK_IN 	 => ctl_in.clk,
        RST_IN   => s_peak_rst_i,
        EN_IN    => s_fir_vld_o, 
        A_IN     => s_peak_a_i,
        B_IN     => (others => '0'),
        PEAK_OUT => s_peak_o );

    props_out.peak <= signed(s_peak_o);
  end generate pm_gen;

  no_pm_gen : if its(not PEAK_MONITOR) generate
    props_out.peak <= (others=>'0');
  end generate no_pm_gen;   
        
end rtl;
