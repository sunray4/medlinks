import chatgpt

# init
bot = chatgpt.SymptomAnalyzer()

# get user details (age, sex)
bot.get_user_inputs(17, 'male')

'''
add user response to conversation.

:param content: str
if bot.can_ask == true, messages are allowed.
if bot.can_ask == false, it means chat session has ended (because a conclusion has been given) or did not call bot.get_user_inputs() first.

returns json
'''
print(bot.add_user_response('I have a headache.'))

while bot.can_ask:
    response = input('Your response: ')
    print(bot.add_user_response(response))