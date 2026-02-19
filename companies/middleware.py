from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin


class CompanyMiddleware(MiddlewareMixin):
    """
    Middleware to set company context for multi-tenancy.
    Sets request.company based on logged-in user's company.
    """
    
    def process_request(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, 'company'):
                request.company = request.user.company
            else:
                request.company = None
        else:
            request.company = None
        return None

