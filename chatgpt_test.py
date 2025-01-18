import config
from openai import OpenAI

client = OpenAI(api_key=config.OPENAI_KEY)

# Initialize the OpenAI API client

def summarize_conversation(conversation):
    response = client.chat.completions.create(model='gpt-3.5-turbo',
    messages=[
        {'role': 'system', 'content': 'You are a helpful assistant that summarizes conversations.'},
        {'role': 'user', 'content': f'Summarize the following conversation:\n\n{conversation}'}
    ],
    max_tokens=150,
    temperature=0.5)
    summary = response.choices[0].message.content
    return summary

if __name__ == "__main__":
    # Example conversation
    conversation = """
    User: Hi, I have a problem with my order.
    Support: I'm sorry to hear that. Can you please provide your order number?
    User: Sure, it's 12345.
    Support: Thank you. I see that your order was shipped yesterday and should arrive tomorrow.
    User: Great, thanks for the update!
    """
    summary = summarize_conversation(conversation)
    print("Summary of the conversation:")
    print(summary)