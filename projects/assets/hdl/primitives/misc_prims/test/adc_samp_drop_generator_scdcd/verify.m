#!/usr/bin/octave

function retval = get_any_error_samp_drop(filename)

  retval = false;
  tmp = textread(filename, '%s');
  for ii=0:length(tmp)
    if(strmcmp(tmp{ii}, "ERROR_SAMP_DROP"))
      retval = true;
    end
  end
endfunction

function retval = length_is_expected_maximal_lfsr_period_12_bits(xx)
  % https://en.wikipedia.org/wiki/Linear-feedback_shift_register#Some_polynomials_for_maximal_LFSRs
  maximal_lfsr_period_12_bits = 4095;

  if(length(xx) == maximal_lfsr_period_12_bits)
    printf("INFO: as expected, %i values passed through UUT\n", maximal_lfsr_period_12_bits)
    retval = true;
  else
    printf("ERROR: %i values passed through UUT instead of the expected %i values\n",
           length(xx), maximal_lfsr_period_12_bits)
    retval = false;
  end
endfunction

function retval = verify_all_lfsr_values_passed_through_uut(data_i, data_q)

  retval = true;

  if((!length_is_expected_maximal_lfsr_period_12_bits(data_i)) ||
     (!length_is_expected_maximal_lfsr_period_12_bits(data_q)) ||
     (!length_is_expected_maximal_lfsr_period_12_bits(unique(data_i))) ||
     (!length_is_expected_maximal_lfsr_period_12_bits(unique(data_q))))
    retval = false;
  end

endfunction

function retval = verify_output_is_not_all_zero(data_i, data_q)

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

function retval = verify_error_samp_drop(data_cell)
  
  retval = 1;

  for ii=1:length(data_cell)
    if(strcmp(data_cell{ii}, "ERROR_SAMP_DROP"))
      retval = 0;
      disp("INFO: as expected, ERROR_SAMP_DROP detected")
      break;
    end
  end
endfunction

function retval = verify_allow_lfsr_backpressure_false(filename)
  
  retval = 0;

  %[data_i, data_q] = textread(filename, '%d,%d');
  tmp = csvread(filename);
  data_i = tmp(:,1);
  data_q = tmp(:,2);

  if((!verify_all_lfsr_values_passed_through_uut(data_i, data_q)) && (!retval))
    retval = 1;
  end

  if((!verify_output_is_not_all_zero(data_i, data_q)) && (!retval))
    retval = 1;
  end
endfunction

function retval = verify_allow_lfsr_backpressure_true(filename)
  retval = verify_error_samp_drop(textread(filename, '%s'));
endfunction

function retval = verify_subtest_0()
  retval = verify_allow_lfsr_backpressure_false('uut_subtest_0_data.txt')
endfunction

function retval = verify_subtest_1()
  retval = verify_allow_lfsr_backpressure_false('uut_subtest_1_data.txt')
endfunction

function retval = verify_subtest_2()
  retval = verify_allow_lfsr_backpressure_true('uut_subtest_2_data.txt')
endfunction

function retval = verify_subtest_3()
  retval = verify_allow_lfsr_backpressure_true('uut_subtest_3_data.txt')
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
