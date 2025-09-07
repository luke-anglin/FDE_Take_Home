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
        self.aspect_ratio_dims = {
            "1:1": (1024, 1024),
            "9:16": (720, 1280),
            "16:9": (1280, 720)
        }
        os.makedirs(self.output_dir, exist_ok=True)

    def _assemble_all_in_one_prompt(self, brief, product_name, product_description, base_images_data: List[Dict]) -> str:
        """Assembles a prompt that now includes instructions for the uploaded base images."""
        brand_colors_str = ", ".join(brief.brand_colors)
        
        base_image_instructions = ""
        if base_images_data:
            base_image_instructions += "\n\n**Base Image Instructions:**\n"
            for i, data in enumerate(base_images_data):
                base_image_instructions += f"- The image provided after this prompt is a '{data['description']}'. Integrate it into the final creative as a core element. If it's a logo, place it tastefully in a corner.\n"
        
        prompt = (
            f"Generate a single, photorealistic ad creative for '{product_name}' ({product_description}).\n"
            f"**Creative Brief:**\n"
            f"- **Target Audience:** {brief.audience}\n"
            f"- **Color Palette:** The image's color scheme MUST be inspired by these brand colors: {brand_colors_str}."
            f"{base_image_instructions}"
            f"\n**Execution Requirements:**\n"
            f"1. **Text Overlay:** The text '{brief.message}' MUST be elegantly rendered directly onto the image.\n"
            f"2. **Aspect Ratio:** This is the most critical instruction. The final image's dimensions MUST strictly match the final, blank white placeholder image provided in the input. Do not deviate from its shape.\n"
        )
        return prompt

    def _generate_image(self, prompt: str, aspect_ratio: str, prepared_images: List[Image.Image]) -> Optional[Image.Image]:
        """Generates an image using the prompt and a list of prepared PIL Image objects."""
        try:
            contents = [prompt]
            contents.extend(prepared_images)
            
            dims = self.aspect_ratio_dims.get(aspect_ratio, (1024, 1024))
            placeholder_image = Image.new('RGB', dims, 'white')
            contents.append(placeholder_image)
            
            response = self.model.generate_content(contents)
            
            if not response.candidates:
                raise ContentGenerationError("Request was blocked by the model's default safety filters.")

            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return Image.open(io.BytesIO(part.inline_data.data))
            
            text_response = response.candidates[0].content.parts[0].text
            raise ContentGenerationError(f"Model returned text instead of an image: '{text_response}'")

        except Exception as e:
            logging.error(f"An unexpected error occurred during image generation: {e}")
            if isinstance(e, ContentGenerationError):
                raise
            else:
                raise e

    def process_and_save_creatives(self, brief, base_images_data: List[Dict]):
        """Processes a brief using the advanced multimodal generation method."""
        generated_files = []
        
        # --- THIS IS THE BUG FIX ---
        # Convert byte streams to PIL Image objects ONCE to prevent stream exhaustion.
        prepared_base_images = []
        prepared_base_images_with_desc = []
        for data in base_images_data:
            try:
                logging.info(f"Preparing base image ('{data['description']}')...")
                image = Image.open(io.BytesIO(data['image_bytes']))
                prepared_base_images.append(image)
                prepared_base_images_with_desc.append({"image": image, "description": data["description"]})
            except Exception as e:
                logging.error(f"Could not process uploaded file for description '{data['description']}': {e}")
                # Skip this file if it's corrupted
                continue
        # --- END OF BUG FIX ---

        for product_name, product_details in brief.products.items():
            for aspect_ratio in self.aspect_ratios:
                logging.info(f"--- Starting generation for '{product_name}' ({aspect_ratio}) ---")
                
                prompt = self._assemble_all_in_one_prompt(brief, product_name, product_details.description, base_images_data)
                
                generated_image = self._generate_image(prompt, aspect_ratio, prepared_base_images)

                if generated_image:
                    ratio_str = aspect_ratio.replace(':', 'x')
                    filename = f"{brief.campaign_name.replace(' ', '_')}_{product_name.replace(' ', '_')}_{ratio_str}_{str(uuid.uuid4())[:8]}.png"
                    output_path = os.path.join(self.output_dir, filename)
                    generated_image.save(output_path)
                    generated_files.append(output_path)
        
        return generated_files