from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1
    fields = ("input_data", "expected_output")


class ProblemAdmin(admin.ModelAdmin):
    list_display = ("title", "difficulty", "created_by", "created_at")
    list_filter = ("difficulty", "tags", "created_at")
    search_fields = ("title", "description")
    filter_horizontal = ("tags",)
    inlines = [TestCaseInline]
    raw_id_fields = ("created_by",)


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "problem", "result", "language", "submitted_at")
    list_filter = ("result", "language", "submitted_at")
    search_fields = ("user__username", "problem__title", "code")
    raw_id_fields = ("user", "problem")


class ContestAdmin(admin.ModelAdmin):
    list_display = ("name", "start_time", "end_time", "is_active")
    filter_horizontal = ("problems", "participants")
    date_hierarchy = "start_time"
    fields = (
        "name",
        "description",
        "start_time",
        "end_time",
        "problems",
        "participants",
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not hasattr(obj, "leaderboard"):
            Leaderboard.objects.create(contest=obj)


class LeaderboardEntryInline(admin.TabularInline):
    model = LeaderboardEntry
    extra = 1
    raw_id_fields = ("user",)


class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ("contest", "last_updated")
    inlines = [LeaderboardEntryInline]

    def last_updated(self, obj):
        return obj.contest.end_time

    last_updated.short_description = "Last Updated"


class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "problem_count")
    search_fields = ("name",)

    def problem_count(self, obj):
        return obj.problems.count()

    problem_count.short_description = "Problems"


class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "content_preview", "target", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "content")
    raw_id_fields = ("user", "problem", "submission", "contest")

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Content"

    def target(self, obj):
        if obj.problem:
            return f"Problem: {obj.problem.title}"
        if obj.submission:
            return f"Submission: {obj.submission.id}"
        if obj.contest:
            return f"Contest: {obj.contest.name}"
        return "-"

    target.short_description = "Target"


class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "rating", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Competitive Programming Profile",
            {"fields": ("display_name", "role", "rating")},
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Information", {"fields": ("display_name", "role", "rating")}),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(Problem, ProblemAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Contest, ContestAdmin)
admin.site.register(Leaderboard, LeaderboardAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Comment, CommentAdmin)
