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
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import os
import hashlib
# below line is for testing only
import xml.etree.ElementTree as ET
from _opencpi.assets.abstract2 import *
from _opencpi.assets.abstract2 import AssetBase

comp_rst_template = """
.. {{asset.name}} documentation

.. Skeleton comment (to be deleted): Alternative names should be listed as
   keywords. If none are to be included delete the meta directive.

.. meta::
   :keywords: skeleton example


.. _{{asset.name}}:


SKELETON NAME (``{{asset.name}}``)
=================================
Skeleton outline: Single line description.

Function
--------
Skeleton outline: The functionality of the component: how it should produce outputs and volatile property values based on inputs and parameter/initial/writable property values (not **how** it is implemented, as that belongs in worker documentation).

The mathematical representation of the component function is given in :eq:`{{asset.name}}-equation`.

.. math::
   :label: {{asset.name}}-equation

   y[n] = \\alpha * x[n]


In :eq:`{{asset.name}}-equation`:

 * :math:`x[n]` is the input values.

 * :math:`y[n]` is the output values.

 * Skeleton, etc.,

A block diagram representation of the component function is given in :numref:`{{asset.name}}-diagram`.

.. _{{asset.name}}-diagram:

.. figure:: {{asset.name}}.svg
   :alt: Skeleton alternative text.
   :align: center

   Caption text.

Interface
---------
.. literalinclude:: ../specs/{{asset.name}}-spec.xml
   :language: xml

Opcode Handling
~~~~~~~~~~~~~~~
Skeleton outline: Description of how the non-stream opcodes are handled.

Properties
~~~~~~~~~~
.. ocpi_documentation_properties::

   property_name: Skeleton outline: List any additional text for properties, which will be included in addition to the description field in the component specification XML.

Ports
~~~~~
.. ocpi_documentation_ports::

   input: Primary input samples port.
   output: Primary output samples port.

Implementations
---------------
.. ocpi_documentation_implementations:: ../{{asset.name}}.hdl ../{{asset.name}}.rcc

Example Application
-------------------
.. literalinclude:: example_app.xml
   :language: xml

Dependencies
------------
The dependencies to other elements in OpenCPI are:

 * Skeleton outline: List primitives or other files within OpenCPI that are used (no need to list protocols).

There is also a dependency on:

 * ``ieee.std_logic_1164``

 * ``ieee.numeric_std``

 * Skeleton outline: Any other standard C++ or HDL packages.

Limitations
-----------
Limitations of ``{{asset.name}}`` are:

 * Skeleton outline: List any limitations, or state "None." if there are none.

Testing
-------
.. ocpi_documentation_test_platforms::

.. Removed ocpi_documentation_test_result_summary directive until it is functional
"""  # noqa: E501

comp_test_rst_template = """
.. {{asset.name}} test detail


:orphan:


``{{asset.name}}`` Test Detail
=============================
.. ocpi_documentation_test_detail::

"""

comp_example_app_rst_template = """
<?xml version="1.0"?>
<application done="file_write">
  <instance component="ocpi.core.file_read" connect="{{asset.name}}">
    <property name="filename" value="input.bin"/>
  </instance>
  <instance component="{{package_id}}.{{library_name}}.{{asset.name}}" connect="file_write">
    <!-- Skeleton application outline, set properties here. Or change this
         example application to do something more real-world appropriate if
         file-read, then component, then file-write is too artifical to be a
         useful example. -->
  </instance>
  <instance component="ocpi.core.file_write">
    <property name="filename" value="output.bin"/>
  </instance>
</application>
"""  # noqa: E501

comp_spec_rst_template = """
.. {{asset.name}} documentation

.. Skeleton comment (to be deleted): Alternative names should be listed as
   keywords. If none are to be included delete the meta directive.

.. meta::
   :keywords: skeleton example


.. _{{asset.name}}:


SKELETON NAME (``{{asset.name}}``)
=================================
Skeleton outline: Single line description.

Design
------
Skeleton outline: Functional description of **what** the component achieves (not **how** it is implemented, as that belongs in primitive documentation).

The mathematical representation of the implementation is given in :eq:`{{asset.name}}-equation`.

.. math::
   :label: {{asset.name}}-equation

   y[n] = \\alpha * x[n]


In :eq:`{{asset.name}}-equation`:

 * :math:`x[n]` is the input values.

 * :math:`y[n]` is the output values.

 * Skeleton, etc.,

A block diagram representation of the implementation is given in :numref:`{{asset.name}}-diagram`.

.. _{{asset.name}}-diagram:

.. figure:: {{asset.name}}.svg
   :alt: Skeleton alternative text.
   :align: center

   Caption text.

Interface
---------
.. literalinclude:: ../specs/{{asset.name}}-spec.xml
   :language: xml

Opcode handling
~~~~~~~~~~~~~~~
Skeleton outline: Description of how the non-stream opcodes are handled.

Properties
~~~~~~~~~~
.. ocpi_documentation_properties::

   property_name: Skeleton outline: List any additional text for properties, which will be included in addition to the description field in the component specification XML.

Ports
~~~~~
.. ocpi_documentation_ports::

   input: Primary input samples port.
   output: Primary output samples port.

Implementations
---------------
.. ocpi_documentation_implementations:: ../{{asset.name}}.hdl ../{{asset.name}}.rcc

Example Application
-------------------
.. literalinclude:: example_app.xml
   :language: xml

Dependencies
------------
The dependencies to other elements in OpenCPI are:

 * Skeleton outline: List primitives or other files within OpenCPI that are used (no need to list protocols).

There is also a dependency on:

 * ``ieee.std_logic_1164``

 * ``ieee.numeric_std``

 * Skeleton outline: Any other standard C++ or HDL packages.

Limitations
-----------
Limitations of ``{{asset.name}}`` are:

 * Skeleton outline: List any limitations, or state "None." if there are none.

Testing
-------
.. ocpi_documentation_test_platforms::

.. ocpi_documentation_test_result_summary::
"""  # noqa: E501

# Protocol templates below:
prot_spec_rst_template = """.. {{asset.name}} documentation


.. _{{asset.name}}-protocol:


SKELETON NAME Protocol (``{{asset.name}}``)
===========================================
Skeleton outline: Purpose and expected use cases of the protocol.

Protocol
--------
.. literalinclude:: {{asset.name}}-prot.xml
   :language: xml

"""


def create_templates(name, spec_create=False):
    comp_templates = {}
    if spec_create:
        comp_templates[name + '-spec.xml'] = g_asset_template
        comp_templates[name + '-spec.rst'] = comp_spec_rst_template
    else:
        comp_templates[name + '-comp.xml'] = g_asset_template
        comp_templates[name + '-comp.rst'] = comp_rst_template
        comp_templates[name + '-test.rst'] = comp_test_rst_template
        comp_templates['example_app.xml'] = comp_example_app_rst_template
    return comp_templates


class OperationArgumentMember(AttributeBase):

    def __init__(self, elem):
        AttributeBase.__init__(self, elem)

    def get_root_tags(self):
        # TODO replace get_root_tags() with self.root_tags
        return ['Member']

    def get_attr_infos(self):
        ret = []
        for key in ['Name', 'Type']:
            ret.append(AttributeInfo(key))
        return ret


class OperationArgument(AttributeBase):
    """ Component Development Guide section 5.1.3.2 """

    def __init__(self, elem):
        self.array_length = -1
        self.sequence_length = -1
        self.members = []
        AttributeBase.__init__(self, elem)
        self.parse(elem)

    def get_root_tags(self):
        # TODO replace get_root_tags() with self.root_tags
        return ['Argument']

    def get_attr_infos(self):
        ret = []
        for key in ['Name', 'Type']:
            ret.append(AttributeInfo(key))
        for key in ['ArrayLength', 'SequenceLength']:
            ret.append(AttributeInfo(key, is_list=True))
        return ret

    def parse(self, elem):
        AttributeBase.parse(self, elem)
        for child in elem.iter():
            try:
                member = OperationArgumentMember(child)
                self.members.append(member)
            except InvalidAttributeError:
                pass


class Operation(AttributeBase):
    """ Component Development Guide section 5.1.3 """

    def __init__(self, elem):
        self.name = ''
        self.arguments = []
        AttributeBase.__init__(self, elem)
        self.parse(elem)

    def get_root_tags(self):
        # TODO replace get_root_tags() with self.root_tags
        return ['Operation']

    def get_attr_infos(self):
        ret = []
        ret.append(AttributeInfo('Name'))
        return ret

    def parse(self, elem):
        AttributeBase.parse(self, elem)
        for child in elem.iter():
            try:
                argument = OperationArgument(child)
                self.arguments.append(argument)
            except InvalidAttributeError:
                pass


class Protocol(AssetBase):
    """ Reference Component Development Guide section 5. A Protocol is
        represented by a xml file (OPS) and knows nothing about the project it
        is in or its package ID. """

    valid_locations = ['specs']

    def __init__(self, xml_abs_path, enable_path_existence_check=True,
                 cli_dict=None):
        self.root_tags = ['Protocol']
        AssetBase.__init__(self, xml_abs_path, enable_path_existence_check)
        self.raise_if_invalid_location()
        self.operations = []
        self.parse(cli_dict, enable_path_existence_check)

    def get_root_tags(self):
        # TODO replace get_root_tags() with self.root_tags
        return ['Protocol']

    def parse(self, cli_dict, enable_path_existence_check):
        AttributeBase.parse(self, cli_dict)
        if enable_path_existence_check:
            for elem in self.get_parsed().iter():
                for key, value in elem.attrib.items():
                    if key.lower() == 'href':
                        href_abs_path = self.abs_path.rsplit('/', 1)[0] + '/'
                        href_abs_path += value
                        href_protocol = Protocol(href_abs_path)
                        self.operations.extend(href_protocol.operations)
                try:
                    operation = Operation(elem)
                    self.operations.append(operation)
                except InvalidAttributeError:
                    pass

    def get_templates(self):
        templates = {}
        templates[self.name + '-prot.xml'] = g_asset_template
        templates[self.name + '-prot.rst'] = prot_spec_rst_template
        return templates

    def create(self):
        """ create self (a protocol) """
        specs_dir_abs_path = '/'.join(self.abs_path.split('/')[:-1])
        prot_templates = self.get_templates()
        AssetBase.create_files(self, prot_templates, specs_dir_abs_path)

    def get_type(self):
        return 'protocol'


class Component(AssetBase):
    """ Reference Component Development Guide section 6. A Component is
        represented by a xml file (OCS) and knows nothing about the project it
        is in or its package ID. """

    def __init__(self, xml_abs_path, enable_path_existence_check=True,
                 cli_dict=None):
        """ xml_abs_path is None for ComponentSpec embedded in OWD """
        self.root_tags = ['ComponentSpec']
        AssetBase.__init__(self, xml_abs_path, enable_path_existence_check)
        Logger().debug('parsing ' + self.get_xml_abs_path())
        self.parse(cli_dict)

    def create(self, package_id, spec_create, project_path):
        library_name = self.abs_path.split('/')[-3]
        if spec_create:
            spec_path = project_path + '/specs'
            spec_templates = create_templates(self.name, spec_create)
            AssetBase.create_files(self, spec_templates, spec_path,
                                   package_id, library_name)
        else:
            component_path = self.get_dir_abs_path()
            comp_templates = create_templates(self.name)
            AssetBase.create_files(self, comp_templates, component_path,
                                   package_id, library_name)

    def get_attr_infos(self):
        ret = []
        ret.append(AttributeInfo('Name'))
        ret.append(AttributeInfo('NoControl',
                                 cli=('-n', '--no-control'),
                                 is_bool=True))
        return ret

    def parse(self, cli_dict=None):
        AssetBase.parse(self, cli_dict)
        if self.attrs['Name'] != '':
            self.name = self.attrs['Name']
        #    for elem in AttributeBase.get_parsed(self.abs_path).iter():
        #        if elem.tag.lower() == self.get_root().lower():
        #            pass
        #        elif elem.tag.lower() == 'property':
        #            pass
        #        elif elem.tag.lower() == 'properties':
        #            pass
        #        elif elem.tag.lower() == 'description':
        #            pass
        #        elif elem.tag.lower() == 'member':
        #            pass
        #        elif elem.tag.lower() == 'port':
        #            pass
        #        elif elem.tag.lower() == 'protocol':
        #            pass
        #        elif elem.tag.lower() == 'operation':
        #            pass
        #        elif elem.tag.lower() == 'argument':
        #            pass
        #        else:
        #            # start pre-2.0 opencpi
        #            if elem.tag.lower() == 'datainterfacespec':
        #                pass
        #            elif elem.tag.lower() == 'protocolsummary':
        #                pass
        #            # end pre-2.0 opencpi
        #            else:
        #                tag = elem.tag
        #                self.throw_invalid_element_error(self.abs_path, tag)

    def get_type(self):
        return 'component'


# TODO iherit from, and consolidate functionality from, AttributeBase
class Property(AttributeBase):
    """ CDG Development Guide section 6.3 """

    def __init__(self, elem):
        AttributeBase.__init__(self)

    def get_root_tags(self):
        # TODO replace get_root_tags() with self.root_tags
        return ['Property']

    def get_attr_infos(self):
        ret = []
        ret.append(AttributeInfo('Name'))  # CDG section 6.3.1
        ret.append(AttributeInfo('Value'))  # CDG section 6.4.11
        return ret


def test_Property(ret):
    fs = TemporaryFilesystem()
    for test in range(6):
        passed = True
        try:
            xml_abs_path = fs.abs_path + '/' + 'foo.xml'
            os.system('mkdir -p ' + fs.abs_path)
            ff = open(xml_abs_path, 'w')
            ff.write('<Foo>\n')
            ff.write('  <Property name=\'myprop\' value=\'abc\'/>\n')
            ff.write('</Foo>\n')
            ff.close()
            tree = ET.parse(xml_abs_path)
            for elem in tree.iter():
                if elem == 'Property':
                    uut = Property(elem)
                    if Environment().ocpi_log_level >= 10:
                        print(uut.__dict__.keys())
                        os.system('cat ' + xml_abs_path)
                    if test == 0:
                        passed = uut.attrs['Name'] == 'myprop'
                    if test == 1:
                        passed = uut.attrs['Value'] == 'abc'
                    break
        except InvalidAssetError:
            passed = False
        if test == 0:
            log_pass_fail('testing Property value', passed)
        if test == 1:
            log_pass_fail('testing Property name', passed)
        if passed is False:
            ret = False
    fs = TemporaryFilesystem()
    file_name = fs.abs_path + '/' + 'tmp.xml'
    prop_elems = 3
    prop_names = [("prop" + str(idx) + "_name") for idx in range(prop_elems)]
    prop_values = [("prop" + str(idx) + "_value") for idx in range(prop_elems)]
    prop_dict = {key: value for key, value in zip(prop_names, prop_values)}

    def create_xml(prop_dict):
        root = ET.Element("instance", elem1="elem1", elem2="elem2")
        for key, value in prop_dict.items():
            ET.SubElement(root, "property", name=key, value=value)
        # Create XML tree
        tree = ET.ElementTree(root)
        # Write the XML tree to a file with indentation
        tree.write(file_name, xml_declaration=True, method="xml")

    def test___init__(ret):
        passed = True
        names = []
        values = []
        tree = ET.parse(file_name)
        for elem in tree.iter():
            if elem == 'Property':
                try:
                    uut = Property(elem)
                    values.append(uut.attrs['Value'])
                    names.append(uut.attrs['Name'])
                except InvalidAttributeError:
                    pass
        for name in names:
            if name in prop_names:
                prop_names.remove(name)
            else:
                passed = False
        for value in values:
            if value in prop_values:
                prop_values.remove(value)
            else:
                passed = False
        if len(prop_values) != 0 or len(prop_names) != 0:
            passed = False
        log_pass_fail('testing Property __init__()', passed)
        if passed is False:
            ret = False
        return ret
    # TODO investigate test coverage of below 4 lines
    # create_xml(prop_dict)
    # passed = test___init__(ret)
    # if passed is False:
    #     ret = False
    return ret


def test_Component(ret):
    ret = test_Property(ret)
    fs = TemporaryFilesystem()
    for test in [0, 1]:
        passed = True
        try:
            dir_abs_path = fs.abs_path + '/' + 'components/specs'
            os.system('mkdir -p ' + dir_abs_path)
            xml_abs_path = dir_abs_path + '/' + 'component.xml'
            ff = open(xml_abs_path, 'w')
            ff.write('<ComponentSpec/>\n')
            ff.close()
            uut = Component(xml_abs_path)
            if Environment().ocpi_log_level >= 10:
                print(uut.__dict__.keys())
                os.system('cat ' + xml_abs_path)
            if test == 0:
                passed = uut.abs_path == xml_abs_path
            if test == 1:
                passed = uut.name == 'component'
        except InvalidAssetError:
            passed = False
        if test == 0:
            log_pass_fail('testing Component abs_path', passed)
        if test == 1:
            log_pass_fail('testing Component name', passed)
        if passed is False:
            ret = False
    return ret


def test_Component_create(ret):
    # TODO: Implement testing for CLI args nocontrol, createtest, project.
    fs = TemporaryFilesystem()
    test_name = 'test_Component_create: '
    name = 'cmp1'
    package_id = 'ocpi.foo'
    project_path = fs.abs_path + '/foo'
    dir_path = project_path + '/components/' + name + '.comp'
    xml_abs_path = dir_path + '/' + name + '-comp.xml'
    try:
        Component(
            xml_abs_path, False, None
        ).create(package_id, False, project_path)
        passed = True
    except Exception as e:
        Logger().debug(test_name + str(e))
    # Test for file existence
    comp_files = ['cmp1-comp.xml', 'cmp1-comp.rst', 'example_app.xml',
                  'cmp1-test.rst']
    for comp_file in comp_files:
        path = dir_path + '/' + comp_file
        if not os.path.exists(path):
            passed = False
    # Test for file integrity
    msg = 'invalid expected md5sum for file: '
    comp_xml = dir_path + '/' + comp_files[0]
    comp_xml_md5 = hashlib.md5(open(comp_xml, 'rb').read()).hexdigest()
    if comp_xml_md5 != '40e1d7cd6cd5242615d28725fce1c2e3':
        passed = False
        Logger().error(test_name + str(msg + xml_abs_path))
    comp_rst = dir_path + '/' + comp_files[1]
    comp_rst_md5 = hashlib.md5(open(comp_rst, 'rb').read()).hexdigest()
    if comp_rst_md5 != '84fc0cece1ea3c7e7c8bc78c0202e50a':
        passed = False
        Logger().error(test_name + str(msg + comp_rst))
    example_app = dir_path + '/' + comp_files[2]
    example_app_md5 = hashlib.md5(open(example_app, 'rb').read()).hexdigest()
    if example_app_md5 != 'fa3bb09634de1f96eda4e647cc698d12':
        passed = False
        Logger().error(test_name + str(msg + example_app))
    comp_test_rst = dir_path + '/' + comp_files[3]
    comp_test_md5 = hashlib.md5(open(comp_test_rst, 'rb').read()).hexdigest()
    if comp_test_md5 != '048f66d77e6625d5cb848140c5cc552e':
        passed = False
        Logger().error(test_name + str(msg + comp_test_rst))
    log_pass_fail('testing Component create()', passed)
    if passed is False:
        ret = False
    return ret
