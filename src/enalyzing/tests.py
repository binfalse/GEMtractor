from django.test import TestCase, Client
from .forms import ExportForm

# Create your tests here.
class EnalyzingTest(TestCase):
  def setUp(self):
    self.client = Client(enforce_csrf_checks=True)
  
  def test_export_form(self):
    form_data = {
      'network_type': 'en',
      'remove_reaction_genes_removed': False,
      'remove_reaction_missing_species': True,
      'network_format': 'sbml',
      }
    form = ExportForm(data=form_data)
    self.assertTrue (form.is_valid())
    self.assertTrue (form.cleaned_data['remove_reaction_genes_removed'])
    
    form_data = {
      'network_type': 'blah',
      'remove_reaction_genes_removed': False,
      'remove_reaction_missing_species': True,
      'network_format': 'sbml',
      }
    form = ExportForm(data=form_data)
    self.assertFalse (form.is_valid())
    
    form_data = {
      'network_type': 'rn',
      'remove_reaction_genes_removed': False,
      'remove_reaction_missing_species': True,
      'network_format': 'gml',
      }
    form = ExportForm(data=form_data)
    self.assertTrue (form.is_valid())
    
    form_data = {
      'network_type': 'rn',
      'remove_reaction_genes_removed': False,
      'remove_reaction_missing_species': True,
      'network_format': 'gasdfml',
      }
    form = ExportForm(data=form_data)
    self.assertFalse (form.is_valid())
