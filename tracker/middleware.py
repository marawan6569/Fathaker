import re


class GetStatisticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip_address = self.get_client_ip(request)
        device_type = self.get_device_type(request)
        browser = self.get_browser(request)
        operating_system = self.get_operating_system(request)
        referer = request.META.get('HTTP_REFERER', None)
        user = request.user
        params = dict(request.GET)
        request_path = request.path

        print('-' * 50)
        print(ip_address)
        print(device_type)
        print(browser)
        print(operating_system)
        print(referer)
        print(user)
        print(params)
        print(request_path)
        print('-' * 50)

        response = self.get_response(request)
        return response

    @staticmethod
    def get_client_ip(request):
        """
        Get the client IP address from the request object.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def get_device_type(request):
        """
        Get the client device type from the User-Agent header.
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        print(user_agent)
        # Basic regex to detect device types
        if re.search('mobile|android|touch|webos|hpwos', user_agent):
            return 'Mobile'
        elif re.search('tablet|ipad', user_agent):
            return 'Tablet'
        else:
            return 'Desktop'

    @staticmethod
    def get_browser(request):
        """
        Get the client browser from the User-Agent header.
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        print(user_agent)

        if 'firefox' in user_agent:
            return 'Firefox'
        elif 'huaweibrowser' in user_agent:
            return 'Huawei Browser'
        elif 'chrome' in user_agent and 'safari' in user_agent:
            return 'Chrome'
        elif 'safari' in user_agent and 'chrome' not in user_agent:
            return 'Safari'
        elif 'msie' in user_agent or 'trident' in user_agent:
            return 'Internet Explorer'
        elif 'edge' in user_agent:
            return 'Edge'
        elif 'opera' in user_agent or 'opr' in user_agent:
            return 'Opera'
        else:
            return 'Unknown'

    @staticmethod
    def get_operating_system(request):
        """
        Get the client operating system from the User-Agent header.
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if 'windows' in user_agent:
            return 'Windows'
        elif 'harmonyos' in user_agent:
            return 'HarmonyOS'
        elif 'android' in user_agent:
            return 'Android'
        elif 'iphone' in user_agent or 'ipad' in user_agent:
            return 'IOS'
        elif 'macintosh' in user_agent or 'mac os' in user_agent:
            return 'MacOS'
        elif 'linux' in user_agent:
            return 'Linux'
        else:
            return 'Unknown'

