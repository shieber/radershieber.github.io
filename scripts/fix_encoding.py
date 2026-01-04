#!/usr/bin/env python3
"""Fix encoding issues in gallery files."""

import os
import glob

REPLACEMENTS = [
    ('Entf�hrung', 'Entführung'),
    ('Zauberfl�te', 'Zauberflöte'),
    ('berfl�te', 'berflöte'),  # partial match
    ('Aum�ller', 'Aumüller'),
    ('Cos�', 'Così'),
    ('Orph�e', 'Orphée'),
    ('P�lleas', 'Pelléas'),
    ('Pell�as', 'Pelléas'),
]

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    original = content
    for old, new in REPLACEMENTS:
        content = content.replace(old, new)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    gallery_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gallery_files = glob.glob(os.path.join(gallery_dir, 'gallery', 'gallery_*.htm'))
    
    fixed = 0
    for filepath in sorted(gallery_files):
        if fix_file(filepath):
            print(f"Fixed: {os.path.basename(filepath)}")
            fixed += 1
    
    print(f"\nFixed {fixed} files")

if __name__ == "__main__":
    main()
