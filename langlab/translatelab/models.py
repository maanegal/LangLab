from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import escape, mark_safe
#from colorful.fields import RGBColorField


class User(AbstractUser):
    is_translator = models.BooleanField(default=False)
    is_supervisor = models.BooleanField(default=False)


class Language(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(max_length=7, default='#007bff')

    def __str__(self):
        return self.name

    def get_html_badge(self):
        name = escape(self.name)
        color = escape(self.color)
        html = '<span class="badge badge-primary" style="background-color: %s">%s</span>' % (color, name)
        return mark_safe(html)


class Translator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    languages = models.ManyToManyField(Language, related_name='qualified_translators')  # !! goal: languages spoken (add 'through' profiency)

    def __str__(self):
        return self.user.username


class Task(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')  # !! rename
    name = models.CharField(max_length=255)  # !! make this into the source name. Eventually, a ForeignKey
    source_content = models.TextField()  # !! should probably be called source_text
    target_languages = models.ManyToManyField(Language, related_name='tasks_target', blank=True)
    source_language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='tasks_source', null=True)
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
            print(score, self.name)
            total_score += score
        print(total_score, max_score)
        status = (total_score / max_score) * 100
        return status


class Translation(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='translations', null=True)  # !! rename: task
    text = models.TextField()  # !! rename: translated text, make blank=True
    validated_text = models.TextField(blank=True)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='translations', null=True)
    translator = models.ForeignKey(Translator, on_delete=models.CASCADE, related_name='translations', null=True)
    translation_time_started = models.DateTimeField(null=True, blank=True)
    translation_time_finished = models.DateTimeField(null=True, blank=True)
    validator = models.ForeignKey(Translator, on_delete=models.CASCADE, related_name='validated_translations', null=True)
    validation_time_started = models.DateTimeField(null=True, blank=True)
    validation_time_finished = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.text
