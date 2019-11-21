import csv
from io import StringIO
from django.http import HttpResponse
from .models import Language


def csv_export(task_list):
    fieldnames = ['name', 'original_text', 'original_language', 'time_spent']
    task_dict_list = []

    for task in task_list:
        name = task.name
        text = task.source_content
        lang = task.source_language.name
        time_spent = 0
        td = {
            'name': name,
            'original_text': text,
            'original_language': lang,
            'time_spent': time_spent
              }
        for trans in task.translations.all():
            trans_name = 'translation_'+trans.language.name.lower()
            if trans.validated_text:
                trans_text = trans.validated_text
            else:
                trans_text = trans.text
            if trans_name not in fieldnames:
                fieldnames.append(trans_name)
            td[trans_name] = trans_text
        task_dict_list.append(td)

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="task_export.csv"'

    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()
    for task in task_dict_list:
        writer.writerow(task)
    return response


def csv_import(csv_data):
    fieldnames = ['name', 'text', 'source language', 'target languages', 'priority', 'instructions']
    priority_acceptable_values = [1, 2, 3, 4, 5]  # , 'Very low', 'Low', 'Default', 'High', 'Very high']
    tasks = []

    csv_data.seek(0)
    csv_reader = csv.DictReader(StringIO(csv_data.read().decode('utf-8')))
    for row in csv_reader:
        task = {
            'name': row.get('name', ''),
            'text': row.get('text', ''),
            'instructions': row.get('instructions', ''),
        }
        p = row.get('priority')
        if p:
            task['priority'] = int(p)
        else:
            task['priority'] = 3

        sl = row.get('source_language', '')
        slq = Language.objects.filter(name=sl) | Language.objects.filter(code=sl)
        if slq:
            task['source_language'] = slq.first().id
        tl = row.get('target_languages', '')
        if not tl or tl.lower() == 'all':
            tlq = list(Language.objects.all().values_list('id', flat=True))
        else:
            tl_list = [x.strip() for x in tl.split(';')]
            tl_lookup = '|'.join(tl_list)
            tlq = list(Language.objects.filter(name__iregex=r'(' + tl_lookup + ')').exclude(name="Unknown").values_list('id', flat=True) |
                       Language.objects.filter(code__iregex=r'(' + tl_lookup + ')').exclude(name="Unknown").values_list('id', flat=True))
        task['target_languages'] = tlq
        tasks.append(task)

    return tasks
