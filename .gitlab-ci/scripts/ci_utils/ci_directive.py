#!/usr/bin/env python3

import re
from collections import defaultdict
from . import ci_platform

class Directive():

    def __init__(self, directive_str, default_host_names=None):
        self.str = directive_str
        self.default_host_names = default_host_names or ''
        self.dict = self.to_dict()

    def to_dict(self):
        """Parses directive to convert it into a dictionary

        Args:
            directive_str:      String representation of directive
            default_host_names: Names of opencpi host platforms to
                                default to in case directive does not
                                contain any

        Returns:
            Dictioanry representation of directive
        """
        platforms = defaultdict(set)
        space_pattern = re.compile(r'([^ $]+)')
        colon_pattern = re.compile(r'([^:$]+)')
        comma_pattern = re.compile(r'([^,$]+)')

        # Find all platforms separated by spaces
        spaces = space_pattern.findall(self.str)
        for space in spaces:
            # Find all patterns separated by a colon (linked platforms)
            colons = colon_pattern.findall(space)
            left = colons[0]

            if left:
                # Find all platforms separated by comma on left side of colon
                l_commas = comma_pattern.findall(left)
                for l_comma in l_commas:
                    if len(colons) == 2:
                        right = colons[1]
                        # Find all platforms separated by comma on right side
                        # of colon
                        r_commas = comma_pattern.findall(right)

                        for r_comma in r_commas:
                            # Associate the platforms on left side of colon
                            # with platforms on right side
                            platforms[l_comma].add(r_comma)
                            platforms[r_comma].add(l_comma)
                    else:
                        platforms[l_comma] = {}
        
        return platforms

    def apply(self, platforms):
        """Applies the directive to a list of Platforms

        Args:
            platforms: List of Platforms to apply directive to

        Returns:
            List of Platforms with directive applied to it
        """
        if not self.dict:
            return platforms

        host_platforms = ci_platform.get_host_platforms(platforms)
        cross_platforms = ci_platform.get_cross_platforms(platforms)
        filtered_platforms = []

        # Set linked platforms for each cross platform
        for cross_platform in cross_platforms:
            if cross_platform.name not in self.dict:
                continue

            cross_platform.linked_platforms = ci_platform.get_linked_platforms(
                cross_platform, cross_platforms, self.dict)

        # Filter host platform and cross platforms to those only specified in
        # directive
        for host_platform in host_platforms:
            if host_platform.name in self.dict:
                filtered_cross_platforms = []
                for cross_platform in host_platform.cross_platforms:
                    if cross_platform.name in self.dict:
                        filtered_cross_platforms.append(cross_platform)
                host_platform.cross_platforms = filtered_cross_platforms
                filtered_platforms.append(host_platform)
                
        # If directive does not include a host platform but does include 
        # cross platforms, use default host platforms
        if self.dict and not filtered_platforms:
            for platform_name in self.default_host_names.split():
                filtered_cross_platforms = []
                default_platform = ci_platform.get_platform(platform_name, 
                                                            platforms)

                if default_platform and default_platform.is_host:
                    for cross_platform in default_platform.cross_platforms:
                        if cross_platform.name in self.dict:
                            filtered_cross_platforms.append(cross_platform)
                    
                    if filtered_cross_platforms:
                        default_platform.cross_platforms = filtered_cross_platforms
                        filtered_platforms.append(default_platform)

        return filtered_platforms

    @classmethod
    def from_env(cls, env):
        """Creates a Directive object from an object containing CI 
           environment variables

        Args:
            env: Object with CI environment variables as attributes

        Returns:
            Directive
        """
        try:
            platforms = env.directive
        except:
            # Get platform names from appropriate env var
            if env.pipeline_source in ['scheduled', 'web']:
                platforms = env.platforms
            elif env.pipeline_source == 'merge_request_event':
                platforms = env.mr_platforms
            elif env.pipeline_source == 'push':     
                commit_directive = re.search(r'\[ *ci (.*) *\]', 
                                             env.commit_message)
                if commit_directive:
                    platforms = commit_directive.group(1)
                else:
                    platforms = env.platforms
            else:
                return cls('', env.default_hosts)

        return cls(platforms, env.default_hosts)