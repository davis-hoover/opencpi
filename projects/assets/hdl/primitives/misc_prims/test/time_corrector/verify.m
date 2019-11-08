#!/usr/bin/octave

function retval = get_time(filename)

  empty_value = -1;
  tmp = dlmread(filename, ",", "emptyvalue", empty_value);
  clk_cnt = tmp(:,1);
  time = tmp(:,end);
  clk_cnt = clk_cnt(time != empty_value);

  retval = time(time != empty_value);

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
      printf("ERROR: UUT output one or more timestamps when 0 were expected\n")
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
    printf("ERROR: UUT output time was %i instead of expected value of %i\n", time(1), value)
  else
    printf("INFO: as expected, UUT output time has value of %i\n", value)
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

  if(err)
    disp("FAILED")
  else
  disp("PASSED")
  end

  quit(err)

endfunction

verify
