#!/usr/bin/octave

graphics_toolkit("gnuplot")

function plot_raster(twod_array_of_zero_or_one)
  imagesc(twod_array_of_zero_or_one)
  colormap gray
endfunction

function do_i_or_q_plot(data, do_zoom, title_str)
  tmp = int32(int32(dec2bin(data+2^16)) == 49);
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


function do_subtest_plots(filename, title_str)
  [data_i,data_q] = textread(filename, '%d,%d');
  do_plot(data_i, data_q, title_str, false)
  do_plot(data_i, data_q, title_str, true)
endfunction

do_subtest_plots('uut_subtest_0_data.txt', 'subtest\_0')
do_subtest_plots('uut_subtest_2_data.txt', 'subtest\_2')

pause
