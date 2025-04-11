from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Problem, TestCase, Submission, Contest, Comment, Tag
from django.forms import inlineformset_factory


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "display_name", "role")


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email")

    class Meta:
        model = User
        fields = ("username", "password")


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("display_name", "email")


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = (
            "title",
            "description",
            "difficulty",
            "time_limit",
            "memory_limit",
            "tags",
        )
        widgets = {
            "tags": forms.CheckboxSelectMultiple(),
        }


class TestCaseForm(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = ("input_data", "expected_output")
        widgets = {
            "input_data": forms.Textarea(attrs={"rows": 5}),
            "expected_output": forms.Textarea(attrs={"rows": 5}),
        }


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ("code", "language")
        widgets = {
            "code": forms.Textarea(attrs={"class": "code-editor", "rows": 15}),
        }


class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ("name", "description", "start_time", "end_time", "problems")
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "problems": forms.CheckboxSelectMultiple(),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("content",)
        widgets = {
            "content": forms.Textarea(attrs={"rows": 3}),
        }


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ("name",)


TestCaseFormset = inlineformset_factory(
    Problem,
    TestCase,
    form=TestCaseForm,
    extra=1,
    can_delete=True,
    fields=('input_data', 'expected_output')
)
