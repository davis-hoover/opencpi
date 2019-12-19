#!/usr/bin/octave

function retval = get_any_error_samp_not_avail(filename)

  retval = false;
  tmp = textread(filename, '%s');
  for ii=0:length(tmp)
    if(strmcmp(tmp{ii}, "ERROR_SAMP_NOT_AVAIL"))
      retval = true;
    end
  end
endfunction

function retval = length_is_expected_maximal_lfsr_period_16_bits(xx)
  % https://en.wikipedia.org/wiki/Linear-feedback_shift_register#Some_polynomials_for_maximal_LFSRs
  maximal_lfsr_period_16_bits = 65535;

  if(length(xx) == maximal_lfsr_period_16_bits)
    printf("INFO: All %i values passed through UUT\n", maximal_lfsr_period_16_bits)
    retval = true;
  else
    printf("ERROR: %i values passed through UUT instead of the expected %i values\n",
           length(xx), maximal_lfsr_period_16_bits)
    retval = false;
  end
endfunction

function retval = verify_all_lfsr_values_passed_through_uut(data_i, data_q)

  retval = true;

  if((!length_is_expected_maximal_lfsr_period_16_bits(data_i)) ||
     (!length_is_expected_maximal_lfsr_period_16_bits(data_q)) ||
     (!length_is_expected_maximal_lfsr_period_16_bits(unique(data_i))) ||
     (!length_is_expected_maximal_lfsr_period_16_bits(unique(data_q))))
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

function retval = verify_error_samp_not_avail(data_cell)
  
  retval = 1;

  for ii=1:length(data_cell)
    if(strcmp(data_cell{ii}, "ERROR_SAMP_NOT_AVAIL"))
      retval = 0;
      disp("INFO: as expected, ERROR_SAMP_NOT_AVAIL detected")
      break;
    end
  end
endfunction

function retval = verify_subtest_0()
  
  retval = 0;

  %[data_i, data_q] = textread('uut_subtest_0_data.txt', '%d,%d');
  tmp = csvread('uut_subtest_0_data.txt');
  data_i = tmp(:,1);
  data_q = tmp(:,2);

  if((!verify_all_lfsr_values_passed_through_uut(data_i, data_q)) && (!retval))
    retval = 1;
  end

  if((!verify_output_is_not_all_zero(data_i, data_q)) && (!retval))
    retval = 1;
  end
endfunction

function retval = verify_subtest_1()
  retval = verify_error_samp_not_avail(textread('uut_subtest_1_data.txt', '%s'));
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

  if(err)
    disp("FAILED")
  else
  disp("PASSED")
  end

  quit(err)
endfunction

graphics_toolkit("gnuplot")
verify
