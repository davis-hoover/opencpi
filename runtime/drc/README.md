# File Description
- base/*/DRC*, base/*/Math* (intended to eventually replace base/*/RadioCtrlr*, base/*/UtilLock*, base/*/UtilValidRanges*, which would reduce SLOC of the replaced by roughly 60%)
- ad9361/*/*DRC* (intended to replace ad9361/*/calc*, ad9361/*/RadioCtrlr*, which would reduce SLOC of the replaced by roughly 60%)

# Testing
The following command builds the C++ unit test(s):
    make -f .Makefile build/test

After building, the following command runs the C++ unit test(s):
    ./build/test # 0 exit status indicates the test succeeded

After running, the following command cleans up all C++ unit test build artifacts:
    make -f .Makefile clean
