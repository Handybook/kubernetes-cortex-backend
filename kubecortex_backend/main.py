from flask import Blueprint, g, request
from flask import current_app as app
import kubecortex_backend.helpers.prometheus_helper as prometheus_helper
import json
import os

main = Blueprint('main', __name__)

prometheus_host = os.environ['PROMETHEUS_HOST']

@main.route('/pods')
def pods():
    try:
        pod_list = prometheus_helper.get_pod_list(prometheus_host)

        sort_by = request.args.get('sort_by', default='az')
        filter_key = request.args.get('filter_key')
        filter_value = request.args.get('filter_value')
        namespace_blacklist = request.args.get('namespace_blacklist')

        sorted_pod_list = sorted(pod_list, key=lambda k: k[sort_by])
        if filter_key != None and filter_value != None:
            final_pod_list = [pod for pod in sorted_pod_list if pod[filter_key] != filter_value]
        else:
            final_pod_list = sorted_pod_list

        if namespace_blacklist:
            final_pod_list = [pod for pod in final_pod_list if not pod['namespace'] in namespace_blacklist]

        return json.dumps(final_pod_list)
    except Exception as ex:
        print(ex)
        return str(ex), 500

#@main.route('/metrics')
#def metrics():
#    pod_name = request.args.get('podname')
#    rs = client.query('SELECT cpu_usage_nanocores / 1000000 FROM kubernetes_pod_container WHERE pod_name = \'{0}\' AND time > now() - 1h GROUP BY pod_name'.format(pod_name))
 #   cpu_points = list(rs.get_points())
 #   rs = client.query('SELECT memory_usage_bytes FROM kubernetes_pod_container WHERE pod_name = \'{0}\' AND time > now() - 1h GROUP BY pod_name'.format(pod_name))
 #   memory_points = list(rs.get_points())
 #   return json.dumps({
 #       "cpu": cpu_points,
 #       "memory": memory_points
 #   })

@main.after_request
def apply_cors_header(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

