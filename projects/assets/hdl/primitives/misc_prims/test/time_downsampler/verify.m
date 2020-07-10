#!/usr/bin/octave

function retval = get_time(filename)

  empty_value = -1;
  tmp = dlmread(filename, ",", "emptyvalue", empty_value);
  time_sec = tmp(2:end,5);
  time_fract_sec = tmp(2:end,4);
  time = bitshift(time_sec, 32) + time_fract_sec;

  retval = time(time_sec != empty_value);

endfunction

function retval = verify_min_num_data_per_time(filename,
    expected_min_num_data_per_time)

  retval = 0;

  time = get_time(filename);
  ss = sort(unique(diff(time)));
  emin = expected_min_num_data_per_time;
  if(min(ss) < emin)
    time
    printf("ERROR: for file %s, min num data per time was %i instead of the expected value of %i\n", filename, min(ss), emin)
    retval = true;
  else
    printf("INFO: as expected, num data_per time exceeded minimum of %i\n", emin)
    retval = false;
  end

endfunction

function verify()

  err = 0;

  if(err == 0)
    err = verify_min_num_data_per_time('uut_subtest_0_data.txt', 4);
  end
  if(err == 0)
    err = verify_min_num_data_per_time('uut_subtest_1_data.txt', 8);
  end
  if(err == 0)
    err = verify_min_num_data_per_time('uut_subtest_2_data.txt', 4);
  end
  if(err == 0)
    err = verify_min_num_data_per_time('uut_subtest_3_data.txt', 8);
  end
  if(err == 0)
    err = verify_min_num_data_per_time('uut_subtest_4_data.txt', 0);
  end
  if(err == 0)
    err = verify_min_num_data_per_time('uut_subtest_5_data.txt', 0);
  end
  if(err == 0)
    err = verify_min_num_data_per_time('uut_subtest_6_data.txt', 0);
  end
  if(err == 0)
    err = verify_min_num_data_per_time('uut_subtest_7_data.txt', 0);
  end

  if(err)
    disp("FAILED")
  else
  disp("PASSED")
  end

  quit(err)

endfunction

verify
