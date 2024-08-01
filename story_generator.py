# Helper functions for story generation and image processing
# Main components:
# - generate_content(): Generates story content using AI models
# - generate_image(): Creates images based on prompts
# - add_text_to_image(): Adds text to generated images
# - extract_story_elements(): Parses JSON data from generated content
# - process_text(): Processes generated text and creates images

## For complete working code please connect with me
## Please read README.md before proceeding further

import os
import random
import requests
import base64
import json
import re
import shutil
import time
import logging
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont
import textwrap
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add api keys
api_keys = []

MODELS = ["meta-llama/Llama-3-8b-chat-hf", "google/gemma-7b-it", "codellama/CodeLlama-13b-Instruct-hf", "mistralai/Mistral-7B-Instruct-v0.2"]
IMAGE_MODELS = ["prompthero/openjourney", "stabilityai/stable-diffusion-xl-base-1.0"]

# Pre-load font
FONT = ImageFont.truetype("PlayfairDisplaySC-Regular.otf", 30)

@lru_cache(maxsize=100)
def generate_content(prompt:str, model: int = 0,temp:float=0.7,top_p:float=0.5) -> str:
    '''
    - Constructs a detailed prompt for story generation
    - Sends a request to an AI model API 
    - Handles potential errors in API communication
    - Returns the generated text or an error message
    '''
    # For complete working code please connect with me
    pass


def generate_image(model: str, prompt: str, negative_prompt: str, title: str, image_index:int) -> List[str]:
    '''
    - Sends a request to an image generation API
    - Handles the API response and potential errors
    - Decodes and saves the generated image
    - Returns the path of the saved image
    '''
    # For complete working code please connect with me
    pass


def add_text_to_image(image_path, text, output_path):
    '''
    - Opens an image file and creates a drawing object
    - Calculates text size and position
    - Adds a semi-transparent background behind the text
    - Writes the text on the image and saves it

    '''
    try:
        # Open the image
        img = Image.open(image_path)

        # Create a drawing object
        draw = ImageDraw.Draw(img)

        # Load a font
        font = FONT

        # Set maximum width for text wrapping
        max_width = img.width - 40

        # Wrap the text
        wrapped_text = textwrap.fill(text, width=40)

        # Calculate text size and position
        text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_position = ((img.width - text_width) / 2, img.height - text_height - 20)

        # Get background color from image
        bg_color = img.getpixel((int(text_position[0]), int(text_position[1])))

        # Add semi-transparent text box
        box_position = (text_position[0] - 10, text_position[1] - 10,
                        text_position[0] + text_width + 10, text_position[1] + text_height + 10)
        draw.rectangle(box_position, fill=(*bg_color, 128))

        # Add text
        draw.multiline_text(text_position, wrapped_text, font=font, fill=(255, 255, 255, 255), align='center')

        # Save the image
        img.save(output_path)

        # Return the modified image
        return output_path

    except Exception as e:
        logging.error(f"Error adding text to image: {str(e)}")
        raise


def extract_story_elements(full_text:str)-> Tuple[str, str, str, List[str]]:
    '''
    - Finds and extracts the JSON string from the full text
    - Parses the JSON data
    - Returns extracted elements as a tuple
    '''
    try:
        # Extract JSON string from the full text
        json_start = full_text.find('{')
        json_end = full_text.rfind('}') + 1
        json_string = full_text[json_start:json_end]
        # Parse JSON
        story_data = json.loads(json_string)
        return story_data['title'], story_data['story'], story_data['moral'], story_data['imagePrompts']
    
    except (json.JSONDecodeError, KeyError) as e:
        logging.error(f"Error extracting story elements: {str(e)}")
        raise

def process_text(text:str)-> Tuple[List[str], str, str]:
    '''
    - Extracts story elements using extract_story_elements()
    - Combines sentences and creates new image prompts
    - Generates images for each part of the story
    - Adds text to images to create storybook pages
    - Moves final images to an output directory
    - Returns paths of created images, output directory, and story title
    '''

    try:
        title_raw, story, moral, image_prompts = extract_story_elements(text)
        replace_special_chars = lambda s: re.sub(r'[?;:%#@*&\^$!<>,\\/]+', ' ', s)
        title = replace_special_chars(title_raw)
        sentences = story.split('. ')
        combined_sentences = []
        image_prompt_new = []
        image_generated_paths = []

        # Combine 2-3 sentences together
        for i in range(0, len(sentences), 3):
            combined = '. '.join(sentences[i:i+3])
            combined_sentences.append(combined)
            prompt = image_prompts[i // 3] if i // 3 < len(image_prompts) else image_prompts[-1]
            new_prompt = f"""Given the following story for context enclosed between the $ symbol: ${combined}$,
                        generate a children's story book style image with the following prompt: {prompt}"""
            image_prompt_new.append(new_prompt)

        folder_name = title.replace(' ', '_') + '_' + str(int(time.time()))
        output_dir = os.path.join('static', 'storybooks', folder_name)
        os.makedirs(output_dir, exist_ok=True)
        
        
        for i, prompt in enumerate(image_prompt_new):
            image_path = generate_image(IMAGE_MODELS[0], prompt, "", title, i)  
            image_generated_paths.append(image_path)

        # Combine text and image paths
        combined_story_with_images = []

        for i, (text, image_path) in enumerate(zip(combined_sentences, image_generated_paths)):
                story_with_image = add_text_to_image(image_path, text, f"image_new_{i}.png")
                output_img_path = os.path.join(output_dir, f"image_new_{i}.png")
                shutil.move(story_with_image, output_img_path)
                combined_story_with_images.append(output_img_path)


        return combined_story_with_images , output_dir, title
    
    except Exception as e:
        logging.error(f"Error processing text: {str(e)}")
        raise
