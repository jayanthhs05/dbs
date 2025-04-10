# Complete views implementation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import *
from .forms import *

import random

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'portal/auth/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'portal/auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    submissions = Submission.objects.filter(user=user).order_by('-submitted_at')[:10]
    return render(request, 'portal/users/profile.html', {
        'profile_user': user,
        'submissions': submissions
    })

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'portal/users/edit_profile.html', {'form': form})

@login_required
def create_problem(request):
    if request.user.role not in ['problem_setter', 'admin']:
        return redirect('home')
    
    if request.method == 'POST':
        form = ProblemForm(request.POST)
        if form.is_valid():
            problem = form.save(commit=False)
            problem.created_by = request.user
            problem.save()
            form.save_m2m()  # Save tags
            messages.success(request, "Problem created successfully!")
            return redirect('problem_detail', problem_id=problem.id)
    else:
        form = ProblemForm()
    return render(request, 'portal/problems/create.html', {'form': form})

@login_required
def add_test_case(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    if request.user != problem.created_by and not request.user.is_superuser:
        return redirect('problem_detail', problem_id=problem_id)
    
    if request.method == 'POST':
        form = TestCaseForm(request.POST)
        if form.is_valid():
            test_case = form.save(commit=False)
            test_case.problem = problem
            test_case.save()
            messages.success(request, "Test case added successfully!")
            return redirect('problem_detail', problem_id=problem_id)
    else:
        form = TestCaseForm()
    return render(request, 'portal/problems/add_test_case.html', {
        'problem': problem,
        'form': form
    })

def problem_list(request):
    problems = Problem.objects.all().annotate(
        submission_count=Count('submissions')
    ).order_by('-created_at')
    
    # Filtering
    difficulty = request.GET.get('difficulty')
    if difficulty in ['easy', 'medium', 'hard']:
        problems = problems.filter(difficulty=difficulty)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        problems = problems.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    return render(request, 'portal/problems/list.html', {
        'problems': problems,
        'search_query': search_query,
        'selected_difficulty': difficulty
    })

@login_required
def create_contest(request):
    if request.user.role not in ['problem_setter', 'admin']:
        return redirect('home')
    
    if request.method == 'POST':
        form = ContestForm(request.POST)
        if form.is_valid():
            contest = form.save(commit=False)
            contest.save()
            form.save_m2m()  # Save problems
            
            # Create leaderboard
            Leaderboard.objects.create(contest=contest)
            
            messages.success(request, "Contest created successfully!")
            return redirect('contest_detail', contest_id=contest.id)
    else:
        form = ContestForm()
    return render(request, 'portal/contests/create.html', {'form': form})

@login_required
def register_contest(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    if request.user not in contest.participants.all():
        contest.participants.add(request.user)
        messages.success(request, "Successfully registered for the contest!")
    else:
        messages.info(request, "You're already registered for this contest.")
    return redirect('contest_detail', contest_id=contest_id)

@login_required
def add_comment(request):
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            
            # Determine target type
            if 'problem_id' in request.POST:
                comment.problem = get_object_or_404(Problem, id=request.POST['problem_id'])
            elif 'contest_id' in request.POST:
                comment.contest = get_object_or_404(Contest, id=request.POST['contest_id'])
            elif 'submission_id' in request.POST:
                comment.submission = get_object_or_404(Submission, id=request.POST['submission_id'])
            
            comment.save()
            messages.success(request, "Comment added successfully!")
            return redirect(request.META.get('HTTP_REFERER', 'home'))
    return redirect('home')

@login_required
def create_tag(request):
    if request.user.role not in ['problem_setter', 'admin']:
        return redirect('home')
    
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tag created successfully!")
            return redirect('problem_list')
    else:
        form = TagForm()
    return render(request, 'portal/tags/create.html', {'form': form})

def global_leaderboard(request):
    users = User.objects.filter(role='competitor').order_by('-rating')[:100]
    return render(request, 'portal/leaderboards/global.html', {'users': users})

# portal/views.py (additional view implementations)

def home(request):
    recent_problems = Problem.objects.all().order_by('-created_at')[:5]
    active_contests = Contest.objects.filter(
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now()
    )
    upcoming_contests = Contest.objects.filter(
        start_time__gt=timezone.now()
    ).order_by('start_time')[:3]
    top_users = User.objects.filter(role='competitor').order_by('-rating')[:10]

    context = {
        'recent_problems': recent_problems,
        'active_contests': active_contests,
        'upcoming_contests': upcoming_contests,
        'top_users': top_users,
    }
    return render(request, 'portal/home.html', context)

def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem.objects.prefetch_related('test_cases', 'tags'), id=problem_id)
    user_submissions = Submission.objects.filter(
        user=request.user, 
        problem=problem
    ).order_by('-submitted_at') if request.user.is_authenticated else None

    comments = Comment.objects.filter(problem=problem).select_related('user')
    comment_form = CommentForm()
    submission_form = SubmissionForm()

    context = {
        'problem': problem,
        'user_submissions': user_submissions,
        'comments': comments,
        'comment_form': comment_form,
        'submission_form': submission_form,
    }
    return render(request, 'portal/problems/detail.html', context)

@login_required
def edit_problem(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    if request.user not in [problem.created_by, 'admin']:
        return redirect('problem_detail', problem_id=problem_id)

    if request.method == 'POST':
        form = ProblemForm(request.POST, instance=problem)
        if form.is_valid():
            form.save()
            messages.success(request, "Problem updated successfully!")
            return redirect('problem_detail', problem_id=problem_id)
    else:
        form = ProblemForm(instance=problem)

    return render(request, 'portal/problems/edit.html', {
        'form': form,
        'problem': problem
    })

@login_required
def submit_solution(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.problem = problem
            submission.save()

            # Simulate judge evaluation
            submission.result = random.choice(
                ['accepted', 'wrong_answer', 'time_limit_exceeded', 'runtime_error']
            )
            submission.runtime = random.randint(10, 500)
            submission.memory = random.randint(1000, 10000)
            submission.save()

            messages.success(request, "Submission evaluated successfully!")
            return redirect('submission_detail', submission_id=submission.id)
    
    else:
        form = SubmissionForm()

    return render(request, 'portal/submissions/submit.html', {
        'problem': problem,
        'form': form
    })

def submission_detail(request, submission_id):
    submission = get_object_or_404(
        Submission.objects.select_related('user', 'problem'),
        id=submission_id
    )
    comments = Comment.objects.filter(submission=submission).select_related('user')
    comment_form = CommentForm()

    context = {
        'submission': submission,
        'comments': comments,
        'comment_form': comment_form
    }
    return render(request, 'portal/submissions/detail.html', context)

@login_required
def user_submissions(request):
    submissions = Submission.objects.filter(
        user=request.user
    ).select_related('problem').order_by('-submitted_at')
    
    return render(request, 'portal/submissions/list.html', {
        'submissions': submissions
    })

def contest_list(request):
    active_contests = Contest.objects.filter(
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now()
    ).order_by('-start_time')
    
    upcoming_contests = Contest.objects.filter(
        start_time__gt=timezone.now()
    ).order_by('start_time')
    
    past_contests = Contest.objects.filter(
        end_time__lt=timezone.now()
    ).order_by('-end_time')

    return render(request, 'portal/contests/list.html', {
        'active_contests': active_contests,
        'upcoming_contests': upcoming_contests,
        'past_contests': past_contests
    })

def contest_detail(request, contest_id):
    contest = get_object_or_404(
        Contest.objects.prefetch_related('problems', 'participants'),
        id=contest_id
    )
    leaderboard = contest.leaderboard
    leaderboard_entries = LeaderboardEntry.objects.filter(
        leaderboard=leaderboard
    ).select_related('user').order_by('-score', 'rank') if leaderboard else None

    is_registered = request.user in contest.participants.all()
    is_active = contest.is_active

    context = {
        'contest': contest,
        'leaderboard_entries': leaderboard_entries,
        'is_registered': is_registered,
        'is_active': is_active
    }
    return render(request, 'portal/contests/detail.html', context)

def search(request):
    query = request.GET.get('q', '')
    results = Problem.objects.none()
    
    if query:
        results = Problem.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct().order_by('-created_at')
    
    return render(request, 'portal/search/results.html', {
        'results': results,
        'query': query
    })

# portal/views.py
@login_required
def admin_dashboard(request):
    if not (request.user.is_superuser or (request.user.role == 'admin' and request.user.is_approved)):
        return redirect('home')
    
    pending_users = User.objects.filter(role='admin', is_approved=False)
    pending_problems = Problem.objects.filter(is_approved=False)
    pending_contests = Contest.objects.filter(is_approved=False)
    
    return render(request, 'portal/admin/dashboard.html', {
        'pending_users': pending_users,
        'pending_problems': pending_problems,
        'pending_contests': pending_contests
    })

@login_required
def approve_content(request, model_name, obj_id):
    if not request.user.is_superuser and not (request.user.role == 'admin' and request.user.is_approved):
        return redirect('home')
    
    model_map = {
        'user': User,
        'problem': Problem,
        'contest': Contest
    }
    
    obj = get_object_or_404(model_map[model_name], id=obj_id)
    obj.is_approved = True
    obj.approved_by = request.user
    obj.save()
    
    messages.success(request, f"{model_name.capitalize()} approved successfully!")
    return redirect('admin_dashboard')

# portal/views.py
@login_required
def create_problem(request):
    if request.user.role not in ['problem_setter', 'admin'] or not request.user.is_approved:
        return redirect('home')
    
    if request.method == 'POST':
        form = ProblemForm(request.POST)
        if form.is_valid():
            problem = form.save(commit=False)
            problem.created_by = request.user
            problem.is_approved = request.user.role == 'admin'  # Auto-approve if created by admin
            problem.save()
            form.save_m2m()
            return redirect('problem_detail', problem_id=problem.id)
    else:
        form = ProblemForm()
    
    return render(request, 'portal/problems/create.html', {'form': form})

@login_required
def delete_problem(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    
    if request.user.role == 'admin' and request.user.is_approved or problem.created_by == request.user:
        problem.delete()
        messages.success(request, "Problem deleted successfully!")
    
    return redirect('problem_list')
