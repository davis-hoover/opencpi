#!/usr/bin/octave

global DATA_DAC_BIT_WIDTH = 12;
global DATA_BIT_WIDTH     = 16;
global max_count_value    = 32767;

function retval = get_any_error_samp_not_avail(filename)

  retval = false;
  tmp = textread(filename, '%s');
  for ii=0:length(tmp)
    if(strmcmp(tmp{ii}, "ERROR_SAMP_NOT_AVAIL"))
      retval = true;
    end
  end
endfunction

function retval = length_is_expected_max_count_value(xx)
  global max_count_value;

  if(length(xx) == max_count_value)
    printf("INFO: All %i values passed through UUT\n", max_count_value)
    retval = true;
  else
    printf("ERROR: %i values passed through UUT instead of the expected %i values\n",
           length(xx), max_count_value)
    retval = false;
  end
endfunction

function retval = successfully_verified_lfsr_passthrough(data_i, data_q)

  retval = true;

  if((!length_is_expected_max_count_value(data_i)) ||
     (!length_is_expected_max_count_value(data_q)))
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

function retval = successfully_verified_expected_error_samp_not_avail(data_cell)
  
  retval = false;

  for ii=1:length(data_cell)
    if(strcmp(data_cell{ii}, "ERROR_SAMP_NOT_AVAIL"))
      retval = true;
      disp("INFO: as expected, ERROR_SAMP_NOT_AVAIL detected")
      break;
    end
  end
endfunction

function retval = is_msb_packed(data)
  global DATA_BIT_WIDTH;
  global DATA_DAC_BIT_WIDTH;
  global max_count_value;
 
  tmp = DATA_BIT_WIDTH - DATA_DAC_BIT_WIDTH;
  expected_output  = bitshift(0:1:max_count_value-1,-tmp);
  output_result = data == expected_output'; %'
    
    retval = sum(output_result) == sum(ones(max_count_value,1));

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
  global DATA_DAC_BIT_WIDTH;
  global max_count_value;

  tmp = 2^DATA_DAC_BIT_WIDTH-1;
  expected_output  = bitand(0:1:max_count_value-1,tmp);
  output_result = data == expected_output'; %'
    retval = sum(output_result) == sum(ones(max_count_value,1));
  
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

function retval = verify_subtest_expecting_no_error_samp_not_avail(filename,
    expecting_msb_pack)

  retval = 0;

  %[data_i, data_q] = textread(filename, '%d,%d');
  tmp = csvread(filename);
  data_i = tmp(:,1);
  data_q = tmp(:,2);

  if((!successfully_verified_lfsr_passthrough(data_i, data_q)) && (!retval))
    retval = 1;
  end

  if((!successfully_verified_output_not_all_zero(data_i, data_q)) && (!retval))
    retval = 1;
  end

  if(expecting_msb_pack)
    if((!successfully_verified_msb_pack(data_i, data_q)) && (!retval))
      retval = 1;
    end
  else
    if((!successfully_verified_lsb_pack(data_i, data_q)) && (!retval))
      retval = 1;
    end
  end
endfunction

function retval = verify_subtest_0()
  
  filename = 'uut_subtest_0_data.txt';
  retval = verify_subtest_expecting_no_error_samp_not_avail(filename, true);
endfunction

function retval = verify_subtest_1()

  retval = 0;

  fn = 'uut_subtest_1_data.txt';
  if(!successfully_verified_expected_error_samp_not_avail(textread(fn, '%s')))
    retval = 1;
  end
endfunction

function retval = verify_subtest_2(expecting_msb_pack)
  
  filename = 'uut_subtest_2_data.txt';
  retval = verify_subtest_expecting_no_error_samp_not_avail(filename, false);
endfunction

function retval = verify_subtest_3()

  retval = 0;

  fn = 'uut_subtest_3_data.txt';
  if(!successfully_verified_expected_error_samp_not_avail(textread(fn, '%s')))
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
