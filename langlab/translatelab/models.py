from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import escape, mark_safe


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


class Task(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=255)  # !! make this into the source name. Eventually, a ForeignKey
    source_content = models.TextField()
    target_languages = models.ManyToManyField(Language, related_name='tasks', blank=True)  # !! this should be multi
    source_language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='tasks_org', null=True)
    time_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    time_updated = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name


class Translation(models.Model):  # This will become the Translation model
    quiz = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='questions')  # !! rename: task
    text = models.TextField()  # !! rename: translated text, make blank=True
    validated_text = models.TextField(blank=True)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='translations', null=True)
    translator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='translations', null=True)
    translation_time_started = models.DateTimeField(null=True, blank=True)
    translation_time_finished = models.DateTimeField(null=True, blank=True)
    validator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='validated_translations', null=True)
    validation_time_started = models.DateTimeField(null=True, blank=True)
    validation_time_finished = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Translation, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    is_correct = models.BooleanField('Correct answer', default=False)

    def __str__(self):
        return self.text


class Translator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    tasks = models.ManyToManyField(Task, through='TakenQuiz')
    languages = models.ManyToManyField(Language, related_name='qualified_translators')  # !! goal: languages spoken (add 'through' profiency)

    def get_unanswered_questions(self, quiz):  # !! find out what this does
        answered_questions = self.quiz_answers \
            .filter(answer__question__quiz=quiz) \
            .values_list('answer__question__pk', flat=True)
        questions = quiz.questions.exclude(pk__in=answered_questions).order_by('text')
        return questions

    def __str__(self):
        return self.user.username


class TakenQuiz(models.Model):
    translator = models.ForeignKey(Translator, on_delete=models.CASCADE, related_name='taken_tasks')
    quiz = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='taken_tasks')
    score = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)


class TranslatorAnswer(models.Model):
    translator = models.ForeignKey(Translator, on_delete=models.CASCADE, related_name='quiz_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='+')
