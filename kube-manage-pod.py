from kubernetes import client, config
from pprint import pprint

class pod_checker:
    SYSTEM_NAMESPACE = ['kube', 'system','dashboard']
    RESTART_THRESHOLD = 5              	          # Maximun restart_count
    FORBIDDEN_COMMAND = ['sleep','tail','null']   # forbidden commands
    ERROR_MESSAGE = ['ImagePullBackOff','ErrImagePull']          # waiting error message
    def __init__(self,
            pod,
            *args,
            **kwargs
            ):
        self.pod = pod
        assert pod_checker.container_status(self.pod)

        self.bool_system_namespace = pod_checker.check_system_namespace(self.pod)
        self.bool_restart_threshold = self.check_restart_count(self.pod)
        self.bool_error_message = self.check_error_message
        self.bool_forbidden_command = self.check_forbidden_command(self.pod)

        self.namespace = self.return_namespace(self.pod)
        self.pod_name = self.pod_name(self.pod)

    def check_kill(self,):
        kill_policy_list = [
                self.bool_system_namespace,
                self.bool_restart_threshold,
                self.bool_error_message,
                self.bool_forbidden_command,
            ]
        return kill_policy_list


    @classmethod
    def check_system_namespace(cls,i):
        system_namespace = cls.SYSTEM_NAMESPACE
        try:
            namespace = str(i.metadata.namespace)
        except:
            namespace = 'None'
        if any([ _namespace in namespace for _namespace in system_namespace]):
            return True
        else:
            return False

    def check_error_message(self,i):
        error_message = pod_checker.ERROR_MESSAGE
        try:
            self.message = str(i.status.container_statuses[0].state.waiting.reason)
        except:
            self.message = 'None'
        if self.message in error_message:
            return True
        else:
            return False

    def check_forbidden_command(self,i):
        forbidden_command = pod_checker.FORBIDDEN_COMMAND
        try:
            command = i.spec.containers[0].command
            args    = i.spec.containers[0].args
        except:
            command = ['None']
            args    = ['None']
        for __command in forbidden_command:
            if any([__command in _com for _com in command]):
                self.break_command = __command
                return True
            if any([__command in _args for _args in args]):
                self.break_command = __command
                return True
        return False

    def check_restart_count(self,i):
        threshold = pod_checker.RESTART_THRESHOLD
        try:
            self.restart_count = int(i.status.container_status[0].restart_count)
        except:
            self.restart_count = 0
        if self.restart_count > threshold:
            return True
        else:
            return False

    def return_namespace(self,i):
        try:
            namespace = str(i.metadata.namespace)
        except:
            namespace = 'None'
        return namespace

    def return_pod_name(self, i):
        try:
            pod_name = i.metadata.name
        except:
            pod_name = 'None'
        return pod_name

    @classmethod
    def container_status(cls,i):
        try:
            status = i.status.container_status
        except:
            status = None
        return status

    def pod_info(self,):

        _namespace = self.namespace
        _pod_name = self.pod_name
        _restart_count = self.restart_count
        _command = self.break_command
        _error = self.message

        info_str = f'namespace: {_namespace:13}, \
                pod: {_pod_name}, \
                restart: {_restart_count}\
                command: {_command}\
                error: {_error}'
        info = dict(
            namespace = _namespace,
            pod = _pod_name,
            restart_count = _restart_count,
            command = _command,
            error = _error,
            log = info_str,
        )
        return info
        

SYSTEM_NAMESPACE = ['kube', 'system','dashboard']
RESTART_THRESHOLD = 5              	          # Maximun restart_count
FORBIDDEN_COMMAND = ['sleep','tail','null']   # forbidden commands
ERROR_MESSAGE = ['ImagePullBackOff','ErrImagePull']          # waiting error message

pod_checker.SYSTEM_NAMESPACE = SYSTEM_NAMESPACE
pod_checker.RESTART_THRESHOLD = RESTART_THRESHOLD
pod_checker.FORBIDDEN_COMMAND = FORBIDDEN_COMMAND
pod_checker.ERROR_MESSAGE = ERROR_MESSAGE


config.load_kube_config()
v1 = client.CoreV1Api()
ret = v1.list_pod_for_all_namespaces()


for i in ret.items:
    #if pod_checker.check_system_namespace(i)
    if pod_checker.check_system_namespace(i):
        continue	# if it is system namespace, continue(pass below code).

    if pod_checker.container_status(i):
        _pod_check = pod_checker(i)
        _namespace = _pod_check.namespace
        _pod_name = _pod_check.pod_name
        # Check pod
        kill_policy = any(_pod_check.check_kill())
        pprint(_pod_check.pod_info()['log'])
        pprint(_pod_check.check_kill())
        # delete pod
        #if kill_policy:
        #    v1.delete_namespaced_pod(name=_pod_name,namespace=_namespace)
        #    print(f'kill pod:{_pod_name}, namespace:{_namespace}')
                    
