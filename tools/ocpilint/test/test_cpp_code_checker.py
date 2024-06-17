#!/usr/bin/env python3

# Test code in cpp_code_checker.py
#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import os
import pathlib
import unittest

from ocpilint.ocpi_linter.cpp_code_checker import CppCodeChecker
from ocpilint.ocpi_linter.linter_settings import LinterSettings


class TestCppCodeChecker(unittest.TestCase):
    def setUp(self):
        self.test_file_path = pathlib.Path("test_file.cc")
        self.test_file_path.touch()
        self.linter_settings = LinterSettings()

    def tearDown(self):
        if self.test_file_path.is_file():
            os.remove(self.test_file_path)

    expected_copyright = """// This file is protected by Copyright. Please refer to the COPYRIGHT file
// distributed with this source distribution.
//
// This file is part of OpenCPI <http://www.opencpi.org>
//
// OpenCPI is free software: you can redistribute it and/or modify it under the
// terms of the GNU Lesser General Public License as published by the Free
// Software Foundation, either version 3 of the License, or (at your option) any
// later version.
//
// OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
// WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
// A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
// more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

    def test_cpp_empty(self):
        code_sample = ""
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(self.test_file_path,
                                      self.linter_settings)
        code_checker._read_in_code()

        results = code_checker.lint()

        # Check an empty file fails lint without raising an exception
        self.assertGreater(len(results), 0)

    # Functionality of linter test 000, 001 and 002 are not tested here since
    # they use external code checkers and formatters and it is assumed those
    # are tested separately - only reporting of errors is tested.

    def test_cpp_000_pass(self):
        code_sample = (
            "// Line with no indent\n" +
            "// Same indent on this line\n" +
            "")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_000()

        self.assertEqual([], issues)

    def test_cpp_000_fail(self):
        code_sample = (
            "// Line with no indent\n" +
            "    // Differently indented line\n" +
            "")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_000()
        print(code_checker._code)

        self.assertEqual(issues, [{
            "line": 2,
            "message": "File was reformatted by clang-format."}])

    def test_cpp_001_pass(self):
        code_sample = (
            "// Test code\n" +
            self.expected_copyright +
            "\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_001()

        self.assertEqual([], issues)

    def test_cpp_001_fail(self):
        code_sample = (
            "// Test code\n" +
            "// with no statement of rights to copy\n" +
            "\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_001()

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["line"], 0)
        # The error message will be similar
        # to "No copyright message found...."

    def test_cpp_002_pass(self):
        code_sample = (
            "void not_leaky() {\n" +
            "  //malloc(12)\n"
            "}\n"
            "")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_002()

        self.assertEqual([], issues)

    def test_cpp_002_fail(self):
        code_sample = (
            "void leaky()\n" +
            "{\n" +
            "  malloc(12)\n"
            "}\n"
            "")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_002()

        self.assertGreaterEqual(len(issues), 1)
        self.assertEqual(3, issues[0]["line"])

    def test_cpp_003_pass(self):
        code_sample = (
            "// Brief description\n" +
            "//\n" +
            self.expected_copyright +
            "\n" +
            "This would be the start of the main file.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_003()

        self.assertEqual([], issues)

    def test_cpp_003_fail_no_header(self):
        code_sample = "A single line of text"
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_003()

        self.assertEqual(1, len(issues))

    def test_cpp_003_fail_license_notice_typo(self):
        code_sample = (
            "// Brief description\n" +
            "//\n" +
            self.expected_copyright.replace("by the Free",
                                            "by the Free typo") +
            "\n" +
            "This would be the start of the main file.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_003()

        self.assertEqual(1, len(issues))
        self.assertEqual(9, issues[0]["line"])

    def test_cpp_003_fail_no_blank_line_after_header(self):
        code_sample = (
            "// Brief description\n" +
            "//\n" +
            self.expected_copyright +
            "This would be the start of the main file.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_003()

        self.assertEqual(1, len(issues))
        self.assertEqual(20, issues[0]["line"])

    def test_cpp_004_pass(self):
        code_sample = (
            "// A single line comment which should be allowed.\n" +
            "Using the symbols that are in block comments like * and /.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_004()

        self.assertEqual([], issues)

    def test_cpp_004_fail(self):
        code_sample = (
            "// A single line comment which should be allowed.\n" +
            "Using the symbols that are in block comments like * and /.\n" +
            "/* Some block comment which should be detected.*/\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_004()

        self.assertEqual(1, len(issues))
        self.assertEqual(3, issues[0]["line"])

    def test_cpp_005_pass(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "Another line.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_005()

        self.assertEqual([], issues)

    def test_cpp_005_fail(self):
        code_sample = (
            "// A single line comment\n" +
            "\n" +
            "#define SOME_VARIABLE 5\n" +
            "\n" +
            "// Some comment.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_005()

        self.assertEqual(1, len(issues))
        self.assertEqual(3, issues[0]["line"])

    def test_cpp_006_pass(self):
        code_sample = ("#include <iostream>\n" +
                       "#include \"some_user_file\"\n" +
                       "\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_006()

        self.assertEqual([], issues)

    def test_cpp_006_fail(self):
        code_sample = (
            "#include <stdio.h>\n" +
            "\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_006()

        self.assertEqual(1, len(issues))
        self.assertEqual(1, issues[0]["line"])

    def test_cpp_007_pass(self):
        code_sample = ("#include <cmath>\n" +
                       "#include \"some_user_file\"\n" +
                       "\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_007()

        self.assertEqual([], issues)

    def test_cpp_007_fail(self):
        code_sample = (
            "#include <iostream>\n" +
            "\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_007()

        self.assertEqual(1, len(issues))
        self.assertEqual(1, issues[0]["line"])

    def test_cpp_008_pass(self):
        code_sample = (
            "// Brief description\n" +
            "//\n" +
            self.expected_copyright +
            "\n" +
            "#include <cmath>\n" +
            "\n" +
            "int main() {\n" +
            "  if (cos(0.3) < 1) {\n" +
            "    return 1;\n" +
            "  } else {\n" +
            "    return 0;\n" +
            "  }\n" +
            "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_008()

        self.assertEqual([], issues)

    def test_cpp_008_fail_no_header(self):
        code_sample = (
            "#include <cmath>\n" +
            "\n" +
            "int main() {\n" +
            "  if (cos(0.3) < 1) {\n" +
            "    return 1;\n" +
            "  } else {\n" +
            "    return 0;\n" +
            "  }\n" +
            "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_008()

        self.assertEqual(1, len(issues))
        self.assertEqual(1, issues[0]["line"])

    def test_cpp_008_fail_no_blank_lines_after_header(self):
        code_sample = (
            "// Brief description\n" +
            "//\n" +
            self.expected_copyright +
            "#include <cmath>\n" +
            "\n" +
            "int main() {\n" +
            "  if (cos(0.3) < 1) {\n" +
            "    return 1;\n" +
            "  } else {\n" +
            "    return 0;\n" +
            "  }\n" +
            "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_008()

        self.assertEqual(1, len(issues))
        self.assertEqual(20, issues[0]["line"])

    def test_cpp_008_fail_two_blank_lines_after_header(self):
        code_sample = (
            "// Brief description\n" +
            "//\n" +
            self.expected_copyright +
            "\n\n"
            "#include <cmath>\n" +
            "\n" +
            "int main() {\n" +
            "  if (cos(0.3) < 1) {\n" +
            "    return 1;\n" +
            "  } else {\n" +
            "    return 0;\n" +
            "  }\n" +
            "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_008()

        self.assertEqual(1, len(issues))
        self.assertEqual(21, issues[0]["line"])

    def test_cpp_008_fail_include_late_in_code(self):
        code_sample = (
            "// Brief description\n" +
            "//\n" +
            self.expected_copyright +
            "\n" +
            "int main() {\n" +
            "  #include <cmath>\n" +
            "  if (cos(0.3) < 1) {\n" +
            "    return 1;\n" +
            "  } else {\n" +
            "    return 0;\n" +
            "  }\n" +
            "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_008()

        self.assertEqual(1, len(issues))
        self.assertEqual(22, issues[0]["line"])

    def test_cpp_009_pass(self):
        code_sample = ("int main(void) {\n" +
                       "  return RCC_FATAL;\n" +
                       "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_009()

        self.assertEqual([], issues)

    def test_cpp_009_fail(self):
        code_sample = ("int main(void) {\n" +
                       "  return RCC_ERROR;\n" +
                       "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_009()

        self.assertEqual(1, len(issues))
        self.assertEqual(2, issues[0]["line"])

    def test_cpp_010_pass(self):
        code_sample = ("int main(void) {\n" +
                       "  setError();"
                       "  return RCC_FATAL;\n" +
                       "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_010()

        self.assertEqual([], issues)

    def test_cpp_010_fail(self):
        code_sample = ("int main(void) {\n" +
                       "  return RCC_FATAL;\n" +
                       "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_010()

        self.assertEqual(1, len(issues))

    def test_cpp_011_pass(self):
        code_sample = ("class Some_exampleWorker\n" +
                       ": public Some_exampleWorkerase {\n" +
                       "}\n" +
                       "\n" +
                       "int main(void) {\n" +
                       "  return 0;\n" +
                       "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_011()

        self.assertEqual([], issues)

    def test_cpp_011_fail_non_worker_class(self):
        code_sample = ("class some_class {\n" +
                       "  public:\n" +
                       "    some_value;\n" +
                       "}\n" +
                       "\n" +
                       "int main(void) {\n" +
                       "  return RCC_ERROR;\n" +
                       "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_011()

        self.assertEqual(1, len(issues))
        self.assertEqual(1, issues[0]["line"])

    def test_cpp_011_fail_two_worker_classes(self):
        code_sample = ("class Some_exampleWorker\n" +
                       ": public Some_exampleWorkerase {\n" +
                       "}\n" +
                       "\n" +
                       "class Some_other_exampleWorker\n" +
                       ": public Some_other_exampleWorkerase {\n" +
                       "}\n" +
                       "\n" +
                       "int main(void) {\n" +
                       "  return 0;\n" +
                       "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_011()

        self.assertEqual(1, len(issues))
        self.assertEqual(5, issues[0]["line"])

    def test_cpp_012_pass(self):
        code_sample = ("int main(void) {\n" +
                       "  uint8_t *some_memory = new uint8_t[10];\n" +
                       "  delete[] some_memory;\n" +
                       "  some_memory = NULL;\n"
                       "  kiss_fft_free();\n"
                       "  return 0;\n" +
                       "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_012()

        self.assertEqual([], issues)

    def test_cpp_012_fail(self):

        code_sample = ("int main(void) {\n" +
                       "  uint8_t *some_memory = malloc(10);\n" +
                       "  free(some_memory);\n" +
                       "  some_memory = NULL;"
                       "  kiss_fft_free();\n"
                       "  return 0;\n" +
                       "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_012()

        self.assertEqual(2, len(issues))
        self.assertEqual(2, issues[0]["line"])
        self.assertEqual(3, issues[1]["line"])

    def test_cpp_013_pass(self):
        code_sample = (
            "uint8_t main(void) {\n" +
            "  uint8_t *string = \"Allow char int float etc in strings\";\n" +
            "  # And in comments\n" +
            "  uint8_t  c;  // char value\n"
            "  uint16_t s;  // short value\n"
            "  uint32_t i;  // int value\n"
            "  uint64_t l;  // long value\n"
            "  RCCFloat f;  // float value\n"
            "  RCCDouble d; // double value\n"
            "  return 0;\n" +
            "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_013()

        self.assertEqual([], issues)

    def test_cpp_013_fail(self):
        code_sample = (
            "uint8_t main(void) {\n" +
            "  uint8_t *string = \"Allow char int float etc in strings\";\n" +
            "  # And in comments\n" +
            "  char   c;  // char value\n"
            "  short  s;  // short value\n"
            "  int    i;  // int value\n"
            "  long   l;  // long value\n"
            "  float  f;  // float value\n"
            "  double d;  // double value\n"
            "  return 0;\n" +
            "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_013()

        self.assertEqual(6, len(issues))
        self.assertEqual(4, issues[0]["line"])
        self.assertEqual(5, issues[1]["line"])
        self.assertEqual(6, issues[2]["line"])
        self.assertEqual(7, issues[3]["line"])
        self.assertEqual(8, issues[4]["line"])
        self.assertEqual(9, issues[5]["line"])

    def test_cpp_013_fail2(self):
        code_sample = (
            "uint8_t main(void) {\n" +
            "  uint8_t *string = \"Allow char int float etc in strings\";\n" +
            "  # And in comments\n" +
            "  char   c;  // char value\n"
            "  /* This is an unfinished block comment\n"
            "  short  s;  // short value\n"
            "  int    i;  // int value\n"
            "  long   l;  // long value\n"
            "  float  f;  // float value\n"
            "  double d;  // double value\n"
            "  return 0;\n" +
            "}\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_cpp_013()

        msg = "Reached end of file without finding end of block comment."
        self.assertEqual(1, len(issues))
        self.assertEqual(msg, issues[0]["message"])
        self.assertEqual(5, issues[0]["line"])

    def test_exception(self):
        code_sample = (
            "// Brief description\n" +
            "//\n" +
            self.expected_copyright +
            "\n" +
            "// A single line comment\n" +
            "\n" +
            "// LINT EXCEPTION: cpp_005: 1: Allow this define.\n"
            "#define SOME_VARIABLE 5\n" +
            "\n" +
            "// Some comment.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        completed_tests = code_checker.lint()

        self.assertEqual(0, completed_tests["cpp_005"].issue_count)

    def test_remove_comments_and_strings(self):
        code_sample = """
        /* This file is meant to have
   a mix of "strings" and // comments
   to remove */
    ;
char* cmd = "rm -rf folder/*";

char* string = "This string // is not a comment";
char* string = "This string /* is not a comment";
char* string = 'This string // is not a comment';
char* string = 'This string /* is not a comment';
// This comment is not a "string".
// Comments could contain " and aren't strings
// This is allowed /* to be in a line comment
int a = 1;
char* code = "*//*";
int answer /* Comment in middle */ = 42;
long number /* Comment in middle*/ =  /* and
over lines */ 123456;
"""
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        expected_code = ["",
                         "        ",
                         "",
                         "",
                         "    ;",
                         "char* cmd = \"\";",
                         "",
                         "char* string = \"\";",
                         "char* string = \"\";",
                         "char* string = '';",
                         "char* string = '';",
                         "",
                         "",
                         "",
                         "int a = 1;",
                         "char* code = \"\";",
                         "int answer  = 42;",
                         "long number  =  ",
                         " 123456;",
                         "",
                         ]

        code_checker = CppCodeChecker(
            self.test_file_path, self.linter_settings)
        code_checker._read_in_code()
        reduced_code = code_checker._remove_comments_and_strings(
            "/*", "*/", "//")

        self.assertEqual(len(reduced_code), len(expected_code))

        for line_number, line_text in enumerate(reduced_code):
            self.assertEqual(line_text, expected_code[line_number],
                             f"Code mismatch on line {line_number}")
