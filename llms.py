from openai import OpenAI
from tools import get_usage_info
from parameters import MODEL, SYSTEM_MSG, OPENAI_KEY, user_prompt

client = OpenAI(api_key=OPENAI_KEY)


def openai_replier(msg, model=MODEL, system_message=SYSTEM_MSG, user_prompt=user_prompt):

    print(f"Sending request to {MODEL} model...")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt(msg)},
            ],
            temperature=0.2,
            max_tokens=1024,
        )

    except Exception as e:
        print("No GPT")
        print(e)

    print("\nUsage Info:")
    print(get_usage_info(response))

    return response.choices[0].message.content


if __name__ == '__main__':

    # Quick check with a local email

    with open("./data/sample-email.txt", "r") as f:
        message = f.read()

    reply = openai_replier(message)

    print("\nReply:")
    print(reply)
