#!/usr/bin/env python3

# Base class for Python implementations to inherit from
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


import abc
import collections


class Implementation(abc.ABC):
    """ Base class for Python test implementations to inherit from
    """

    def __init__(self, **properties):
        """ Initialise an implementation specific case

        Args:
            properties (various, optional): Properties and parameters of the
                implementation should be passed in as key word arguments. The
                name should be the property / parameter name and the value the
                value of the property / parameter for this test case.

        Returns:
            Initialised implementation instance.
        """
        for key, value in properties.items():
            setattr(self, key, value)

        #: Default implementation, if a different set of ports is needed set as
        #: part of specific implementation code.
        self.input_ports = ["input"]
        self.output_ports = ["output"]

        # Set the input port that non-sample opcode messages will be used from.
        # Must be the index number that matches that of the port to be used as
        # set in self.input_ports.
        self.non_sample_opcode_port_select = 0

        # When there are no input ports these are the settings that are used to
        # define the behaviour output generation. Any values are passed as key
        # work arguments to self.generate (self.generate needs to be defined
        # for implementations with no input ports).
        self.no_input_settings = {}

        # Define the methods (functions) to be called for each type of message
        # opcode. Avoids the use of getattr() with the called attribute defined
        # by an incoming data source.
        self._message_functions = {
            "sample": self.sample,
            "time": self.time,
            "sample_interval": self.sample_interval,
            "flush": self.flush,
            "discontinuity": self.discontinuity,
            "metadata": self.metadata}

    def process_messages(self, *inputs, **named_inputs):
        """ Generate the output messages for a set of input messages

        Args:
            inputs (lists, optional), named_inputs (lists, optional): The input
                messages. If positional arguments are used the input port order
                must match the port order used in ``self.input_ports``. If
                ``named_inputs`` are used the input port names should be the
                argument name as defined in ``self.input_ports``. If both
                positional, ``inputs``, and keyword arguments,
                ``named_inputs``, are used then the same port cannot be given
                input messages via both argument types.

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. The order of the elements in the tuple, so order of
                port's outputs, matches that as defined in self.output_ports;
                the names used for the named tuple are that as defined in
                self.output_ports.
        """
        if len(inputs) + len(named_inputs) != len(self.input_ports):
            raise ValueError("Number of inputs (total by position and name) " +
                             "must equal the number of named input ports in " +
                             "self.input_ports. " +
                             f"{len(inputs) + len(named_inputs)} inputs " +
                             f"given, {len(self.input_ports)} inputs " +
                             "expected")

        for named_input in named_inputs:
            # Check named input defined
            if named_input not in self.input_ports:
                raise ValueError(f"{named_input} is not defined as an input " +
                                 "port name")

            # Check the named_inputs do not duplicate any positional arguments
            if named_input in self.input_ports[0:len(inputs)]:
                raise ValueError("Positional arguments define " +
                                 f"{named_input} so cannot define as " +
                                 "keyword argument")

        # Combine positional and keyword arguments
        inputs = list(inputs)
        if len(named_inputs) > 0:
            # Do not use "[[]] * n" type code in the below line as creates
            # shallow copies (i.e. nested lists are to the same pointer so
            # cannot be individually modified).
            inputs = inputs + [[] for _ in range(
                len(self.input_ports) - len(inputs))]
            for port_name, input_value in named_inputs.items():
                inputs[self.input_ports.index(port_name)] = input_value

        # Take the input messages and pass to the matching opcode function

        # Do not use "[[]] * n" type code in the below line as creates
        # shallow copies (i.e. nested lists are to the same pointer so cannot
        # be individually modified).
        output_messages = [[] for _ in self.output_ports]
        if len(self.input_ports) == 1:
            for message in inputs[0]:
                # Flush and discontinuity messages do not have data so use
                # True / False as arguments to indicate if a flush or
                # discontinuity message has been received on a port.
                if message["opcode"] in ["flush", "discontinuity"]:
                    resulting_messages = \
                        self._message_functions[message["opcode"]](True)
                else:
                    resulting_messages = \
                        self._message_functions[message["opcode"]](
                            message["data"])

                for port_index, port_data in enumerate(resulting_messages):
                    output_messages[port_index] = \
                        output_messages[port_index] + port_data

        elif len(self.input_ports) > 1:
            # When there are multiple inputs, self.select_input() will be
            # called first with the input arguments being the opcodes available
            # next on each input. self.select_input() must return the index of
            # the input it wishes to advance. Then the data on all input ports
            # with the same opcode as the port index returned by
            # self.select_input() will be passed using the methods defined for
            # each opcode in self._message_functions().
            #
            # self.select_inputs() must be overloaded by any multiple input
            # implementations (no input or one input implementations do not
            # need to overload this method).)

            # Define the index of the next message to be processed for each
            # port
            next_message_index = [0] * len(self.input_ports)

            # Loop until all input messages have been read
            while any([next_message_index[index]
                       < len(inputs[index]) for index in range(len(inputs))]):
                # Use self.select_input() to determine which data to be
                # processed next. To do this, first determine the next message
                # on each input port.
                select_input_arguments = [None] * len(self.input_ports)
                for index in range(len(self.input_ports)):
                    # All data on input port processed - skip input port
                    if next_message_index[index] >= len(inputs[index]):
                        continue
                    select_input_arguments[index] = \
                        inputs[index][next_message_index[index]]["opcode"]
                requested_input = self.select_input(*select_input_arguments)

                # If self.select_input() call requests a port which is
                # exhausted of data then raise an error.
                if next_message_index[requested_input] >= \
                        len(inputs[requested_input]):
                    raise ValueError(
                        "Call of self.select_input("
                        + f"{str(select_input_arguments)[1:-1]}) returned "
                        + "request for data on input port index "
                        + f"{requested_input} which is exhausted of data")

                opcode_requested = inputs[requested_input][next_message_index[
                    requested_input]]["opcode"]

                # Get the data for any messages that are the next to be read
                # for each port as requested by self.select_input().
                if opcode_requested in ["flush", "discontinuity"]:
                    # Flush and discontinuity opcodes have no data so use true
                    # and false to mark if called on an input port.
                    arguments = [False] * len(self.input_ports)
                else:
                    arguments = [None] * len(self.input_ports)
                for index in range(len(self.input_ports)):
                    # All data on input port processed - skip input port
                    if next_message_index[index] >= len(inputs[index]):
                        continue

                    if inputs[index][next_message_index[index]]["opcode"] == \
                            opcode_requested:
                        if opcode_requested in ["flush", "discontinuity"]:
                            arguments[index] = True
                        else:
                            arguments[index] = inputs[index][
                                next_message_index[index]]["data"]
                        next_message_index[index] = (
                            next_message_index[index] + 1)

                # Call the function method the data has been prepared for and
                # record the output.
                resulting_messages = self._message_functions[opcode_requested](
                    *arguments)
                for port_index, port_data in enumerate(resulting_messages):
                    output_messages[port_index] = \
                        output_messages[port_index] + port_data

        else:
            output_messages = self.generate(**self.no_input_settings)

        return self.output_formatter(*output_messages)

    def output_formatter(self, *outputs):
        """ Format the output from all opcode message handling methods

        All methods that relate to an opcode and process input messages should
        use this method to prepare their outputs into the correct named tuple
        output format.

        Args:
            outputs (multiple arguments, each lists): There should be an
                argument for each port defined in self.output_ports, in a
                matching order. The lists must be lists of dictionaries where
                each dictionary is a message. Empty lists for ports are allowed.

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. The order of the elements in the tuple, so order of
                port's outputs, matches that as defined in self.output_ports;
                the names used for the named tuple are that as defined in
                self.output_ports.
        """
        # Check that each output has a list of messages
        if not all([isinstance(output, list) for output in outputs]):
            raise TypeError("All outputs must be a list of messages, not " +
                            f"{[type(output) for output in outputs]}")

        output_format = collections.namedtuple("output_named_tuple",
                                               self.output_ports)
        return output_format(*outputs)

    @abc.abstractmethod
    def reset(self):
        """ Put the implementation into the same state as at initialisation

        The result of this method should place the implementation into the same
        state as at initialisation and as if no data had previously been passed
        through the implementation.

        This is a testing artefact, so does not need to match the same reset
        behaviour of the implementation under test being replicated - although
        it may do by coincidence.

        Specific implementation must be defined in Python component test
        implementation.
        """
        raise NotImplementedError("All inherited test implementations must " +
                                  "define their own reset() implementation")

    @abc.abstractmethod
    def sample(self, *inputs):
        """ Functionality that a sample opcode message triggers

        Specific implementation must be defined in Python component test
        implementation.

        Args:
            inputs* (various): Sample data value for the input ports. There
                should be as many inputs arguments as there are input ports.
                Set to None if no sample message on a port.

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. Each tuple element (port) is a list of dictionaries which
                are the output messages for the port. The order of lists in the
                tuple, so order of port's outputs, matches that as defined in
                self.output_ports; the names used for the named tuple are that
                as defined in self.output_ports. The message dictionaries
                within the lists within the named tuple, have the keys "opcode"
                and "data".
        """
        raise NotImplementedError("All inherited test implementations must " +
                                  "define their own sample() implementation")

    def time(self, *inputs):
        """ Get messages resulting from a time message

        Set with default behaviour here, however if a different behaviour is
        needed this should be overridden by the specific implementation. A
        specific implementation can either have code to implement the expected
        behaviour or call a different time case (e.g. self._time_fixed_delay).

        Args:
            inputs* (floats): Time value for the input ports. There should be
                as many inputs arguments as there are input ports. Set to None
                if no time message on a port (used when a time message is
                present on another port).

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. Each tuple element (port) is a list of dictionaries which
                are the output messages for the port. The order of lists in the
                tuple, so order of port's outputs, matches that as defined in
                self.output_ports; the names used for the named tuple are that
                as defined in self.output_ports. The message dictionaries
                within the lists within the named tuple, have the keys "opcode"
                and "data".
        """
        return self._time_default(*inputs)

    def _time_default(self, *inputs):
        """ Get messages resulting from a time message - default case

        Default behaviour on receiving a time message is to pass on time
        message, without delay, from the input port set by
        ``self.non_sample_opcode_port_select`` only and drop time messages on
        any other input port.

        Args:
            inputs (float, multiple): Time value for the input ports, in the
                order set in ``self.input_ports``. Set to ``None`` if no time
                message on this port (used when a time message is present on
                another port).

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. Each tuple element (port) is a list of dictionaries which
                are the output messages for the port. The order of lists in the
                tuple, so order of port's outputs, matches that as defined in
                self.output_ports; the names used for the named tuple are that
                as defined in self.output_ports. The message dictionaries
                within the lists within the named tuple, have the keys "opcode"
                and "data".
        """
        # Get the input value from the port that is being used for non-sample
        # input messages.
        time = inputs[self.non_sample_opcode_port_select]

        if time is not None:
            other_outputs = [[]] * (len(self.output_ports) - 1)
            return self.output_formatter([{"opcode": "time", "data": time}],
                                         *other_outputs)

        # Drop time on any port other than the selected input.
        else:
            outputs = [[]] * len(self.output_ports)
            return self.output_formatter(*outputs)

    def _time_example_other_behaviour(self, *inputs):
        """ Example: Common behaviours

        Args:
            input_1 (float): Time value for the first input port. Behaviour is
                to pass this message on without delay. Set to None if no time
                message on this port (used when input time on other port).
            other_inputs (float): Time value for any other port. Behaviour is
                to drop time values from any input port which is not the first
                input port, so all time values passed here are dropped.

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. Each tuple element (port) is a list of dictionaries which
                are the output messages for the port. The order of lists in the
                tuple, so order of port's outputs, matches that as defined in
                self.output_ports; the names used for the named tuple are that
                as defined in self.output_ports. The message dictionaries
                within the lists within the named tuple, have the keys "opcode"
                and "data".
        """
        raise NotImplementedError("Not yet implemented. Common cases on how " +
                                  "different message opcodes are handled " +
                                  "should be added as possible options.")

    def sample_interval(self, *inputs):
        """ Get messages resulting from a sample interval message

        Set with default behaviour here, however if a different behaviour is
        needed this should be overridden by the specific implementation. A
        specific implementation can either have code to implement the expected
        behaviour or call a different sample interval behaviour defined in this
        class.

        Args:
            inputs* (floats): Sample interval value for the input ports. There
                should be as many inputs arguments as there are input ports.
                Set to None if no sample interval message on a port (used when
                a sample interval message is present on another port).

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. Each tuple element (port) is a list of dictionaries which
                are the output messages for the port. The order of lists in the
                tuple, so order of port's outputs, matches that as defined in
                self.output_ports; the names used for the named tuple are that
                as defined in self.output_ports. The message dictionaries
                within the lists within the named tuple, have the keys "opcode"
                and "data".
        """
        return self._sample_interval_default(*inputs)

    def _sample_interval_default(self, *inputs):
        """ Get messages resulting from a sample interval message - default

        Default behaviour on receiving a sample interval message is to pass on
        sample interval message, without delay, from the input port set by
        ``self.non_sample_opcode_port_select`` only and drop sample interval
        messages on any other input port.

        Args:
            *inputs (float, multiple): Sample interval value for the input
                ports, in the order set in ``self.input_ports``. Set to
                ``None`` if no sample interval message on this port (used when
                a sample interval message is present on another port).

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. Each tuple element (port) is a list of dictionaries which
                are the output messages for the port. The order of lists in the
                tuple, so order of port's outputs, matches that as defined in
                self.output_ports; the names used for the named tuple are that
                as defined in self.output_ports. The message dictionaries
                within the lists within the named tuple, have the keys "opcode"
                and "data".
        """
        # Get the input value from the port that is being used for non-sample
        # input messages.
        sample_interval = inputs[self.non_sample_opcode_port_select]

        if sample_interval is not None:
            other_outputs = [[]] * (len(self.output_ports) - 1)
            return self.output_formatter(
                [{"opcode": "sample_interval", "data": sample_interval}],
                *other_outputs)

        # Drop sample interval messages on any port other than the selected
        # input.
        else:
            outputs = [[]] * len(self.output_ports)
            return self.output_formatter(*outputs)

    def flush(self, *inputs):
        """ Get messages resulting from a flush message

        Set with default behaviour here, however if a different behaviour is
        needed this should be overridden by the specific implementation. A
        specific implementation can either have code to implement the expected
        behaviour or call a different flush behaviour defined in this class.

        Args:
            inputs* (bools): Indicate if a flush message has been received on
                an input port (True) or not received (False). There must be as
                many inputs arguments as there are input ports. The order of
                ports and inputs arguments matches that defined in
                self.input_ports.

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. Each tuple element (port) is a list of dictionaries which
                are the output messages for the port. The order of lists in the
                tuple, so order of port's outputs, matches that as defined in
                self.output_ports; the names used for the named tuple are that
                as defined in self.output_ports. The message dictionaries
                within the lists within the named tuple, have the keys "opcode"
                and "data".
        """
        return self._flush_default(*inputs)

    def _flush_default(self, *inputs):
        """ Get messages resulting from a flush message - default

        Default behaviour on receiving a flush message is to pass on the flush
        message, without delay, from the input port set by
        ``self.non_sample_opcode_port_select`` only and drop flush messages on
        any other input port.

        Args:
            *inputs (bool, multiple): Set as ``True`` for any input port which
                has received a flush message. Set to ``False`` for any input
                port which has not received a flush message.

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. Each tuple element (port) is a list of dictionaries which
                are the output messages for the port. The order of lists in the
                tuple, so order of port's outputs, matches that as defined in
                self.output_ports; the names used for the named tuple are that
                as defined in self.output_ports. The message dictionaries
                within the lists within the named tuple, have the keys "opcode"
                and "data".
        """
        # Get the input value from the port that is being used for non-sample
        # input messages.
        flush = inputs[self.non_sample_opcode_port_select]

        if flush is True:
            other_outputs = [[]] * (len(self.output_ports) - 1)
            return self.output_formatter([{"opcode": "flush", "data": None}],
                                         *other_outputs)

        # Drop flush on any port other than the selected input.
        else:
            outputs = [[]] * len(self.output_ports)
            return self.output_formatter(*outputs)

    def discontinuity(self, *inputs):
        """ Get messages resulting from a discontinuity message

        Set with default behaviour here, however if a different behaviour is
        needed this should be overridden by the specific implementation. A
        specific implementation can either have code to implement the expected
        behaviour or call a different discontinuity behaviour defined in this
        class.

        Args:
            inputs* (bools): Indicate if a discontinuity message has been
                received on an input port (True) or not received (False). There
                must be as many inputs arguments as there are input ports. The
                order of ports and inputs arguments matches that defined in
                self.input_ports.

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. Each tuple element (port) is a list of dictionaries which
                are the output messages for the port. The order of lists in the
                tuple, so order of port's outputs, matches that as defined in
                self.output_ports; the names used for the named tuple are that
                as defined in self.output_ports. The message dictionaries
                within the lists within the named tuple, have the keys "opcode"
                and "data".
        """
        return self._discontinuity_default(*inputs)

    def _discontinuity_default(self, *inputs):
        """ Get messages resulting from a discontinuity message - default

        Default behaviour on receiving a discontinuity message is to pass on
        the discontinuity message, without delay, from the input port set by
        ``self.non_sample_opcode_port_select`` only and drop discontinuity
        messages on any other input port.

        Args:
            *inputs (bool, multiple): Set as ``True`` for any input port which
                has received a discontinuity message. Set to ``False`` for any
                input port which has not received a discontinuity message.

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. Each tuple element (port) is a list of dictionaries which
                are the output messages for the port. The order of lists in the
                tuple, so order of port's outputs, matches that as defined in
                self.output_ports; the names used for the named tuple are that
                as defined in self.output_ports. The message dictionaries
                within the lists within the named tuple, have the keys "opcode"
                and "data".
        """
        # Get the input value from the port that is being used for non-sample
        # input messages.
        discontinuity = inputs[self.non_sample_opcode_port_select]

        if discontinuity is True:
            other_outputs = [[]] * (len(self.output_ports) - 1)
            return self.output_formatter(
                [{"opcode": "discontinuity", "data": None}],
                *other_outputs)

        # Drop discontinuity on any port other than the selected input.
        else:
            outputs = [[]] * len(self.output_ports)
            return self.output_formatter(*outputs)

    def metadata(self, *inputs):
        """ Get messages resulting from a metadata message

        Set with default behaviour here, however if a different behaviour is
        needed this should be overridden by the specific implementation. A
        specific implementation can either have code to implement the expected
        behaviour or call a different metadata behaviour defined in this class.

        Args:
            inputs* (dict): Input metadata for input ports. Metadata must be
                given as dictionaries with the keys "id" and "value". There
                must be as many inputs arguments as there are input ports. The
                order of ports and inputs arguments matches that defined in
                ``self.input_ports``.

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. Each tuple element (port) is a list of dictionaries which
                are the output messages for the port. The order of lists in the
                tuple, so order of port's outputs, matches that as defined in
                self.output_ports; the names used for the named tuple are that
                as defined in self.output_ports. The message dictionaries
                within the lists within the named tuple, have the keys "opcode"
                and "data".
        """
        return self._metadata_default(*inputs)

    def _metadata_default(self, *inputs):
        """ Get messages resulting from a metadata message - default

        Default behaviour on receiving a metadata message is to pass on the
        metadata message, without delay, from the input port set by
        ``self.non_sample_opcode_port_select`` only and drop metadata messages
        on any other input port.

        Args:
            *inputs (float, multiple): Metadata for the input ports, in the
                order set in ``self.input_ports``. Set to ``None`` if no
                metadata message on this port (used when a metadata message is
                present on another port).

        Returns:
            A named tuple where each item in the tuple relates to each output
                port. Each tuple element (port) is a list of dictionaries which
                are the output messages for the port. The order of lists in the
                tuple, so order of port's outputs, matches that as defined in
                self.output_ports; the names used for the named tuple are that
                as defined in self.output_ports. The message dictionaries
                within the lists within the named tuple, have the keys "opcode"
                and "data".
        """
        # Get the input value from the port that is being used for non-sample
        # input messages.
        metadata = inputs[self.non_sample_opcode_port_select]

        if metadata is not None:
            other_outputs = [[]] * (len(self.output_ports) - 1)
            return self.output_formatter(
                [{"opcode": "metadata", "data": metadata}],
                *other_outputs)

        # Drop metadata on any port other than the selected input.
        else:
            outputs = [[]] * len(self.output_ports)
            return self.output_formatter(*outputs)

    def generate(self, *args, **kwargs):
        """ Generate output data when there are no input ports

        As there are no input ports to trigger the output data generation, this
        method is used instead.

        For implementations with no input ports this must be overloaded.

        Args:
            args, kwargs (optional, various): The input keyword arguments
                will be those set in the dictionary self.no_input_settings.

        Returns:
            Messages which are generated by the implementation.
        """
        raise NotImplementedError(
            "Implementations that do not have any input ports must define a "
            + "self.generate() method, which will generate the output when "
            + "called with any arguments set in self.no_input_settings.")

    def select_input(self, *inputs):
        """ Determine which input port should be advanced

        Will take an input argument for each input port the implementation has,
        where these arguments are the opcode of the next message on each input
        port. The order of inputs is as defined in ``self.input_ports``. The
        returned index is the port which has the opcode type to be passed next
        to the implementation. If there are multiple ports with the same next
        opcode, and one of these input ports with the same opcode is select (by
        returned index) all ports with the same opcode will be advanced by the
        next opcode method call.

        For implementations with more than one input port this must be
        overloaded.

        Args:
            inputs (str): String of the opcode name of the next message for
                each input port.

        Returns:
            An integer of the input port to be advanced, indexed from zero.
        """
        raise NotImplementedError(
            "Implementations with more than one input port must define a "
            + "self.select_input() method, which must take in the same number "
            + "of arguments as input ports where each is the opcode of the "
            + "next message to be read on that port. It must then return an "
            + "integer which is the index of the port type to be read.")
