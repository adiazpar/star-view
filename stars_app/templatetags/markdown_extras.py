import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def markdown_format(text):
    """
    Convert markdown text to HTML, supporting basic formatting:
    - **bold** -> <strong>bold</strong>
    - *italic* -> <em>italic</em>  
    - __underline__ -> <u>underline</u>
    """
    if not text:
        return ""
    
    # Process nested formatting properly using regex
    import re
    
    # Handle bold (**text**)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Handle underline (__text__)  
    text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)
    
    # Handle italic (*text*) - but avoid touching content inside ** 
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
    
    # Handle line breaks - convert \n to <br> and \n\n to <br><br>
    # First handle double newlines for blank lines
    text = text.replace('\n\n', '<br><br>')
    # Then handle single newlines
    text = text.replace('\n', '<br>')
    
    return mark_safe(text)