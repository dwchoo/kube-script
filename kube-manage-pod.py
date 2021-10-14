from kubernetes import client, config

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


restart_threshold = 5                         # Maximun restart_count
error_message = ['ImagePullBackOff']          # waiting error message
forbidden_command = ['sleep','tail','null']   # forbidden commands


config.load_kube_config()
v1 = client.CoreV1Api()
ret = v1.list_pod_for_all_namespaces()

for i in ret.items:
	_namespace = str(i.metadata.namespace)
	if 'kube' in _namespace:
		continue
	if i.status.container_statuses:
		_pod_name = str(i.metadata.name)
		kill_policy = any([
			check_restart_count(i,restart_threshold),
			check_forbidden_command(i, forbidden_command),
			check_waiting_error(i, error_message),
		])
		if kill_policy:
			v1.delete_namespaced_pod(name=_pod_name,namespace=_namespace)
