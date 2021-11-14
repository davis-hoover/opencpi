#!/usr/bin/env python3

# Test code in implementation.py
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


import collections
import unittest

import ocpi_testing


# A simple pass through implementation as the sample data handling
class SomeImplementation(ocpi_testing.Implementation):
    def reset(self):
        pass

    def sample(self, *inputs):
        # If the number of input and output ports do not match, put all sample
        # data on the first port
        if len(self.input_ports) != len(self.output_ports):
            # Do not use "[[]] * n" type code in the below line as creates
            # shallow copies (i.e. nested lists are to the same pointer so
            # cannot be individually modified).
            resultant_messages = [[] for _ in self.output_ports]
            for port_data in inputs:
                if port_data is not None:
                    resultant_messages[0].append(
                        {"opcode": "sample", "data": port_data})
        else:
            resultant_messages = [[] for _ in self.output_ports]
            for index, port_data in enumerate(inputs):
                if port_data is not None:
                    resultant_messages[index].append({"opcode": "sample",
                                                      "data": port_data})

        return self.output_formatter(*resultant_messages)


class TestImplementation(unittest.TestCase):
    def setUp(self):
        self.implementation = SomeImplementation()

    def test_no_sample_error(self):
        class no_sample_implementation(ocpi_testing.Implementation):
            def reset(self):
                pass
        with self.assertRaises(TypeError):
            implementation = no_sample_implementation()

    def test_no_reset_error(self):
        class no_reset_implementation(ocpi_testing.Implementation):
            def sample(self, *inputs):
                pass
        with self.assertRaises(TypeError):
            implementation = no_reset_implementation()

    def test_properties_set(self):
        implementation = SomeImplementation(property_1=5)
        self.assertEqual(implementation.property_1, 5)

    # Will test default time handling behaviour
    def test_time_single_port(self):
        output = self.implementation.time(0.123456)

        self.assertEqual(output.output, [{"opcode": "time", "data": 0.123456}])
        self.assertEqual(output[0], [{"opcode": "time", "data": 0.123456}])

    # Will test default time handling behaviour
    def test_time_multiple_inputs_on_primary(self):
        self.implementation.input_ports = ["input_1", "input_2"]
        output = self.implementation.time(0.123456, None)

        self.assertEqual(output.output, [{"opcode": "time", "data": 0.123456}])
        self.assertEqual(output[0], [{"opcode": "time", "data": 0.123456}])

    # Will test default time handling behaviour
    def test_time_multiple_inputs_on_non_primary(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        output = self.implementation.time(None, 0.123456, None)

        self.assertEqual(output.output, [])
        self.assertEqual(output[0], [])

    def test_time_multiple_inputs_use_different_port(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        self.implementation.non_sample_opcode_port_select = 1
        output = self.implementation.time(None, 0.123456, None)

        self.assertEqual(output.output, [{"opcode": "time", "data": 0.123456}])

    def test_time_multiple_inputs_use_different_port_drop(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        self.implementation.non_sample_opcode_port_select = 1
        output = self.implementation.time(0.123456, None, None)

        self.assertEqual(output.output, [])

    # Will test default time handling behaviour
    def test_time_multiple_outputs(self):
        self.implementation.output_ports = ["output_1", "output_2"]
        output = self.implementation.time(0.123456)

        self.assertEqual(output.output_1,
                         [{"opcode": "time", "data": 0.123456}])
        self.assertEqual(output[0], [{"opcode": "time", "data": 0.123456}])
        self.assertEqual(output.output_2, [])
        self.assertEqual(output[1], [])

    # Will test default sample interval handling behaviour
    def test_sample_interval_single_port(self):
        output = self.implementation.sample_interval(0.123456)

        self.assertEqual(output.output,
                         [{"opcode": "sample_interval", "data": 0.123456}])
        self.assertEqual(output[0],
                         [{"opcode": "sample_interval", "data": 0.123456}])

    # Will test default sample interval handling behaviour
    def test_sample_interval_multiple_inputs_on_primary(self):
        self.implementation.input_ports = ["input_1", "input_2"]
        output = self.implementation.sample_interval(0.123456, None)

        self.assertEqual(output.output,
                         [{"opcode": "sample_interval", "data": 0.123456}])
        self.assertEqual(output[0],
                         [{"opcode": "sample_interval", "data": 0.123456}])

    # Will test default sample interval handling behaviour
    def test_sample_interval_multiple_inputs_on_non_primary(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        output = self.implementation.sample_interval(None, 0.123456, None)

        self.assertEqual(output.output, [])
        self.assertEqual(output[0], [])

    def test_sample_interval_multiple_inputs_use_different_port(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        self.implementation.non_sample_opcode_port_select = 1
        output = self.implementation.sample_interval(None, 0.123456, None)

        self.assertEqual(output.output,
                         [{"opcode": "sample_interval", "data": 0.123456}])

    def test_sample_interval_multiple_inputs_use_different_port_drop(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        self.implementation.non_sample_opcode_port_select = 1
        output = self.implementation.sample_interval(0.123456, None, None)

        self.assertEqual(output.output, [])

    # Will test default sample interval handling behaviour
    def test_sample_interval_multiple_outputs(self):
        self.implementation.output_ports = ["output_1", "output_2"]
        output = self.implementation.sample_interval(0.123456)

        self.assertEqual(output.output_1,
                         [{"opcode": "sample_interval", "data": 0.123456}])
        self.assertEqual(output[0],
                         [{"opcode": "sample_interval", "data": 0.123456}])
        self.assertEqual(output.output_2, [])
        self.assertEqual(output[1], [])

    # Will test default flush handling behaviour
    def test_flush_single_port(self):
        output = self.implementation.flush(True)

        self.assertEqual(output.output,
                         [{"opcode": "flush", "data": None}])
        self.assertEqual(output[0],
                         [{"opcode": "flush", "data": None}])

    # Will test default flush handling behaviour
    def test_flush_multiple_inputs_flush_on_primary(self):
        self.implementation.input_ports = ["input_1", "input_2"]
        output = self.implementation.flush(True, False)

        self.assertEqual(output.output,
                         [{"opcode": "flush", "data": None}])
        self.assertEqual(output[0], [{"opcode": "flush", "data": None}])

    # Will test default flush handling behaviour
    def test_flush_multiple_inputs_flush_on_non_primary(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        output = self.implementation.flush(False, True, False)

        self.assertEqual(output.output, [])
        self.assertEqual(output[0], [])

    def test_flush_multiple_inputs_use_different_port(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        self.implementation.non_sample_opcode_port_select = 1
        output = self.implementation.flush(False, True, False)

        self.assertEqual(output.output, [{"opcode": "flush", "data": None}])

    def test_flush_multiple_inputs_use_different_port_drop(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        self.implementation.non_sample_opcode_port_select = 1
        output = self.implementation.flush(True, False, False)

        self.assertEqual(output.output, [])

    # Will test default flush handling behaviour
    def test_flush_multiple_outputs(self):
        self.implementation.output_ports = ["output_1", "output_2"]
        output = self.implementation.flush(True)

        self.assertEqual(output.output_1,
                         [{"opcode": "flush", "data": None}])
        self.assertEqual(output[0], [{"opcode": "flush", "data": None}])
        self.assertEqual(output.output_2, [])
        self.assertEqual(output[1], [])

    # Will test default discontinuity handling behaviour
    def test_discontinuity_single_port(self):
        output = self.implementation.discontinuity(True)

        self.assertEqual(output.output,
                         [{"opcode": "discontinuity", "data": None}])
        self.assertEqual(output[0],
                         [{"opcode": "discontinuity", "data": None}])

    # Will test default discontinuity handling behaviour
    def test_discontinuity_multiple_inputs_discontinuity_on_primary(self):
        self.implementation.input_ports = ["input_1", "input_2"]
        output = self.implementation.discontinuity(True, False)

        self.assertEqual(output.output,
                         [{"opcode": "discontinuity", "data": None}])
        self.assertEqual(output[0],
                         [{"opcode": "discontinuity", "data": None}])

    # Will test default discontinuity handling behaviour
    def test_discontinuity_multiple_inputs_discontinuity_on_non_primary(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        output = self.implementation.discontinuity(False, True, False)

        self.assertEqual(output.output, [])
        self.assertEqual(output[0], [])

    def test_discontinuity_multiple_inputs_use_different_port(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        self.implementation.non_sample_opcode_port_select = 1
        output = self.implementation.discontinuity(False, True, False)

        self.assertEqual(output.output,
                         [{"opcode": "discontinuity", "data": None}])

    def test_discontinuity_multiple_inputs_use_different_port_drop(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        self.implementation.non_sample_opcode_port_select = 1
        output = self.implementation.discontinuity(True, False, False)

        self.assertEqual(output.output, [])

    # Will test default discontinuity handling behaviour
    def test_discontinuity_multiple_outputs(self):
        self.implementation.output_ports = ["output_1", "output_2"]
        output = self.implementation.discontinuity(True)

        self.assertEqual(output.output_1,
                         [{"opcode": "discontinuity", "data": None}])
        self.assertEqual(output[0],
                         [{"opcode": "discontinuity", "data": None}])
        self.assertEqual(output.output_2, [])
        self.assertEqual(output[1], [])

    # Will test default metadata handling behaviour
    def test_sample_single_port(self):
        metadata = {"id": 100, "value": 123456}
        output = self.implementation.metadata(metadata)

        self.assertEqual(output.output,
                         [{"opcode": "metadata", "data": metadata}])
        self.assertEqual(output[0],
                         [{"opcode": "metadata", "data": metadata}])

    # Will test default metadata handling behaviour
    def test_sample_multiple_inputs_on_primary(self):
        self.implementation.input_ports = ["input_1", "input_2"]
        metadata = {"id": 100, "value": 123456}
        output = self.implementation.metadata(metadata, None)

        self.assertEqual(output.output,
                         [{"opcode": "metadata", "data": metadata}])
        self.assertEqual(output[0],
                         [{"opcode": "metadata", "data": metadata}])

    # Will test default metadata handling behaviour
    def test_metadata_multiple_inputs_on_non_primary(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        metadata = {"id": 100, "value": 123456}
        output = self.implementation.metadata(None, metadata, None)

        self.assertEqual(output.output, [])
        self.assertEqual(output[0], [])

    def test_metadata_multiple_inputs_use_different_port(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        metadata = {"id": 100, "value": 123456}
        self.implementation.non_sample_opcode_port_select = 1
        output = self.implementation.metadata(None, metadata, None)

        self.assertEqual(output.output,
                         [{"opcode": "metadata", "data": metadata}])

    def test_metadata_multiple_inputs_use_different_port_drop(self):
        self.implementation.input_ports = ["input_1", "input_2", "input_3"]
        metadata = {"id": 100, "value": 123456}
        self.implementation.non_sample_opcode_port_select = 1
        output = self.implementation.metadata(metadata, None, None)

        self.assertEqual(output.output, [])

    # Will test default metadata handling behaviour
    def test_metadata_multiple_outputs(self):
        self.implementation.output_ports = ["output_1", "output_2"]
        metadata = {"id": 100, "value": 123456}
        output = self.implementation.metadata(metadata)

        self.assertEqual(output.output_1,
                         [{"opcode": "metadata", "data": metadata}])
        self.assertEqual(output[0],
                         [{"opcode": "metadata", "data": metadata}])
        self.assertEqual(output.output_2, [])
        self.assertEqual(output[1], [])

    def test_process_messages_too_many_inputs(self):
        messages = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 10}},
            {"opcode": "sample_interval", "data": 0.01},
            {"opcode": "sample", "data": [1, 2, 3, 4, 5]},
            {"opcode": "sample", "data": [11, 12, 13, 14, 15]}]

        with self.assertRaises(ValueError):
            self.implementation.process_messages(messages, messages)

    def test_process_messages_single_input(self):
        messages = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 10}},
            {"opcode": "sample_interval", "data": 0.01},
            {"opcode": "sample", "data": [1, 2, 3, 4, 5]},
            {"opcode": "sample", "data": [11, 12, 13, 14, 15]}]
        output = self.implementation.process_messages(messages)

        self.assertEqual(output.output, messages)
        self.assertEqual(output[0], messages)

    def test_process_messages_multiple_inputs_by_position_argument(self):
        self.implementation.input_ports = ["input_1", "input_2"]

        # A specific implementation of select_input is needed when there are
        # multiple input ports.
        def select_input(*inputs):
            for index, input_ in enumerate(inputs):
                if input_ is not None:
                    return index
        self.implementation.select_input = select_input

        messages_1 = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 10}},
            {"opcode": "sample_interval", "data": 0.01},
            {"opcode": "sample", "data": [1, 2, 3, 4, 5]},
            {"opcode": "sample", "data": [11, 12, 13, 14, 15]}]
        messages_2 = [
            {"opcode": "flush", "data": None},
            {"opcode": "time", "data": 0.5},
            {"opcode": "sample", "data": [2.1, 2.2, 2.3, 2.4, 2.5]},
            {"opcode": "sample", "data": [21, 22, 23, 24, 25]}]
        expected_output = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 10}},
            {"opcode": "sample_interval", "data": 0.01},
            {"opcode": "sample", "data": [1, 2, 3, 4, 5]},
            {"opcode": "sample", "data": [11, 12, 13, 14, 15]},
            {"opcode": "sample", "data": [2.1, 2.2, 2.3, 2.4, 2.5]},
            {"opcode": "sample", "data": [21, 22, 23, 24, 25]}]

        output = self.implementation.process_messages(messages_1, messages_2)

        self.assertEqual(expected_output, output.output)

    def test_process_messages_multiple_inputs_by_keyword_argument(self):
        self.implementation.input_ports = ["input_1", "input_2"]

        # A specific implementation of select_input is needed when there are
        # multiple input ports.
        def select_input(*inputs):
            for index, input_ in enumerate(inputs):
                if input_ is not None:
                    return index
        self.implementation.select_input = select_input

        messages_1 = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 10}},
            {"opcode": "sample_interval", "data": 0.01},
            {"opcode": "sample", "data": [1, 2, 3, 4, 5]},
            {"opcode": "sample", "data": [11, 12, 13, 14, 15]}]
        messages_2 = [
            {"opcode": "flush", "data": None},
            {"opcode": "time", "data": 0.5},
            {"opcode": "sample", "data": [2.1, 2.2, 2.3, 2.4, 2.5]},
            {"opcode": "sample", "data": [21, 22, 23, 24, 25]}]
        expected_output = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 10}},
            {"opcode": "sample_interval", "data": 0.01},
            {"opcode": "sample", "data": [1, 2, 3, 4, 5]},
            {"opcode": "sample", "data": [11, 12, 13, 14, 15]},
            {"opcode": "sample", "data": [2.1, 2.2, 2.3, 2.4, 2.5]},
            {"opcode": "sample", "data": [21, 22, 23, 24, 25]}]

        output = self.implementation.process_messages(input_1=messages_1,
                                                      input_2=messages_2)

        self.assertEqual(output.output, expected_output)
        self.assertEqual(output[0], expected_output)

    def test_process_messages_multiple_inputs_more_on_non_primary_port(self):
        self.implementation.input_ports = ["input_1", "input_2"]

        # A specific implementation of select_input is needed when there are
        # multiple input ports.
        def select_input(*inputs):
            for index, input_ in enumerate(inputs):
                if input_ is not None:
                    return index
        self.implementation.select_input = select_input

        messages_1 = [
            {"opcode": "flush", "data": None},
            {"opcode": "sample", "data": [1.1, 1.2, 1.3, 1.4, 1.5]}]
        messages_2 = [
            {"opcode": "flush", "data": None},
            {"opcode": "sample", "data": [2.1, 2.2, 2.3, 2.4, 2.5]},
            {"opcode": "sample", "data": [21, 22, 23, 24, 25]},
            {"opcode": "sample_interval", "data": 0.01},
            {"opcode": "sample", "data": [210, 220, 230, 240, 250]}]
        expected_output = [
            {"opcode": "flush", "data": None},
            {"opcode": "sample", "data": [1.1, 1.2, 1.3, 1.4, 1.5]},
            {"opcode": "sample", "data": [2.1, 2.2, 2.3, 2.4, 2.5]},
            {"opcode": "sample", "data": [21, 22, 23, 24, 25]},
            {"opcode": "sample", "data": [210, 220, 230, 240, 250]}]

        output = self.implementation.process_messages(messages_1, messages_2)

        self.assertEqual(output.output, expected_output)

    def test_process_messages_multiple_inputs_different_size_sample(self):
        self.implementation.input_ports = ["input_1", "input_2"]

        # A specific implementation of select_input is needed when there are
        # multiple input ports.
        def select_input(*inputs):
            for index, input_ in enumerate(inputs):
                if input_ is not None:
                    return index
        self.implementation.select_input = select_input

        messages_1 = [
            {"opcode": "flush", "data": None},
            {"opcode": "sample", "data": [1.1, 1.2, 1.3]},
            {"opcode": "sample", "data": [1.4, 1.5]}]
        messages_2 = [
            {"opcode": "flush", "data": None},
            {"opcode": "sample", "data": [2.1, 2.2, 2.3, 2.4, 2.5]},
            {"opcode": "sample", "data": [2.6]},
            {"opcode": "sample", "data": [2.7]}]
        expected_output = [
            {"opcode": "flush", "data": None},
            {"opcode": "sample", "data": [1.1, 1.2, 1.3]},
            {"opcode": "sample", "data": [2.1, 2.2, 2.3, 2.4, 2.5]},
            {"opcode": "sample", "data": [1.4, 1.5]},
            {"opcode": "sample", "data": [2.6]},
            {"opcode": "sample", "data": [2.7]}]

        output = self.implementation.process_messages(messages_1, messages_2)

        self.assertEqual(output.output, expected_output)

    def test_process_messages_multiple_input_duplicate_arguments(self):
        self.implementation.input_ports = ["input_1", "input_2"]

        # A specific implementation of select_input is needed when there are
        # multiple input ports.
        def select_input(*inputs):
            for index, input_ in enumerate(inputs):
                if input_ is not None:
                    return index
        self.implementation.select_input = select_input

        messages = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 10}},
            {"opcode": "sample_interval", "data": 0.01},
            {"opcode": "sample", "data": [1, 2, 3, 4, 5]},
            {"opcode": "sample", "data": [11, 12, 13, 14, 15]}]

        with self.assertRaises(ValueError):
            self.implementation.process_messages(
                messages, input_1=messages, input_2=messages)

    def test_process_messages_input_by_keyword_not_defined(self):
        self.implementation.input_ports = ["input_1", "input_2"]

        # A specific implementation of select_input is needed when there are
        # multiple input ports.
        def select_input(*inputs):
            for index, input_ in enumerate(inputs):
                if input_ is not None:
                    return index
        self.implementation.select_input = select_input

        messages = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 10}},
            {"opcode": "sample_interval", "data": 0.01},
            {"opcode": "sample", "data": [1, 2, 3, 4, 5]},
            {"opcode": "sample", "data": [11, 12, 13, 14, 15]}]

        with self.assertRaises(ValueError):
            self.implementation.process_messages(random_input=messages)

    def test_process_messages_multiple_outputs(self):
        self.implementation.output_ports = ["output_1", "output_2"]
        messages = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 10}},
            {"opcode": "sample_interval", "data": 0.01},
            {"opcode": "sample", "data": [1, 2, 3, 4, 5]},
            {"opcode": "sample", "data": [11, 12, 13, 14, 15]}]
        output = self.implementation.process_messages(messages)

        self.assertEqual(output.output_1, messages)
        self.assertEqual(output[0], messages)
        self.assertEqual(output.output_2, [])
        self.assertEqual(output[1], [])

    def test_process_messages_multiple_inputs_multiple_outputs(self):
        self.implementation.input_ports = ["input_1", "input_2"]
        self.implementation.output_ports = ["output_1", "output_2"]

        # A specific implementation of select_input is needed when there are
        # multiple input ports.
        def select_input(*inputs):
            for index, input_ in enumerate(inputs):
                if input_ is not None:
                    return index
        self.implementation.select_input = select_input

        messages_1 = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 10}},
            {"opcode": "sample_interval", "data": 0.01},
            {"opcode": "sample", "data": [1, 2, 3, 4, 5]},
            {"opcode": "sample", "data": [11, 12, 13, 14, 15]}]
        messages_2 = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 101}},
            {"opcode": "sample", "data": [2.1, 2.2, 2.3, 2.4, 2.5]},
            {"opcode": "sample", "data": [21, 22, 23, 24, 25]}]
        expected_output_1 = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 10}},
            {"opcode": "sample_interval", "data": 0.01},
            {"opcode": "sample", "data": [1, 2, 3, 4, 5]},
            {"opcode": "sample", "data": [11, 12, 13, 14, 15]}]
        expected_output_2 = [
            {"opcode": "sample", "data": [2.1, 2.2, 2.3, 2.4, 2.5]},
            {"opcode": "sample", "data": [21, 22, 23, 24, 25]}]

        output = self.implementation.process_messages(messages_1, messages_2)

        self.assertEqual(output.output_1, expected_output_1)
        self.assertEqual(output[0], expected_output_1)
        self.assertEqual(output.output_2, expected_output_2)
        self.assertEqual(output[1], expected_output_2)

    def test_process_messages_select_input_invalid_return(self):
        self.implementation.input_ports = ["input_1", "input_2"]

        # This test ensures that if select_input() requests a port with no data
        # an error occurs, for this reason the below select_input is
        # purposefully wrong - and always returns port 0.
        def select_input(*inputs):
            return 00
        self.implementation.select_input = select_input

        messages_1 = [
            {"opcode": "flush", "data": None},
            {"opcode": "sample", "data": [1, 2, 3, 4, 5]},
            {"opcode": "sample", "data": [11, 12, 13, 14, 15]}]
        messages_2 = [
            {"opcode": "flush", "data": None},
            {"opcode": "metadata", "data": {"id": 1, "value": 101}},
            {"opcode": "sample", "data": [2.1, 2.2, 2.3, 2.4, 2.5]},
            {"opcode": "sample", "data": [21, 22, 23, 24, 25]}]

        with self.assertRaises(ValueError):
            self.implementation.process_messages(messages_1, messages_2)
