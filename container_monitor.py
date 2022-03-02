# -*- coding: utf-8 -*-
from kubernetes import config, client
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

import pandas as pd
from datetime import datetime, timedelta
from copy import deepcopy

GPU_USAGE_COMMAND = 'nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits'
GPU_PID_COMMAND = 'nvidia-smi --query-compute-apps=pid --format=csv,noheader'
CPU_USAGE_PID = 'ps -p <pid> -o %cpu --no-header'
CPU_TOP_PID = 'ps ahux --sort=-c'
'''
### command result ###
0
1
0
0
# there are percentage of usage of each gpu
'''

# It show total cpu usage(not only my container)
def get_cpu_usage(result_raw):
    assert len(result_raw) > 5
    result_usage = result_raw.splitlines()
    '''
    # command: ps ahux --sort=-c
    # result_splited_data
     'root     70679  0.2  0.0  56656  7080 pts/1    Ss+  13:00   0:02 /bin/zsh',
     'root         1  0.0  0.0  21776  3408 pts/0    Ss+  Feb21   0:00 /bin/bash /root/run_server.sh',
     'root        14  0.0  0.0  72308  4004 ?        Ss   Feb21   0:00 /usr/sbin/sshd',
     'root        15  0.0  0.0  21776  1772 pts/0    S+   Feb21   0:00 /bin/bash /root/run_server.sh',
     'root        16  0.0  0.0 869964 85184 pts/0    Sl+  Feb21   2:06 /usr/bin/python3.7 /usr/local/bin/jupyter-lab',
     'root        17  0.0  0.0 623004 47692 pts/0    Sl+  Feb21   0:01 /usr/lib/code-server/lib/node /usr/lib/code-server',
     'root        38  0.0  0.0 623980 47484 pts/0    Sl+  Feb21   0:07 /usr/lib/code-server/lib/node /usr/lib/code-server',
     'root        59  0.0  0.0      0     0 pts/0    Z+   Feb21   0:02 [TabNine] <defunct>',
     'root      3982  0.0  0.0  36096 11376 ?        Ss   Feb24   1:08 tmux',
     'root      4221  0.0  0.0  60476  8868 pts/2    Ss+  Feb24   0:06 -zsh',
     'root     34085  0.0  0.0  56296  6568 pts/3    Ss   Feb24   0:00 -zsh',
     'root     34200  0.0  0.0 338152 52260 pts/3    Sl+  Feb24   2:35 /usr/bin/python3.7 /usr/local/bin/ipython',
     'root     50753  0.0  0.0  60116  8588 pts/4    Ss+  Feb24   0:14 -zsh',
     'root     70889  0.0  0.0   4648   812 ?        S    13:15   0:00 /bin/sh -c ps ahux --sort=-c',
     'root     70890  0.0  0.0  37804  3324 ?        R    13:15   0:00 ps ahux --sort=-c'
    '''
    process_list_dict = []
    for index, data in enumerate(result_usage):
        _splited_data = data.split()
        _pid = _splited_data[1]
        _usage=float(_splited_data[2])
        _command=' '.join(_splited_data[10:])
        if _usage > 0.1:
            process_list_dict.append(dict(
                pid=_pid,
                usage=_usage,
                command=_command))
            # process_list_dict = [{'pid': '70679', 'usage': 0.2, 'command': '/bin/zsh'}]
        if index > 5:
            break
    if len(process_list_dict) < 0:
        return True
    return process_list_dict # process_list_dict = [{'pid': '70679', 'usage': 0.2, 'command': '/bin/zsh'}]


def get_gpu_usage(result_raw):
    # check the container has a gpu
    if len(result_raw) < 1:
        return False
    if 'No' in result_raw:
        return False
    # return gpu usage
    gpus_usage = [float(data) for data in result_raw.splitlines()]
    num_gpus = len(gpus_usage)
    return gpus_usage



    
# test shell command
def test_code(command):
    import subprocess
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    result_raw = result.stdout.decode('utf-8')
    #result_raw
    return result_raw


def exec_commands(api_instance,pod_name,namespace,command):
    try:
        resp = api_instance.read_namespaced_pod(
            name=pod_name,
            namespace=namespace,
        )
    except ApiException as e:
        if e.status != 404:
            print("EXEC Unknown error: %s" % e)
            return False
        resp = api_instance.read_namespaced_pod(
            name = pod_name,
            namespace=namespace,
        )
        if resp.status.phase != 'Running':
            return False
        
    exec_command = ['/bin/bash' ,'-c',command]
    resp = stream(api_instance.connect_get_namespaced_pod_exec,
                  pod_name,
                  namespace,
                  command=exec_command,
                  stderr=True, stdin=True,
                  stdout=True, tty=False,
                  )
    return str(resp)

class process_checker:
    CPU_USAGE_THRESHOLD=30.0
    GPU_USAGE_THRESHOLD=1.0
    LIMITLISS_USER = ['pusan']
    def __init__(self,api_instance, pod_name, namespace):
        self.api_instance = api_instance
        self.pod_name = pod_name
        self.namespace = namespace
        
        self.cpu_usage = self.return_cpu_usage()
        self.gpu_usage = self.return_gpu_usage()
        
        self.bool_cpu_usage = self.return_bool_cpu_usage()
        self.bool_gpu_usage = self.return_bool_gpu_usage()
        

        
    def return_cpu_usage(self,):
        command = CPU_TOP_PID
        cpu_usage_raw = self.exec_commands(command)
        cpu_usage = get_cpu_usage(cpu_usage_raw)
        return cpu_usage
        
    def return_gpu_usage(self,):
        command = GPU_USAGE_COMMAND
        gpu_usage_raw = self.exec_commands(command)
        gpu_usage = get_gpu_usage(gpu_usage_raw)
        return gpu_usage
    
    def return_bool_cpu_usage(self,):
        threshold = process_checker.CPU_USAGE_THRESHOLD
        cpu_usage = self.cpu_usage
        if cpu_usage == False:
            return False
        if cpu_usage == True:
            return True
        elif all([ pid_usage.get('usage',0.0) < threshold \
                for pid_usage in cpu_usage]):
            return True
        return False
    
    def return_bool_gpu_usage(self,):
        threshold = process_checker.GPU_USAGE_THRESHOLD
        gpu_usage = self.gpu_usage
        if gpu_usage == False:
            return False
        if gpu_usage == True:
            return True
        elif all([ pid_usage < threshold for pid_usage in gpu_usage]):
            return True
        return False
        
    def exec_commands(self,command):
        results = exec_commands(
            self.api_instance,
            self.pod_name,
            self.namespace,
            command,
        )
        return results
    
    
class process_manager:
    TIME_DELTA = 2
    SAFE_THRESHOLD = 4
    COLUMN = dict(
        namespace='object',
        pod_name='object',
        report='datetime64',
        check='datetime64',
        expire='datetime64',
        safe_count='int8',
    )
    def __init__(self,manage_list_path):
        self.now_time = datetime.now()
        pass
    
    
    def generate_data(self, namespace, pod_name):
        dict_data = dict(
            namespace = namespace,
            pod_name  = pod_name,
            report    = deepcopy(self.now_time),
            check     = deepcopy(self.now_time),
            expire    = self.now_time + \
                            timedelta(hours=process_manager.TIME_DELTA),
            safe_count = 0,
        )
        return dict_data
    
    def generate_DataFrame():
        column = process_manager.COLUMN
        df = pd.DataFrame(columns=column.keys()).astype(column)
        return df
    


#    def add_new_data(dict_data,DataFrame):
#        DataFrame = DataFrame.append(dict_data, ignore_index=True)
#        return DataFrame
#
#    def return_index_find_data(namespace,pod_name,DataFrame):
#        df = DataFrame
#        index = df.index[(df['namespace'] == namespace) & (df['pod_name']==pod_name)].tolist()
#        return index_list
#
#    def update_check(index,DataFrame):
#        df = DataFrame
#        df.loc[index,'check'] = datetime.now()
#
#    # mybe not use
#    def update_expire(index,DataFrame):
#        df = DataFrame
#        df.loc[index,'expire'] = datetime.now() + timedelta(hours=TIME_DELTA)
#
#    # mybe not use
#    def update_safe_count(index,DataFrame):
#        df = DataFrame
#        df.loc[index,'safe_count'] += 1
#
#    def remove_data(index, DataFrame):
#        df = DataFrame
#        df.drop(index, inplace=True)
#        df.reset_index(inplace=True)
#
#
#    def check_safe_count_list(DataFrame):
#        df = DataFrame
#        index_list = df.index[ df['safe_count'] >= SAFE_THRESHOLD].tolist() # change SAFE_THRESHOLD
#        return index_list
#
#    def check_not_updated_pod(DataFrame):
#        df = DataFrame
#        now_time = datatime.now()
#        index_list = df.index[ df['expire'] < now_time].tolist()
#        return index_list
#
#    def check_pod_expire(index,DataFrame):
#        df = DataFrame
#        now_time = datetime.now()
#        exipre_time = df.loc[index,'expire']
#        remain_time = (expire_time - now_time).days
#        if remain_time < 0:
#            return True
#        return False


    
    
    
    
    
if __name__ == '__main__':
    config.load_kube_config()
    api_instance = client.CoreV1Api()
    #try:
    #    c = Configuration().get_default_copy()
    #except AttributeError:
    #    c = Configuration()
    #    c.assert_hostname = False
    #Configuration.set_default(c)
    #api_instance = core_v1_api.CoreV1Api()
    
    pod_name = 'dwchoo-tf'
    namespace = 'id201899212'
    
    my_pod = process_checker(
        api_instance,
        pod_name,
        namespace,
    )
    
    cpu_bool = my_pod.bool_cpu_usage
    gpu_bool = my_pod.bool_gpu_usage
    
    cpu_usage = my_pod.cpu_usage
    gpu_usage = my_pod.gpu_usage
    
    print(f"""cpu : {cpu_usage} 
cpu bool : {cpu_bool}
gpu : {gpu_usage}
gpu bool : {gpu_bool}
""")