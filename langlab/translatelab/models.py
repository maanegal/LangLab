from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import escape, mark_safe
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime, timezone
from pytz import common_timezones


def get_sentinel_user():
    user = get_user_model().objects.get_or_create(username='Deleted user')[0]
    user.is_translator = True
    user.is_deleted = True
    user.is_active = False
    user.save()
    Translator.objects.get_or_create(user=user)
    return user


def get_sentinel_language():
    return Language.objects.get_or_create(name='Unknown')[0]


class User(AbstractUser):
    is_translator = models.BooleanField(default=False)
    is_supervisor = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    TIMEZONE_CHOICES = [(t, t) for t in common_timezones]
    timezone = models.CharField(max_length=100, choices=TIMEZONE_CHOICES, default=settings.TIME_ZONE)


class Language(models.Model):
    name = models.CharField(max_length=30)
    code = models.CharField(max_length=5, default='')
    style_guide = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def get_html_badge(self):
        name = escape(self.name)
        code = escape(self.code)
        html = '<span class="badge badge-light" style="margin-right:3px;"><span class="flag-icon flag-icon-%s"></span>&nbsp;%s</span>' % (code, name)
        return mark_safe(html)


class Translator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    languages = models.ManyToManyField(Language, related_name='qualified_translators')  # !! goal: languages spoken (add 'through' profiency)
    points_earned = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username


class Task(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user), related_name='tasks')  # !! rename
    name = models.CharField(max_length=255)  # !! make this into the source name. Eventually, a ForeignKey
    source_content = models.TextField()  # !! should probably be called source_text
    instructions = models.TextField(default='', blank=True)
    source_language = models.ForeignKey(Language, on_delete=models.SET(get_sentinel_language), related_name='tasks_source', null=True)
    time_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    time_updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    PRIORITY_CHOICES = [
        (5, 'Very high'),
        (4, 'High'),
        (3, 'Default'),
        (2, 'Low'),
        (1, 'Very low'),
    ]
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=3,
    )
    point_score = models.IntegerField(default=0)
    point_score_version = models.IntegerField(default=0)
    word_count = models.IntegerField(default=0)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_status(self):
        max_score = self.translations.count() * 4
        total_score = 0
        for translation in self.translations.all():
            score = 0
            for point in [translation.translation_time_started,
                          translation.translation_time_finished,
                          translation.validation_time_started,
                          translation.validation_time_finished]:
                if point:
                    score += 1
            total_score += score
        status = (total_score / max_score) * 100
        return int(status)


class Translation(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='translations', null=True)
    text = models.TextField()  # !! rename: translated text, make blank=True
    validated_text = models.TextField(blank=True)
    comment = models.TextField(default='', blank=True)
    language = models.ForeignKey(Language, on_delete=models.SET(get_sentinel_language), related_name='translations', null=True)
    translator = models.ForeignKey(Translator, on_delete=models.CASCADE, related_name='translations', null=True)
    translation_time_started = models.DateTimeField(null=True, blank=True)
    translation_time_finished = models.DateTimeField(null=True, blank=True)
    validator = models.ForeignKey(Translator, on_delete=models.CASCADE, related_name='validated_translations', null=True)
    validation_time_started = models.DateTimeField(null=True, blank=True)
    validation_time_finished = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.text

    def get_translation_time(self, get_seconds=False):
        """Returns int of number of seconds spent on a translation task.
        If the task has not been started, 0 is returned.
        If the task has not been completed, time from now is calculated
        !! not finished...
        """
        if self.translation_time_started:
            if self.translation_time_finished:
                td = self.translation_time_finished - self.translation_time_started
            else:
                td = self.translation_time_finished - datetime.now(timezone.utc)

        else:
            return 0
