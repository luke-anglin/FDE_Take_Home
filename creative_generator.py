import os
import logging
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
import io
import uuid
from typing import Optional, List, Dict

# Load environment variables and configure logging/API
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
GEMINI_IMG_MODEL = os.getenv("GEMINI_IMG_MODEL")
if not GEMINI_IMG_MODEL:
    raise ValueError("CRITICAL: GEMINI_IMG_MODEL is not set in your .env file.")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in your .env file.")
genai.configure(api_key=GOOGLE_API_KEY)

class ContentGenerationError(Exception):
    """Custom exception for when content fails to generate as expected."""
    pass

class CreativeGenerator:
    """Generates creative assets using an advanced multimodal prompting technique."""

    def __init__(self):
        try:
            self.model = genai.GenerativeModel(model_name=GEMINI_IMG_MODEL)
            self.model.generate_content("test")
            logging.info(f"Successfully connected to Gemini API with '{GEMINI_IMG_MODEL}'.")
        except Exception as e:
            raise RuntimeError(f"API connection failed for model '{GEMINI_IMG_MODEL}': {e}")

        self.output_dir = 'temp_outputs'
        self.aspect_ratios = ["1:1", "9:16", "16:9"]
        self.aspect_ratio_dims = {"1:1": (1024, 1024), "9:16": (720, 1280), "16:9": (1280, 720)}
        os.makedirs(self.output_dir, exist_ok=True)

    def _assemble_all_in_one_prompt(self, brief, product_name, product_description, base_images_data: List[Dict]) -> str:
        brand_colors_str = ", ".join(brief.brand_colors)
        base_image_instructions = ""
        if base_images_data:
            base_image_instructions += "\n\n**Base Image Instructions:**\n"
            for data in base_images_data:
                base_image_instructions += f"- The image provided after this prompt is a '{data['description']}'. Integrate it into the final creative as a core element. If it's a logo, place it tastefully in a corner.\n"
        
        prompt = (
            f"Generate a single, photorealistic ad creative for '{product_name}' ({product_description}).\n"
            f"**Creative Brief:**\n"
            f"- **Target Audience:** {brief.audience}\n"
            f"- **Color Palette:** The image's color scheme MUST be inspired by these brand colors: {brand_colors_str}."
            f"{base_image_instructions}"
            f"\n**Execution Requirements:**\n"
            f"1. **Text Overlay:** The text '{brief.message}' MUST be elegantly rendered directly onto the image.\n"
            f"2. **Aspect Ratio:** The final image's dimensions MUST strictly match the final, blank white placeholder image provided in the input.\n"
        )
        return prompt

    def _generate_image(self, prompt: str, aspect_ratio: str, prepared_images: List[Image.Image]) -> Optional[Image.Image]:
        try:
            contents = [prompt]
            contents.extend(prepared_images)
            dims = self.aspect_ratio_dims.get(aspect_ratio, (1024, 1024))
            placeholder_image = Image.new('RGB', dims, 'white')
            contents.append(placeholder_image)
            
            response = self.model.generate_content(contents)
            
            # --- THIS IS THE CRITICAL BUG FIX ---
            # Check for candidates BEFORE trying to access the list index.
            if not response.candidates:
                reason = "Unknown"
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    reason = response.prompt_feedback.block_reason.name
                # Raise the specific error that the main loop will catch.
                raise ContentGenerationError(f"Request blocked by safety filters. Reason: {reason}")

            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return Image.open(io.BytesIO(part.inline_data.data))
            
            text_response = response.candidates[0].content.parts[0].text
            raise ContentGenerationError(f"Model returned text instead of an image: '{text_response}'")

        except Exception as e:
            # Re-raise known errors or wrap unknown ones for consistent handling.
            if isinstance(e, ContentGenerationError):
                raise
            else:
                raise ContentGenerationError(f"An unexpected API error occurred: {e}")

    def process_and_save_creatives(self, brief, base_images_data: List[Dict]):
        generated_files = []
        
        prepared_base_images = []
        for data in base_images_data:
            try:
                image = Image.open(io.BytesIO(data['image_bytes']))
                prepared_base_images.append(image)
            except Exception as e:
                logging.error(f"Could not process uploaded file for description '{data['description']}': {e}")
                continue

        for product_name, product_details in brief.products.items():
            for aspect_ratio in self.aspect_ratios:
                logging.info(f"--- Starting generation for '{product_name}' ({aspect_ratio}) ---")
                
                # --- NEW: Wrap individual generation in a try/except block ---
                try:
                    prompt = self._assemble_all_in_one_prompt(brief, product_name, product_details.description, base_images_data)
                    generated_image = self._generate_image(prompt, aspect_ratio, prepared_base_images)

                    if generated_image:
                        ratio_str = aspect_ratio.replace(':', 'x')
                        filename = f"{brief.campaign_name.replace(' ', '_')}_{product_name.replace(' ', '_')}_{ratio_str}_{str(uuid.uuid4())[:8]}.png"
                        output_path = os.path.join(self.output_dir, filename)
                        generated_image.save(output_path)
                        generated_files.append(output_path)

                except ContentGenerationError as e:
                    # Log the specific failure and continue to the next image.
                    logging.error(f"Failed to generate creative for '{product_name}' ({aspect_ratio}). Reason: {e}")
                    continue # This is key to making the system resilient.
        
        return generated_files