import os, glob

replacements = {
    '<div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem;">': '<div class="layout-demo-btns">',
    '<div style="display:grid; grid-template-columns:1fr 320px; gap:1.5rem;">': '<div class="layout-content-sidebar">',
    '<div style="display:grid; grid-template-columns:1fr 300px; gap:1.5rem;">': '<div class="layout-content-sidebar">',
    '<div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem;">': '<div class="layout-2-col">',
}

for root, dirs, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            original_content = content
            for old, new in replacements.items():
                content = content.replace(old, new)
            
            # also fixing one specific one in books/view.html manually for the 3-col:
            content = content.replace(
                '<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.75rem; text-align:center; margin-bottom:1rem;">',
                '<div class="book-meta-grid" style="margin-bottom:1rem;">'
            )
            
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Updated {filepath}')
