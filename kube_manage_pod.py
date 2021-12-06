from kubernetes import client, config
from pprint import pprint
from datetime import datetime, timezone
import argparse

class pod_checker:
    SYSTEM_NAMESPACE = ['kube', 'system','dashboard']
    RESTART_THRESHOLD = 5              	          # Maximun restart_count
    FORBIDDEN_COMMAND = ['sleep','tail','null']   # forbidden commands
    ERROR_MESSAGE = ['ImagePullBackOff','ErrImagePull']          # waiting error message
    NOT_RUNNING_THRESHOLD = 2                     # threshold of pod not started days
    def __init__(self,
            pod,
            *args,
            **kwargs
            ):
        self.pod = pod
        assert pod_checker.container_status(self.pod)

        self.bool_system_namespace = pod_checker.check_system_namespace(self.pod)
        self.bool_restart_threshold = self.check_restart_count(self.pod)
        self.bool_error_message = self.check_error_message(self.pod)
        self.bool_forbidden_command = self.check_forbidden_command(self.pod)
        self.bool_not_running = self.check_container_not_running(self.pod)

        self.namespace = self.return_namespace(self.pod)
        self.pod_name = self.return_pod_name(self.pod)

    def check_kill(self,):
        kill_policy_list = [
                self.bool_system_namespace,
                self.bool_restart_threshold,
                self.bool_error_message,
                self.bool_forbidden_command,
                self.bool_not_running,
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
        self.break_command = 'None'
        return False

    def check_restart_count(self,i):
        threshold = pod_checker.RESTART_THRESHOLD
        try:
            self.restart_count = int(i.status.container_statuses[0].restart_count)
        except:
            self.restart_count = 0
        if self.restart_count > threshold:
            return True
        else:
            return False

    def check_container_not_running(self,i):
        threshold = pod_checker.NOT_RUNNING_THRESHOLD
        today = datetime.now(timezone.utc)
        try:
            container_status = i.status.container_statuses[-1].state
            running_state = container_status.running
            if running_state:
                self.running = True
                return False
            else:
                self.running = False
                date_delta = (today-container_status.terminated.finished_at).days
                if date_delta > threshold:
                    return True
                else:
                    return False
        except:
            self.running = False
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
            status = i.status.container_statuses
        except:
            status = None
        return status

    def pod_info(self,):

        _namespace = self.namespace
        _pod_name = self.pod_name
        _pod_running = self.running
        _restart_count = self.restart_count
        _command = self.break_command
        _error = self.message

        info_str = f'''namespace: {_namespace:13}
pod name: {_pod_name}
running: {_pod_running}
restart: {_restart_count}
command: {_command}
error: {_error}'''
        info = dict(
            namespace = _namespace,
            pod = _pod_name,
            restart_count = _restart_count,
            command = _command,
            error = _error,
            log = info_str,
        )
        return info
        


def main():
    parser = argparse.ArgumentParser(description='Kubernetes pod killer')
    parser.add_argument('--delete', action='store_true')
    parser.add_argument('--info',action='store_true')
    args = parser.parse_args()

    SYSTEM_NAMESPACE = ['kube', 'system','dashboard']
    RESTART_THRESHOLD = 5              	          # Maximun restart_count
    FORBIDDEN_COMMAND = ['sleep','tail','null','while true']   # forbidden commands
    ERROR_MESSAGE = ['ImagePullBackOff','ErrImagePull']          # waiting error message
    NOT_RUNNING_THRESHOLD = 2                       # Days of pod not running


    pod_checker.SYSTEM_NAMESPACE = SYSTEM_NAMESPACE
    pod_checker.RESTART_THRESHOLD = RESTART_THRESHOLD
    pod_checker.FORBIDDEN_COMMAND = FORBIDDEN_COMMAND
    pod_checker.ERROR_MESSAGE = ERROR_MESSAGE
    pod_checker.NOT_RUNNING_THRESHOLD = NOT_RUNNING_THRESHOLD

    config.load_kube_config()
    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces()
    #ret = v1.list_namespaced_pod('')           # select one pod
    deleted_pod = 0

    if not args.delete:
        print(f"POD IS NOT DELETED")
        print(f"If you want to delete, add '--delete' args")

    for i in ret.items:
        if pod_checker.check_system_namespace(i):
            continue	# if it is system namespace, continue(pass below code).

        if pod_checker.container_status(i):
            _pod_check = pod_checker(i)
            _namespace = _pod_check.namespace
            _pod_name = _pod_check.pod_name
            
            # Check pod
            kill_policy = any(_pod_check.check_kill())
            if args.info:
                print(f'==============================')
                print(_pod_check.pod_info()['log'])
                print(_pod_check.check_kill())

            # delete pod
            if kill_policy:
                deleted_pod += 1
                if args.delete:
                    print(f'kill pod:{_pod_name}, namespace:{_namespace}')
                    v1.delete_namespaced_pod(name=_pod_name,namespace=_namespace)
                else:
                    print(f'NOT DELETED kill pod:{_pod_name}, namespace:{_namespace}')
    if deleted_pod == 0:
        print(f"There is no pod to delete")
                    

if __name__ == '__main__':
    main()
