from ..LLMInterface import LLMInterface
from ..LLMEnums import DocumentsTypeEnum, GeminiEnums
import logging
from google import genai
from google.genai import types


class GeminiProvider(LLMInterface):
    def __init__(self, api_key: str,
                 default_input_max_characters: int = 1000,
                 default_generation_max_output_tokens: int = 1000,
                 default_generation_temperature: float = 0.1):

        self.api_key = api_key

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None

        self.client = genai.Client(api_key=self.api_key)

        self.enums = GeminiEnums

        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()

    def generate_text(self, prompt: str, chat_history: list = [], max_output_tokens: int = None,
                      temperature: float = None):

        if not self.client:
            self.logger.error("Gemini client wasn't set")
            return None

        if not self.generation_model_id:
            self.logger.error("generation model for Gemini wasn't set")
            return None

        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        chat_history = list(chat_history) if chat_history else []
        chat_history.append(self.construct_prompt(prompt=prompt, role=GeminiEnums.USER.value))

        contents = []
        for message in chat_history:
            role = message.get("role", GeminiEnums.USER.value)
            content = message.get("parts") or message.get("content") or message.get("text") or ""
            if isinstance(content, list):
                if content and isinstance(content[0], dict):
                    content = content[0].get("text", "")
                else:
                    content = str(content)
            if role == GeminiEnums.ASSISTANT.value or role == "assistant":
                role = "model"
            elif role == GeminiEnums.SYSTEM.value or role == "system":
                role = "user"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=content)]))

        generation_config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        try:
            response = self.client.models.generate_content(
                model=self.generation_model_id,
                contents=contents,
                config=generation_config,
            )
        except Exception as e:
            self.logger.error(f"Error while generating text with Gemini: {e}")
            return None

        if not response or not getattr(response, "text", None):
            self.logger.error("Error while generating text with Gemini")
            return None

        return response.text

    def embed_text(self, text: str, document_type: str = None):
        if not self.client:
            self.logger.error("Gemini client wasn't set")
            return None

        if not self.embedding_model_id:
            self.logger.error("embedding model for Gemini wasn't set")
            return None

        task_type = "RETRIEVAL_QUERY" if document_type == DocumentsTypeEnum.QUERY.value else "RETRIEVAL_DOCUMENT"
        embedding_config = types.EmbedContentConfig(
            output_dimensionality=self.embedding_size,
            task_type=task_type,
        )

        try:
            response = self.client.models.embed_content(
                model=self.embedding_model_id,
                contents=[self.process_text(text)],
                config=embedding_config,
            )
        except Exception as e:
            self.logger.error(f"Error while embedding text with Gemini: {e}")
            return None

        if not response:
            self.logger.error("Error while embedding text with Gemini")
            return None

        embedding = None
        if hasattr(response, "embeddings") and response.embeddings:
            emb = response.embeddings[0]
            if hasattr(emb, "values") and emb.values:
                embedding = emb.values
            elif hasattr(emb, "embedding") and emb.embedding:
                embedding = emb.embedding
            elif isinstance(emb, list):
                embedding = emb
        elif hasattr(response, "embedding") and response.embedding:
            embedding = response.embedding

        if not embedding:
            self.logger.error("Error while embedding text with Gemini")
            return None

        return embedding

    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "parts": [{"text": self.process_text(prompt)}],
        }
