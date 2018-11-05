import requests
import json
import requests_futures

def get_pod_list(prometheus_host):
    from concurrent.futures import ThreadPoolExecutor
    from concurrent.futures import as_completed
    
    base_query_url = 'https://{0}/api/v1/query?query='.format(prometheus_host)

    kube_pod_info_query = '(kube_pod_info * on(node) group_left(label_failure_domain_beta_kubernetes_io_zone) kube_node_labels)'

    kube_pod_info_results = requests.get(base_query_url + kube_pod_info_query)
    kube_pod_info_dict = json.loads(kube_pod_info_results.text)
    kube_pod_info_metrics = kube_pod_info_dict['data']['result']

    pods = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(assemble_pod, pod, prometheus_host) for pod in kube_pod_info_metrics]
        for future in as_completed(futures):
            pods.append(future.result())

    return pods

def assemble_pod(full_pod_info, prometheus_host):
    node = full_pod_info['metric'].get('node', 'Unknown')
    pod_name = full_pod_info['metric'].get('pod', 'Unknown')
    az = full_pod_info['metric'].get('label_failure_domain_beta_kubernetes_io_zone', 'Unknown')
    namespace = full_pod_info['metric'].get('namespace', 'Unknown')
    host_ip = full_pod_info['metric'].get('host_ip', 'Unknown')

    pod_info = get_pod_metrics(pod_name, prometheus_host)
    pod_info['name'] = pod_name
    pod_info['node'] = node
    pod_info['az'] = az
    pod_info['namespace'] = namespace
    pod_info['host_ip'] = host_ip

    return pod_info

def pod_info_parser(request):
    result = request.result()
    result_dict = json.loads(result.content)
    metrics = result_dict['data']['result']

    return metrics

def get_pod_metrics(pod, prometheus_host):
    from requests_futures.sessions import FuturesSession
    
    base_query_url = 'https://{0}/api/v1/query?query='.format(prometheus_host)

    phase_query = '(kube_pod_status_phase{{pod="{0}"}} == 1)'.format(pod)
    ready_query = '(kube_pod_status_ready{{pod="{0}"}} == 1)'.format(pod)
    created_at_query = 'kube_pod_created{{pod="{0}"}}'.format(pod)

    session = FuturesSession(max_workers=9)

    phase_request = session.get(base_query_url + phase_query)
    ready_request = session.get(base_query_url + ready_query)
    created_at_request = session.get(base_query_url + created_at_query)
    
    phase_object = pod_info_parser(phase_request)
    ready_object = pod_info_parser(ready_request)
    created_at_object = pod_info_parser(created_at_request)

    metrics = {
        'phase': get_at(phase_object, 0, {}).get('metric', {}).get('phase', 'error'),
        'ready': get_at(ready_object, 0, {}).get('metric', {}).get('condition', 'false'),
        'created_at': get_at(get_at(created_at_object, 0, {}).get('value', []), 1, 'unknown')
    }

    return metrics

def get_at(list, index, default=None):
  return list[index] if max(~index, index) < len(list) else default
