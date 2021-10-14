from kubernetes import client, config

def check_system_namespace(i,system_namespace):
    try:
        namespace = str(i.metadata.namespace)
    except:
        namespace = 'None'
    if any([ _namespace in namespace for _namespace in system_namespace]):
        return True
    else:
        return False

def check_waiting_error(i,error_message):
    try:
        message = str(i.status.container_statuses[0].state.waiting.reason)
    except:
        message = None
    if message in error_message:
        return True
    else:
        return False

def check_forbidden_command(i,forbidden_command):
    try:
        command = i.spec.containers[0].command
    except:
        command = None
    for __command in forbidden_command:
        if any([__command in _com for _com in command]):
            return True
    return False

def check_restart_count(i,threshold=5):
    try:
        restart_count = int(i.status.container_status[0].restart_count)
    except:
        restart_count = 0
    if restart_count > threshold:
        return True
    else:
        return False

SYSTEM_NAMESPACE = ['kube', 'system','dashboard']
RESTART_THRESHOLD = 5              	          # Maximun restart_count
FORBIDDEN_COMMAND = ['sleep','tail','null']   # forbidden commands
ERROR_MESSAGE = ['ImagePullBackOff']          # waiting error message



config.load_kube_config()
v1 = client.CoreV1Api()
ret = v1.list_pod_for_all_namespaces()

for i in ret.items:
    if check_system_namespace(i,SYSTEM_NAMESPACE):
        continue	# if it is system namespace, continue(pass below code).
    if i.status.container_statuses:
        _namespace = str(i.metadata.namespace)
        _pod_name = str(i.metadata.name)
        # Check pod
        kill_policy = any([
            check_restart_count(i,RESTART_THRESHOLD),
            check_forbidden_command(i, FORBIDDEN_COMMAND),
            check_waiting_error(i, ERROR_MESSAGE),
        ])
        # delete pod
        if kill_policy:
            v1.delete_namespaced_pod(name=_pod_name,namespace=_namespace)
            #print(f'kill {_pod_name}')
                    
