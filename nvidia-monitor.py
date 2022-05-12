#!/usr/bin/awk BEGIN{a=ARGV[1];sub(/[a-z_.]+$/,".venv/bin/python",a);system(a"\t"ARGV[1])}
import time
from pynvml import *
from pynvml.smi import nvidia_smi

TIMESTAMP = 0

nvmlInit()
gpus_count = nvmlDeviceGetCount()
for index in range(gpus_count):
    _handle = nvmlDeviceGetHandleByIndex(index)
    _process_list = nvmlDeviceGetComputeRunningProcesses_v2(_handle)
    if _process_list:
        _tmp_process_util_list = nvmlDeviceGetProcessUtilization(_handle,TIMESTAMP)
        TIMESTAMP = max(min((s.timeStamp for s in _tmp_process_util_list), default=0) - 100000, 0)
        _process_util_list = nvmlDeviceGetProcessUtilization(_handle,TIMESTAMP)
        print(f'index : {index} process : {[__proc.pid for __proc in _process_list]}')
        print(f'index : {index} process_mem : {[__poc.usedGpuMemory for __poc in _process_list]}')
        print(f'index : {index} process_name : {[nvmlSystemGetProcessName(__poc.pid) for __poc in _process_list]}')
        print(f'index : {index} process_sm : {[__proc.smUtil for __proc in _process_util_list]}')
    #_G_process_list = nvmlDeviceGetGraphicsRunningProcesses_v2(_handle)
    #if _G_process_list:
    #    print(f'index : {index} G-process : {[__poc.pid for __poc in _G_process_list]}')
