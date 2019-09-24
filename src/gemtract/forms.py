from django import forms

TYPE = (
    ('en', 'Enzyme-centric Network'),
    ('rn', 'Reaction-centric Network'),
    ('mn', 'Metabolite-Reaction Network'),
)
FORMAT = (
    ('sbml', 'SBML'),
    ('graphml', 'GraphML'),
    ('dot', 'DOT'),
    ('gml', 'GML'),
    ('csv', 'CSV'),
)

class ExportForm (forms.Form):
  network_type = forms.ChoiceField(choices=TYPE)
  remove_reaction_enzymes_removed = forms.BooleanField(required=False)
  remove_ghost_species = forms.BooleanField(required=False)
  discard_fake_enzymes = forms.BooleanField(required=False)
  remove_reaction_missing_species = forms.BooleanField(required=False)
  removing_enzyme_removes_complex = forms.BooleanField(required=False)
  network_format = forms.ChoiceField(choices=FORMAT)
  def clean(self):
      cleaned_data = super().clean()
      if cleaned_data.get("network_type") == "en":
        cleaned_data["remove_reaction_enzymes_removed"] = True;
