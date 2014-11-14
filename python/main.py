workers    = ['numenor', 'moria', 'gondolin']
ntasks_max = [6, 6, 4]
only_night = [False, False, True]


gas_to_dust_mass_ratio_s = [1e2]
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


param_collection = [star_spectral_types, disk_dust_masses, gas_to_dust_mass_ratio_s, r_in_s, r_out_s]


def generate_config_files():
    return


