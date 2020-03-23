#!/usr/bin/octave

function retval = get_time(filename)

  empty_value = -1;
  tmp = dlmread(filename, ",", "emptyvalue", empty_value);
  time_sec = tmp(2:end,5);
  time_fract_sec = tmp(2:end,4);
  time = bitshift(time_sec, 32) + time_fract_sec;

  retval = time(time_sec != empty_value);

endfunction

function retval = verify_valid_time(filename, expecting_any_valid_time)

  retval = 0;

  time = get_time(filename);

  if(expecting_any_valid_time)
    if(length(time) == 0)
      retval = 1;
      printf("ERROR: UUT output 0 timestamps when one or more were expected\n")
    else
      printf("INFO: as expected, UUT output one or more valid timestamps\n")
    end
  else
    if(length(time) > 0)
      retval = 1;
      printf("ERROR: for file %s, UUT output one or more timestamps when 0 were expected\n", filename)
    else
      printf("INFO: as expected, UUT output one or more timestamps\n")
    end
  end

endfunction

function retval = verify_time_value(filename, value)

  retval = 0;

  time = get_time(filename);

  if(time(1) != value)
    retval = 1;
    printf("ERROR: for file %s, UUT output time was %i instead of expected value of %i\n", filename, time(1), value)
  else
    printf("INFO: as expected, UUT output time has value of %i\n", value)
  end

endfunction

function retval = verify_no_overflow(filename)
  retval = 0; % no error
  COLUMN_IDX_STATUS_OVERFLOW = 4;
  empty_value = -1;
  tmp = dlmread(filename, ",", "emptyvalue", empty_value);
  overflow = tmp(2:end,COLUMN_IDX_STATUS_OVERFLOW);
  if(max(overflow) == 1)
    retval = 1; % error
    printf("ERROR: for file %s, overflow was unexpectedly detected\n", filename)
  else
    printf("INFO: as expected, UUT did not detect overflow\n")
  end
endfunction

function verify()

  err = 0;

  if(err == 0)
    err = verify_valid_time('uut_subtest_0_data.txt', true);
  end
  if(err == 0)
    err = verify_valid_time('uut_subtest_1_data.txt', false);
  end
  if(err == 0)
    err = verify_valid_time('uut_subtest_2_data.txt', true);
  end
  if(err == 0)
    err = verify_valid_time('uut_subtest_3_data.txt', true);
  end
  if(err == 0)
    err = verify_valid_time('uut_subtest_4_data.txt', true);
  end
  if(err == 0)
    err = verify_valid_time('uut_subtest_5_data.txt', true);
  end
  if(err == 0)
    err = verify_time_value('uut_subtest_0_data.txt', 0);
  end
  if(err == 0)
    err = verify_time_value('uut_subtest_2_data.txt', 1);
  end
  if(err == 0)
    err = verify_time_value('uut_subtest_3_data.txt', 102);
  end
  if(err == 0)
    err = verify_time_value('uut_subtest_4_data.txt', 101);
  end
  if(err == 0)
    err = verify_time_value('uut_subtest_5_data.txt', 103);
  end
  if(err == 0)
    err = verify_no_overflow('uut_subtest_6_ctrl.txt');
  end

  if(err)
    disp("FAILED")
  else
  disp("PASSED")
  end

  quit(err)

endfunction

verify
