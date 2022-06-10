import _opencpi.util as ocpiutil

def get_noun():
    """
    Get noun from call to opencpi utility function get_dir_info().
    Format returned dirtype as needed.
    """
    make_type, asset_type, _, _, _ = ocpiutil.get_dir_info()
    if asset_type:
        if asset_type.endswith('-worker'):
            asset_type = 'worker'
        if asset_type in ['hdl-core', 'hdl-library']:
            # Command line expects 'hdl-primitive-core' or 
            # 'hdl-primitive-library' as a list
            asset_type = 'hdl-primitive-' + asset_type[4:]
    else:
        asset_type = make_type
    if asset_type is not None:
        asset_type = asset_type.split('-')
    return asset_type

"""Dicts of args to be used by ocpidev.py"""

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
    'component_library': {
        'long': ['--component-library','--comp-lib'],
        'short': '-y',
        'action': 'append'
    },
    'primitive_library': {
        'long': ['--primitive-library', '--prim-lib'],
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
        'action': 'store_true'
    },
    'file_only': {
        'long': '--file-only',
        'action': 'store_true'
    },
    'create_test': {
        'long': '--create-test',
        'short': '-t',
        'action': 'store_true'
    },
    'project': {
        'long': '--project',
        'short': '-p',
        'action': 'store_true',
        'mut_exc_group': 'project'
    },
    'library': {
        'long': '--library',
        'short': '-l',
        'mut_exc_group': 'project'
    },
    'hdl_library': {
        'long': '--hdl-library',
        'short': '-h',
        'choices': [ 'devices', 'cards', 'adapters' ],
        'mut_exc_group': 'project'
    },
    'standalone': {
        'long': '--standalone',
        'short': '-s',
        'action': 'store_true'
    },
    'spec': {
        'long': ['--spec', '--component'],
        'short': '-S'
    },
    'platform': {
        'long': '--platform',
        'short': '-P',
        'mut_exc_group': 'project'
    },
    'language': {
        'long': '--language',
        'short': '-L'
    },
    'other': {
        'long': ['--other', '--other-source-file'],
        'short': '-O',
        'action': 'append'
    },
    'core': {
        'long': ['--core', '--primitive-core'],
        'short': '-C',
        'action': 'append'
    },
    'rcc_static_prereq': {
        'long': ['--rcc-static-prereq', '--static-prereq'],
        'short': '-R',
        'action': 'append'
    },
    'rcc_dynamic_prereq': {
        'long': ['--rcc-dynamic-prereq', '--dynamic-prereq'],
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
        'action': 'store'
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
    'no_sdp': {
        'long': '--no-sdp',
        'short': '-u',
        'action': 'store_true'
    },
    'only_target': {
        'long': '--only-target',
        'short': '-T',
        'action': 'append'
    },
    'exclude_target': {
        'long': '--exclude-target',
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
    'top_module': {
        'long': ['--top-module','--module'],
        'short': '-M'
    },
    'prebuilt_core': {
        'long': ['--prebuilt-core','--prebuilt'],
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
    'no_libraries': {
        'long': ['--no-libraries','--no-depend'],
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
    'clean_all':{
        'long': '--clean-all',
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
    'generate': {
        'long': '--generate',
        'action': 'store_true'
    },
    'simulation': {
        'long': '--simulation',
        'action': 'store_true'
    },
    'execution': {
        'long': ['--execution', '--execute'],
        'action': 'store_true'
    },
    'optimize': {
        'long': '--optimize',
        'action': 'store_true'
    },
    'dynamic': {
        'long': '--dynamic',
        'action': 'store_true'
    },
    'worker': {
        'long': '--worker',
        'short': '-W',
        'action': 'append'
    },
    'hdl_rcc_platform': {
        'long': [
            '--rcc-hdl-platform',
            '--build-rcc-hdl-platform',
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
    'phase': {
        'long': '--phase',
        'choices': ["prepare", "run", "verify", "view"],
        'action': 'append'
    },
    'mode': {
        'long': '--mode',
        'choices': ["all", "gen", "gen_build", "prep_run_verify", "prep", "run", "prep_run",
                    "verify", "view", "clean_all", "clean_run", "clean_sim"],
    },
    'keep_simulations': {
        'long': '--keep-simulations',
        'action': 'store_true',
    },
    'accumulate_errors': {
        'long': '--accumulate-errors',
        'action': 'store_true',
    },
    'view': {
        'long': '--view',
        'action': 'store_true',
    },
    'case': {
        'long': '--case',
        'action': 'append'
    },
    'run_arg': {
        'long': '--run-arg',
        'action': 'append'
    },
    'run_before': {
        'long': ['--run-before', '--before'],
        'action': 'append'
    },
    'run_after': {
        'long': ['--run-after', '--after'],
        'action': 'append'
    },
    'remotes': {
        'long': '--remotes',
        'action': 'append'
    },
    'table': {
        'long': '--table',
        'action' : 'store_true',
        'mut_exc_group' : 'format',
     },
    'json': {
        'long': '--json',
        'action' : 'store_true',
        'mut_exc_group' : 'format',
     },
    'simple': {
        'long': '--simple',
        'action' : 'store_true',
        'mut_exc_group' : 'format',
     },
    'local_scope': {
        'long': '--local-scope',
        'action' : 'store_true',
        'mut_exc_group' : 'scope',
     },
    'global_scope': {
        'long': '--global_scope',
        'action' : 'store_true',
        'mut_exc_group' : 'scope',
     },
    'format': {
        'long': '--format',
        # latex is legacy and only applies to utilization
        'choices': [ 'simple', 'table', 'json', 'latex'],
        'mut_exc_group' : 'format',
     },
    'export': {
        'long': '--export',
        'action': 'store_true'
    }
}

# Verbs with nouns and options, including options referencing those above
verbs = {
    'build': {
        'options': {
            'name': {
                'nargs': '?',
            }
        },
        'nouns': {
            'default': get_noun,
            'application': {
                'options': {
                    'optimize': options['optimize'],
                    'dynamic': options['dynamic'],
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'workers_as_needed' : options['workers_as_needed'],
                    'xml_app': options['xml_app'],
                    'xml_dir_app': options['xml_dir_app'],
                    'export': options['export']
                }
            },
            'applications': {
                'options': {
                    'optimize': options['optimize'],
                    'dynamic': options['dynamic'],
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'workers_as_needed' : options['workers_as_needed'],
                    'export': options['export']
                }
            },
            'hdl': {
                'options': {
                    'workers_as_needed' : options['workers_as_needed'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform'],
                    'export': options['export']
                },
                'nouns': {
                    'assembly': {
                    },
                    'assemblies': None,
                    'device': None,
                    'platform': None,
                    'platforms': None,
                    'primitive': {
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
                    'hdl': options['hdl'],
                    'rcc': options['rcc'],
                    'optimize': options['optimize'],
                    'dynamic': options['dynamic'],
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'workers_as_needed' : options['workers_as_needed'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform'],
                    'export': options['export']
                }
            },
            'libraries': {
                'options': {
                    'hdl': options['hdl'],
                    'rcc': options['rcc'],
                    'optimize': options['optimize'],
                    'dynamic': options['dynamic'],
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'workers_as_needed' : options['workers_as_needed'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform'],
                    'export': options['export']
                }
            },
            'project': {
                'options': {
                    'hdl_assembly': options['hdl_assembly'],
                    'no_assemblies': options['no_assemblies'],
                    'hdl': options['hdl'],
                    'rcc': options['rcc'],
                    'optimize': options['optimize'],
                    'dynamic': options['dynamic'],
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'workers_as_needed' : options['workers_as_needed'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform']
                }
            },
            'test': {
                'options': {
                    'optimize': options['optimize'],
                    'dynamic': options['dynamic'],
                    'generate': options['generate'],
                    'workers_as_needed' : options['workers_as_needed'],
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform'],
                    'library': options['library'],
                    'hdl_library': options['hdl_library'],
                    'platform': options['platform'],
                    'export': options['export']
                }
            },
            'tests': {
                'options': {
                    'optimize': options['optimize'],
                    'dynamic': options['dynamic'],
                    'generate': options['generate'],
                    'workers_as_needed' : options['workers_as_needed'],
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform'],
                    'library': options['library'],
                    'hdl_library': options['hdl_library'],
                    'platform': options['platform'],
                    'export': options['export']
                }
            },
            'worker': {
                'options': {
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform'],
                    'library': options['library'],
                    'export': options['export']
                }
            },
            'component': {
                'options': {
                    'library': options['library'],
                    'export': options['export']
                }
            }
        }
    },
    'clean': {
        'options': {
            'name': {
                'nargs': '?',
            }
        },
        'nouns': {
            'default': get_noun,
            'application': {
                'options': {
                    'xml_app': options['xml_app'],
                    'xml_dir_app': options['xml_dir_app']
                }
            },
            'applications': {
                'options': {}
            },
            'hdl': {
                'options': {
                    'workers_as_needed' : options['workers_as_needed'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform'],
                    'platform': options['platform']
                },
                'nouns': {
                    'assembly': None,
                    'assemblies': None,
                    'device': None,
                    'platform': None,
                    'platforms': None,
                    'primitive': {
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
                    'hdl': options['hdl'],
                    'rcc': options['rcc'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform']
                }
            },
            'libraries': {
                'options': {
                    'hdl': options['hdl'],
                    'rcc': options['rcc'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform']
                }
            },
            'project': {
                'options': {
                    'clean_all': options['clean_all'],
                    'hdl_assembly': options['hdl_assembly'],
                    'no_assemblies': options['no_assemblies'],
                    'hdl': options['hdl'],
                    'rcc': options['rcc'],
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform']
                }
            },
            'test': {
                'options': {
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform'],
                    'simulation': options['simulation'],
                    'execution': options['execution'],
                    'library': options['library'],
                    'hdl_library': options['hdl_library'],
                    'platform': options['platform']
                }
            },
            'tests': {
                'options': {
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform'],
                    'simulation': options['simulation'],
                    'execution': options['execution'],
                    'library': options['library'],
                    'hdl_library': options['hdl_library'],
                    'platform': options['platform']
                }
            },
            'worker': {
                'options': {
                    'hdl_rcc_platform': options['hdl_rcc_platform'],
                    'rcc_platform': options['rcc_platform'],
                    'hdl_target': options['hdl_target'],
                    'hdl_platform': options['hdl_platform'],
                    'library': options['library']
                }
            },
            'component': {
                'options': {
                    'library': options['library']
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
            'default': get_noun,
            'application': {
                'options': {
                    'xml_app': options['xml_app'],
                    'xml_dir_app': options['xml_dir_app']
                }
            },
            'component': {
                'options': {
                    'name': None,
                    'file_only': options['file_only'],
                    'no_control': options['no_control'],
                    'platform': options['platform'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library'],
                    'project': options['project']
                }
            },
            'library': {
                'options': {
                    'pkg_prefix': options['pkg_prefix'],
                    'pkg_id': options['pkg_id'],
                    'pkg_name': options['pkg_name'],
                    'xml_include': options['xml_include'],
                    'include_dir': options['include_dir'],
                    'component_library': options['component_library'],
                    'primitive_library': options['primitive_library']
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
                    'card': {
                        'options' : {
                            'platform': options['platform']
                        }
                    },
                    'device': {
                        'options': {
                            'xml_include': options['xml_include'],
                            'include_dir': options['include_dir'],
                            'component_library': options['component_library'],
                            'primitive_library': options['primitive_library'],
                            'hdl_library': options['hdl_library'],
                            'library': options['library'],
                            'core': options['core'],
                            'emulates': options['emulates'],
                            'supports': options['supports'],
                            'exclude_platform': options['exclude_platform'],
                            'only_platform': options['only_platform'],
                            'only_target': options['only_target'],
                            'exclude_target': options['exclude_target'],
                            'spec': options['spec'],
                            'platform': options['platform']
                        }
                    },
                    'platform': {
                        'options': {
                            'xml_include': options['xml_include'],
                            'include_dir': options['include_dir'],
                            'component_library': options['component_library'],
                            'primitive_library': options['primitive_library'],
                            'core': options['core'],
                            'hdl_part': options['hdl_part'],
                            'time_freq': options['time_freq'],
                            'no_sdp': options['no_sdp']
                        }
                    },
                    'primitive': {
                        'options': {
                            'exclude_platform': options['exclude_platform'],
                            'only_platform': options['only_platform'],
                            'only_target': options['only_target'],
                            'exclude_target': options['exclude_target'],
                            'include_dir': options['include_dir'],
                        },
                        'nouns': {
                            'core': {
                                'options': {
                                    'no_libraries': options['no_libraries'],
                                    'prebuilt_core': options['prebuilt_core'],
                                    'top_module': options['top_module']
                                }
                            },
                            'library': {
                                'options': {
                                    'no_libraries': options['no_libraries'],
                                    'no_elaborate': options['no_elaborate']
                                }
                            }
                        }
                    },
                    'slot': {
                        'options' : {
                            'platform': options['platform'], # for a particular platform
                            'project': options['project']    # project level definition
                        }
                    }
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
                    'component_library': options['component_library'],
                    'primitive_library': options['primitive_library']
                }
            },
            'protocol': {
                'options': {
                    'platform': options['platform'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library'],
                    'project': options['project']
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
                    'project': options['project']
                }
            },
            'test': {
                'options': {
                    'spec': options['spec'],
                    'library': options['library'],
                    'hdl_library': options['hdl_library'],
                    'platform': options['platform']
                }
            },
            'worker': {
                'options': {
                    'xml_include': options['xml_include'],
                    'include_dir': options['include_dir'],
                    'component_library': options['component_library'],
                    'primitive_library': options['primitive_library'],
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
            'name': {
                'nargs': '?',
            }
        },
        'nouns': {
            'default': get_noun,
            'application': {
                'options': {
                    'xml_app': options['xml_app'],
                    'xml_dir_app': options['xml_dir_app']
                }
            },
            'component': {
                'options': {
                    'file_only': options['file_only'],
                    'project': options['project'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library'],
                    'platform': options['platform']
                }
            },
            'hdl': {
                'nouns': {
                    'assembly': None,
                    'card': None,
                    'device': {
                        'options': {
                            'hdl_library': options['hdl_library'],
                            'library': options['library'],
                            'platform': options['platform']
                        }
                    },
                    'platform': None,
                    'primitive': {
                        'nouns': {
                            'core': None,
                            'library': None
                        }
                    },
                    'slot': {
                        'options': {
                            'hdl_library': options['hdl_library'],
                            'platform': options['platform']
                        }
                    }
                }
            },
            'library': None,
            'libraries': None,
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
                    'library': options['library'],
                    'platform': options['platform']
                }
            },
            'test': {
                'options': {
                    'library': options['library'],
                    'hdl_library': options['hdl_library'],
                    'platform': options['platform']
                }
            },
            'worker': {
                'options': {
                    'hdl_library': options['hdl_library'],
                    'platform': options['platform'],
                    'library': {
                        'long': '--library',
                        'short': '-l'
                    }
                }
            }
        }
    },
    'refresh': {
        'options': {
            'name': {
                'nargs': '?',
            }
        },
        'nouns': {
            'default': get_noun,
            'project': None
        }
    },
    'register': {
        'options': {
            'name': {
                'nargs': '?',
            }
        },
        'nouns': {
            'default': get_noun,
            'project': None
        }
    },
    'run': {
        'options': {
            'name': {
                'nargs': '?',
            },
        },
        'nouns': {
            'default': get_noun,
            'application': {
                'options': {
                    'run_arg': options['run_arg'],
                    'run_before': options['run_before'],
                    'run_after': options['run_after'],
                    'xml_app': options['xml_app'],
                    'xml_dir_app': options['xml_dir_app']
                }
            },
            'applications': {
            },
            'library': {
                'options': {
                    'phase': options['phase'],
                    'mode': options['mode'],
                    'view': options['view'],
                    'accumulate_errors': options['accumulate_errors'],
                    'keep_simulations': options['keep_simulations'],
                    'only_platform': options['only_platform'],
                    'exclude_platform': options['exclude_platform']
                },
            },
            'libraries': {
                'options': {
                    'phase': options['phase'],
                    'mode': options['mode'],
                    'view': options['view'],
                    'accumulate_errors': options['accumulate_errors'],
                    'keep_simulations': options['keep_simulations'],
                    'only_platform': options['only_platform'],
                    'exclude_platform': options['exclude_platform']
                },
            },
            'project': {
                'options': {
                    'phase': options['phase'],
                    'mode': options['mode'],
                    'view': options['view'],
                    'accumulate_errors': options['accumulate_errors'],
                    'keep_simulations': options['keep_simulations'],
                    'only_platform': options['only_platform'],
                    'exclude_platform': options['exclude_platform']
                }
            },
            'test': {
                'options': {
                    'library': options['library'],
                    'platform': options['platform'],
                    'hdl_library': options['hdl_library'],
                    'phase': options['phase'],
                    'mode': options['mode'],
                    'view': options['view'],
                    'case': options['case'],
                    'accumulate_errors': options['accumulate_errors'],
                    'keep_simulations': options['keep_simulations'],
                    'only_platform': options['only_platform'],
                    'exclude_platform': options['exclude_platform']
                }
            },
            'tests': {
                'options': {
                    'library': options['library'],
                    'platform': options['platform'],
                    'hdl_library': options['hdl_library'],
                    'phase': options['phase'],
                    'mode': options['mode'],
                    'view': options['view'],
                    'accumulate_errors': options['accumulate_errors'],
                    'keep_simulations': options['keep_simulations'],
                    'only_platform': options['only_platform'],
                    'exclude_platform': options['exclude_platform'],
                },
            },
        },
    },
    'set': {
        'options': {
            # This is not the name of the noun, but the registry directory
            'name': {
                'nargs': '?',
            }
        },
        'nouns': {
            'registry': None
        }
    },
    'show': {
        'options': {
            'name': {
                'nargs': '?',
            },
            'table' : options['table'],
            'json' : options['json'],
            'simple' : options['simple'],
            'format' : options['format'],
            'local_scope' : options['local_scope'],
            'global_scope' : options['global_scope'],
        },
        'nouns': {
            'default': get_noun,
            'application': {
                'options': {
                    'xml_app': options['xml_app'],
                    'xml_dir_app': options['xml_dir_app']
                }
            },
            'component': {
                'options' : {
                    'project': options['project'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library'],
                    'platform': options['platform'],
                    'file_only': options['file_only'],
                }
            },
            'components': {
                'options' : {
                    'project': options['project'],
                    'local_scope': options['local_scope'],
                    'global_scope': options['global_scope'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library'],
                    'platform': options['platform']
                }
            },
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
                    'platforms': None,
                    'primitive': {
                        'nouns': {
                            'core': None,
                            'library': None
                        }
                    },
                    'slot': None,
                    'targets': None,
                    'worker': None,
                    'workers': None,
                }
            },
            'library': None,
            'libraries': {
                'options' : {
                    'local_scope': options['local_scope'],
                    'global_scope': options['global_scope'],
                }
            },
            'platforms': None,
            'prerequisites': None,
            'project': None,
            'projects': None,
            'protocol': {
                'options': {
                    'project': options['project'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library']
                }
            },
            'rcc': {
                'nouns': {
                    'platforms': None,
                    'targets': None,
                    'worker': None,
                    'workers': None,
                }
            },
            'registry': None,
            'spec': {
                'options': {
                    'project': options['project'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library'],
                    'platform': options['platform']
                }
            },
            'targets': None,
            'test': {
                'options': {
                    'library': options['library'],
                    'hdl_library': options['hdl_library'],
                    'platform': options['platform']
                }
            },
            'tests': {
                'options' : {
                    'local_scope': options['local_scope'],
                    'global_scope': options['global_scope'],
                    'hdl_library': options['hdl_library'],
                    'library': options['library'],
                    'platform': options['platform']
                }
            },
            'worker': {
                'options': {
                    'hdl_library': options['hdl_library'],
                    'platform': options['platform'],
                    'library': options['library'],
                }
            },
            'workers': {
                'options' : {
                    'hdl_library': options['hdl_library'],
                    'platform': options['platform'],
                    'library': options['library'],
                    'local_scope': options['local_scope'],
                    'global_scope': options['global_scope'],
                }
            },
        }
    },
    'unregister': {
        'options': {
            'name': {
                'nargs': '?',
            }
        },
        'nouns': {
            'default': get_noun,
            'project': None
        }
    },
    'unset': {
        'nouns': {
            'default': get_noun,
            'registry': None
        }
    },
    'utilization': {
        'options': {
            'name': {
                'nargs': '?',
            },
            'format' : options['format'],
            'hdl_platform' : options['hdl_platform'],
            'hdl_target' : options['hdl_target'],
        },
        'nouns': {
            'default': get_noun,
            'hdl': {
                'nouns': {
                    'assembly': None,
                    'assemblies': None,
                    'device': {
                        'options': {
                            'hdl_library': options['hdl_library'],
                            'library': options['library']
                        }
                    },
                    'platform': None,
                    'platforms': None,
                }
            },
            'library': None,
            'libraries': None,
            'project': None,
            'projects': None,
            'worker': {
                'options': {
                    'hdl_library': options['hdl_library'],
                    'platform': options['platform'],
                    'library': options['library'],
                }
            },
            'workers': {
                'options' : {
                    'local_scope': options['local_scope'],
                    'global_scope': options['global_scope'],
                }
            },
        }
    },
}

# Collection of options, common options, and verbs to be imported by ocpidev
args_dict = {
    'options': options,
    'verbs': verbs
}
