from bytez import Bytez
from api_key_manager import ApiKeyManager
from utils import logger, format_error
import os

class BytezSolver:
    """Solves captchas using Bytez API."""
    
    def __init__(self, model="google/gemini-3-pro-preview", level=0):
        self.model_name = model
        self.api_key_manager = ApiKeyManager(used_by="github-gen-mobile", level=level)
        self.current_api_key = None
        self.current_api_key_id = None
        
    def solve_puzzle(self, image_path, question, level=0, max_retries=3):
        """
        Solves the visual puzzle.
        
        Args:
            image_path: Path to the puzzle image.
            question: The specific rule/question for the puzzle.
            level: Logging indentation level.
            max_retries: Number of times to retry with different keys/attempts.
            
        Returns:
            int: The 1-based index of the answer (1-5), or None if failed.
        """
        logger(f"[Bytez] Solving puzzle: {question}", level=level)
        
        # Prepare data once (image conversion)
        try:
            import base64
            with open(image_path, "rb") as img_file:
                base64_img = base64.b64encode(img_file.read()).decode('utf-8')
            data_uri = f"data:image/png;base64,{base64_img}"
        except Exception as e:
            logger(f"❌ Error preparing image: {format_error(e)}", level=level+1)
            return None

        # Prepare Prompt
        prompt_text = f"""You are an automated puzzle solver. I will upload an image containing a visual logic puzzle (often a "CAPTCHA" style test) and provide the specific question or rule.

Your task:
1. Analyze the "Reference" (usually a separate image, a list, or a thought bubble).
2. Compare it against the row of "Options" (usually 5 images arranged horizontally).
3. Identify which Option matches the Reference based on the rule provided.
4. Count the Options from Left to Right (1, 2, 3, 4, 5).

OUTPUT REQUIREMENT:
You must reply with ONLY the single digit of the correct answer. Do not include any text, punctuation, explanation, or reasoning. Just the number.

Example:
User: [Image] "Select the matching pair"
AI: 3


instruction: {question}"""

        for attempt in range(1, max_retries + 1):
            logger(f"[Bytez] Attempt {attempt}/{max_retries} to solve...", level=level+1)
            
            # 1. Acquire Key
            api_key_id, api_key = self.api_key_manager.acquire_key(self.model_name, level=level+2)
            if not api_key:
                logger("❌ Failed to acquire API key (no keys available?)", level=level+2)
                # If we can't get a key, retrying might not help unless one is released externally, 
                # but we can try wait or just continue. 
                # For now, let's continue to next attempt/stop.
                if attempt < max_retries:
                    import time
                    time.sleep(2)
                    continue
                return None
                
            try:
                # 4. Call Bytez
                sdk = Bytez(api_key)
                model = sdk.model(self.model_name)
                
                payload = [
                  {
                    "role": "user",
                    "content": [
                      {
                        "type": "text",
                        "text": prompt_text
                      },
                      {
                        "type": "image",
                        "url": data_uri
                      }
                    ]
                  }
                ]
                
                logger(f"   Sending request to {self.model_name}...", level=level+2)
                result = model.run(payload)
                
                if result.error:
                    logger(f"   ❌ Bytez Error: {result.error}", level=level+2)
                    self.api_key_manager.log_usage(api_key_id, api_key, self.model_name, False, error=result.error, level=level+2)
                    
                    # Check for quota/credit errors to expire key
                    err_str = str(result.error).lower()
                    if "quota" in err_str or "credit" in err_str or "unauthorized" in err_str:
                         logger(f"   ⚠ Key expired or invalid, marking as expired.", level=level+2)
                         self.api_key_manager.mark_key_expired_and_release(api_key, self.model_name, level=level+2)
                    else:
                         self.api_key_manager.release_key(api_key, level=level+2)
                    
                    # Continue to next retry
                    continue
                
                # Parse output
                # The output structure from Bytez SDK seems to be: {'role': 'assistant', 'content': '3'}
                # Or sometimes just a string? User says it's an object with role and content keys.
                
                raw_output = result.output
                if isinstance(raw_output, dict) and 'content' in raw_output:
                    output_text = raw_output['content'].strip()
                elif hasattr(raw_output, 'content'): # Maybe an object?
                     output_text = raw_output.content.strip()
                else:
                    output_text = str(raw_output).strip()
                    
                logger(f"   ✓ Bytez Response: {output_text}", level=level+2)
                
                self.api_key_manager.log_usage(api_key_id, api_key, self.model_name, True, level=level+2)
                self.api_key_manager.release_key(api_key, level=level+2)
                
                # Parse output (should be a single digit)
                import re
                match = re.search(r'\d', output_text)
                if match:
                    return int(match.group(0))
                else:
                    logger(f"   ❌ Could not parse number from response: {output_text}", level=level+2)
                    # Maybe retry if parsing failed? Or give up on this image?
                    # Let's retry with a new key/call just in case the model failed to follow instructions.
                    continue

            except Exception as e:
                logger(f"   ❌ Error in BytezSolver attempt: {format_error(e)}", level=level+2)
                self.api_key_manager.release_key(api_key, level=level+2)
                # Continue retry
                
        logger(f"❌ BytezSolver failed after {max_retries} attempts.", level=level+1)
        return None
