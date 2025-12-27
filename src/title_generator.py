"""
Pillow-based Title Image Generator

Generates title images with custom letter spacing for video overlays.
This approach allows precise control over character spacing that MoviePy's
TextClip doesn't provide.
"""

import os
import logging
import tempfile
from PIL import Image, ImageDraw, ImageFont
from src.config import VIDEO_WIDTH

logger = logging.getLogger(__name__)


class TitleGenerator:
    """
    Generates title images with custom letter spacing using Pillow.
    """
    
    def __init__(self, font_path: str = None):
        """
        Initialize TitleGenerator.
        
        Args:
            font_path: Path to font file. If not provided, uses default Gungsuh.
        """
        if font_path:
            self.font_path = font_path
        else:
            self.font_path = os.path.join(os.getcwd(), "fonts/Gungseouche.ttf")
    
    def create_title_image(
        self,
        text: str,
        font_size: int = 100,
        letter_spacing: int = -30,
        text_color: str = 'white',
        stroke_color: str = 'black',
        stroke_width: int = 0,
        max_width: int = 800,
        line_height: float = 1.0,  # 줄간격 배수 (1.0 = 빼곡, 1.3 = 기본, 2.0 = 넓게)
        font_path: str = None
    ) -> str:
        """
        Create a title image with custom letter spacing.
        
        Args:
            text: Title text to render
            font_size: Font size in pixels
            letter_spacing: Space between characters 
                           (negative = tighter, 0 = normal, positive = wider)
            text_color: Text fill color (name or hex)
            stroke_color: Stroke/outline color
            stroke_width: Stroke thickness in pixels
            max_width: Maximum width before word wrapping
            line_height: Line spacing multiplier (1.0 = tight, 1.3 = normal, 2.0 = wide)
            font_path: Optional override for font path
        
        Returns:
            Path to generated PNG image (transparent background)
        """
        font_path = font_path or self.font_path
        
        # Load font
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            logger.warning(f"Failed to load font {font_path}: {e}. Using default.")
            font = ImageFont.load_default()
        
        # Helper: Calculate text width with custom spacing
        def get_text_width(chars: str) -> int:
            total = 0
            for i, char in enumerate(chars):
                bbox = font.getbbox(char)
                char_width = bbox[2] - bbox[0]
                total += char_width
                if i < len(chars) - 1:
                    total += letter_spacing
            return total
        
        # Word wrap: split text into lines that fit within max_width
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip() if current_line else word
            if get_text_width(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        if not lines:
            lines = [text]
        
        # Calculate total image size
        line_height_px = int(font_size * line_height)
        total_height = line_height_px * len(lines) + stroke_width * 2
        
        # Find max line width for image width
        max_line_width = max(get_text_width(line) for line in lines) if lines else max_width
        img_width = min(max_line_width + stroke_width * 4, VIDEO_WIDTH)
        
        # Create transparent image
        img = Image.new('RGBA', (img_width, total_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw each line
        y_offset = stroke_width
        for line in lines:
            # Calculate starting x to center the line
            line_width = get_text_width(line)
            x_offset = (img_width - line_width) // 2
            
            # Draw character by character with custom spacing
            for char in line:
                bbox = font.getbbox(char)
                char_width = bbox[2] - bbox[0]
                
                # Draw stroke (outline) - draw text multiple times offset
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text((x_offset + dx, y_offset + dy), char, font=font, fill=stroke_color)
                
                # Draw main text
                draw.text((x_offset, y_offset), char, font=font, fill=text_color)
                
                x_offset += char_width + letter_spacing
            
            y_offset += line_height_px
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        temp_path = temp_file.name
        temp_file.close()
        img.save(temp_path, 'PNG')
        
        logger.info(f"Created title image: {temp_path} ({img_width}x{total_height}px)")
        return temp_path
    
    def get_image_dimensions(self, image_path: str) -> tuple:
        """
        Get the dimensions of an image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Tuple of (width, height)
        """
        with Image.open(image_path) as img:
            return img.size


# Convenience function for direct use
def create_title_image(text: str, **kwargs) -> str:
    """
    Quick function to create a title image.
    
    Args:
        text: Title text
        **kwargs: Passed to TitleGenerator.create_title_image()
    
    Returns:
        Path to generated PNG image
    """
    generator = TitleGenerator()
    return generator.create_title_image(text, **kwargs)
