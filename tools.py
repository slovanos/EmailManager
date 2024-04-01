# Some tool functions

# https://openai.com/pricing
# ToDo: improve scrapping updated values

def get_usage_info(response):

    usage_info = {}
    usage_info["model"] = response.model
    usage_info["object"] = response.object
    usage_info["prompt_tokens"] = response.usage.prompt_tokens
    usage_info["completion_tokens"] = response.usage.completion_tokens
    usage_info["total_tokens"] = response.usage.total_tokens

    if usage_info["model"].startswith('gpt-3.5-turbo'):
        # (4K context model)
        price_input = 0.015 / 10000
        price_output = 0.02 / 10000  # (~ 2 cents for 7500 english words)

    elif usage_info["model"].startswith('gpt-4-0125') or usage_info["model"].startswith(
        'gpt-4-1106'
    ):
        # (8K context model)
        price_input = 0.1 / 10000
        price_output = 0.3 / 10000  # (~ 30 cents for 7500 english words)

    elif usage_info["model"].startswith('gpt-4'):
        # (8K context model)
        price_input = 0.3 / 10000
        price_output = 0.6 / 10000  # (~ 60 cents for 7500 english words)
    else:
        price_input, price_output = None, None

    if price_input:
        usage_info["cost"] = round(
            usage_info.get("prompt_tokens") * price_input
            + usage_info.get("completion_tokens") * price_output,
            3,
        )
    else:
        usage_info["cost"] = "N/A"

    return usage_info
