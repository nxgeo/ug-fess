from os import environ

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
import google.generativeai as genai
from google.generativeai.protos import Candidate
from msrest.authentication import CognitiveServicesCredentials
from streamlit.runtime.uploaded_file_manager import UploadedFile
from urlextract import URLExtract


def has_inappropriate_content(text: str) -> bool:
    genai.configure(api_key=environ["GEMINI_API_KEY"])

    safety_settings = {
        "HARASSMENT": "BLOCK_LOW_AND_ABOVE",
        "HATE_SPEECH": "BLOCK_LOW_AND_ABOVE",
        "SEXUALLY_EXPLICIT": "BLOCK_LOW_AND_ABOVE",
        "DANGEROUS": "BLOCK_LOW_AND_ABOVE",
    }

    generation_config = genai.GenerationConfig(
        max_output_tokens=1,
        temperature=0,
        top_p=0.95,
        top_k=64,
        response_mime_type="text/x.enum",
        response_schema={
            "type": "STRING",
            "enum": ["true", "false"],
        },
    )

    system_instruction = (
        "You are tasked with content moderation. Your goal is to determine whether the provided text "
        "violates any specific rules. Make sure to assess the entire content objectively and "
        "accurately based on the listed categories."
    )

    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        safety_settings,
        generation_config,
        system_instruction=system_instruction,
    )

    prompt = (
        "Does the following text violate any of the following rules: inappropriate/sexual content, harassment, "
        "bullying, racism, hate speech, hoax, slander, defamation, black campaign, doxing, threat, violence, "
        "gore, gambling, or fraud? Text: " + text
    )

    response = model.generate_content(prompt)

    FinishReason = Candidate.FinishReason

    if response.candidates[0].finish_reason in {
        FinishReason.SAFETY,
        FinishReason.PROHIBITED_CONTENT,
        FinishReason.SPII,
    }:
        return True

    try:
        if response.text == "true":
            return True
    except ValueError:
        pass

    return False


def has_disallowed_entities(text: str) -> bool:
    url_extractor = URLExtract()
    url_extractor.update_when_older(7)

    return "#" in text or "@" in text or url_extractor.has_urls(text)


def has_inappropriate_image(images: list[UploadedFile]) -> bool:
    azureaivision_client = ComputerVisionClient(
        environ["AZUREAIVISION_ENDPOINT"],
        CognitiveServicesCredentials(environ["AZUREAIVISION_KEY"]),
    )

    for image in images:
        image.seek(0)

        result = azureaivision_client.analyze_image_in_stream(
            image, [VisualFeatureTypes.adult]
        ).adult

        if result.is_adult_content or result.is_racy_content or result.is_gory_content:
            return True

    return False
