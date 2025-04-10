from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/<str:username>/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),
    path("problems/", views.problem_list, name="problem_list"),
    path("problems/<int:problem_id>/", views.problem_detail, name="problem_detail"),
    path("problems/create/", views.create_problem, name="create_problem"),
    path('problems/edit/<int:problem_id>/', views.edit_problem, name='edit_problem'),
    path(
        "problems/<int:problem_id>/add-test-case/",
        views.add_test_case,
        name="add_test_case",
    ),
    path(
        "problems/<int:problem_id>/submit/",
        views.submit_solution,
        name="submit_solution",
    ),
    path(
        "submissions/<int:submission_id>/",
        views.submission_detail,
        name="submission_detail",
    ),
    path("submissions/", views.user_submissions, name="user_submissions"),
    path("contests/", views.contest_list, name="contest_list"),
    path("contests/<int:contest_id>/", views.contest_detail, name="contest_detail"),
    path("contests/create/", views.create_contest, name="create_contest"),
    path(
        "contests/<int:contest_id>/register/",
        views.register_contest,
        name="register_contest",
    ),
    path("comments/add/", views.add_comment, name="add_comment"),
    path("tags/create/", views.create_tag, name="create_tag"),
    path("leaderboard/", views.global_leaderboard, name="global_leaderboard"),
    path("search/", views.search, name="search"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path(
        "approve/admin/<str:model_name>/<int:obj_id>/",
        views.approve_content,
        name="approve_content",
    ),
    path("problems/my/", views.my_problems, name="my_problems"),
    path(
        "problems/delete/<int:problem_id>/", views.delete_problem, name="delete_problem"
    ),
    path("admin/delete-user/<int:user_id>/", views.delete_user, name="delete_user"),
    path(
        "admin/delete-problem/<int:problem_id>/",
        views.delete_problem_admin,
        name="delete_problem_admin",
    ),
]
