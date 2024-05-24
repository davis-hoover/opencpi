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


import xml.etree.ElementTree as ET
import os
import sys
# if os.path.isfile(os.getcwd() + '/platform.py'):
#     # collision with uuid's 'import platform' and this directory's platform.py
#     raise Exception('do not run this from the assets directory!')
import uuid
import glob
import jinja2


# TODO make a class member, probably ComponentLibrary or Project class
g_libraries_mk = False
g_asset_template = """<?xml version="1.0"?>\n<{{asset.root_tags[0]}}{% for key,val in asset.attrs.items() %}{% if val != '' and val != [] %}\n
    {{key}}=\'{{val}}\'{% endif %}{% endfor %}/>\n\n"""
global_dependency_tree = dict()


def log_pass_fail(msg, passed):
    spaces = ''
    for count in range(60-len(msg)):
        spaces += ' '
    if passed:
        msg += spaces + '\033[92mPASS\033[0m'
    else:
        msg += spaces + '\033[91mFAIL\033[0m'
    print(msg)


# TODO consolidate with AttributeBase method of the same name
def get_xml_val_list(val):
    return ' '.join(val.replace('\n', '').split()).split(' ')


# TODO probably a single authoritative xml is needed to parse this from....
def get_hdl_target(hdl_platform):
    # TODO parse tools/include/hdl/hdl-targets.xml, hdl/platforms/ml605/ml605.mk instead of below code
    ret = hdl_platform
    if hdl_platform == 'zed':
        ret = 'zynq'
    elif hdl_platform == 'zcu106':
        ret = 'zynq_ultra'
    elif hdl_platform == 'zed_ise':
        ret = 'zynq_ise'
    elif hdl_platform == 'zcu104':
        ret = 'zynq_ultra'
    elif hdl_platform == 'zed_ether':
        ret = 'zynq'
    elif hdl_platform == 'ml605':
        ret = 'virtex6'
    elif hdl_platform == 'alst4x':
        ret = 'stratix'
    elif hdl_platform == 'alst4':
        ret = 'stratix'
    elif hdl_platform == 'matchstiq_z1':
        ret = 'zynq'
    elif hdl_platform == 'e31x':
        ret = 'zynq'
    elif hdl_platform == 'zrf8_48dr':
        ret = 'zynq_ultra'
    return ret


# TODO properly separate into extensible tool
def get_worker_build_output_extension(hdl_platform):
    ret = 'edf'
    target = get_hdl_target(hdl_platform)
    if target.startswith('virtex'):
        ret = 'qsf'
    elif target.startswith('stratix'):
        ret = 'qsf'
    return ret

# TODO properly separate into extensible tool
def get_assembly_build_output_extension(hdl_platform):
    ret = 'bitz'
    target = get_hdl_target(hdl_platform)
    if target.startswith('virtex'):
        ret = 'sof'
    elif target.startswith('stratix'):
        ret = 'sof'
    return ret


# TODO move to Project, or perhaps ProjectRegistry, class
def raise_not_found_in_projects(msg, name):
    raise Exception(msg + ' ' + name + ' not found in any registered project')


class InvalidAssetError(Exception):
    pass


class InvalidAttributeError(Exception):
    pass


class Environment():
    """ Reference OpenCPI User Guide section 5 """

    def __init__(self):
        ocpi_log_level = os.environ.get('OCPI_LOG_LEVEL')
        if ocpi_log_level == '':
            ocpi_log_level = 0
        if ocpi_log_level is None:
            ocpi_log_level = 0
        self.ocpi_log_level = int(ocpi_log_level)


class Logger(Environment):

    def __init__(self):
        Environment.__init__(self)

    def get_log_str(self, level):
        ret = 'OCPI('
        if level < 10:
            ret += ' '
        # TODO put time in string below
        ret += str(level) + ':       ): '
        return ret

    def log(self, level, msg, pre=''):
        if level >= 9:
            pre = '\033[96m'
        if self.ocpi_log_level >= level:
            _str = pre + self.get_log_str(level) + msg + '\033[0m'
            print(_str, file=sys.stderr)

    def info(self, msg):
        if self.ocpi_log_level >= 7:
            self.log(7, 'INFO:  ' + msg)

    def warn(self, msg):
        self.log(0, 'WARN:  ' + msg, '\033[93m')

    def debug(self, msg):
        self.log(10, 'DEBUG: ' + msg, '\033[96m')

    def error(self, msg):
        self.log(0, 'ERROR: ' + msg, '\033[91m')


class System():
    def __init__(self, cmd):
        Logger().debug('making system call: ' + cmd)
        if os.system(cmd):
            raise Exception('cmd failed: ' + cmd)


class TemporaryFilesystem():
    """ A convenient directory for doing temporary work. Directory is deleted when
        this object goes out of scope. """

    def __init__(self):
        # uuid avoids collisions during simultaneous executions of ocpidev2
        self.abs_path = '/tmp/ocpidev2.' + str(uuid.uuid4())
        os.system('mkdir -p ' + self.abs_path)

    def __del__(self):
        os.system('rm -rf ' + self.abs_path)


class DependencyTree():
    def __init__(self):
        self.dependents = []


class GNUMakeTarget():

    def __init__(self, string, phony = False):
        self.string = string
        self.phony = phony

    def __str__(self):
        return self.string


class GNUMakeRule():
    """ https://www.gnu.org/software/make/manual/html_node/Rules.html """

    def __init__(self):
        self.targets = []
        self.prerequisites = []
        self.recipe = ""

    def __str__(self):
        ret = ''
        first = True
        for target in self.targets:
          if not first:
            ret += ' '
          ret += target.string
        ret += ': '
        ret += ' '.join(self.prerequisites) + '\n'
        if self.recipe is not None:
            ret += '\t' + self.recipe
        return ret


class GNUMakefile():
    """ https://www.gnu.org/software/make/manual/make.html#Makefiles """

    def __init__(self, abs_path):
        self.abs_path = abs_path
        self.variables = dict()
        self.rules = dict()
        if abs_path is not None:
            self.parse(open(abs_path).readlines())

    def parse_string(self, string, define=False, endef=False):
        (expanded, define, endef) = self.expand_immediate(
                string, define, endef)
        if ('=' in expanded) or (define is not None):
            self.internalize_operation(expanded, define)
        return (expanded, define, endef)

    def parse(self, file_lines):
        """ https://www.gnu.org/software/make/manual/html_node/Parsing-Makefiles.html # nopep8
        """
        file_line_idx = 0
        done = False
        define = None
        endef = False
        while file_line_idx < len(file_lines):
            (logical_line, file_line_idx) = self.read_file_line(
                    file_lines, file_line_idx)
            logical_line = logical_line.split('#')[0]
            if len(logical_line) == 0:
                continue
            while (len(logical_line) > 0) and (logical_line[0] == '\t') and \
                    (file_line_idx < len(file_lines)):
                (logical_line, file_line_idx) = self.read_file_line(
                        file_lines, file_line_idx)
            (expanded, define, endef) = self.parse_string(
                    logical_line, define, endef)

    def read_file_line(self, file_lines, file_line_idx):
        """ https://www.gnu.org/software/make/manual/html_node/Splitting-Lines.html # nopep8
        """
        logical_line = ''
        line_complete = False
        while not line_complete:
            file_line = file_lines[file_line_idx]
            # Logger().debug('file read line: ' + file_line[:-1])
            file_line_idx = file_line_idx + 1
            tmp = file_line.replace('\n', '')
            line_complete = True
            if (len(tmp) > 0) and (tmp[-1] == '\\'):
                line_complete = False
                tmp = tmp[:-1]
            logical_line += tmp
        return (logical_line, file_line_idx)

    def expand_immediate(self, string, define, endef):
        """ https://www.gnu.org/software/make/manual/html_node/Reading-Makefiles.html # nopep8
        """
        if endef:
            define = None
            endef = False
        lhs_is_var_name = False
        lhs_is_target = False
        is_subst_ref = False
        setting_variable = False
        rhs = False
        expanded = ''
        if len(string) > 0:
            while (len(string) > 0) and (string[0] == ' '):
                string = string[1:]
            if string[0:7] == 'define ':
                define = string[7:]
            if string[0:5] == 'endef':
                define = False
                endef = True
        idx = 0
        state = 0
        reference_or_function = ''
        indent = 0
        global g_libraries_mk
        if string[0:7] == 'include':
            if string.strip().endswith('libraries.mk'):
                g_libraries_mk = True
        while (idx < len(string)) and (not define) and (not endef):
            if string[idx] == '#':
                break
            # print(expanded)
            # print(reference_or_function)
            # print(str(state))
            if state == 0:
                # either advance to reference/function handling or
                # parse target/var name
                if string[idx] == '$':
                    reference_or_function = ''
                    state = 2
                elif string[idx] == ' ':
                    lhs_is_var_name = True
                    if rhs:
                        expanded += string[idx]
                elif string[idx] == '+':
                    expanded += string[idx]
                    lhs_is_var_name = True
                elif string[idx] == ':':
                    lhs_is_target = True
                    state = 1
                elif string[idx] == '=':
                    expanded += string[idx]
                    lhs_is_var_name = not lhs_is_target
                    rhs = True
                else:
                    # target or var name which does not need expansion
                    expanded += string[idx]
            elif state == 1:
                # finalize lhs/rhs separation
                if string[idx] == '=':
                    expanded += string[idx]
                    lhs_is_var_name = not lhs_is_target
                rhs = True
                state = 0
            elif state == 2:
                # lhs - handle reference/function
                if (string[idx] == '('):
                    if indent != 0:
                        reference_or_function += string[idx]
                    indent += 1
                elif (string[idx] == ':'):
                    reference_or_function += string[idx]
                    is_subst_ref = True
                elif (string[idx] == ' '):
                    reference_or_function += string[idx]
                elif (string[idx] == ')'):
                    indent -= 1
                    if indent == 0:
                        if reference_or_function in self.variables.keys():
                            expanded += self.expand_variable_reference(
                                    reference_or_function)
                        elif is_subst_ref and (
                                reference_or_function.split(':')[0] in
                                self.variables.keys()):
                            expanded += self.expand_variable_reference(
                                    reference_or_function)
                        elif (reference_or_function[0:9] == 'wildcard ') or \
                                (reference_or_function[0:8] == 'foreach ') or \
                                (reference_or_function[0:3] == 'or ') or \
                                (reference_or_function[0:4] == 'and ') or \
                                (reference_or_function[0:9] == 'patsubst ') \
                                or \
                                (reference_or_function[0:5] == 'info ') or \
                                (reference_or_function[0:5] == 'eval ') or \
                                (reference_or_function[0:5] == 'call '):
                            expanded += self.invoke_function(
                                    reference_or_function)
                        is_subst_ref = False
                        state = 0
                    else:
                        reference_or_function += string[idx]
                else:
                    reference_or_function += string[idx]
            idx += 1
        expanded2 = ''
        last_char = ''
        first = True
        for char in expanded:
            if first:
                first = False
                expanded2 += char
            elif not (last_char == ' ' and char == ' '):
                expanded2 += char
            last_char = char
        # print('** expanded2 ' + expanded2)
        return (expanded2, define, endef)

    def invoke_wildcard(self, string):
        """ https://www.gnu.org/software/make/manual/html_node/Wildcard-Function.html # nopep8
        """
        # Logger().debug('    expand_' + string)
        pattern = string[9:]
        path = self.abs_path[:self.abs_path.rfind('/')+1]
        filepaths = glob.glob(path + pattern)
        tmp = []
        for filepath in filepaths:
            tmp.append(filepath.replace(path, ''))
        return ' '.join(tmp)

    def invoke_foreach(self, string):
        """ https://www.gnu.org/software/make/manual/html_node/Foreach-Function.html # nopep8
        """
        # Logger().debug('    expand_' + string)
        string = string[8:]
        idx = string.find(',')
        var = string[0:idx]
        string = string[idx+1:]
        indent = 0
        state = 0
        _list = ''
        text = ''
        for char in string:
            if state < 3:
                _list += char
            else:
                text += char
            if (state == 0) and (char == ','):
                state = 3
                _list = _list[:-1]
            elif (state == 0) and (char == '$'):
                state = 1
            elif (state == 1) and (char == '('):
                state = 2
                indent += 1
            elif state == 2:
                if char == '(':
                    indent += 1
                elif char == ')':
                    indent -= 1
                    if indent == 0:
                        state = 0
        var_dict = dict()
        result = []
        # Logger().debug('    invoke_foreach _list ' + _list)
        while (_list[0] == ' '):
            _list = _list[1:]
        if _list[0:2] == '$(':
            (_list, d1, d2) = self.parse_string(_list)
        for entry in _list.split(' '):
            tmp = ' '.join(text.replace('$' + var, entry).split())
            if tmp[0:2] == '$(':
                (tmp, d1, d2) = self.parse_string(tmp)
            # result.append(' '.join(tmp).split())
            result.append(tmp)
        return ' '.join(result)

    def invoke_conditional_function(self, string):
        """ https://www.gnu.org/software/make/manual/html_node/Conditional-Functions.html # nopep8
        """
        # Logger().debug('    expand_' + string)
        if string[0:3] == 'or ':
            for condition in string[3:].split(','):
                if condition != '':
                    if condition[0:2] == '$(':
                        (condition, d1, d2) = self.parse_string(condition)
                    string = condition
        elif string[0:4] == 'and ':
            string = string[4:]
            idx = 0
            state = 0
            indent = 0
            string_to_expand = ''
            ret = ''
            while idx < len(string):
                if (string[idx] == '('):
                    indent += 1
                elif (string[idx] == ')'):
                    indent -= 1
                if (indent == 0) and (string[idx] == ','):
                    (expanded, d1, d2) = self.parse_string(string_to_expand)
                    ret += expanded
                    string_to_expand = ''
                    if expanded == '':
                        break
                else:
                    string_to_expand += string[idx]
                idx += 1
            string = ret
        return string

    def invoke_string_substitution_function(self, string):
        """ https://www.gnu.org/software/make/manual/html_node/Text-Functions.html # nopep8
        """
        # _str = string
        # Logger().debug('    invoke_string_substitution_function ' + _str)
        if string[0:9] == 'patsubst ':
            (pattern, replacement, text) = string[9:].split(',')
            if pattern[0:2] == '$(':
                (pattern, d1, d2) = self.parse_string(pattern)
            if replacement[0:2] == '$(':
                (replacement, d1, d2) = self.parse_string(replacement)
            if text[0:2] == '$(':
                (text, d1, d2) = self.parse_string(text)
            (pat_pre_percent, pat_post_percent) = pattern.split('%')
            (rep_pre_percent, rep_post_percent) = replacement.split('%')
            mat_pre_percent = ''
            if pat_pre_percent == '':
                mat_pre_percent = text.split(' ')[1:]
            else:
                mat_pre_percent = text.split(pat_pre_percent)[1:]
            match = []
            for entry in mat_pre_percent:
                if pat_post_percent == '':
                    match.append(entry)
                else:
                    match.append(entry.split(pat_post_percent)[0])
            result = []
            for entry in match:
                xx = rep_pre_percent + entry + rep_post_percent
                result.append(xx)
            string = (' '.join(result))
        return string

    def invoke_control_function(self, string):
        """ https://www.gnu.org/software/make/manual/html_node/Make-Control-Functions.html # nopep8
        """
        # Logger().debug('    invoke_control_function ' + string)
        # if string[0:5] == 'info ':
        #     print(string[5:])
        return ''

    def invoke_eval(self, string):
        """ https://www.gnu.org/software/make/manual/html_node/Eval-Function.html # nopep8
        """
        # Logger().debug('    invoke_eval ' + string)
        (string, d1, d2) = self.parse_string(string[5:])
        return string

    def invoke_call(self, string):
        """ https://www.gnu.org/software/make/manual/html_node/Call-Function.html # nopep8
        """
        # Logger().debug('    invoke_call ' + string)
        name = string[5:].split(',')[0]
        if name in self.variables.keys():
            for string in self.variables[name]:
                # TODO concat all returns strings?
                (string, d1, d2) = self.parse_string(string)
        return string

    def expand_variable_substitution_reference(self, string):
        """ https://www.gnu.org/software/make/manual/html_node/Substitution-Refs.html # nopep8
        """
        # s
        # Logger().debug('    expand_variable_substitution_reference ' + s)
        tmp = string.split(':')
        var_name = tmp[0]
        tmp = tmp[-1].split('=')
        a = tmp[0]
        b = tmp[1]
        equivalent = 'patsubst ' + a + ',' + b + ',' + self.variables[var_name]
        return self.invoke_string_substitution_function(equivalent)

    def expand_variable_reference(self, string):
        """ https://www.gnu.org/software/make/manual/html_node/Reference.html # nopep8
        """
        # Logger().debug('    expand_variable_reference ' + string)
        if ':' in string:
            string = self.expand_variable_substitution_reference(string)
        else:
            if string in self.variables.keys():
                string = self.variables[string]
            else:
                string = ''
        return string

    def parse_variable_set(self, string):
        """ https://www.gnu.org/software/make/manual/html_node/Setting.html # nopep8
        """
        # Logger().debug('  parse_variable_set ' + string)
        lhs = ''
        rhs = ''
        append = False
        is_lhs = True
        idx = 0
        while idx < len(string):
            if (string[idx] == '='):
                is_lhs = False
            if is_lhs:
                if string[idx] == '+':
                    append = True
                else:
                    lhs += string[idx]
            elif (string[idx] != '='):
                rhs += string[idx]
            idx += 1
        return (lhs, rhs, append)

    def invoke_function(self, string):
        """  https://www.gnu.org/software/make/manual/html_node/Syntax-of-Functions.html # nopep8
        """
        # Logger().debug('  invoke_function ' + string)
        if string[0:9] == 'wildcard ':
            string = self.invoke_wildcard(string)
        elif string[0:8] == 'foreach ':
            string = self.invoke_foreach(string)
        elif string[0:3] == 'or ':
            string = self.invoke_conditional_function(string)
        elif string[0:4] == 'and ':
            string = self.invoke_conditional_function(string)
        elif string[0:9] == 'patsubst ':
            string = self.invoke_string_substitution_function(string)
        elif string[0:5] == 'info ':
            string = self.invoke_control_function(string)
        elif string[0:5] == 'eval ':
            string = self.invoke_eval(string)
        elif string[0:5] == 'call ':
            string = self.invoke_call(string)
        else:
            pass
        return string

    def internalize_operation(self, string, define):
        if define is None:
            (lhs, rhs, append) = self.parse_variable_set(string)
            # ap = str(append)
            # Logger().debug('parse var lh ' + lhs + ' ' + rhs + ' ' + ap)
            if append and (lhs in self.variables.keys()):
                self.variables[lhs] += ' ' + rhs
            else:
                self.variables[lhs] = rhs
        else:
            if define not in self.variables.keys():
                self.variables[define] = ''
            self.variables[define] += string
    def emit(self):
        ff = open(self.abs_path, 'w')
        phony = False
        for rule in self.rules.values():
            for target in rule.targets:
                if target.phony:
                    phony = True
                    ff.write('.PHONY: ' + str(target) + "\n")
        if phony:
            ff.write("\n")
        for rule in self.rules.values():
            if rule is not None:
                ff.write(str(rule) + "\n")
            ff.write("\n")
        ff.close()


global_makefile = GNUMakefile(None)


class AttributeInfo():
    def __init__(self, key, is_list=False, is_int=False, cli=None):
        """ key is the string attribute from the Dev Guide, e.g. 'Property' """
        self.key = key
        self.is_list = is_list
        self.is_int = is_int
        self.cli = cli

class AttributeBase():
    """ a thing which contains opencpi (XML) attributes, either intermediary
        elem already parsed with ElementTree, or XML file itself, or perhaps a
        Makefile for pre-2.0 OpenCPI assets """

    def __init__(self, elem):
        """ elem is an ElementTree Element intended to represent, e.g., Property
            within a <RccWorker><Property/></RccWorker> """
        if elem.tag.lower() not in \
                [tag.lower() for tag in self.get_root_tags()]:
            self.raise_invalid_attribute_error(elem.tag)
        self.attrs = dict()

    def get_attr_infos(self):
        return []

    def parse(self, elem, paths=[], cli_dict=None):
        """ use elem to parse an XML ElementTree directly, and paths to specify
            a list of XML/makefile files to parse """
        for info in self.get_attr_infos():
            if info.is_list:
                val = self.get_attr_list(info.key, elem, paths, cli_dict)
            else:
                val = self.get_attr(info.key, elem, paths, cli_dict)
            if info.is_int and (not info.is_list):
                val = int(val) if val != '' else 0
            if (info.is_list and val != []) or \
               (not info.is_list and val != ''):
                # this is where ALL attribute values are finally placed into
                # self.attrs dict
                self.attrs[info.key] = val

    @staticmethod
    def get_xml_val_list(val):
        """ this takes in a val (string) that is space-and-newline-separated (as
            is commonly done in OpenCPI XML files) and separates it into a
            returned list"""
        return ' '.join(val.replace('\n', '').split()).split(' ')

    @staticmethod
    def get_variable_val_list_from_gnu_makefile(var_name, abs_makefile_path):
        """ this extracts the value of the GNUMake variable, whose name is var
            name, that is specified in the abs_makefile_path, and separates the
            value into a returned list """
        # start pre-2.0 opencpi
        ret = []
        makefile = GNUMakefile(abs_makefile_path)
        if var_name in makefile.variables.keys():
            var = GNUMakefile(abs_makefile_path).variables[var_name]
            ret = ' '.join(var.split()).split(' ')
        return ret
        # end pre-2.0 opencpi

    def get_attr_common(self, attr, elem, is_list, makefile_abs_paths=[], cli_dict=None):
        if is_list:
            ret = []
        else:
            ret = ''
        if cli_dict is None:
            if makefile_abs_paths == []:
                makefile_abs_paths.append('') # TODO fix this hack to make xml work
            if is_list:
                ret2 = []
            else:
                ret2 = ''
            for makefile_abs_path in makefile_abs_paths:
                # start pre-2.0 opencpi
                if elem is None:
                    # TODO remove below 2 lines which are a horrible hack
                    if makefile_abs_path == self.get_xml_abs_path():
                        makefile_abs_path = ''
                # end pre-2.0 opencpi
                # not all assets have XML, e.g., pre-2.0 HdlLibrary (hdl primitive)
                # in the cases where XML doesn't exist, simply return ret from above
                go = True
                if elem is None:
                    if makefile_abs_path == '':
                        go = os.path.isfile(self.get_xml_abs_path())
                    else:
                        go = os.path.isfile(makefile_abs_path)
                    attr_abs_path = self.abs_path
                else:
                    attr_abs_path = ''
                if go:
                    if makefile_abs_path == '':
                        if elem is None:
                            iteration_obj = self.get_parsed().getroot().attrib
                        else:
                            iteration_obj = elem
                        for key, val in iteration_obj.items():
                            # tmp = self.get_valid_attributes()
                            # if key.lower() in [attr.lower() for attr in tmp]:
                            if key.lower() == attr.lower():
                                if is_list:
                                    ret2 = self.get_xml_val_list(val)
                                else:
                                    ret2 = val
                            # else:
                            #     self.throw_invalid_element_error(self, abs_path, key)
                    else:
                        # start pre-2.0 opencpi
                        attr_abs_path = makefile_abs_path
                        ret2 = self.get_variable_val_list_from_gnu_makefile(attr, attr_abs_path)
                        if not is_list:
                            if len(ret2) > 0:
                                ret2 = ret2[0]
                            else:
                                ret2 = ''
                        # end pre-2.0 opencpi
                    #if attr_abs_path != '':
                    #    if (ret2 != '') and (ret2 != []):
                    #        Logger().debug('** parsed ' + attr_abs_path + ' ' + attr +
                    #                       ' value of ' + str(ret2))
                if (is_list and ret2 != []) or ((not is_list) and (ret2 != '')):
                    ret = ret2
        else:
            for attr_info in self.get_attr_infos():
                if attr.lower() == attr_info.key.lower():
                    if attr_info.cli is not None:
                        ret = cli_dict[attr_info.cli[1].replace('-', '')]
        return ret

    def get_attr(self, attr, elem=None, makefile_abs_paths=[], cli_dict=None):
        """ Retrieves the singular value, as a string, of the attribute
            indicated by the attr string, from the following places (in
            precedence order):
            1) cli_dict if it is not None,
            2) makefiles indicated in makefile_abs_paths list entries, if the
               file indicated by the entry exists, in list order with the latter
               entries taking precedence for overriding values
            3) the pre-parsed XML element in elem,
            4) XML file pointed to by self.get_xml_abs_path().
            Examples of attr are 'Property' and 'Instance' """
        return self.get_attr_common(attr, elem, False, makefile_abs_paths, cli_dict)

    def get_attr_list(self, attr, elem=None, makefile_abs_paths=[], cli_dict=None):
        """ Same as get_attr() but retrieves the value as a list of strings.
            Examples of attr are 'Workers' and 'Containers' """
        return self.get_attr_common(attr, elem, True, makefile_abs_paths, cli_dict)

    def raise_invalid_attribute_error(self, elem_str):
        # msg = abs_path + ': ' + elem_str + ' is an invalid attribute'
        msg = elem_str + ' is an invalid attribute'
        # Logger().warn(msg)
        raise InvalidAttributeError(msg)


# TODO rename AssetBase to AssetBase
class AssetBase(AttributeBase):
    """ Contains functionality common to all assets, e.g., all
        Protocols/Workers/Assemblies/etc. Child classes must define
        get_root_tags() method which returns list of strings of permissible
        tags to verify during construction. Each asset has a directory that is
        retrievable via get_dir_abs_path(). Assets that have XML files can query
        get_xml_abs_path(). Every child class is intended to also define a
        get_type() string that is used for log messaging and internal asset
        conditionalization."""

    def __init__(self, abs_path, enable_path_existence_check=True):
        """ abs_path is either to a xml file (Component/Protocol/etc) or a dir
            (HdlAssembly/etc) or none for some cases (Component embedded in
            OWD, platform base config) """
        self.attrs = dict()
        for info in self.get_attr_infos():
            if info.is_list:
                self.attrs[info.key] = []
            else:
                self.attrs[info.key] = ''
        # IMPORTANT - derived classes should not retrieve self.abs_path
        # directly, use self.get_dir_abs_path() and self.get_xml_abs_path()
        # instead
        # TODO - rename to self._abs_path
        self.abs_path = abs_path  # can be None, e.g., for base platform config
        if self.abs_path is not None:
            while '//' in self.abs_path:
                self.abs_path = self.abs_path.replace('//', '/')
            if self.abs_path.endswith('/'):
                self.abs_path = self.abs_path[:,-1]
        self.name = self.get_name() # CDG section 6.1.1, section 8.1.1, etc
        if (self.abs_path is not None):
            if enable_path_existence_check:
                self.raise_if_path_does_not_exist()

    def get_root_tags(self):
        # TODO replace get_root_tags() with self.root_tags
        return self.root_tags

    def get_name(self):
        # TODO replace get_root_tags() with self.root_tags
        self.name = self.get_name()  # CDG section 6.1.1, section 8.1.1, etc
        if (self.abs_path is not None):
            if enable_path_existence_check:
                self.raise_if_path_does_not_exist()

    def get_name(self):
        if self.get_is_xml():
            name = self.get_name_from_abs_path(self.abs_path)
            strs_to_remove = []
            if self.get_root_tags() == ['ComponentSpec']:
                strs_to_remove += ['-spec']  # CDG section 6
                strs_to_remove += ['_spec', '-comp']  # undocumented
            if self.get_root_tags() == ['Protocol']:
                # below line is CDG section 5
                strs_to_remove += ['-prot', '-protocol', '_protocol']
                strs_to_remove += ['_prot']  # undocumented
            if self.get_root_tags() == ['HdlWorker']:
                strs_to_remove += ['-hdl']  # undocumented
            if self.get_root_tags() == ['RccWorker']:
                strs_to_remove += ['-rcc']  # undocumented
            for str_to_remove in strs_to_remove:
                name = name.split(str_to_remove, -1)[0]
        else:
            # self.abs_path is not None for makefiles but will be be None for base
            # platform configuration
            if self.abs_path is None:
                name = 'base'
            else:
                name = self.abs_path.split('/')[-1]
        return name

    def get_abs_path_exists(self):
        if self.get_is_xml():
            exists = os.path.isfile(self.get_xml_abs_path())
        else:
            exists = os.path.isdir(self.abs_path)
        return exists

    def raise_if_path_does_not_exist(self):
        if not self.get_abs_path_exists():
            self.raise_abs_path_does_not_exist()
        if os.path.isfile(self.get_xml_abs_path()):
            lowers = [tag.lower() for tag in self.get_root_tags()]
            tag = self.get_tag(None)
            if tag.lower() not in lowers:
                msg = self.get_xml_abs_path() + ' (root tag ' + tag
                msg += ') is not a ' + self.get_root_tags()[0]
                # TODO investigate moving to ComponentLibrary/HdlPlatform
                if self.get_dir_abs_path().endswith('hdl/platforms'):
                    # Logger().warn(msg)
                    pass
                else:
                    raise InvalidAssetError(msg)

    def create_files(self, templates):
        if self.get_abs_path_exists():
            raise Exception(self.get_type() + ' ' + self.abs_path + ' already exists')
        else:
            os.makedirs(self.get_dir_abs_path(), exist_ok=False)
        for fname, fcontents in templates.items():
            fcontents = jinja2.Template(fcontents, trim_blocks=True)
            fcontents = fcontents.render(asset=self)
            out_file = open(self.abs_path + '/' + fname, 'w')
            out_file.write(fcontents)
            out_file.close()

    def get_paths_to_parse(self):
        return []

    def parse(self, cli_dict=None):
        paths = self.get_paths_to_parse()
        for path in paths:
            Logger().debug('parsing ' + path)
        AttributeBase.parse(self, None, paths, cli_dict)
        Logger().debug('parsed attributes: ' + str(self.attrs))

    @staticmethod
    def get_name_from_abs_path(abs_path):
        #return abs_path.rsplit('/', 1)[1].split('.xml')[0]
        return abs_path.rsplit('/', 1)[1].split('.')[0]

    @staticmethod
    def listdir_assets(dir_abs_path):
        """ return list of names of (non-recursive) entries within dir_abs_path
            which are to be considered as assets to be discovered """
        # TODO this method probably needs a better name or consolidation
        return [entry for entry in os.listdir(dir_abs_path) if
                (os.path.isfile(entry) or (entry != 'lib'))]

    @staticmethod
    def get_existing_abs_dir_paths_for_asset_consideration(parent_abs_path):
        """ return list of absolute paths of (non-recursive) directories
            within parent_abs_path which exist and are to be considered as
            assets to be discovered """
        return [(parent_abs_path + '/' + entry) for entry in
                os.listdir(parent_abs_path) if (os.path.isdir(parent_abs_path + '/' + entry) and
                (entry != 'lib') and (entry != 'specs'))]

    def get_is_xml(self):
        ret = False
        if self.abs_path is not None:
            ret = self.abs_path.endswith('.xml')
        return ret

    def get_xml_abs_path(self):
        """ returns asboslute path to asset's xml file, regardless of asset
            type """
        ret = None
        # self.abs_path can be None, e.g., for base platform configuration
        if self.abs_path is not None:
            ret = self.abs_path + '/' + self.name + '.xml'
            if self.get_is_xml():
                ret = self.abs_path
        return ret

    def get_dir_abs_path(self):
        """ returns asboslute path to asset's directory, regardless of asset
            type """
        ret = self.abs_path
        if self.get_is_xml():
            ret = self.abs_path.rsplit('/', 1)[0]
        return ret

    def get_parsed(self):
        xml_abs_path = self.get_xml_abs_path()
        _file = open(self.get_xml_abs_path(), 'r')
        _str = _file.read()
        # can be removed when OpenCPI follows XML Specification
        elems = ['ComponentSpec', 'Protocol']
        elems += ['HdlWorker', 'HdlDevice', 'RccWorker']
        for elem in elems:
            # ugly ugly fix... (e.g. file_read OCS)
            # below line adds && operator support (CDG section 7.11.2)
            _str = _str.replace('\%\%', '\&amp;\%amp;')
            # below 2 lines avoid corruption of ProtocolSummary attribute
            _str = _str.replace('protocolsummary', 'foosummary')
            _str = _str.replace('ProtocolSummary', 'foosummary')
            for _elem in [elem, elem.lower()]:
                from_str = '<' + _elem
                to_str = '<' + _elem + " xmlns:xi=\"http://www.w3.org/2001/XInclude\" "
                # below line hacks xi:include support (CDG section 5.1)
                _str = _str.replace(from_str, to_str)
            # below line avoids corruption of ProtocolSummary attribute
            _str = _str.replace('foosummary', 'ProtocolSummary')
        # below line adds support for newlines in attributes (undocumented in OpenCPI)
        _str = _str.replace('\n', ' ')
        try:
            ret = ET.ElementTree(ET.fromstring(_str))
        except ET.ParseError as err:
            msg = 'malformed xml: ' + self.get_xml_abs_path()
            # Logger().warn('skipping ' + msg + ' ' + str(err))
            Logger().warn('skipping ' + msg)
            raise InvalidAssetError(msg)
        return ret

    def get_list_of_existing_abs_paths_to_parse(self, abs_paths):
        """ abs_paths is list of absolute paths to xml or Makefile to be parsed,
            which is then pruned to contain only files that exist before
            returning the pruned list, with the list order maintained """
        ret = []
        for abs_path in abs_paths:
            if os.path.exists(abs_path):
                ret.append(abs_path)
        return ret

    def get_tag(self, elem):
        ret = None
        if elem is None:
            ret = self.get_parsed().getroot().tag
        else:
            ret = elem.tag
        return ret

    def raise_abs_path_does_not_exist(self):
        """ useful check for *directory* variants of AssetBase (AssetBase
            does not check for XML existence of directory variants) """
        pre = 'dir'
        if self.abs_path.endswith('.xml'):
            pre = 'xml file'
        msg = pre + ' ' + self.abs_path + ' does not exist'
        raise InvalidAssetError(msg)

    def raise_invalid_asset_error(self):
        raise InvalidAssetError('not a ' + self.get_root_tags()[0])


def test_GNUMakefile(ret):
    log_pass_fail('testing GNUMakefile', False)
    return ret
