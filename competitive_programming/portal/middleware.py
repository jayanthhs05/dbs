from django.shortcuts import redirect

class AdminApprovalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.user.is_authenticated and 
            request.user.role == 'admin' and 
            not request.user.is_approved and 
            not request.path.startswith('/admin/')):
            return redirect('home')
        return self.get_response(request)