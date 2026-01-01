from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont
import io
import os

app = FastAPI(title="Pagination Image Generator API", version="1.0.0")

def create_pagination_image(selected_number):
    # 1. මූලික සැකසුම් (Settings & Colors)
    # -------------------------------------
    selected_number = int(selected_number)
    
    # Colors (HEX codes based on the style)
    COLOR_BG = "#000000"       # Background Black
    COLOR_ORANGE = "#ff9900"   # The Theme Orange
    COLOR_GREY = "#1b1b1b"     # Unselected Grey
    COLOR_WHITE = "#ffffff"    # Text White
    COLOR_BLACK = "#000000"    # Text Black

    # Font Settings (Arial is standard, trying to load it)
    try:
        # Windows/Mac වල arial font එක තිබුනොත් ලස්සනට එයි
        font = ImageFont.truetype("arial.ttf", 20)
        font_bold = ImageFont.truetype("arialbd.ttf", 20)
    except IOError:
        # නැත්නම් default font එක ගනී
        font = ImageFont.load_default()
        font_bold = font

    # Box Sizes
    box_height = 50
    num_box_width = 50
    nav_box_width = 90  # For Prev/Next buttons
    spacing = 8
    padding = 20  # Image padding

    # 2. Page Numbers තීරණය කිරීම
    # -------------------------------------
    # තෝරාගත් අංකය මැදට එන විදියට අංක 5ක් ගමු (උදා: 10 දුන්නොත් -> 8, 9, 10, 11, 12)
    start_num = max(1, selected_number - 2)
    pages_to_show = list(range(start_num, start_num + 5))

    # 3. Image එකේ ප්‍රමාණය ගණනය කිරීම
    # -------------------------------------
    # Width = Padding + Prev + Spacing + (5 * NumBoxes) + (4 * Spacing) + Spacing + Next + Padding
    total_width = (padding * 2) + (nav_box_width * 2) + (num_box_width * 5) + (spacing * 7)
    total_height = box_height + (padding * 2)

    # අලුත් Image එකක් හදමු (Black Background)
    img = Image.new('RGB', (total_width, total_height), color=COLOR_BG)
    draw = ImageDraw.Draw(img)

    current_x = padding

    # Function to draw rounded rectangle with text
    def draw_button(x, text, bg_color, text_color, is_border_only=False):
        # Draw Box
        shape = [x, padding, x + (nav_box_width if len(text) > 3 else num_box_width), padding + box_height]
        
        if is_border_only:
            # Highlight එක (Border එක විතරක් Orange)
            draw.rounded_rectangle(shape, radius=5, fill=COLOR_BG, outline=COLOR_ORANGE, width=2)
        else:
            # සාමාන්‍ය Button එක
            draw.rounded_rectangle(shape, radius=5, fill=bg_color)
        
        # Draw Text (Centered)
        # Text size calculation using getbbox for newer Pillow versions
        left, top, right, bottom = font_bold.getbbox(text)
        text_w = right - left
        text_h = bottom - top
        
        # Center position
        btn_w = nav_box_width if len(text) > 3 else num_box_width
        text_x = x + (btn_w - text_w) / 2
        text_y = padding + (box_height - text_h) / 2 - 4 # Little adj for vertical center
        
        draw.text((text_x, text_y), text, fill=text_color, font=font_bold)
        
        return x + btn_w + spacing

    # 4. Buttons ඇඳීම
    # -------------------------------------
    
    # [Prev] Button
    current_x = draw_button(current_x, "Prev", COLOR_ORANGE, COLOR_BLACK)

    # [Number] Buttons
    for page in pages_to_show:
        if page == selected_number:
            # Selected Page (Black bg, Orange Border)
            current_x = draw_button(current_x, str(page), COLOR_BG, COLOR_WHITE, is_border_only=True)
        else:
            # Unselected Page (Grey bg)
            current_x = draw_button(current_x, str(page), COLOR_GREY, COLOR_WHITE)

    # [Next] Button
    current_x = draw_button(current_x, "Next", COLOR_ORANGE, COLOR_BLACK)

    return img


@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "message": "Welcome to Pagination Image Generator API",
        "endpoints": {
            "generate_image": "/pagination/{page_number}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/pagination/{page_number}")
async def get_pagination_image(page_number: int):
    """
    Generate a pagination image for the given page number.
    
    Args:
        page_number (int): The page number to generate pagination for
    
    Returns:
        PNG image as binary data
    """
    try:
        if page_number < 1:
            raise HTTPException(status_code=400, detail="Page number must be greater than 0")
        
        # Generate the image
        image = create_pagination_image(page_number)
        
        # Convert image to bytes
        image_stream = io.BytesIO()
        image.save(image_stream, format="PNG")
        image_stream.seek(0)
        
        # Return as streaming response
        return StreamingResponse(
            iter([image_stream.getvalue()]),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=page_{page_number}.png"}
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid page number: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)