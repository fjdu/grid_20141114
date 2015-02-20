import datetime
import time
import os
import physical_constants as phy
from math import exp, sqrt

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
        elif type(info[k]) == int:
            update_a_template(templates[config_key]['data'],
                k, '{0:d}'.format(info[k]), comment=comment)
        elif type(info[k]) == str:
            update_a_template(templates[config_key]['data'],
                k, '\'{0:s}\''.format(info[k]), comment=comment)
        elif type(info[k]) == bool:
            update_a_template(templates[config_key]['data'],
                k, '.true.' if info[k] else '.false.', comment=comment)
        else:
            pass


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
    tw_hya_UV_lumi = 7.0e29 # erg s-1, from 900 to 2000 Angstrom
    UV_range = (900.0, 2000.0)
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
    mc_info = {
        'mc_conf%use_blackbody_star': \
            tw_hya_UV_lumi > \
            calc_star_lumi_bb_CGS(spectral_to_temperature[star_type],
                                 spectral_to_radius[star_type],
                                 UV_range[0]*1e-8, UV_range[1]*1e-8),
        'mc_conf%TdustMax': max(2e3, est_Tdust(spectral_to_temperature[star_type],
                                     spectral_to_radius[star_type], rin) * 2.0)
    }
    #
    update_config_info(templates, disk_info, 'disk', comment=comment)
    update_config_info(templates, grid_info, 'grid', comment=comment)
    update_config_info(templates, iter_info, 'iter', comment=comment)
    update_config_info(templates, rt_info,   'rt',   comment=comment)
    update_config_info(templates, mc_info,   'mc',   comment=comment)
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


def check_system_resource():
    import psutil
    return (psutil.cpu_percent()*0.01,
            psutil.virtual_memory().percent*0.01)


def _open_and_lock_file(fname):
    import fcntl
    try:
        f = open(fname_task, 'r+')
    except:
        return 'failed', None
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return 'success', f
    except:
        return 'failed', None


def _unlock_file(f):
    import fcntl
    fcntl.flock(f, fcntl.LOCK_UN)
    return


def open_and_lock_file(fname):
    import time
    fname_tmp =fname + '_tmp{0:06d}'.format(int(time.time())%1000000)
    fname_lock = fname + '.lockfile'
    if os.path.exists(fname_lock):
        return 'locked', None
    with open(fname_tmp, 'w') as f:
        pass
    os.link(fname_tmp, fname_lock)
    os.remove(fname_tmp)
    try:
        f = open(fname, 'r+')
    except Exception:
        raise
    return 'success', f


def unlock_file(fname):
    fname_lock = fname + '.lockfile'
    os.remove(fname_lock)
    return


def check_task_todo(f):
    tasklist = []
    try:
        tasklist = f.readlines()
    except:
        return 'FAILED'
    if len(tasklist) == 0:
        return 'FINISHED'
    else:
        return tasklist[0].strip()


def update_task_file(f):
    f.seek(0)
    s = f.readlines()
    f.seek(0)
    f.truncate()
    if len(s) > 1:
        f.writelines(s[1:])
    return


def truncate_stdout_file(f_s, nline=2000, wait_time_seconds=180):
    while True:
        for fn in f_s:
            with open(fn, 'r') as f:
                s = f.readlines()
                l = len(s)
            if l > nline:
                with open(fn, 'w') as f:
                    f.writelines(s[-nline:])
                # print 'Truncating stdout file: ', fn
        time.sleep(wait_time_seconds)
    return


def wait_for_interaction():
    i_cmd = 1
    while True:
        s = raw_input('Input [{0:d}] '.format(i_cmd))
        i_cmd += 1
        n = len(s)
        if n > 0 and s.lower() == 'break':
            break
        try:
            #exec(s)
            c = compile(s, 'string', 'single')
            exec c
        except:
            #print 'Exception passed.'
            print 'Type break to exit this loop.'
            raise
    return



def exec_task(s_task, f_out):
    import subprocess
    print s_task
    subprocess.call(s_task.split(), stdout=f_out)
    return


def save_to_log(fname, s, mode='a', allow_empty=False):
    if allow_empty:
        with open(fname, mode) as f:
            if len(s.strip()) > 0:
                f.write(s)
    else:
        if len(s.strip()) > 0:
            with open(fname, mode) as f:
                f.write(s)
    return


def load_file_lines(fname):
    try:
        with open(fname, 'r') as f:
            return f.readlines()
    except:
        return []

def set_self_as_master(working_dir, host):
    f_lock = os.path.join(working_dir, 'master.lockfile')
    with open(f_lock, 'w') as f:
        f.write(host)
    return

def master_already_exist(working_dir):
    f_lock = os.path.join(working_dir, 'master.lockfile')
    if os.path.exists(f_lock):
        return True
    else:
        return False

def planck_B_lambda(T, lambda_CGS):
    TH = 1e-8
    tmp = (phy.phy_hPlanck_CGS * phy.phy_SpeedOfLight_CGS) / \
          (lambda_CGS * phy.phy_kBoltzmann_CGS * T)
    if tmp >= phy.phy_max_exp:
        return 0.0
    if tmp > TH:
        tmp = exp(tmp) - 1.0
    return 2e0*phy.phy_hPlanck_CGS * phy.phy_SpeedOfLight_CGS**2 / \
           lambda_CGS**5 / tmp


def calc_star_lumi_bb_CGS(T_K, R_Rsun, lammin_CGS, lammax_CGS,
                          rtol = 1e-4, atol = 1e0):
    from scipy.integrate import quad
    s = quad(lambda x: planck_B_lambda(T_K, x),
             lammin_CGS, lammax_CGS,
             epsrel = rtol, epsabs = atol)
    return s[0] * phy.phy_Pi * \
           (4.0 * phy.phy_Pi * (R_Rsun*phy.phy_Rsun_CGS)**2)


def est_Tdust(Tstar_K, Rstar_Rsun, R_AU):
    return Tstar_K * sqrt(Rstar_Rsun * phy.phy_Rsun_CGS / (phy.phy_AU2cm * R_AU))




def main_loop(host_name = 'moria',
              max_task = 4,
              max_pcpu = 0.6,
              log_dir = None,
              t_wait_seconds = 10,
              t_wait_seconds_long = 60,
              max_task_fname = None,
              fname_task = None):
    import time
    import subprocess
    from multiprocessing import Process, Manager
    #
    log_file = os.path.join(log_dir, 'log.' + host_name)
    log_running = os.path.join(log_dir, 'running.' + host_name)
    log_running_all = os.path.join(log_dir, 'running.all')
    log_finished = os.path.join(log_dir, 'finished.' + host_name)
    log_finished_all = os.path.join(log_dir, 'finished.all')
    log_error = os.path.join(log_dir, 'error_exit.all')
    log_status = os.path.join(log_dir, 'workers.status')
    #
    manager = Manager()
    #
    p_s = []
    f_stdout_s = []
    fname_stdout_s = manager.list()
    tasks_running = []
    #
    i_task = 0
    no_task_left = False
    n_task_running = 0
    p_clean_stdout = Process(target = truncate_stdout_file, args=(fname_stdout_s,))
    p_clean_stdout.start()
    #
    while True:
        #
        still_running = [_p.is_alive() for _p in p_s]
        len_p_s = len(p_s)
        n_task_running = sum(still_running)
        _p_s = []
        _t_r = []
        _t_f = []
        _t_e = []
        for i in xrange(len_p_s):
            if not still_running[i]:
                f_stdout_s[i].close()
                p_s[i].join()
                _t_f.append(tasks_running[i])
                if p_s[i].exitcode != 0:
                    _t_e.append(tasks_running[i])
            else:
                _p_s.append(p_s[i])
                _t_r.append(tasks_running[i])
        p_s = _p_s
        tasks_running = _t_r
        tasks_finished = _t_f
        tasks_finished_error = _t_e
        #
        tasks_finished_all = [_.strip() for _ in load_file_lines(log_finished_all)] \
                             + tasks_finished
        tasks_finished_all = list(set(tasks_finished_all))
        #
        tasks_running_all = [_.strip() for _ in load_file_lines(log_running_all)] \
                            + tasks_running
        tasks_running_all = list(set(tasks_running_all))
        tasks_running_all = [_ for _ in tasks_running_all if _ not in tasks_finished_all]
        #
        tasks_finished.sort()
        tasks_finished_all.sort()
        tasks_finished_error.sort()
        ## !! tasks_running.sort()  # DO NOT sort!!
        tasks_running_all.sort()
        #
        save_to_log(log_running, '\n'.join(tasks_running), mode='w', allow_empty=no_task_left)
        save_to_log(log_running_all, '\n'.join(tasks_running_all), mode='w', allow_empty=no_task_left)
        save_to_log(log_finished, '\n'.join(tasks_finished) + \
                                  ('\n' if len(tasks_finished)>=1 else ''), mode='a')
        save_to_log(log_finished_all, '\n'.join(tasks_finished_all), mode='w')
        save_to_log(log_error, '\n'.join(tasks_finished_error), mode='a')
        #
        if n_task_running == 0 and no_task_left:
            break
        if n_task_running > 0 and no_task_left:
            # Wait for the running tasks to finish, or for the new task to come in
            time.sleep(t_wait_seconds_long)
        #
        max_task_realtime = load_file_lines(max_task_fname)
        if len(max_task_realtime) > 0:
            try:
                max_task = int(max_task_realtime[0])
            except:
                pass
        #
        pcpu, pvmem = check_system_resource()
        resource_available = (pcpu < max_pcpu and n_task_running < max_task)
        #
        if not resource_available:
            time.sleep(t_wait_seconds_long)
            continue
        #
        sfopen, f = open_and_lock_file(fname_task)
        #
        if sfopen != 'success':
            print 'Faile to open the task file:'
            print fname_task
            print 'Will retry in {0:d} seconds.'.format(t_wait_seconds)
            time.sleep(t_wait_seconds)
            continue
        #
        no_task_left = False
        s_task = check_task_todo(f)
        #
        if s_task == 'FINISHED':
            unlock_file(fname_task)
            f.close()
            no_task_left = True
            continue
        if s_task == 'FAILED':
            unlock_file(fname_task)
            f.close()
            print 'Cannot read the task file!'
            break
        #
        update_task_file(f)
        unlock_file(fname_task)
        f.close()
        #
        i_task += 1
        fname_stdout = os.path.join(log_dir,
                       'stdout.' + host_name + \
                       '.{0:03d}'.format(i_task))
        f_stdout = open(fname_stdout, 'a')
        f_stdout_s.append(f_stdout)
        fname_stdout_s.append(fname_stdout)
        #
        p_s.append(Process(target=exec_task, args=(s_task, f_stdout)))
        tasks_running.append(s_task)
        #
        print 'Running task {0:5d}'.format(i_task)
        #
        p_s[-1].start()
        #
        dstamp = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        #
        save_to_log(log_file, dstamp + ': ' + s_task + '\n')
        save_to_log(log_status, dstamp + ': ' + host_name + ': ' + s_task + '\n')
        #
        time.sleep(t_wait_seconds)
    #
    for f in f_stdout_s:
        f.close()
    p_clean_stdout.terminate()
    print 'Tasks finished.'
    return 0

