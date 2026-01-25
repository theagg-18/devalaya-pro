import os
import re

def minify_css(content):
    # Remove comments
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    # Remove whitespace around delimiters
    content = re.sub(r'\s*([{:;,])\s*', r'\1', content)
    # Remove trailing ; before }
    content = re.sub(r';}', '}', content)
    # Minimize repeated whitespace (but keep space in calc etc if needed, be careful)
    # Safe approach: replace newlines with space, then multi-space with single space
    content = content.replace('\n', ' ')
    content = re.sub(r'\s+', ' ', content)
    return content.strip()

css_path = os.path.join('static', 'css', 'style.css')
if os.path.exists(css_path):
    with open(css_path, 'r', encoding='utf-8') as f:
        original = f.read()
    
    minified = minify_css(original)
    
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(minified)
        
    print(f"Minified style.css: {len(original)} -> {len(minified)} bytes")
