import logging
import httpx

from google.genai import errors, types
from pydantic import ValidationError

from analysis_models import ChunkAnalysisResponse


logger = logging.getLogger(__name__)


# ============================================================
# CUSTOM PROVIDER EXCEPTIONS
# ============================================================

class GeminiProviderError(RuntimeError):
    pass


class GeminiConfigurationError(GeminiProviderError):
    pass


class GeminiUnavailableError(GeminiProviderError):
    pass


class GeminiInvalidResponseError(GeminiProviderError):
    pass


# ============================================================
# GEMINI PROVIDER ADAPTER
# ============================================================

class GeminiProvider:

    def __init__(self, client, models):

        if client is None:
            raise GeminiConfigurationError(
                "Gemini client is not configured."
            )

        if not models:
            raise GeminiConfigurationError(
                "No Gemini models configured."
            )

        self.client = client
        self.models = tuple(models)

    # ========================================================
    # PROVIDER EXECUTION
    # ========================================================

    def __call__(
        self,
        system_instruction: str,
        prompt: str,
    ) -> dict:

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_json_schema=(
                ChunkAnalysisResponse.model_json_schema()
            ),
        )

        last_failure = None

        for model_name in self.models:

            logger.info(
                "Attempting Gemini model: %s",
                model_name,
            )

            try:

                response = (
                    self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config,
                    )
                )

                response_text = response.text

                if not response_text:
                    raise GeminiInvalidResponseError(
                        "Gemini returned an empty response."
                    )

                validated_response = (
                    ChunkAnalysisResponse.model_validate_json(
                        response_text
                    )
                )

                logger.info(
                    "Gemini response validated: %s",
                    model_name,
                )

                return validated_response.model_dump()

            # ------------------------------------------------
            # MALFORMED AI RESPONSE
            # ------------------------------------------------

            except (
                ValidationError,
                GeminiInvalidResponseError,
            ):

                last_failure = "invalid_response"

                logger.warning(
                    "Invalid structured response from %s",
                    model_name,
                )

                continue

            # ------------------------------------------------
            # NETWORK AND TRANSPORT ERRORS
            # ------------------------------------------------

            except httpx.TransportError as exc:

                last_failure = "unavailable"

                logger.warning(
                    "Gemini transport failure: model=%s type=%s",
                    model_name,
                    type(exc).__name__,
                )

                continue

            # ------------------------------------------------
            # GEMINI API ERRORS
            # ------------------------------------------------

            except errors.APIError as exc:

                status_code = exc.code

                logger.warning(
                    "Gemini API failure: model=%s status=%s",
                    model_name,
                    status_code,
                )

                # Invalid credentials or permissions.
                if status_code in (401, 403):

                    raise GeminiConfigurationError(
                        "Gemini authentication or "
                        "authorization failed."
                    ) from None

                # Invalid request or unsupported configuration.
                if status_code == 400:

                    raise GeminiConfigurationError(
                        "Gemini rejected the request "
                        "configuration."
                    ) from None

                # Model unavailable, rate limits or
                # potentially temporary service failures.
                if status_code in (
                    404,
                    408,
                    429,
                    500,
                    502,
                    503,
                    504,
                ):

                    last_failure = "unavailable"

                    continue

                raise GeminiProviderError(
                    "Unexpected Gemini API failure."
                ) from None

        # ====================================================
        # ALL CONFIGURED MODELS FAILED
        # ====================================================

        if last_failure == "invalid_response":

            raise GeminiInvalidResponseError(
                "No configured Gemini model returned "
                "a valid structured response."
            )

        raise GeminiUnavailableError(
            "Configured Gemini models are unavailable "
            "or failed to complete the request."
        )