import csv
from django.http import HttpResponse


def csv_export(task_list):
    fieldnames = ['name', 'original text', 'original language', 'time spent']
    task_dict_list = []

    for task in task_list:
        name = task.name
        text = task.source_content
        lang = task.source_language.name
        time_spent = 0
        td = {
            'name': name,
            'original text': text,
            'original language': lang,
            'time spent': time_spent
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
    tasks = []
    csv_reader = csv.DictReader(csv_data)
    for row in csv_reader:
        missing = []
        for field in fieldnames:
            if not row.get('field', ''):
                missing.append(field)

