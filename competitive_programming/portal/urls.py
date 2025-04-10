# portal/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # User management
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    
    # Problems
    path('problems/', views.problem_list, name='problem_list'),
    path('problems/<int:problem_id>/', views.problem_detail, name='problem_detail'),
    path('problems/create/', views.create_problem, name='create_problem'),
    path('problems/<int:problem_id>/edit/', views.edit_problem, name='edit_problem'),
    path('problems/<int:problem_id>/add-test-case/', views.add_test_case, name='add_test_case'),
    
    # Submissions
    path('problems/<int:problem_id>/submit/', views.submit_solution, name='submit_solution'),
    path('submissions/<int:submission_id>/', views.submission_detail, name='submission_detail'),
    path('submissions/', views.user_submissions, name='user_submissions'),
    
    # Contests
    path('contests/', views.contest_list, name='contest_list'),
    path('contests/<int:contest_id>/', views.contest_detail, name='contest_detail'),
    path('contests/create/', views.create_contest, name='create_contest'),
    path('contests/<int:contest_id>/register/', views.register_contest, name='register_contest'),
    
    # Comments
    path('comments/add/', views.add_comment, name='add_comment'),
    
    # Tags
    path('tags/create/', views.create_tag, name='create_tag'),
    
    # Leaderboards
    path('leaderboard/', views.global_leaderboard, name='global_leaderboard'),
    
    # Search
    path('search/', views.search, name='search'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/approve/<str:model_name>/<int:obj_id>/', views.approve_content, name='approve_content'),
]
