import os
import glob
import re

template_dir = r"d:\class data\certificate_portal\templates"
html_files = glob.glob(os.path.join(template_dir, "*.html"))

tilt_attrs = 'data-tilt data-tilt-glare="true" data-tilt-max-glare="0.2" data-tilt-scale="1.02"'

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    def replacer(match):
        tag = match.group(0)
        if 'data-tilt' in tag:
            return tag
        return tag[:-1] + f' {tilt_attrs}>'
        
    new_content = re.sub(r'<div\s+class="[^"]*glass-panel[^"]*"[^>]*>', replacer, content)
    new_content = re.sub(r'<a\s+href="[^"]*"\s+class="[^"]*portal-card[^"]*"[^>]*>', replacer, new_content)
    
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {os.path.basename(file)}")
