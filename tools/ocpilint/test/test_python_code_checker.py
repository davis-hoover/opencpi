#!/usr/bin/env python3

# Test code in python_code_checker.py
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

from ocpilint.ocpi_linter.python_code_checker import PythonCodeChecker
from ocpilint.ocpi_linter.linter_settings import LinterSettings


class TestPythonCodeChecker(unittest.TestCase):
    def setUp(self):
        self.test_file_path = pathlib.Path("test_file.py")
        self.test_file_path.touch()
        self.test_settings = LinterSettings()

    def tearDown(self):
        if self.test_file_path.is_file():
            os.remove(self.test_file_path)

    expected_copyright = """# This file is protected by Copyright. Please refer to the COPYRIGHT file
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
"""

    def test_py_empty(self):
        code_sample = ""
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(self.test_file_path,
                                         self.test_settings)
        code_checker._read_in_code()

        results = code_checker.lint()

        # Check an empty file fails lint without raising an exception
        self.assertGreater(len(results), 0)

    # Functionality of linter test 000 and 001 are not tested here since
    # they use external code checkers and formatters and it is assumed those
    # are tested separately - only reporting of errors is tested.

    def test_py_000_pass(self):
        code_sample = (
            "#!/usr/bin/env python3\n" +
            "\n" +
            "# Brief description\n" +
            "#\n" +
            self.expected_copyright +
            "\n" +
            "This would be the start of the main file.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_000()

        self.assertEqual([], issues)

    def test_py_000_fail(self):
        code_sample = (
            "#!/usr/bin/env python3\n" +
            "\n" +
            "\t\t# Over-indented Brief description\n" +
            "#\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_000()

        self.assertGreater(len(issues), 0)
        self.assertEqual(3, issues[0]["line"])

    def test_py_001_pass(self):
        code_sample = (
            "#!/usr/bin/env python3\n" +
            "\n" +
            "# Brief description\n" +
            "#\n" +
            "")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_001()

        self.assertEqual([], issues)

    def test_py_001_fail(self):
        code_sample = (
            "#!/usr/bin/env python3\n" +
            "\n" +
            "# Arguments on first line forbidden when" +
            " not using vertical alignment.\n" +
            "foo = long_function_name(var_one, var_two,\n" +
            "    var_three, var_four)\n" +
            "\n\n" +
            "# Mixed tabs and spaces not allowed.\n" +
            "def mixed_indent():\n" +
            "    pass\n" +
            "\tpass\n" +
            "")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)

        code_checker._read_in_code()

        _, issues = code_checker.test_py_001()

        self.assertGreaterEqual(len(issues), 2)
        self.assertEqual(5, issues[0]["line"])
        self.assertEqual(11, issues[1]["line"])

    def test_py_002_pass(self):
        code_sample = (
            "#!/usr/bin/env python3\n" +
            "\n" +
            "# Brief description\n" +
            "#\n" +
            self.expected_copyright +
            "\n" +
            "This would be the start of the main file.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_002()

        self.assertEqual([], issues)

    def test_py_002_fail_no_header(self):
        code_sample = "A single line of text"
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_002()

        self.assertEqual(1, len(issues))

    def test_py_002_fail_license_notice_typo(self):
        code_sample = (
            "#!/usr/bin/env python3\n" +
            "\n" +
            "# Brief description\n" +
            "#\n" +
            self.expected_copyright.replace("published by the Free",
                                            "published by the Frre") +
            "\n" +
            "This would be the start of the main file.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_002()

        self.assertEqual(1, len(issues))
        self.assertEqual(11, issues[0]["line"])

    def test_py_002_fail_no_blank_line_after_header(self):
        code_sample = (
            "#!/usr/bin/env python3\n" +
            "\n" +
            "# Brief description\n" +
            "#\n" +
            self.expected_copyright +
            "This would be the start of the main file.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_002()

        self.assertEqual(1, len(issues))
        self.assertEqual(22, issues[0]["line"])

    def test_py_003_pass(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "A line with a \"double quote\".\n" +
                       "print(\"A single quote ' in a string\")\n" +
                       "\"\"\" A single quote ' in a docstring \"\"\"\n" +
                       "print(\"Many\", \"strings\")")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_003()

        self.assertEqual([], issues)

    def test_py_003_fail(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "A line with a 'single quote'.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_003()

        self.assertEqual(1, len(issues))
        self.assertEqual(3, issues[0]["line"])

    def test_py_003_fail2(self):
        code_sample = ("#Single comment\n" +
                       "\"\"\"This is an unfinished docstring\n" +
                       "Which should fail the test.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_003()

        msg = "Reached end of file without finding end of block comment."
        self.assertEqual(1, len(issues))
        self.assertEqual(msg, issues[0]["message"])
        self.assertEqual(2, issues[0]["line"])

    def test_py_004_pass(self):
        code_sample = (
            "This is a line of text\n" +
            "\n" +
            "# Comment with complex literal pattern 0j\n" +
            "# Next line includes valid use of letter j\n" +
            "jump()\n" +
            "# Next lines have complex literal pattern in string\n" +
            "print(\"1 + 1.2j\")\n" +
            "print('1 + 5j')\n" +
            "\"\"\" Now a docstring 1.6j\n" +
            "   This is still docstring 1 + 2j\n" +
            "\"\"\"\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_004()

        self.assertEqual([], issues)

    def test_py_004_fail(self):
        code_sample = ("# This is a line of text\n" +
                       "\n" +
                       "value = 1 + 2j\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_004()

        self.assertEqual(1, len(issues))
        self.assertEqual(3, issues[0]["line"])

    def test_py_005_pass(self):
        code_sample = (
            "\"\"\"Test code.\"\"\"\n" +
            "def test_py_005(self):\n" +
            "    \"\"\"Docstring checker test.\n" +
            "\n" +
            "    Returns:\n" +
            "    tuple: tuple of test name, and dictionary of any issues.\n" +
            "    \"\"\"\n" +
            "    test_name = \"Python function docstrings\"\n" +
            "    return (test_name, None)\n" +
            "")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_005()

        self.assertEqual([], issues)

    def test_py_005_fail(self):
        code_sample = (
            "\n" +
            "def test_py_005(self, arg1, arg2):\n" +
            "    \"\"\"Docstring checker test.\n" +
            "    \n" +
            "    Args:\n" +
            "        arg1 (bool): First argument\n" +
            "    \"\"\"\n" +
            "    test_name = \"Python function docstrings\"\n" +
            "    return (test_name, None)\n" +
            "")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_py_005()

        self.assertEqual(2, len(issues))
        self.assertEqual(issues[0]["line"], 1)
        self.assertEqual(issues[1]["line"], 3)

    def test_exception(self):
        code_sample = (
            "#!/usr/bin/env python3\n" +
            "\n" +
            "# Brief description\n" +
            "#\n" +
            self.expected_copyright +
            "\n" +
            "if __name__ == \"__main__\":\n" +
            "    # LINT EXCEPTION: py_004: 2: Allow complex literal.\n" +
            "    # Another comment between lint exception and code\n" +
            "    complex_ = 5j\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        completed_tests = code_checker.lint()

        self.assertEqual(0, completed_tests["py_004"].issue_count)

    def test_remove_comments_and_strings(self):
        test_text = (
            "This line should stay\n" +
            "  This line should stay\n" +
            "  This part of this line should stay    # This part should go\n" +
            "This part of this line should stay \"This part should go\"\n" +
            "This part of this line should stay 'This part should go'\n" +
            "\"This part should go\" This part of this line should stay\n" +
            "'This part should go' This part of this line should stay\n" +
            "  Stay \"Go\" Stay \"Go\" Stay\n" +
            "  Stay 'Go' Stay 'Go' Stay\n" +
            "This part should stay \"\"\"This part should go\"\"\"\n" +
            "This part should stay\n" +
            "\"\"\"This part should go\n" +
            "This line should go\n" +
            "This line should go \"\"\"\n" +
            "This line should stay\n" +
            "  \"\\n\" This should stay \n" +
            "\"String with # symbol\" This should stay\n")

        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(test_text)

        code_checker = PythonCodeChecker(
            self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        reduced_code = code_checker._remove_comments_and_strings(
            "\"\"\"", "\"\"\"", "#")

        expected_text = [
            "This line should stay",
            "  This line should stay",
            "  This part of this line should stay    ",
            "This part of this line should stay \"\"",
            "This part of this line should stay ''",
            "\"\" This part of this line should stay",
            "'' This part of this line should stay",
            "  Stay \"\" Stay \"\" Stay",
            "  Stay '' Stay '' Stay",
            "This part should stay ",
            "This part should stay",
            "",
            "",
            "",
            "This line should stay",
            "  \"\" This should stay ",
            "\"\" This should stay",
            ""]

        self.assertEqual(expected_text, reduced_code)
