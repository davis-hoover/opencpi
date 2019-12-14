#!/usr/bin/octave

function retval = verify_min_num_data_per_time(filename,
    expected_min_num_data_per_time)

  retval = 0;

  empty_value = -1;
  tmp = dlmread(filename, ",", "emptyvalue", empty_value);
  time = tmp(:,5);
  time = time(time != empty_value);
  ss = sort(unique(diff(time)));
  emin = expected_min_num_data_per_time;
  if(min(ss) < emin)
    printf("ERROR: expected num data per time to be >= %i\n", emin)
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
