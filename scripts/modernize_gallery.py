#!/usr/bin/env python3
"""
Modernize gallery pages from old FrontPage HTML to modern CSS-based layout.
"""

import os
import re
import glob
from html import unescape
from pathlib import Path

GALLERY_DIR = Path(__file__).parent.parent / "gallery"
ARCHIVE_DIR = Path(__file__).parent.parent / "archive" / "gallery_pages"

def extract_production_info(content):
    """Extract production details from the old HTML."""
    # Find the font block with production info
    match = re.search(
        r'<font size="2" color="#FFFFFF">(.*?)</font>',
        content,
        re.DOTALL | re.IGNORECASE
    )
    if not match:
        return None
    
    info_html = match.group(1)
    
    # Extract title (in italic tags)
    title_match = re.search(r'<i>(.*?)</i>', info_html, re.DOTALL | re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else ""
    # Clean up title - remove <br> tags and extra whitespace
    title = re.sub(r'<br\s*/?>', '', title, flags=re.IGNORECASE).strip()
    
    # Remove the title from info to parse the rest
    rest = re.sub(r'<i>.*?</i>', '', info_html, flags=re.DOTALL | re.IGNORECASE)
    
    # Split by <br> and clean up
    lines = re.split(r'<br\s*/?>', rest, flags=re.IGNORECASE)
    lines = [unescape(line.strip()) for line in lines if line.strip()]
    
    # Parse the remaining lines
    composer = lines[0] if len(lines) > 0 else ""
    venue = lines[1] if len(lines) > 1 else ""
    year = lines[2] if len(lines) > 2 else ""
    
    # Extract optional credits
    scenery = ""
    costumes = ""
    lights = ""
    choreography = ""
    
    for line in lines[3:]:
        if line.startswith("Scenery:"):
            scenery = line
        elif line.startswith("Costumes:"):
            costumes = line
        elif line.startswith("Lights:"):
            lights = line
        elif line.startswith("Choreography:"):
            choreography = line
    
    return {
        'title': unescape(title),
        'composer': composer,
        'venue': venue,
        'year': year,
        'scenery': scenery,
        'costumes': costumes,
        'lights': lights,
        'choreography': choreography,
    }

def extract_thumbnails(content):
    """Extract thumbnail links and images."""
    thumbnails = []
    # Find all thumbnail links
    pattern = r'<a href="(gallery_[^"]+\.htm)"[^>]*>\s*<img[^>]+src="([^"]+)"[^>]*>'
    matches = re.findall(pattern, content, re.IGNORECASE)
    
    for href, src in matches:
        # Only include if it's a thumbnail (small image)
        if '_sm.' in src:
            thumbnails.append({'href': href, 'src': src})
    
    return thumbnails

def extract_navigation(content, thumbnails, current_filename):
    """Extract prev/next navigation links, inferring from thumbnails if needed."""
    prev_link = ""
    next_link = ""
    
    # Find prev arrow link
    prev_match = re.search(
        r'<a href="(gallery_[^"]+\.htm)"[^>]*>\s*<img[^>]+src="[^"]*prev_arrow',
        content,
        re.IGNORECASE
    )
    if prev_match:
        prev_link = prev_match.group(1)
    
    # Find next arrow link
    next_match = re.search(
        r'<a href="(gallery_[^"]+\.htm)"[^>]*>\s*<img[^>]+src="[^"]*next_arrow',
        content,
        re.IGNORECASE
    )
    if next_match:
        next_link = next_match.group(1)
    
    # If missing prev or next, infer from thumbnails (for first/last photos)
    if thumbnails and (not prev_link or not next_link):
        thumb_hrefs = [t['href'] for t in thumbnails]
        try:
            current_idx = thumb_hrefs.index(current_filename)
            if not prev_link:
                # Wrap around to last
                prev_link = thumb_hrefs[-1] if current_idx == 0 else thumb_hrefs[current_idx - 1]
            if not next_link:
                # Wrap around to first
                next_link = thumb_hrefs[0] if current_idx == len(thumb_hrefs) - 1 else thumb_hrefs[current_idx + 1]
        except ValueError:
            pass
    
    return prev_link, next_link

def extract_large_image(content):
    """Extract the large image path."""
    # Find large image (not a thumbnail, not a navigation image)
    match = re.search(
        r'<img[^>]+src="(\.\./images/gallery/[^"]+_lg\.jpg)"',
        content,
        re.IGNORECASE
    )
    if match:
        return match.group(1)
    return ""

def extract_photo_credit(content):
    """Extract photo credit."""
    match = re.search(
        r'<font size="1">\s*Photo:\s*([^<]+)</font>',
        content,
        re.IGNORECASE
    )
    if match:
        return "Photo: " + match.group(1).strip()
    return ""

def get_current_photo_number(filename):
    """Extract the photo number from filename like gallery_2016_orphee_01.htm"""
    match = re.search(r'_(\d+)\.htm$', filename)
    if match:
        return int(match.group(1))
    return 1

def generate_modern_html(info, thumbnails, prev_link, next_link, large_image, photo_credit, current_filename):
    """Generate the modernized HTML."""
    current_num = get_current_photo_number(current_filename)
    
    # Build production info section
    info_lines = [f"          <i>{info['title']}</i><br>"]
    info_lines.append(f"          {info['composer']}<br>")
    info_lines.append(f"          {info['venue']}<br>")
    info_lines.append(f"          {info['year']}")
    
    if info['scenery']:
        info_lines.append(f"<br>\n          {info['scenery']}")
    if info['costumes']:
        info_lines.append(f"<br>\n          {info['costumes']}")
    if info['lights']:
        info_lines.append(f"<br>\n          {info['lights']}")
    if info['choreography']:
        info_lines.append(f"<br>\n          {info['choreography']}")
    
    production_info = "\n".join(info_lines)
    
    # Build thumbnail grid
    thumb_lines = []
    for i, thumb in enumerate(thumbnails, 1):
        is_active = (thumb['href'] == current_filename)
        active_class = " active" if is_active else ""
        thumb_lines.append(
            f'        <a href="{thumb["href"]}" class="thumb{active_class}">'
            f'<img src="{thumb["src"]}" alt="Photo {i}"></a>'
        )
    thumbnail_grid = "\n".join(thumb_lines)
    
    # Build the full HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chas Rader-Shieber - Stage Director</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body>

  <div class="gallery-detail-layout">
    
    <!-- Left Black Sidebar with production info and thumbnails -->
    <aside class="gallery-detail-sidebar">
      <div class="production-detail-info">
        <p>
{production_info}
        </p>
      </div>
      <div class="thumbnail-grid">
{thumbnail_grid}
      </div>
    </aside>

    <!-- Header -->
    <header class="header">
      <a href="../index.htm" class="logo">
        <img src="../images/crs_sd.gif" alt="Chas Rader-Shieber - Stage Director">
      </a>
      <nav class="main-nav">
        <a href="gallery.htm" class="nav-link">
          <img src="../images/gallery.gif" alt="Gallery" class="nav-img-default">
          <img src="../images/gallery_on.gif" alt="Gallery" class="nav-img-hover">
        </a>
        <a href="../schedule.htm" class="nav-link">
          <img src="../images/schedule.gif" alt="Schedule" class="nav-img-default">
          <img src="../images/schedule_on.gif" alt="Schedule" class="nav-img-hover">
        </a>
        <a href="../resume.htm" class="nav-link">
          <img src="../images/resume.gif" alt="Résumé" class="nav-img-default">
          <img src="../images/resume_on.gif" alt="Résumé" class="nav-img-hover">
        </a>
        <a href="../contact.htm" class="nav-link">
          <img src="../images/contact.gif" alt="Contact" class="nav-img-default">
          <img src="../images/contact_on.gif" alt="Contact" class="nav-img-hover">
        </a>
      </nav>
    </header>

    <!-- Main Content: Photo viewer -->
    <main class="photo-viewer">
      <div class="photo-nav">
        <a href="{prev_link}" class="nav-arrow">
          <img src="../images/prev_arrow.gif" alt="Previous" class="nav-img-default">
          <img src="../images/prev_arrow_on.gif" alt="Previous" class="nav-img-hover">
        </a>
        <a href="{next_link}" class="nav-arrow">
          <img src="../images/next_arrow.gif" alt="Next" class="nav-img-default">
          <img src="../images/next_arrow_on.gif" alt="Next" class="nav-img-hover">
        </a>
      </div>
      <div class="large-photo">
        <img src="{large_image}" alt="{info['title']} - Photo {current_num}">
      </div>
      <p class="photo-credit-detail">{photo_credit}</p>
    </main>

  </div>

</body>
</html>
'''
    return html

def is_already_modernized(content):
    """Check if a file has already been modernized."""
    return '<!DOCTYPE html>' in content and 'gallery-detail-layout' in content

def process_gallery_file(filepath):
    """Process a single gallery file."""
    filename = os.path.basename(filepath)
    
    # Skip the main gallery index and already-modernized orphee file
    if filename in ('gallery.htm', 'gallery_old.htm', 'gallery-new.htm'):
        return None, "Skipped (index file)"
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        return None, f"Error reading: {e}"
    
    # Check if already modernized
    if is_already_modernized(content):
        return None, "Already modernized"
    
    # Extract all data
    info = extract_production_info(content)
    if not info:
        return None, "Could not extract production info"
    
    thumbnails = extract_thumbnails(content)
    if not thumbnails:
        return None, "Could not extract thumbnails"
    
    prev_link, next_link = extract_navigation(content, thumbnails, filename)
    if not prev_link or not next_link:
        return None, "Could not extract navigation"
    
    large_image = extract_large_image(content)
    if not large_image:
        return None, "Could not extract large image"
    
    photo_credit = extract_photo_credit(content)
    
    # Generate new HTML
    new_html = generate_modern_html(
        info, thumbnails, prev_link, next_link, 
        large_image, photo_credit, filename
    )
    
    return new_html, "Success"

def main():
    """Main function to process all gallery files."""
    # Create archive directory if it doesn't exist
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all gallery files
    gallery_files = sorted(glob.glob(str(GALLERY_DIR / "gallery_*.htm")))
    
    print(f"Found {len(gallery_files)} gallery files")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for filepath in gallery_files:
        filename = os.path.basename(filepath)
        new_html, status = process_gallery_file(filepath)
        
        if new_html:
            # Archive the original
            archive_path = ARCHIVE_DIR / filename
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                original_content = f.read()
            with open(archive_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write the new file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_html)
            
            print(f"✓ {filename}")
            success_count += 1
        elif status == "Already modernized":
            print(f"- {filename} (already done)")
            skip_count += 1
        elif status.startswith("Skipped"):
            print(f"- {filename} ({status})")
            skip_count += 1
        else:
            print(f"✗ {filename}: {status}")
            error_count += 1
    
    print(f"\nDone! Processed {success_count} files, skipped {skip_count}, errors {error_count}")
    print(f"Original files archived to: {ARCHIVE_DIR}")

if __name__ == "__main__":
    main()

