import datetime
import time
import os

workers    = ['numenor', 'moria', 'gondolin']
ntasks_max = [6, 6, 4]
only_night = [False, False, True]


dust_to_gas_mass_ratio_s = [1e-2]
disk_dust_masses = [1e-4, 5e-4, 1e-5, 5e-5]
star_spectral_types = ['A', 'B', 'F', 'G', 'K', 'M']

r_in_s = [1e0, 5.0, 1e1, 5e1]
r_out_s = [4e2]

config_file_template = ''

lines_to_model = ['H2O ground', 'CO (6-5)', 'CO (10-9)']

config_file_lines = {
    'H2O ground': '',
    'CO (6-5)': '',
    'CO (10-9)': '',
}

param_collection = {'sptype': star_spectral_types,
                    'mdust':  disk_dust_masses,
                    'd2g':    dust_to_gas_mass_ratio_s,
                    'rin':    r_in_s,
                    'rout':   r_out_s}

section_keys = ['grid', 'chem', 'hc', 'mc', 'dust', 'disk', 'rt', 'cell', 'ana', 'iter']

working_dir = '/n/Users/fdu/now/'
template_dir = os.path.join(working_dir, 'grid_20141114/template/')
config_dir = os.path.join(working_dir, 'grid_20141114/config_files/')
storage_dir = os.path.join(working_dir, 'grid_20141114/data_dump/')
res_dir = os.path.join(working_dir, 'grid_20141114/results/')
executable = os.path.join(working_dir, 'src/rac')

templates_info = {
    'disk': {'fname': 'disk_configure_template.dat', 'data': None},
    'grid': {'fname': 'grid_configure_template.dat', 'data': None},
    'hc':   {'fname': 'heating_cooling_configure_template.dat', 'data': None},
    'chem': {'fname': 'chemistry_configure_template.dat', 'data': None},
    'dust': {'fname': 'dustmix_configure_template.dat', 'data': None},
    'cell': {'fname': 'cell_configure_template.dat', 'data': None},
    'mc':   {'fname': 'montecarlo_configure_template.dat', 'data': None},
    'ana':  {'fname': 'analyse_configure_template.dat', 'data': None},
    'iter': {'fname': 'iteration_configure_template.dat', 'data': None},
    'rt':   {'fname': 'raytracing_configure_template.dat', 'data': None},
}

from functions import *

templates = load_templates(template_dir, templates_info)

if not os.access(config_dir, os.F_OK):
    os.mkdir(config_dir)

cfiles = generate_config_files(templates,
                               base_dir = working_dir,
                               storage_dir = storage_dir,
                               res_dir = res_dir,
                               config_dir = config_dir,
                               section_keys = section_keys,
                               param_collection = param_collection,
                               lut_fname = 'LUT.dat')

#for cf in cfiles:
#    while True:
#        if cpu_usage() < 0.5 and memory_usage() < 0.5:
#           executable + ' ' + os.path.join(config_dir, cf)
#            break
#        else:
#            time.sleep(60)
#        time.sleep(5)
