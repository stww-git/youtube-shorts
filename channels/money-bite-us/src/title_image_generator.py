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
from config.model_config import VIDEO_WIDTH
from config.title_config import (
    TITLE_FONT_PATH, 
    TITLE_FONT_SIZE,
    TITLE_TEXT_COLOR, 
    TITLE_STROKE_COLOR, 
    TITLE_STROKE_WIDTH,
    TITLE_LETTER_SPACING,
    TITLE_MAX_WIDTH,
    TITLE_LINE_HEIGHT,
    TITLE_LINE_COLORS  # Import added
)

logger = logging.getLogger(__name__)


class TitleGenerator:
    """
    Generates title images with custom letter spacing using Pillow.
    """
    
    def __init__(self, font_path: str = None):
        """
        Initialize TitleGenerator.
        
        Args:
            font_path: Path to font file.
        """
        self.font_path = font_path or TITLE_FONT_PATH
    
    def create_title_image(
        self,
        text: str,
        font_size: int = TITLE_FONT_SIZE,
        letter_spacing: int = TITLE_LETTER_SPACING,
        text_color: str = TITLE_TEXT_COLOR,
        stroke_color: str = TITLE_STROKE_COLOR,
        stroke_width: int = TITLE_STROKE_WIDTH,
        max_width: int = TITLE_MAX_WIDTH,
        line_height: float = TITLE_LINE_HEIGHT,
        font_path: str = None,
        line_colors: list = None  # New argument for multi-color support
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
            line_colors: Optional list of colors for each line (overrides text_color)
        
        Returns:
            Path to generated PNG image (transparent background)
        """
        font_path = font_path or self.font_path
        
        # Use default line colors from config if not provided
        if line_colors is None:
            line_colors = TITLE_LINE_COLORS
        
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
        
        # Balanced Word Wrap
        # Try to split into 2 lines with similar widths if text exceeds max_width or looks unbalanced
        words = text.split()
        
        # 1. Check if it fits in one line
        full_text = " ".join(words)
        total_text_width = get_text_width(full_text)
        
        if total_text_width <= max_width:
             lines = [full_text]
        else:
            # 2. Find best split point for 2 lines
            # logic: minimize difference between line 1 width and line 2 width
            best_split_index = -1
            min_width_diff = float('inf')
            
            # Try splitting at every space
            for i in range(1, len(words)):
                line1_words = words[:i]
                line2_words = words[i:]
                
                line1 = " ".join(line1_words)
                line2 = " ".join(line2_words)
                
                w1 = get_text_width(line1)
                w2 = get_text_width(line2)
                
                # Check allowing max_width constraint (soft)
                # Ideally both should be <= max_width, but balance is priority as per request
                diff = abs(w1 - w2)
                
                if diff < min_width_diff:
                    min_width_diff = diff
                    best_split_index = i
            
            if best_split_index != -1:
                lines = [
                    " ".join(words[:best_split_index]),
                    " ".join(words[best_split_index:])
                ]
            else:
                # Fallback (shouldn't happen for >1 words)
                lines = [full_text]
        
        # Calculate total image size
        line_height_px = int(font_size * line_height)
        # Add 20px padding (10 top, 10 bottom) to prevent tails of g, p, y from clipping
        padding_y = 20
        total_height = line_height_px * len(lines) + stroke_width * 2 + padding_y
        
        # Find max line width for image width
        max_line_width = max(get_text_width(line) for line in lines) if lines else max_width
        img_width = min(max_line_width + stroke_width * 4, VIDEO_WIDTH)
        
        # Create transparent image
        img = Image.new('RGBA', (img_width, total_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw each line
        y_offset = stroke_width
        for i, line in enumerate(lines):
            # Calculate starting x to center the line
            line_width = get_text_width(line)
            x_offset = (img_width - line_width) // 2
            
            # Determine color for this line
            current_color = text_color
            if line_colors and i < len(line_colors):
                current_color = line_colors[i]
            
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
                draw.text((x_offset, y_offset), char, font=font, fill=current_color)
                
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
