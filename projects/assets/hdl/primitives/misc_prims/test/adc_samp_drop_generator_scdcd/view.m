#!/usr/bin/octave

graphics_toolkit("gnuplot")

function plot_raster(twod_array_of_zero_or_one)
  imagesc(twod_array_of_zero_or_one)
  colormap gray
endfunction

function do_i_or_q_plot(data, do_zoom, title_str)
  tmp = int32(int32(dec2bin(data+2048)) == 49);
  tmp(:,1) = -(tmp(:,1)-1); % undoing +2048
  twod_array_of_zero_or_one = tmp;
  plot_raster(twod_array_of_zero_or_one)
  if(do_zoom)
    ylim([0 512])
    title_str = [title_str ' (zoomed in)'];
  end

  %xlabel('Output sample value bit number')
  %ylabel('Output sample time index')
  axis off % removes misleading axis box

  title(title_str)
endfunction

function do_plot(data_i, data_q, title_str, do_zoom)
  figure
  subplot(1,5,2)
  do_i_or_q_plot(data_i, do_zoom, [title_str ' I'])
  subplot(1,5,4)
  do_i_or_q_plot(data_q, do_zoom, [title_str ' Q'])
endfunction

[subtest_0_data_i,subtest_0_data_q] = textread('uut_subtest_0_data.txt', '%d,%d');

do_plot(subtest_0_data_i, subtest_0_data_q, 'subtest\_0', false)
do_plot(subtest_0_data_i, subtest_0_data_q, 'subtest\_0', true)

%[subtest_1_data_i,subtest_1_data_q] = textread('uut_subtest_1_data.txt', '%d,%d', 'headerlines', 0);
%figure
%subplot(2,1,2)
%plot(subtest_1_data_q)
%ylabel('I')
%subplot(2,1,1)
%plot(subtest_1_data_i)
%ylabel('Q')
%title('subtest\_1')

system('xsim sim.wdb -gui')

pause
