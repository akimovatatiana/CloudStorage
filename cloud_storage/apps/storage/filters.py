import django_filters

from django import forms

from cloud_storage.apps.storage.models import File

FILTER_CHOICES = (
    ('Image', 'Image'),
    ('Audio', 'Audio'),
    ('Video', 'Video'),
    ('Document', 'Document'),
    ('Table', 'Table Sheet'),
    ('Presentation', 'Presentation'),
)


class FileFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(label="", lookup_expr='icontains',
                                      widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    type = django_filters.ChoiceFilter(label="", empty_label="All Types", choices=FILTER_CHOICES)

    class Meta:
        model = File
        fields = ['title', 'type']
        exclude = ['user', 'file']