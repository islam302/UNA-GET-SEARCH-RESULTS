from django import forms

class SearchWordForm(forms.Form):
    word = forms.CharField(label='Search Word', max_length=255)
    time_option = forms.ChoiceField(
        label='Time Option',
        choices=[
            ('anytime', 'Any time'),
            ('y', 'last year'),
            ('m', 'last month'),
            ('w', 'last week'),
            ('d', 'last day'),
            ('h', 'last hour')
        ]
    )
    max_results = forms.IntegerField(label='Max Results')
    excluded_domains = forms.CharField(
        label='Excluded Domains (comma-separated)',
        max_length=255,
        required=False
    )
    # If file input is needed
    file = forms.FileField(required=False)
