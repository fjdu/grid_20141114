import datetime
import time
import os

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


def load_templates(template_directory, info):
    for k in info.keys():
        info[k]['data'] = \
            load_a_template(os.path.join(template_directory,
                                         info[k]['fname']))
        #print info[k]['data']
    return info


def load_a_template(fname):
    with open(fname, 'r') as f:
        return f.readlines()


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
    Note that a key never contains space.
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
                           ncol = 150,
                           n_max_num_of_cells = 10000,
                           dist = 100.0,
                           dump_dir = None,
                           dump_sub_dir = None,
                           iter_dir = None,
                           section_keys = None,
                           ):
    #
    def template_to_str(template):
        s = ''
        for k in section_keys:
            s += ''.join(template[k]['data'])
        return s
    #
    #comment = '  ! ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    comment = '  ! GeneratedAutomatically'
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
        'grid_config%largest_cell_size':  rout * 0.02,
    }
    iter_info = {
        'a_disk_iter_params%max_num_of_cells': n_max_num_of_cells,
        'a_disk_iter_params%dump_common_dir': dump_dir,
        'a_disk_iter_params%dump_sub_dir_out': dump_sub_dir,
        'a_disk_iter_params%iter_files_dir': iter_dir,
        'a_disk_iter_params%dust2gas_mass_ratio_deflt': d2g,
    }
    rt_info = {
        'raytracing_conf%dist': dist,
    }
    #
    update_config_info(templates, disk_info, 'disk', comment=comment)
    update_config_info(templates, grid_info, 'grid', comment=comment)
    update_config_info(templates, iter_info, 'iter', comment=comment)
    update_config_info(templates, rt_info,   'rt',   comment=comment)
    return template_to_str(templates)

def generate_config_files(templates,
                          base_dir = None,
                          storage_dir = None,
                          res_dir = None,
                          config_dir = None,
                          section_keys = None,
                          param_collection = None,
                          lut_fname = None,
                          ):
    #
    from itertools import product, starmap
    from collections import namedtuple
    def named_product(**items):
        Product = namedtuple('Product', items.keys())
        return starmap(Product, product(*items.values()))
    #
    counter = 0
    dstamp = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
    info_this = [dstamp]
    cfiles = []
    #
    for p in named_product(**param_collection):
        p = p._asdict()
        counter += 1
        sub_dir = 'run_{0:03d}'.format(counter)
        #
        cf = generate_a_config_file(templates,
              rin = p['rin'],
              rout = p['rout'],
              d2g = p['d2g'],
              dust_mass = p['mdust'],
              star_type = p['sptype'],
              dump_dir = os.path.join(base_dir, storage_dir),
              dump_sub_dir = sub_dir + '/',
              iter_dir = os.path.join(base_dir, res_dir, sub_dir + '/'),
              section_keys = section_keys,
              )
        #
        info_this.append( \
            '{0:03d}: '.format(counter) + \
            ('rin = {0:.2e}, rout = {1:.2e}, d2g = {2:.2e}, ' + \
             'mdust = {3:.2e}, spectralType = {4:s}').\
            format(p['rin'], p['rout'], p['d2g'], p['mdust'], p['sptype']))
        #
        cf_fname = 'conf_' + sub_dir + '.dat'
        cfiles.append(cf_fname)
        #
        with open(os.path.join(config_dir, cf_fname), 'w') as f:
              f.writelines(cf)
    #
    with open(os.path.join(config_dir, lut_fname), 'w') as f:
          f.writelines('\n'.join(info_this))
    return cfiles
