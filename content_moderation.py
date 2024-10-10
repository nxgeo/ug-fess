from os import environ

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from streamlit.runtime.uploaded_file_manager import UploadedFile


def has_inappropriate_image(images: list[UploadedFile]) -> bool:
    azureaivision_client = ComputerVisionClient(
        environ["AZUREAIVISION_ENDPOINT"],
        CognitiveServicesCredentials(environ["AZUREAIVISION_KEY"]),
    )

    for image in images:
        result = azureaivision_client.analyze_image_in_stream(
            image, [VisualFeatureTypes.adult]
        ).adult

        if result.is_adult_content or result.is_racy_content or result.is_gory_content:
            return True

    return False
