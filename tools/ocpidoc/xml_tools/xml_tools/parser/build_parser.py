#!/usr/bin/env python3

# Class for parsing build configuration XML files.
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

import xml.etree.ElementTree as ET
import itertools
import copy

from . import base_parser
from . import worker_spec_parser
from . import component_spec_parser


class BuildParser(base_parser.BaseParser):
    """ Class for parsing <build> elements in XML files
    """

    def __init__(self, filename, include_filepaths=["."]):
        """ Initialize build configuration parser class.

        Handles parsing an XML file with a <build> root element.

        Args:
            filename (``string``): File path and name of the XML file to parse.
            include_filepaths (``list``): List of strings containing the
                filepaths to search for a file specified in an XML include
                statement.

        Returns:
            An initialized BuildParser instance.
        """
        super().__init__(filename=filename,
                         include_filepaths=include_filepaths,
                         force_lowercase=True)

        # Check root tag
        root_tag = "build"
        file_root_tag = self._get_root_tag()
        if not file_root_tag == root_tag:
            raise ValueError(
                f"Root XML tag must be {root_tag}, not {file_root_tag}")

    def get_dictionary(self, owd_file=None, ocs_file=None):
        """ Gets a dictionary containing the build information.

        When an OWD and/or an OCS file are specified the default values of any
        parameters not listed in the build file are included in the dictionary.

        Args:
            owd_file (``string``): File path and name of the OWD XML file to
                parse for default property values.
            ocs_file (``string``): File path and name of the OCS XML file to
                parse for default property values.

        Returns:
            A dictionary containing information from the build XML file.
            Parameters defined in the build XML outside of a configuration
            are listed in the "global_parameters" sub-dictionary, where the
            name of each parameter is the key, and the value is a list of
            string values. Configurations specified without the id attribute
            are specified as a list of dictionaries with the key
            "configuration_no_id". Each dictionary in the list uses the name
            of each parameter listed in the configuration as the key, and the
            value as a list of strings. Configurations specified with the id
            attribute are specified as a sub-dictionary with the key
            "configurations". Within this sub-dictionary the id is used as the
            key, and each value is a sub-dictionary uses the name of each
            parameter listed in the configuration as the key, and the
            value as a string. For example:

            .. code-block:: python

               {"global_parameters": {
                   "param_a": ["1"],
                   "param_b": ["10","11"]},
               "configurations_no_id": [
                   {"param_c": ["200"],
                    "param_a": ["10","20"]},
                   {"param_c": ["300","400","500"]}],
               "configurations": {
                   "0": {
                       "param_a": "20",
                       "param_b": "30",
                       "param_c": "60"},
                   "1": {
                       "param_a": "2",
                       "param_b": "3",
                       "param_c": "6"}}}
        """
        dictionary = {}
        dictionary["global_parameters"] = self._get_parameters(
            self._xml_root, force_list=True)
        dictionary["configurations_no_id"] = \
            self._get_configurations_with_no_id(self._xml_root)
        dictionary["configurations"] = self._get_configurations_with_id(
            self._xml_root)

        if owd_file:
            # If an OWD file is supplied then parse the OWD and OCS file
            worker = worker_spec_parser.WorkerSpecParser(
                filename=owd_file,
                include_filepaths=self._include_filepaths)
            component_dict = worker.get_combined_dictionary(ocs_file)
        elif ocs_file:
            # If just an OCS file is supplied, then only parse that
            component = component_spec_parser.ComponentSpecParser(
                filename=ocs_file,
                include_filepaths=self._include_filepaths)
            component_dict = component.get_dictionary()

        if owd_file or ocs_file:
            # Make sure all parameters are defined in config dictionary
            for name, property_ in component_dict["properties"].items():
                # Ignore non-parameter properties
                if not property_["access"]["parameter"]:
                    continue
                # Get parameter value
                if property_["value"] is not None:
                    val = property_["value"]
                elif property_["default"] is not None:
                    val = property_["default"]
                else:
                    # Ignore parameters with no value/default
                    continue

                # Add any extra parameters to global list
                if name not in dictionary["global_parameters"].keys():
                    dictionary["global_parameters"][name] = [val]

                # Step through each config and check it contains all parameters
                for config_id, config in dictionary["configurations"].items():
                    if name not in config.keys():
                        dictionary["configurations"][config_id][name] = val

        return dictionary

    def get_all_configurations(self, owd_file=None, ocs_file=None):
        """ Gets a list containing all build configurations.

        Gets a list of dictionaries each containing the value of all parameters
        for all build configurations based on the information provided in the
        build XML file. All duplicate configurations are removed. The order
        that the configurations are listed in will not necessarily match the
        order configurations are numbered by OpenCPI.

        When an OWD and/or an OCS file are specified the default values of any
        parameters not listed in the build file are included in the dictionary.

        Args:
            owd_file (``string``): File path and name of the OWD XML file to
                parse for default property values.
            ocs_file (``string``): File path and name of the OCS XML file to
                parse for default property values.

        Returns:
            A list of dictionaries containing all specified build
            configurations in the build XML file. Each dictionary in the list
            uses the name of each parameter listed in the configuration as the
            key, and the value as a string. When an OCS or OWD file is
            specified all parameters are included in each dictionary, even if
            the value is constant for all build configurations. If an OCS/OWD
            is not specified then only the parameters listed in the build XML
            will be included in each dictionary. For example:

            .. code-block:: python

               [{'param_a': '2', 'param_b': '10', 'param_c': '100'},
                {'param_a': '2', 'param_b': '10', 'param_c': '101'},
                {'param_a': '2', 'param_b': '11', 'param_c': '100'},
                {'param_a': '2', 'param_b': '11', 'param_c': '101'},
                {'param_a': '1', 'param_b': '10', 'param_c': '200'},
                {'param_a': '1', 'param_b': '10', 'param_c': '201'}]
        """
        config_list = []
        config_dict = self.get_dictionary(owd_file, ocs_file)

        # Add all named configs
        for config in config_dict["configurations"].values():
            config_list.append(config)

        # When there are no configs without ids
        if not config_dict["configurations_no_id"]:
            config_list += self._get_parameter_cross_product(
                config_dict["global_parameters"])
        else:
            # For all configs
            for config in config_dict["configurations_no_id"]:
                # Create a copy of the global parameters dictionary
                config_dict_copy = copy.deepcopy(
                    config_dict["global_parameters"])
                # For each config step through each parameter and override
                # the global parameter value.
                for parameter, val in config.items():
                    config_dict_copy[parameter] = val
                # Get the cross product of the global properties now they have
                # been overridden by the config
                config_list += self._get_parameter_cross_product(
                    config_dict_copy)

        # Remove any duplicate configs
        deduplicate_configs = []
        for config in config_list:
            if config not in deduplicate_configs:
                deduplicate_configs.append(config)

        return deduplicate_configs

    def _get_parameter_cross_product(self, dictionary):
        """ Gets all possible combinations of a dictionary of parameter values.

         Args:
            dictionary (``dict``): A dictionary where the keys are the names
                of the parameters, and the values are lists of parameter
                values.
        Returns:
            An list of dictionaries containing all unique combinations of the
            parameter values specified in the dictionary. Each dictionary in
            the list uses the name of each parameter as the key, and the value
            as a string. For example:

            .. code-block:: python

               [{'param_a': '2', 'param_b': '10', 'param_c': '100'},
                {'param_a': '2', 'param_b': '10', 'param_c': '101'},
                {'param_a': '2', 'param_b': '11', 'param_c': '100'},
                {'param_a': '2', 'param_b': '11', 'param_c': '101'},
                {'param_a': '1', 'param_b': '10', 'param_c': '200'},
                {'param_a': '1', 'param_b': '10', 'param_c': '201'}]
        """
        config_list = []
        # Get list of all parameter names
        parameters = list(dictionary.keys())
        # Get iterator for all parameter values
        values = dictionary.values()

        # Calculate the cross product of all combinations of parameter
        # values.
        for config in itertools.product(*values):
            # For each combination of parameter values make a dictionary
            # of all the parameter values
            dictionary = {}
            for parameter_index, value in enumerate(config):
                dictionary[parameters[parameter_index]] = value
            config_list.append(dictionary)

        return config_list

    def _get_parameters(self, xml_element, force_list=True):
        """ Gets a dictionary containing all parameter values.

        Only gets <parameter> values that are direct children of the
        specified xml_element.

         Args:
            xml_element (``xml.etree.ElementTree.Element``): Object containing
                an XML element which contains <parameter> sub-elements.
            force_list (``bool``): When true, values read from a value or
                valuefile attribute are stored as a string in a list of length
                one. When false, value and valuefile attribute values are
                stored directly as a string.
        Returns:
            A dictionary where the name of each parameter is the key, and the
            value is typically a list of strings (unless force_list=False and
            the parameter value is specified by a value or valuefile
            attribute).
            For example:
            ``{'param_a': '2', 'param_b': '10', 'param_c': '100'}``
        """
        parameter_dict = {}
        for parameter in xml_element.findall("parameter"):
            if "name" in parameter.attrib.keys():
                if "value" in parameter.attrib.keys():
                    if force_list:
                        parameter_dict[parameter.attrib["name"]] =\
                            [parameter.attrib["value"]]
                    else:
                        parameter_dict[parameter.attrib["name"]] =\
                            parameter.attrib["value"]
                elif "values" in parameter.attrib.keys():
                    parameter_dict[parameter.attrib["name"]] =\
                        self._get_list_attribute(parameter, "values")
                elif "valuefile" in parameter.attrib.keys():
                    # Support for valuefile to be added
                    raise NotImplementedError(
                        "Support for reading valuefile not yet implemented")
                elif "valuesfile" in parameter.attrib.keys():
                    # Support for valuesfile to be added
                    raise NotImplementedError(
                        "Support for reading valuesfile not yet implemented")

        return parameter_dict

    def _get_configurations_with_no_id(self, xml_element):
        """ Gets a list of dictionary containing configurations with no ID.

        Args:
            xml_element (``xml.etree.ElementTree.Element``): Object containing
                an XML element which contains <configuration> sub-elements.

        Returns:
            A list of dictionaries where each dictionary in the list uses the
            name of each parameter listed in the configuration as the key, and
            the value as a list of strings. For example:

            .. code-block:: python

               [{"param_c": ["200"]},
                   "param_d": ["10","20"]},
                {"param_c": ["300","400","500"]}]
        """
        configuration_list = []
        for config in xml_element.findall("configuration"):
            if "id" in config.attrib.keys():
                continue
            config_parameters = self._get_parameters(config, force_list=True)
            if config_parameters:
                configuration_list.append(config_parameters)

        return configuration_list

    def _get_configurations_with_id(self, xml_element):
        """ Gets a dictionary containing configurations with an ID attribute.

        Args:
            xml_element (``xml.etree.ElementTree.Element``): Object containing
                an XML element which contains <configuration> sub-elements.

        Returns:
            A dictionary where the ID of each configuration is the key and the
            value is a dictionary. Within each configuration dictionary the key
            is the name of each parameter listed in the configuration, and the
            value is as a string containing the parameter value for that
            configuration. For example:

            .. code-block:: python

               {"0": {
                       "param_a": "20",
                       "param_b": "30",
                       "param_c": "60"},
                "1": {
                       "param_a": "2",
                       "param_b": "3",
                       "param_c": "6"}}
        """
        configuration_dict = {}
        for config in xml_element.findall("configuration"):
            if "id" not in config.attrib.keys():
                continue
            config_parameters = self._get_parameters(config, force_list=False)
            if config_parameters:
                configuration_dict[config.attrib["id"]] = config_parameters

        return configuration_dict
