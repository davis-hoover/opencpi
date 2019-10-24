echo "******************** RESULTS ******************** "
for logfile in $(find . -name results\*)
do
  echo $logfile; grep -e PASSED -e FAILED $logfile
done
