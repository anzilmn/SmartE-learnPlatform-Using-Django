from django.shortcuts import redirect
from django.urls import reverse

class BlockCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If user is logged in and blocked
        if request.user.is_authenticated:
            if hasattr(request.user, 'profile') and request.user.profile.is_blocked:
                # Allow them to see the blocked page and logout only
                allowed_urls = [reverse('blocked_page'), reverse('logout')]
                if request.path not in allowed_urls and not request.path.startswith('/admin/'):
                    return redirect('blocked_page')

        response = self.get_response(request)
        return response