LOG=.tmp.log
xvhdl $@ | tee $LOG
grep -q ERROR $LOG
XX=$?
rm -rf $LOG
[ "$XX" == "0" ] && exit 1
exit 0
