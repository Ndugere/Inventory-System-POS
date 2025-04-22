from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import logout

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            last_activity = request.session.get('last_activity')

            if last_activity:
                elapsed_time = now - timezone.datetime.fromisoformat(last_activity)
                if elapsed_time > timedelta(seconds=settings.SESSION_COOKIE_AGE):
                    logout(request)
                    request.session.flush()  # remove session data
            request.session['last_activity'] = now.isoformat()

        return self.get_response(request)
