from pathlib import Path

"""Dicts of args to be used by ocpidev.py"""

# Options common to all verbs
common_options = {
    'directory': {
        'long': '--directory',
        'short': '-d',
        'default': str(Path.cwd())
    },
    'force': {
        'long': '--force',
        'short': '-f',
        'action': 'store_true'
    }
}

# Options to be used for pre-processing user args and to reference
# in verb-specific options
options = {
    'pkg_prefix': {
        'long': '--package-prefix',
        'short': '-F'
    },
    'pkg_id': {
        'long': '--package-id',
        'short': '-K'
    },
    'pkg_name': {
        'long': '--package-name',
        'short': '-N'
    },
    'xml_include': {
        'long': '--xml-include',
        'short': '-A',
        'action': 'append'
    },
    'include_dir': {
        'long': '--include-dir',
        'short': '-I',
        'action': 'append'
    },
    'comp_lib': {
        'long': '--comp-lib',
        'short': '-y',
        'action': 'append'
    },
    'prim_lib': {
        'long': '--prim-lib',
        'short': '-Y',
        'action': 'append'
    },
    'keep': {
        'long': '--keep',
        'short': '-k',
        'action': 'store_true'
    },
    'depend': {
        'long': '--depend',
        'short': '-D',
        'action': 'append'
    },
    'register': {
        'long': '--register',
        'action': 'store_true'
    },
    'no_control': {
        'long': '--no-control',
        'short': '-n',
        'action': 'store_false'
    },
    'create_test': {
        'long': '--create-test',
        'short': '-t',
        'action': 'store_true'
    },
    'project': {
        'long': '--project',
        'short': '-p',
        'action': 'store_true'
    },
    'library': {
        'long': '--library',
        'short': '-l'
    },
    'hdl_library': {
        'long': '--hdl-library',
        'short': '-h',
        'choices': [
            'devices',
            'cards',
            'adapters'
        ]
    },
    'standalone': {
        'long': '--standalone',
        'short': '-s',
        'action': 'store_true'
    },
    'spec': {
        'long': '--spec',
        'short': '-S'
    },
    'platform': {
        'long': '--platform',
        'short': '-P'
    },
    'language': {
        'long': '--language',
        'short': '-L'
    },
    'other': {
        'long': '--other',
        'short': '-O',
        'action': 'append'
    },
    'core': {
        'long': '--core',
        'short': '-C',
        'action': 'append'
    },
    'rcc_static_prereq': {
        'long': '--rcc-static-prereq',
        'short': '-R',
        'action': 'append'
    },
    'rcc_dynamic_prereq': {
        'long': '--rcc-dynamic-prereq',
        'short': '-r',
        'action': 'append'
    },
    'slave_worker': {
        'long': '--slave-worker',
        'short': '-V',
        'action': 'append'
    },
    'emulates': {
        'long': '--emulates',
        'short': '-E',
        'action': 'append'
    },
    'supports': {
        'long': '--supports',
        'short': '-U',
        'action': 'append'
    },
    'hdl_part': {
        'long': '--hdl-part',
        'short': '-g'
    },
    'time_freq': {
        'long': '--time-freq',
        'short': '-q'
    },
    'no_dsp': {
        'long': '--no-dsp',
        'short': '-u',
        'action': 'store_true'
    },
    'only_target': {
        'long': '--only-target',
        'short': '-T',
        'action': 'append'
    },
    'exclude_target': {
        'long': '--exclude_target',
        'short': '-Z',
        'action': 'append'
    },
    'only_platform': {
        'long': '--only-platform',
        'short': '-G',
        'action': 'append'
    },
    'exclude_platform': {
        'long': '--exclude-platform',
        'short': '-Q',
        'action': 'append'
    },
    'module': {
        'long': '--module',
        'short': '-M'
    },
    'prebuilt': {
        'long': '--prebuilt',
        'short': '-B'
    },
    'xml_app': {
        'long': '--xml-app',
        'short': '-X',
        'action': 'store_true',
        'mut_exc_group': 'xml_app'
    },
    'xml_dir_app': {
        'long': '--xml-dir-app',
        'short': '-x',
        'action': 'store_true',
        'mut_exc_group': 'xml_app'
    },
    'no_depend': {
        'long': '--no-depend',
        'short': '-H',
        'action': 'store_true'
    },
    'no_elaborate': {
        'long': '--no-elaborate',
        'short': '-J'
    },
    'hdl_assembly': {
        'long': [
            '--hdl-assembly',
            '--build--assembly',
            '--build-hdl-assembly'
        ],
        'action': 'append'
    },
    'no_assemblies': {
        'long': [
            '--no-assemblies',
            '--build-no-assemblies'
        ],
        'action': 'store_true'
    },
    'hdl': {
        'long': [
            '--hdl',
            '--build-hdl'
        ],
        'action': 'store_true'
    },
    'rcc': {
        'long': [
            '--rcc',
            '--build-rcc'
        ],
        'action': 'store_true'
    },
    'worker': {
        'long': '--worker',
        'short': '-W',
        'action': 'append'
    },
    'hdl_rcc_platform': {
        'long': [
            '--hdl-rcc-platform',
            '--build-hdl-rcc-platform'
        ],
        'action': 'append'
    },
    'rcc_platform': {
        'long': [
            '--rcc-platform',
            '--build-rcc-platform'
        ],
        'action': 'append'
    },
    'hdl_target': {
        'long': [
            '--hdl-target',
            '--build-hdl-target'
        ],
        'action': 'append'
    },
    'hdl_platform': {
        'long': [
            '--hdl-platform',
            '--build-hdl-platform'
        ],
        'action': 'append'
    },
    'workers_as_needed': {
        'long': '--workers-as-needed',
        'action': 'store_true'
    },
}

# Verbs with nouns and options, including options referencing those above
verbs = {
    'build': {
        'nouns': {
            'required': False,
            'application': {
                'options': {
                    'name': None,
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform']
                }
            },
            'applications': {
                'options': {
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform']
                }
            },
            'hdl': {
                'options': {
                    'workers_as_needed' : options['workers_as_needed'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform']
                },
                'nouns': {
                    'assembly': {
                        'options': {
                            'name': None
                        }
                    },
                    'assemblies': None,
                    'device': {
                        'options': {
                            'name': None
                        }
                    },
                    'platform': {
                        'options': {
                            'name': None
                        }
                    },
                    'platforms': None,
                    'primitive': {
                        'options': {
                            'name': None
                        },
                        'nouns': {
                            'core': None,
                            'library': None
                        }
                    },
                    'primitives': None
                }
            },
            'library': {
                'options': {
                    'name': {'nargs': '?'},
                    'hdl': options['hdl'],
                    'rcc': options['rcc'],
                    'worker': options['worker'],
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform']
                }
            },
            'project': {
                'options': {
                    'name': {'nargs': '?'},
                    'hdl_assembly': options['hdl_assembly'],
                    'no_assemblies': options['no_assemblies'],
                    'hdl': options['hdl'],
                    'rcc': options['rcc'],
                    'worker': options['worker'],
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'workers_as_needed' : options['workers_as_needed'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform']
                }
            },
            'test': {
                'options': {
                    'name': {'nargs': '?'},
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform'],
                    'library': options['library']
                }
            },
            'worker': {
                'options': {
                    'name': None,
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform'],
                    'library': options['library']
                }
            }
        }
    },
    'clean': {
        'nouns': {
            'required': False,
            'application': {
                'options': {
                    'name': None
                }
            },
            'applications': None,
            'hdl': {
                'nouns': {
                    'assembly': {
                        'options': {
                            'name': None
                        }
                    },
                    'assemblies': None,
                    'device': {
                        'options': {
                            'name': None
                        }
                    },
                    'platform': {
                        'options': {
                            'name': None
                        }
                    },
                    'platforms': None,
                    'primitive': {
                        'options': {
                            'name': None
                        },
                        'nouns': {
                            'core': None,
                            'library': None
                        }
                    },
                    'primitives': {
                        'nouns': {
                            'core': None,
                            'library': None
                        }
                    }
                }
            },
            'library': {
                'options': {
                    'name': None
                }
            },
            'project': {
                'options': {
                    'name': None
                }
            },
            'test': {
                'options': {
                    'name': {
                        'nargs': '?'
                    }
                }
            },
            'worker': {
                'options': {
                    'library': options['library'],
                    'name': None
                }
            }
        }
    },
    'create': {
        'options': {
            'name': None,
            'keep': options['keep'],
        },
        'nouns': {
            'application': {
                'options': {
                    'xml_app': options['xml_app'],
                    'xml_dir_app': options['xml_dir_app']
                }
            },
            'component': None,
            'library': {
                'options': {
                    'name': None,
                    'pkg_prefix': options['pkg_prefix'],
                    'pkg_id': options['pkg_id'],
                    'pkg_name': options['pkg_name'],
                    'xml_include': options['xml_include'],
                    'include_dir': options['include_dir'],
                    'comp_lib': options['comp_lib'],
                    'prim_lib': options['prim_lib']
                }
            },
            'hdl': {
                'nouns': {
                    'assembly': {
                        'options': {
                            'exclude_platform': options['exclude_platform'],
                            'only_platform': options['only_platform'],
                            'only_target': options['only_target'],
                            'exclude_target': options['exclude_target']
                        }
                    },
                    'card': None,
                    'device': {
                        'options': {
                            'xml_include': options['xml_include'],
                            'include_dir': options['include_dir'],
                            'comp_lib': options['comp_lib'],
                            'prim_lib': options['prim_lib'],
                            'hdl_library': options['hdl_library'],
                            'library': options['library'],
                            'core': options['core'],
                            'emulates': options['emulates'],
                            'supports': options['supports'],
                            'exclude_platform': options['exclude_platform'],
                            'only_platform': options['only_platform'],
                            'only_target': options['only_target'],
                            'exclude_target': options['exclude_target']
                        }
                    },
                    'platform': {
                        'options': {
                            'xml_include': options['xml_include'],
                            'include_dir': options['include_dir'],
                            'comp_lib': options['comp_lib'],
                            'prim_lib': options['prim_lib'],
                            'core': options['core'],
                            'hdl_part': options['hdl_part'],
                            'time_freq': options['time_freq'],
                            'no_dsp': options['no_dsp']
                        }
                    },
                    'primitive': {
                        'options': {
                            'exclude_platform': options['exclude_platform'],
                            'only_platform': options['only_platform'],
                            'only_target': options['only_target'],
                            'exclude_target': options['exclude_target'],
                        },
                        'nouns': {
                            'core': {
                                'options': {
                                    'prebuilt': options['prebuilt'],
                                    'module': options['module']
                                }
                            },
                            'library': {
                                'options': {
                                    'no_depend': options['no_depend'],
                                    'no_elaborate': options['no_elaborate']
                                }
                            }
                        }
                    },
                    'slot': None
                }
            },
            'project': {
                'options': {
                    'depend': options['depend'],
                    'register': options['register'],
                    'pkg_prefix': options['pkg_prefix'],
                    'pkg_id': options['pkg_id'],
                    'pkg_name': options['pkg_name'],
                    'xml_include': options['xml_include'],
                    'include_dir': options['include_dir'],
                    'comp_lib': options['comp_lib'],
                    'prim_lib': options['prim_lib']
                }
            },
            'protocol': {
                'options': {
                    'platform': options['platform'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library'],
                }
            },
            'registry': None,
            'spec': {
                'options': {
                    'no_control': options['no_control'],
                    'create_test': options['create_test'],
                    'platform': options['platform'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library'],
                }
            },
            'test': {
                'options': {
                    'spec': options['spec']
                }
            },
            'worker': {
                'options': {
                    'xml_include': options['xml_include'],
                    'include_dir': options['include_dir'],
                    'comp_lib': options['comp_lib'],
                    'prim_lib': options['prim_lib'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library'],
                    'rcc_static_prereq': options['rcc_static_prereq'],
                    'rcc_dynamic_prereq': options['rcc_dynamic_prereq'],
                    'slave_worker': options['slave_worker'],
                    'worker': options['worker'],
                    'core': options['core'],
                    'language': options['language'],
                    'platform': options['platform'],
                    'other': options['other'],
                    'spec': options['spec'],
                    'exclude_platform': options['exclude_platform'],
                    'only_platform': options['only_platform'],
                    'only_target': options['only_target'],
                    'exclude_target': options['exclude_target']
                }
            }
        }
    },
    'delete': {
        'options': {
            'name': None
        },
        'nouns': {
            'application': None,
            'hdl': {
                'nouns': {
                    'assembly': None,
                    'card': None,
                    'device': {
                        'options': {
                            'hdl_library': options['hdl_library'],
                            'library': options['library']
                        }
                    },
                    'platform': None,
                    'primitive': {
                        'nouns': {
                            'core': None,
                            'library': None
                        }
                    },
                    'slot': None
                }
            },
            'library': None,
            'project': None,
            'protocol': {
                'options': {
                    'project': options['project'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library']
                }
            },
            'registry': None,
            'spec': {
                'options': {
                    'project': options['project'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library']
                }
            },
            'test': None,
            'worker': {
                'options': {
                    'hdl_library': options['hdl_library'],
                    'library': {
                        'long': '--library',
                        'short': '-l'
                    }
                }
            }
        }
    },
    'refresh': {
        'nouns': {
            'project': None
        }
    },
    'register': {
        'options': {
            'name': {'nargs': '?'}
        },
        'nouns': {
            'project': None
        }
    },
    'run': {
        'nouns': None
    },
    'set': {
        'options': {
            'registry_directory': {
                'nargs': '?',
                'metavar': 'registry-directory'
            }
        },
        'nouns': {
            'registry': None
        }
    },
    'show': {
        'nouns': None
    },
    'unregister': {
        'options': {
            'name': {'nargs': '?'}
        },
        'nouns': {
            'project': None
        }
    },
    'unset': {
        'nouns': {
            'registry': None
        }
    },
    'utilization': {
        'nouns': None
    }
}

# Collection of options, common options, and verbs to be imported by ocpidev
args_dict = {
    'common_options': common_options,
    'options': options,
    'verbs': verbs
}
