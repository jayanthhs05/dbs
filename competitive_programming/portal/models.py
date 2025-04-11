from django.db import models


from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ("competitor", "Competitor"),
        ("problem_setter", "Problem Setter"),
        ("admin", "Admin"),
    )
    display_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="competitor")
    rating = models.IntegerField(default=1500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class Problem(models.Model):
    DIFFICULTY_CHOICES = (
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    time_limit = models.IntegerField(help_text="Time limit in milliseconds")
    memory_limit = models.IntegerField(help_text="Memory limit in KB")
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_problems"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField("Tag", related_name="problems")
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.title


class TestCase(models.Model):
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="test_cases"
    )
    input_data = models.TextField()
    expected_output = models.TextField()

    def __str__(self):
        return f"Test case for {self.problem.title}"


class Submission(models.Model):
    RESULT_CHOICES = (
        ("accepted", "Accepted"),
        ("wrong_answer", "Wrong Answer"),
        ("time_limit_exceeded", "Time Limit Exceeded"),
        ("memory_limit_exceeded", "Memory Limit Exceeded"),
        ("runtime_error", "Runtime Error"),
        ("compilation_error", "Compilation Error"),
        ("pending", "Pending"),
    )
    LANGUAGE_CHOICES = (
        ("python", "Python"),
        ("java", "Java"),
        ("cpp", "C++"),
        ("c", "C"),
        ("javascript", "JavaScript"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="submissions"
    )
    code = models.TextField()
    language = models.CharField(max_length=15, choices=LANGUAGE_CHOICES)
    result = models.CharField(max_length=25, choices=RESULT_CHOICES, default="pending")
    runtime = models.IntegerField(
        null=True, blank=True, help_text="Runtime in milliseconds"
    )
    memory = models.IntegerField(null=True, blank=True, help_text="Memory usage in KB")
    submitted_at = models.DateTimeField(auto_now_add=True)
    test_cases = models.ManyToManyField(TestCase, through="SubmissionTestCase")
    status = models.CharField(max_length=20, default="pending")

    def __str__(self):
        return f"{self.user.username}'s submission for {self.problem.title}"


class Contest(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    problems = models.ManyToManyField(Problem, related_name="contests")
    participants = models.ManyToManyField(User, related_name="participated_contests")
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_contests"
    )

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not hasattr(self, 'leaderboard'):
            leaderboard = Leaderboard.objects.create(contest=self)


class Leaderboard(models.Model):
    contest = models.OneToOneField(
        Contest, on_delete=models.CASCADE, related_name="leaderboard"
    )

    def __str__(self):
        return f"Leaderboard for {self.contest.name}"


class LeaderboardEntry(models.Model):
    leaderboard = models.ForeignKey(
        Leaderboard, on_delete=models.CASCADE, related_name="entries"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    rank = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("leaderboard", "user")
        ordering = ["-score", "rank"]

    def __str__(self):
        return f"{self.user.username}'s entry in {self.leaderboard}"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Comment by {self.user.username}"


class SubmissionTestCase(models.Model):
    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name="test_results"
    )
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    passed = models.BooleanField()
    actual_output = models.TextField()

    class Meta:
        unique_together = ("submission", "test_case")
