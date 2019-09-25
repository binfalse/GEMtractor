from django import template

register = template.Library()

@register.filter(name='addclass')
def addclass(field, css):
    """
    adds another CSS class to a DOM element
    
    :param field: the DOM element
    :param css: the additional CSS class
    
    :return: the field with attached class
    """
    return field.as_widget(attrs={"class":css})
