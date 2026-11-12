import logging
import time
from typing import Any

from litellm import completion
from litellm.exceptions import APIConnectionError, ServiceUnavailableError


logger = logging.getLogger(__name__)
REQUEST_TIMEOUT_SECONDS = 30


class ProviderClientError(RuntimeError):
    pass


def generate_text(
    provider: str,
    model: str,
    prompt: str,
    api_key: str,
    **provider_options: Any,
) -> str:
    if not api_key:
        raise ProviderClientError(f"{provider} API key is not configured.")

    messages = [{"role": "user", "content": prompt}]
    for attempt in range(2):
        try:
            response = completion(
                model=model,
                api_key=api_key,
                messages=messages,
                timeout=REQUEST_TIMEOUT_SECONDS,
                **provider_options,
            )
            choices = getattr(response, "choices", None)
            content = (
                getattr(choices[0].message, "content", None)
                if choices else None
            )
            if not isinstance(content, str):
                raise ProviderClientError(
                    f"{provider} returned no text response."
                )
            return content
        except (APIConnectionError, ServiceUnavailableError) as error:
            if attempt == 0:
                logger.warning(
                    "%s request had a transient connection failure; retrying once (%s)",
                    provider,
                    type(error).__name__,
                )
                time.sleep(0.25)
                continue
            logger.warning(
                "%s request failed after one retry (%s)",
                provider,
                type(error).__name__,
            )
            raise RuntimeError(
                f"{provider} request failed after one retry "
                f"({type(error).__name__})."
            ) from None
        except ProviderClientError:
            raise
        except Exception as error:
            logger.warning(
                "%s request failed (%s)",
                provider,
                type(error).__name__,
            )
            raise RuntimeError(
                f"{provider} request failed ({type(error).__name__})."
            ) from None

    raise RuntimeError(f"{provider} request failed.")
