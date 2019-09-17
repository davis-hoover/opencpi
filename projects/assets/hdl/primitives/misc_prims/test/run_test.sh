test=$1

pushd $test && ./run.sh
XX=$?
popd
[ "$XX" != "0" ] && exit $XX

exit $XX
