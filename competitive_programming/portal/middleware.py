from django.shortcuts import redirect
from django.contrib import messages

class AdminApprovalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        safe_paths = [
            '/', '/login/', '/logout/', '/profile/',
            '/problems/my/', '/problems/create/', '/contests/create/', '/problems/edit/'
        ]
        
        if (request.user.is_authenticated and 
            request.user.role in ['admin', 'problem_setter'] and 
            not request.user.is_approved and
            not any(request.path.startswith(url) for url in safe_paths)):
            
            messages.warning(request, "Your account requires approval")
            return redirect('home')
            
        return self.get_response(request)
