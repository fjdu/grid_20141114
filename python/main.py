import datetime
import os
workers    = ['numenor', 'moria', 'gondolin']
ntasks_max = [6, 6, 4]
only_night = [False, False, True]


dust_to_gas_mass_ratio_s = [1e-2]
disk_dust_masses = [5e-4, 1e-4, 5e-5, 1e-5]
star_spectral_types = ['A', 'B', 'F', 'G', 'K', 'M']

r_in_s = [1e-1, 1e0, 1e1, 5e1]
r_out_s = [4e2]

config_file_template = ''

lines_to_model = ['H2O ground', 'CO (6-5)', 'CO (10-9)']

config_file_lines = {
    'H2O ground': '',
    'CO (6-5)': '',
    'CO (10-9)': '',
}

spectral_to_temperature = \
    { 'O': 41.00e3,
      'B': 31.00e3,
      'A':  9.50e3,
      'F':  7.24e3,
      'G':  5.92e3,
      'K':  5.30e3,
      'M':  3.85e3,
    }

spectral_to_radius = \
    { 'O': 6.6,
      'B': 4.0,
      'A': 1.6,
      'F': 1.3,
      'G': 1.0,
      'K': 0.8,
      'M': 0.7,
    }

spectral_to_mass = \
    { 'O': 20.0,
      'B': 10.0,
      'A':  2.0,
      'F':  1.3,
      'G':  0.9,
      'K':  0.7,
      'M':  0.3,
    }


param_collection = [star_spectral_types, disk_dust_masses, dust_to_gas_mass_ratio_s, r_in_s, r_out_s]

templates = {
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

section_keys = ['grid', 'chem', 'hc', 'mc', 'dust', 'disk', 'rt', 'cell', 'ana', 'iter']


def update_config_info(templates, info, config_key, comment=''):
    for k in info.keys():
        if type(info[k]) == float:
            update_a_template(templates[config_key]['data'],
                k, '{0:.4e}'.format(info[k]), comment=comment)
        if type(info[k]) == int:
            update_a_template(templates[config_key]['data'],
                k, '{0:d}'.format(info[k]), comment=comment)
        if type(info[k]) == str:
            update_a_template(templates[config_key]['data'],
                k, '\'{0:s}\''.format(info[k]), comment=comment)


def update_a_template(template, key, new_value, comment=''):
    '''
    A template is simply a list of strings
    To update a template, first try to match a key-value pair in the format of
          key = value,
    then replace value with new_value.
    Note that key never contains space.
    '''
    c = '  ' + key + ' = ' + new_value + comment + '\n'
    not_found = True
    for i, t in enumerate(template):
        s = t.split()
        if len(s) == 0:
            continue
        if s[0] == key:
            template[i] = c
            not_found = False
            break
    if not_found:
        template.insert(1, c)
    return template


def generate_a_config_file(templates,
                           rin = 1e-1,
                           rout = 4e2,
                           d2g = 1e-2,
                           dust_mass = 1e-4,
                           star_type = 'G',
                           dump_dir = '/n/Users/fdu/now/storage/data_dump_201411/',
                           dump_sub_dir = '20141105_a0',
                           iter_dir = '/n/Users/fdu/now/storage/201411/20141105_a0/',
                           ):
    #
    def template_to_str(template):
        s = ''
        for k in section_keys:
            s += ''.join(template[k]['data'])
        return s
    #
    #comment = '  ! ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    comment = '  ! generated automatically'
    #
    ncol = 150
    n_max_num_of_cells = 10000
    #
    disk_info = {
        'a_disk%star_mass_in_Msun': spectral_to_mass[star_type],
        'a_disk%star_radius_in_Rsun': spectral_to_radius[star_type],
        'a_disk%star_temperature': spectral_to_temperature[star_type],
        'a_disk%andrews_gas%Md': dust_mass/d2g,
        'a_disk%andrews_gas%rin': rin,
        'a_disk%andrews_gas%rout': rout,
        'a_disk%andrews_gas%rc': rout,
        'a_disk%andrews_gas%hc': rout * 0.1,
        'a_disk%dustcompo(1)%andrews%Md':   dust_mass,
        'a_disk%dustcompo(1)%andrews%rin':  rin,
        'a_disk%dustcompo(1)%andrews%rout': rout,
        'a_disk%dustcompo(1)%andrews%rc':   rout,
        'a_disk%dustcompo(1)%andrews%hc':   rout*0.1,
    }
    grid_info = {
        'grid_config%rmin': rin, 
        'grid_config%rmax': rout,
        'grid_config%zmin': 0.0,
        'grid_config%zmax': rout,
        'grid_config%ncol': ncol,
        'grid_config%dr0':  min(rin * 0.2, (rout-rin) / float(ncol*3)),
        'grid_config%smallest_cell_size': rin  * 0.05,
        'grid_config%largest_cell_size':  rout * 0.05,
    }
    iter_info = {
        'a_disk_iter_params%max_num_of_cells': n_max_num_of_cells,
        'a_disk_iter_params%dump_common_dir': dump_dir,
        'a_disk_iter_params%dump_sub_dir_out': dump_sub_dir,
        'a_disk_iter_params%iter_files_dir': iter_dir,
        'a_disk_iter_params%dust2gas_mass_ratio_deflt': d2g,
    }
    rt_info = {
    }
    #
    update_config_info(templates, disk_info, 'disk', comment=comment)
    update_config_info(templates, grid_info, 'grid', comment=comment)
    update_config_info(templates, iter_info, 'iter', comment=comment)
    return template_to_str(templates)

def load_a_template(fname):
    with open(fname, 'r') as f:
        return f.readlines()

def load_templates(templates):
    for k in templates.keys():
        templates[k]['data'] = \
            load_a_template(os.path.join(template_dir, templates[k]['fname']))
        #print templates[k]['data']
    return templates

def generate_config_files(templates,
    base_dir = '/n/Users/fdu/now/',
    storage_dir = 'storage/data_dump_201411/',
    res_dir = 'storage/201411/',
    config_dir = '/n/Users/fdu/now/config_files/',
    ):
    dstamp = datetime.datetime.now().strftime('%Y%m%d-%H%M')
    for rin in r_in_s:
      for rout in r_out_s:
        for d2g in dust_to_gas_mass_ratio_s:
          for mdisk in disk_dust_masses:
            for sp in star_spectral_types:
              sub_dir = dstamp + \
                '_rin_{0:.2e}_rout_{1:.2e}_d2g_{2:.2e}_md_{3:.2e}_sp_{4:s}'.format( \
                rin, rout, d2g, mdisk, sp)
              cf = generate_a_config_file(templates,
                    rin = rin,
                    rout = rout,
                    d2g = d2g,
                    dust_mass = mdisk,
                    star_type = sp,
                    dump_dir = os.path.join(base_dir, storage_dir),
                    dump_sub_dir = '/' + sub_dir + '/',
                    iter_dir = os.path.join(base_dir, res_dir, sub_dir + '/') \
                    )
              cf_fname = 'conf_' + sub_dir + '.dat'
              with open(os.path.join(config_dir, cf_fname), 'w') as f:
                    f.writelines(cf)
    return


template_dir = '../template/'

templates = load_templates(templates)

#print generate_a_config_file(templates)
generate_config_files(templates)
