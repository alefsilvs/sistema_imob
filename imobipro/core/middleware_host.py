from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class CanonicalDevHostMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host()
        host_no_port = host.split(':')[0]
        port = host.split(':')[1] if ':' in host else ''

        if host_no_port not in ['127.0.0.1', '0.0.0.0']:
            return None

        scheme = 'https' if request.is_secure() else 'http'
        target_host = 'localhost'
        target = f"{scheme}://{target_host}"
        if port:
            target += f":{port}"
        target += request.get_full_path()

        return redirect(target, permanent=False)
