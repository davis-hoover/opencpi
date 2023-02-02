# Testing
The following command builds the C++ unit test(s):
    make -f .Makefile

After building, the following command runs the C++ unit test(s):
    ./build/test # 0 exit status indicates the test succeeded

After running, the following command cleans up all C++ unit test build artifacts:
    make -f .Makefile clean
