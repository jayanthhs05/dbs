from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import *
from .forms import *

import random


def register_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect("home")
    else:
        form = UserRegistrationForm()
    return render(request, "portal/auth/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

                next_url = request.GET.get("next", "home")
                if next_url == request.path:
                    next_url = "home"
                return redirect(next_url)
    else:
        form = UserLoginForm()
    return render(request, "portal/auth/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    submissions = Submission.objects.filter(user=user).order_by("-submitted_at")[:10]
    return render(
        request,
        "portal/users/profile.html",
        {"profile_user": user, "submissions": submissions},
    )


@login_required
def edit_profile_view(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile", username=request.user.username)
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, "portal/users/edit_profile.html", {"form": form})


@login_required
def create_problem(request):
    if request.user.role not in ["problem_setter", "admin"]:
        return redirect("home")

    if request.method == "POST":
        form = ProblemForm(request.POST)
        if form.is_valid():
            problem = form.save(commit=False)
            problem.created_by = request.user
            problem.save()
            form.save_m2m()
            messages.success(request, "Problem created successfully!")
            return redirect("problem_detail", problem_id=problem.id)
    else:
        form = ProblemForm()
    return render(request, "portal/problems/create.html", {"form": form})


@login_required
def add_test_case(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    if request.user != problem.created_by and not request.user.is_superuser:
        return redirect("problem_detail", problem_id=problem_id)

    if request.method == "POST":
        form = TestCaseForm(request.POST)
        if form.is_valid():
            test_case = form.save(commit=False)
            test_case.problem = problem
            test_case.save()
            messages.success(request, "Test case added successfully!")
            return redirect("problem_detail", problem_id=problem_id)
    else:
        form = TestCaseForm()
    return render(
        request,
        "portal/problems/add_test_case.html",
        {"problem": problem, "form": form},
    )


def problem_list(request):
    selected_difficulty = request.GET.get("difficulty", "")
    selected_tags = request.GET.getlist("tags", [])

    problems = Problem.objects.all()
    if request.user.is_authenticated:
        problems = problems.filter(Q(is_approved=True) | Q(created_by=request.user))
    else:
        problems = problems.filter(is_approved=True)

    if selected_difficulty in ["easy", "medium", "hard"]:
        problems = problems.filter(difficulty=selected_difficulty)

    if selected_tags:
        problems = problems.filter(tags__id__in=selected_tags).distinct()

    all_tags = Tag.objects.all()

    context = {
        "problems": problems.order_by("-created_at"),
        "all_tags": all_tags,
        "selected_tags": [int(tag) for tag in selected_tags],
        "selected_difficulty": selected_difficulty,
    }

    return render(request, "portal/problems/list.html", context)


@login_required
def create_contest(request):
    if not (
        request.user.role in ["problem_setter", "admin"] and request.user.is_approved
    ):
        messages.error(request, "You don't have permission to create contests")
        return redirect("home")

    if request.method == "POST":
        form = ContestForm(request.POST)
        if form.is_valid():
            contest = form.save(commit=False)
            contest.created_by = request.user
            contest.is_approved = request.user.role == "admin"
            contest.save()
            form.save_m2m()

            if not hasattr(contest, "leaderboard"):
                leaderboard = Leaderboard.objects.create(contest=contest)
            contest.save()
            messages.success(
                request,
                "Contest created successfully! It will be visible after admin approval!",
            )
            return redirect("contest_detail", contest_id=contest.id)
        else:
            messages.error(request, "Error creating contest. Please check the form.")
    else:
        form = ContestForm()

    return render(request, "portal/contests/create.html", {"form": form})


@login_required
def register_contest(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    if request.user not in contest.participants.all():
        contest.participants.add(request.user)
        messages.success(request, "Successfully registered for the contest!")
    else:
        messages.info(request, "You're already registered for this contest.")
    return redirect("contest_detail", contest_id=contest_id)


@login_required
def add_comment(request):
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user

            if "problem_id" in request.POST:
                comment.problem = get_object_or_404(
                    Problem, id=request.POST["problem_id"]
                )
                redirect_url = reverse(
                    "problem_detail", args=[request.POST["problem_id"]]
                )

            elif "contest_id" in request.POST:
                comment.contest = get_object_or_404(
                    Contest, id=request.POST["contest_id"]
                )
                redirect_url = reverse(
                    "contest_detail", args=[request.POST["contest_id"]]
                )

            elif "submission_id" in request.POST:
                comment.submission = get_object_or_404(
                    Submission, id=request.POST["submission_id"]
                )
                redirect_url = reverse(
                    "submission_detail", args=[request.POST["submission_id"]]
                )

            else:
                messages.error(request, "Invalid comment target")
                return redirect("home")

            comment.save()
            messages.success(request, "Comment added successfully!")
            return redirect(redirect_url)

        messages.error(request, "Comment cannot be empty")
    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def create_tag(request):
    if request.user.role not in ["problem_setter", "admin"]:
        return redirect("home")

    if request.method == "POST":
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tag created successfully!")
            return redirect("problem_list")
    else:
        form = TagForm()
    return render(request, "portal/tags/create.html", {"form": form})


def global_leaderboard(request):
    users = User.objects.filter(role="competitor").order_by("-rating")[:100]
    return render(request, "portal/leaderboards/global.html", {"users": users})


def home(request):
    selected_difficulty = request.GET.get("difficulty", "")
    selected_tags = request.GET.getlist("tags", [])
    recent_problems = Problem.objects.filter(is_approved=True)
    if selected_difficulty in ["easy", "medium", "hard"]:
        recent_problems = recent_problems.filter(difficulty=selected_difficulty)
    if selected_tags:
        recent_problems = recent_problems.filter(tags__id__in=selected_tags).distinct()
    recent_problems = recent_problems.order_by("-created_at")[:5]
    active_contests = Contest.objects.filter(
        start_time__lte=timezone.now(), end_time__gte=timezone.now()
    )
    upcoming_contests = Contest.objects.filter(start_time__gt=timezone.now()).order_by(
        "start_time"
    )[:3]
    top_users = User.objects.filter(role="competitor").order_by("-rating")[:10]
    all_tags = Tag.objects.all()

    context = {
        "recent_problems": recent_problems,
        "active_contests": active_contests,
        "upcoming_contests": upcoming_contests,
        "top_users": top_users,
        "all_tags": all_tags,
        "selected_tags": selected_tags,
        "selected_difficulty": selected_difficulty,
    }

    return render(request, "portal/home.html", context)


def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)

    if not problem.is_approved:
        if not (
            request.user.is_authenticated
            and (request.user == problem.created_by or request.user.role == "admin")
        ):
            messages.error(request, "This problem is not available yet")
            return redirect("problem_list")

    user_submissions = (
        (
            Submission.objects.filter(user=request.user, problem=problem)
            .prefetch_related("test_results__test_case")
            .order_by("-submitted_at")
        )
        if request.user.is_authenticated
        else None
    )

    comments = Comment.objects.filter(problem=problem).select_related("user")
    comment_form = CommentForm()
    submission_form = SubmissionForm()
    comments = problem.comments.all().order_by("-created_at")
    test_cases = problem.test_cases.all()

    context = {
        "problem": problem,
        "user_submissions": user_submissions,
        "comments": comments,
        "comment_form": comment_form,
        "submission_form": submission_form,
        "test_cases": test_cases,
        "comments": comments,
    }
    return render(request, "portal/problems/detail.html", context)


@login_required
def edit_problem(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    if not (request.user == problem.created_by or request.user.role == "admin"):
        messages.error(request, "You don't have permission to edit this problem")
        return redirect("problem_detail", problem_id=problem_id)

    if request.method == "POST":
        form = ProblemForm(request.POST, instance=problem)
        test_case_formset = TestCaseFormset(
            request.POST, instance=problem, prefix="testcases"
        )
        if form.is_valid() and test_case_formset.is_valid():
            problem = form.save()
            test_case_formset.save()
            messages.success(request, "Problem updated successfully with test cases!")
            return redirect("problem_detail", problem_id=problem.id)
    else:
        form = ProblemForm(instance=problem)
        test_case_formset = TestCaseFormset(instance=problem, prefix="testcases")

    return render(
        request,
        "portal/problems/edit.html",
        {"form": form, "problem": problem, "test_case_formset": test_case_formset},
    )


def simulate_code_execution(code, input_data, expected_output):
    if random.choice([True, False]):
        return expected_output
    else:
        error_types = [
            expected_output[::-1],
            expected_output.upper(),
            "",
            f"error_{random.randint(1000,9999)}",
            expected_output[:-1],
        ]
        return random.choice(error_types)


@login_required
def submit_solution(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    if request.method == "POST":
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.problem = problem
            submission.status = "running"
            submission.save()

            all_passed = True
            total_runtime = 0
            max_memory = 0

            for test_case in problem.test_cases.all():
                actual_output = simulate_code_execution(
                    submission.code, test_case.input_data, test_case.expected_output
                )
                passed = actual_output.strip() == test_case.expected_output.strip()

                test_runtime = random.randint(10, 20)
                test_memory = random.randint(8, 16)
                total_runtime += test_runtime
                max_memory = max(max_memory, test_memory)

                SubmissionTestCase.objects.create(
                    submission=submission,
                    test_case=test_case,
                    passed=passed,
                    actual_output=actual_output,
                )

                if not passed:
                    all_passed = False

            submission.status = "accepted" if all_passed else "wrong_answer"
            submission.runtime = total_runtime
            submission.memory = max_memory
            submission.save()
            messages.success(request, "Submission evaluated successfully!")
            return redirect("submission_detail", submission_id=submission.id)
    else:
        form = SubmissionForm()

    return render(
        request, "portal/submissions/submit.html", {"problem": problem, "form": form}
    )


def submission_detail(request, submission_id):
    submission = get_object_or_404(
        Submission.objects.select_related("user", "problem").prefetch_related(
            "test_results__test_case"
        ),
        id=submission_id,
    )
    comments = Comment.objects.filter(submission=submission).select_related("user")
    comment_form = CommentForm()

    context = {
        "submission": submission,
        "comments": comments,
        "comment_form": comment_form,
    }
    return render(request, "portal/submissions/detail.html", context)


@login_required
def user_submissions(request):
    submissions = (
        Submission.objects.filter(user=request.user)
        .select_related("problem")
        .order_by("-submitted_at")
    )

    return render(request, "portal/submissions/list.html", {"submissions": submissions})


def contest_list(request):
    active_contests = Contest.objects.filter(
        start_time__lte=timezone.now(), end_time__gte=timezone.now()
    ).order_by("-start_time")

    upcoming_contests = Contest.objects.filter(start_time__gt=timezone.now()).order_by(
        "start_time"
    )

    past_contests = Contest.objects.filter(end_time__lt=timezone.now()).order_by(
        "-end_time"
    )

    return render(
        request,
        "portal/contests/list.html",
        {
            "active_contests": active_contests,
            "upcoming_contests": upcoming_contests,
            "past_contests": past_contests,
        },
    )


def contest_detail(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)

    if not contest.is_approved:
        if not (
            request.user.is_authenticated
            and (request.user == contest.created_by or request.user.role == "admin")
        ):
            messages.error(request, "This contest is not available yet")
            return redirect("contest_list")

    leaderboard = contest.leaderboard
    leaderboard_entries = (
        LeaderboardEntry.objects.filter(leaderboard=leaderboard)
        .select_related("user")
        .order_by("-score", "rank")
        if leaderboard
        else None
    )

    is_registered = request.user in contest.participants.all()
    is_active = contest.is_active
    comments = contest.comments.all().order_by("-created_at")

    context = {
        "contest": contest,
        "leaderboard_entries": leaderboard_entries,
        "is_registered": is_registered,
        "is_active": is_active,
        "comments": comments,
    }
    return render(request, "portal/contests/detail.html", context)


def search(request):
    query = request.GET.get("q", "")
    results = Problem.objects.none()

    if query:
        results = (
            Problem.objects.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(tags__name__icontains=query)
            )
            .distinct()
            .order_by("-created_at")
        )

    return render(
        request, "portal/search/results.html", {"results": results, "query": query}
    )


@login_required
def admin_dashboard(request):

    if not (
        request.user.is_superuser
        or (request.user.role == "admin" and request.user.is_approved)
    ):
        messages.error(
            request, "You don't have permission to access the admin dashboard."
        )
        return redirect("home")

    pending_users = User.objects.filter(
        Q(role="admin") | Q(role="problem_setter"), is_approved=False
    ).order_by("date_joined")

    pending_problems = (
        Problem.objects.filter(is_approved=False)
        .select_related("created_by")
        .order_by("-created_at")
    )

    pending_contests = Contest.objects.filter(is_approved=False).order_by("-start_time")

    return render(
        request,
        "portal/admin/dashboard.html",
        {
            "pending_users": pending_users,
            "pending_problems": pending_problems,
            "pending_contests": pending_contests,
        },
    )


@login_required
def approve_content(request, model_name, obj_id):

    if not (
        request.user.is_superuser
        or (request.user.role == "admin" and request.user.is_approved)
    ):
        messages.error(request, "You don't have permission to approve content.")
        return redirect("home")

    model_map = {"user": User, "problem": Problem, "contest": Contest}

    if model_name not in model_map:
        messages.error(request, f"Invalid content type: {model_name}")
        return redirect("admin_dashboard")

    try:
        obj = get_object_or_404(model_map[model_name], id=obj_id)
        obj.is_approved = True
        obj.approved_by = request.user
        obj.save()

        messages.success(request, f"{model_name.capitalize()} approved successfully!")
    except Exception as e:
        messages.error(request, f"Error approving {model_name}: {str(e)}")

    return redirect("admin_dashboard")


def create_problem(request):
    if not (
        request.user.role in ["problem_setter", "admin"] and request.user.is_approved
    ):
        messages.error(request, "You don't have permission to create problems")
        return redirect("home")

    if request.method == "POST":
        form = ProblemForm(request.POST)
        test_case_formset = TestCaseFormset(request.POST, prefix="testcases")
        if form.is_valid() and test_case_formset.is_valid():
            problem = form.save(commit=False)
            problem.created_by = request.user
            problem.is_approved = request.user.role == "admin"
            problem.save()
            form.save_m2m()
            test_case_formset.instance = problem
            test_case_formset.save()
            messages.success(request, "Problem created successfully with test cases!")
            return redirect("problem_detail", problem_id=problem.id)
    else:
        form = ProblemForm()
        test_case_formset = TestCaseFormset(prefix="testcases")

    return render(
        request,
        "portal/problems/create.html",
        {"form": form, "test_case_formset": test_case_formset},
    )


@login_required
def delete_problem(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)

    if (
        request.user.role == "admin"
        and request.user.is_approved
        or problem.created_by == request.user
    ):
        problem.delete()
        messages.success(request, "Problem deleted successfully!")

    return redirect("problem_list")


@login_required
def delete_user(request, user_id):
    if not (
        request.user.is_superuser
        or (request.user.role == "admin" and request.user.is_approved)
    ):
        messages.error(request, "You don't have permission to delete users")
        return redirect("home")

    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.delete()
        messages.success(request, f"User {user.username} deleted successfully")
        return redirect("admin_dashboard")

    return render(
        request,
        "portal/admin/confirm_delete.html",
        {"object": user, "object_type": "user"},
    )


@login_required
def delete_problem_admin(request, problem_id):
    if not (
        request.user.is_superuser
        or (request.user.role == "admin" and request.user.is_approved)
    ):
        messages.error(request, "You don't have permission to delete problems")
        return redirect("home")

    problem = get_object_or_404(Problem, id=problem_id)
    if request.method == "POST":
        problem.delete()
        messages.success(request, "Problem deleted successfully")
        return redirect("admin_dashboard")

    return render(
        request,
        "portal/admin/confirm_delete.html",
        {"object": problem, "object_type": "problem"},
    )


@login_required
def my_problems(request):
    if request.user.role != "problem_setter" or not request.user.is_approved:
        return redirect("home")

    problems = Problem.objects.filter(created_by=request.user).order_by("-created_at")
    return render(request, "portal/problems/my_problems.html", {"problems": problems})


@login_required
def delete_problem(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)

    if request.user != problem.created_by and not (
        request.user.role == "admin" and request.user.is_approved
    ):
        messages.error(request, "You don't have permission to delete this problem")
        return redirect("home")

    if request.method == "POST":
        problem.delete()
        messages.success(request, "Problem deleted successfully")
        return redirect("my_problems")

    return render(request, "portal/problems/confirm_delete.html", {"problem": problem})
