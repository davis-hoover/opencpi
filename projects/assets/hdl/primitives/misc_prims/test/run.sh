echo "******************** RESULTS ******************** "
for logfile in $(find . -name results\*)
do
  echo $logfile; grep -e PASSED -e FAILED $logfile
done
XX=0
[ -f .fail ] && XX=1
[ -f .fail ] && rm -rf .fail
exit $XX
