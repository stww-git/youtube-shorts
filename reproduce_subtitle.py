
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from src.subtitle_config import get_keyword_color, SUBTITLE_IMPACT_KEYWORDS

# Mock MotionEffectsComposer
class MockComposer:
    def __init__(self):
        self.font = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"

    def _create_subtitle_image(self, text, style):
        print(f"DEBUG: Creating subtitle for text: '{text}'")
        try:
            # Unpack style
            font_path = style.get('font_path', self.font)
            font_size = style.get('font_size', 80)
            text_color = style.get('text_color', 'white')
            stroke_color = style.get('stroke_color', 'black')
            stroke_width = style.get('stroke_width', 3)
            max_width = style.get('max_width', 960)
            
            print(f"DEBUG: Style - font_size={font_size}, color={text_color}, stroke={stroke_width}")
            
            # Load font
            try:
                font = ImageFont.truetype(font_path, font_size)
                print("DEBUG: Font loaded successfully")
            except:
                print("DEBUG: Font load failed, using default")
                font = ImageFont.load_default()
            
            # Wrap text and calculate layout
            dummy_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            words = text.split()
            line_layouts = [] 
            current_line_words = []
            current_line_width = 0
            
            # Calculate space width once
            space_bbox = dummy_draw.textbbox((0, 0), " ", font=font)
            space_width = space_bbox[2] - space_bbox[0]
            print(f"DEBUG: Space width = {space_width}")
            
            for word in words:
                word_bbox = dummy_draw.textbbox((0, 0), word, font=font)
                word_width = word_bbox[2] - word_bbox[0]
                
                if current_line_words and (current_line_width + space_width + word_width > max_width):
                    line_layouts.append(current_line_words)
                    current_line_words = []
                    current_line_width = 0
                
                # Add word to current line
                color = get_keyword_color(word, text_color)
                current_line_words.append({
                    "text": word,
                    "width": word_width,
                    "color": color
                })
                current_line_width += word_width
                if len(current_line_words) > 1:
                    current_line_width += space_width
            
            if current_line_words:
                line_layouts.append(current_line_words)
            
            print(f"DEBUG: Layout calculated. {len(line_layouts)} lines.")
            for idx, line in enumerate(line_layouts):
                print(f"  Line {idx}: {[w['text'] for w in line]}")

            # Calculate total image size
            line_spacing = 10
            total_text_height = 0
            max_line_width = 0
            line_heights = [] 
            
            for line_data in line_layouts:
                line_max_word_height = 0
                line_total_width = 0
                for i, word_info in enumerate(line_data):
                    bbox = dummy_draw.textbbox((0, 0), word_info['text'], font=font)
                    h = bbox[3] - bbox[1]
                    line_max_word_height = max(line_max_word_height, h)
                    
                    line_total_width += word_info['width']
                    if i < len(line_data) - 1:
                        line_total_width += space_width
                
                line_heights.append(line_max_word_height)
                total_text_height += line_max_word_height
                max_line_width = max(max_line_width, line_total_width)
            
            if line_layouts:
                 total_text_height += line_spacing * (len(line_layouts) - 1)
            
            padding = stroke_width * 2 + 10
            img_width = max_line_width + padding * 2
            img_height = total_text_height + padding * 2
            
            print(f"DEBUG: Canvas size - {img_width}x{img_height}")
            
            # Create image
            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw text
            current_y = padding
            for line_idx, line_data in enumerate(line_layouts):
                line_total_width = 0
                for i, word_info in enumerate(line_data):
                    line_total_width += word_info['width']
                    if i < len(line_data) - 1:
                        line_total_width += space_width
                        
                start_x = (img_width - line_total_width) // 2
                current_x = start_x
                
                for i, word_info in enumerate(line_data):
                    word_text = word_info['text']
                    color = word_info['color']
                    
                    if stroke_width > 0:
                        for dx in range(-stroke_width, stroke_width + 1):
                            for dy in range(-stroke_width, stroke_width + 1):
                                if dx == 0 and dy == 0: continue
                                if dx*dx + dy*dy > stroke_width*stroke_width + 1: continue 
                                draw.text((current_x + dx, current_y + dy), word_text, font=font, fill=stroke_color)
                    
                    draw.text((current_x, current_y), word_text, font=font, fill=color)
                    
                    current_x += word_info['width']
                    if i < len(line_data) - 1:
                        current_x += space_width
                
                current_y += line_heights[line_idx] + line_spacing
            
            return img 
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    composer = MockComposer()
    style = {
        'font_size': 80,
        'text_color': 'white',
        'stroke_color': 'black',
        'stroke_width': 3,
        'max_width': 960
    }
    
    text = "잡채 당면 절대 이렇게 하지마세요"
    img = composer._create_subtitle_image(text, style)
    
    if img:
        print("Success! Saving to debug_subtitle.png")
        img.save("debug_subtitle.png")
    else:
        print("Failed to create image")

if __name__ == "__main__":
    main()
