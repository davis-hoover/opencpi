#!/usr/bin/octave

function do_plot(filename)

  emptyvalue = -1;
  tmp = dlmread(filename, ",", "emptyvalue", emptyvalue);
  clk_cnt = tmp(:,1);
  time = tmp(:,end);
  clk_cnt = clk_cnt(time != emptyvalue);
  time = time(time != emptyvalue);

  plot(clk_cnt, time, 'x')
  xlabel('clk_cnt')
  ylabel('TIME')
  title(filename)
endfunction

graphics_toolkit("gnuplot")

figure
subplot(2,3,1)
do_plot('uut_subtest_0_data.txt');
subplot(2,3,2)
do_plot('uut_subtest_1_data.txt');
subplot(2,3,3)
do_plot('uut_subtest_2_data.txt');
subplot(2,3,4)
do_plot('uut_subtest_3_data.txt');
subplot(2,3,5)
do_plot('uut_subtest_4_data.txt');
subplot(2,3,6)
do_plot('uut_subtest_5_data.txt');

pause
