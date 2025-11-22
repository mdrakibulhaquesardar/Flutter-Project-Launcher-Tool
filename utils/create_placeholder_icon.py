"""Utility script to create placeholder icons for FluStudio branding."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys


def create_placeholder_icon(size: int = 256, output_path: Path = None):
    """
    Create a simple placeholder icon with FluStudio branding.
    
    Args:
        size: Icon size in pixels (default: 256)
        output_path: Output file path (default: assets/icons/app_icon.png)
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL/Pillow is required. Install it with: pip install Pillow")
        return False
    
    if output_path is None:
        output_path = Path(__file__).parent.parent / "assets" / "icons" / "app_icon.png"
    
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw background circle
    margin = size // 10
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(0, 90, 158, 255),  # FluStudio blue
        outline=(0, 70, 130, 255),
        width=max(2, size // 64)
    )
    
    # Draw text "FS" or "F"
    try:
        # Try to use a nice font
        font_size = size // 3
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    text = "FS"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((size - text_width) // 2, (size - text_height) // 2 - text_height // 4)
    draw.text(position, text, fill=(255, 255, 255, 255), font=font)
    
    # Save as PNG
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, 'PNG')
    print(f"✓ Created placeholder icon: {output_path}")
    
    # Also create ICO if on Windows
    if sys.platform == 'win32':
        ico_path = output_path.parent / "app_icon.ico"
        # Create multiple sizes for ICO
        sizes = [16, 32, 48, 64, 128, 256]
        icons = []
        for s in sizes:
            if s <= size:
                resized = img.resize((s, s), Image.Resampling.LANCZOS)
                icons.append(resized)
        
        if icons:
            icons[0].save(ico_path, format='ICO', sizes=[(i.size[0], i.size[1]) for i in icons])
            print(f"✓ Created Windows icon: {ico_path}")
    
    return True


if __name__ == "__main__":
    print("Creating placeholder icons for FluStudio...")
    success = create_placeholder_icon(256)
    if success:
        print("\n✓ Icons created successfully!")
        print("You can replace these with your custom branding icons.")
    else:
        print("\n✗ Failed to create icons. Install Pillow: pip install Pillow")

