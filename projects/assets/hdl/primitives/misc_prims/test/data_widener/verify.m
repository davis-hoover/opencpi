#!/usr/bin/octave

global DATA_ADC_BIT_WIDTH = 12;
global DATA_BIT_WIDTH     = 16;

function retval = get_any_error_samp_drop(filename)

  retval = false;
  tmp = textread(filename, '%s');
  for ii=2:length(tmp)
    row = strsplit(tmp{ii}, ",", "collapsedelimiters", false);
    if(strcmp(row(8), "sync"))
      retval = true;
    end
  end
endfunction

function retval = length_is_expected_maximal_lfsr_period_12_bits(xx, filename)
  % https://en.wikipedia.org/wiki/Linear-feedback_shift_register#Some_polynomials_for_maximal_LFSRs
  maximal_lfsr_period_12_bits = 4095;

  if(length(xx) == maximal_lfsr_period_12_bits)
    printf("INFO: All %i values passed through UUT\n", maximal_lfsr_period_12_bits)
    retval = true;
  else
    printf("ERROR: for %s, %i values passed through UUT instead of the expected %i values\n",
           filename, length(xx), maximal_lfsr_period_12_bits)
    retval = false;
  end
endfunction

function retval = successfully_verified_lfsr_passthrough(data_i, data_q, filename)

  retval = true;

  if((!length_is_expected_maximal_lfsr_period_12_bits(data_i, filename)) ||
     (!length_is_expected_maximal_lfsr_period_12_bits(data_q, filename)) ||
     (!length_is_expected_maximal_lfsr_period_12_bits(unique(data_i), filename)) ||
     (!length_is_expected_maximal_lfsr_period_12_bits(unique(data_q), filename)))
    retval = false;
  end

endfunction

function retval = successfully_verified_output_not_all_zero(data_i, data_q)

  retval = true;

  if((min(data_i) == 0) && (max(data_i) == 0))
    disp("ERROR: unexpected - I data is all zero")
    retval = false;
  end
  if((min(data_q) == 0) && (max(data_q) == 0))
    disp("ERROR: unexpected - Q data is all zero")
    retval = false;
  end
  if(retval)
    disp("INFO: as expected, I and Q data not all zero")
  end
endfunction

function retval = successfully_verified_expected_error_samp_drop(filename)
  
  retval = get_any_error_samp_drop(filename);
  if(retval)
    disp("INFO: as expected, sync detected")
  end


endfunction

function retval = is_msb_packed(data)
  global DATA_BIT_WIDTH;
  global DATA_ADC_BIT_WIDTH;

  tmp = DATA_BIT_WIDTH - DATA_ADC_BIT_WIDTH;
  retval = sum(int32(mod(data, 2^tmp)) != 0) == 0;

  if(retval)
    disp("INFO: as expected, data is MSB-packed")
  else
    disp("ERROR: data is unexpectedly not MSB-packed")
  end
endfunction

function retval = successfully_verified_msb_pack(data_i, data_q)

  retval = is_msb_packed(data_i);

  if(retval)
    retval = is_msb_packed(data_q);
  end
endfunction

function retval = is_lsb_packed(data)
  global DATA_ADC_BIT_WIDTH;

  tmp = 2^(DATA_ADC_BIT_WIDTH-1);
  retval = (min(data) >= -tmp) && (max(data) <= tmp-1);
  if(retval)
    disp("INFO: as expected, data is LSB-packed")
  else
    disp("ERROR: data is unexpectedly not LSB-packed")
  end
endfunction

function retval = successfully_verified_lsb_pack(data_i, data_q)

  retval = is_lsb_packed(data_i);

  if(!retval)
    retval = is_lsb_packed(data_q);
  end
endfunction

function retval = verify_subtest_expecting_no_error_samp_drop(filename,
    expecting_msb_pack)

  retval = 0;

  %[data_i, data_q] = textread(filename, '%d,%d');
  empty_value = 32768; % one higher than is possible
  tmp = dlmread(filename, ",", "emptyvalue", empty_value);
  data_i = tmp(2:end,2);
  data_i = data_i(data_i != empty_value);
  data_q = tmp(2:end,3);
  data_q = data_q(data_q != empty_value);

  if((!retval) && (!successfully_verified_lfsr_passthrough(data_i, data_q, filename)))
    retval = 1;
  end

  if((!retval) && (!successfully_verified_output_not_all_zero(data_i, data_q, filename)))
    retval = 1;
  end

  if(expecting_msb_pack)
    if((!retval) && (!successfully_verified_msb_pack(data_i, data_q, filename)))
      retval = 1;
    end
  else
    if((!retval) && (!successfully_verified_lsb_pack(data_i, data_q, filename)))
      retval = 1;
    end
  end
endfunction

function retval = verify_subtest_0()
  
  filename = 'uut_subtest_0_data.txt';
  retval = verify_subtest_expecting_no_error_samp_drop(filename, true);
endfunction

function retval = verify_subtest_1()

  retval = 0;

  filename = 'uut_subtest_1_data.txt';
  if(!successfully_verified_expected_error_samp_drop(filename))
    retval = 1;
  end
endfunction

function retval = verify_subtest_2(expecting_msb_pack)
  
  filename = 'uut_subtest_2_data.txt';
  retval = verify_subtest_expecting_no_error_samp_drop(filename, false);
endfunction

function retval = verify_subtest_3()

  retval = 0;

  filename = 'uut_subtest_3_data.txt';
  if(!successfully_verified_expected_error_samp_drop(filename))
    retval = 1;
  end
endfunction

function verify()

  err = 0;

  if(!err)
    disp("***** --- SUBTEST 0 --- *****")
    err = verify_subtest_0();
  end
  if(!err)
    disp("***** --- SUBTEST 1 --- *****")
    err = verify_subtest_1();
  end
  if(!err)
    disp("***** --- SUBTEST 2 --- *****")
    err = verify_subtest_2();
  end
  if(!err)
    disp("***** --- SUBTEST 3 --- *****")
    err = verify_subtest_3();
  end

  if(err)
    disp("FAILED")
  else
  disp("PASSED")
  end

  quit(err)
endfunction

graphics_toolkit("gnuplot")
verify
