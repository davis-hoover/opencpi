test=$1

pushd $test && ./run.sh
XX=$?
popd
[ $XX -ne 0 ] && touch .fail && exit $XX

exit $XX
