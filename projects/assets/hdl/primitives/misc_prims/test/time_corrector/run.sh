make cleantxt
[ "$1" == "-gui" ] && xsim sim $1 -t no_exit.tcl
[ "$1" != "-gui" ] && xsim sim $1 -t tcl.tcl
./verify.m
