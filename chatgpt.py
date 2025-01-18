from openai import OpenAI
import config

class SymptomAnalyzer:
    def __init__(self):
        self.age = None
        self.sex = None
        self.symptoms = None
        
        self.client = OpenAI(api_key=config.OPENAI_KEY)
        self.conversation_history = [
            {'role': 'developer', 'content': 'You are a doctor intern. The patient (the user) will provide you with some symptoms that they are facing, and you will ask follow-up questions that will help the real doctor diagnose the patient. Your follow-up questions should provide a comprehensive understanding of the patient\'s symptoms. Ask one question at a time, without any formatting (i.e. no bullet points, no numbering), just the question in pure String. Conclude the conversation after approximately 5 to 6 questions.'},
        ]
        
        self.questions_counter = 0
        self.max_questions = 6
        
    def get_user_inputs(self, age, sex, symptoms):
        self.age = age
        self.sex = sex
        self.symptoms = symptoms
        
        prompt = (
            f'Patient details:\n'
            f'Age: {self.age}\n'
            f'Sex: {self.sex}\n'
            f'Symptoms: {self.symptoms}\n'
        )
        
        self.conversation_history.append({'role': 'user', 'content': prompt})
        
    def analyze_symptoms(self):
        while self.questions_counter < self.max_questions:
            response = self.client.chat.completions.create(model='gpt-4o-mini', messages=self.conversation_history)
            
            assistant_message = response.choices[0].message.content
            print(f'Assistant: {assistant_message}')
            
            user_input = input('You: ')
            self.conversation_history.append({'role': 'assistant', 'content': assistant_message})
            self.conversation_history.append({'role': 'user', 'content': user_input})
            
            self.questions_counter += 1
        
        conclusion_prompt = ('''Based on the information gathered, provide a summary of the patient\'s symptoms and possible next steps in JSON format.
{
    "patient_details": {
        "age": 20,
        "sex": "male"
    },
    "conversation_history": [
        {
            "role": "developer",
            "content": "You are a doctor intern. The patient (the user) will provide you with some symptoms that they are facing, and you will ask follow-up questions that will help the real doctor diagnose the patient. Your follow-up questions should provide a comprehensive understanding of the patient's symptoms. Ask one question at a time, without any formatting (i.e. no bullet points, no numbering), just the question in pure String. Conclude the conversation after approximately 5 to 6 questions."
        },
        {
            "role": "user",
            "content": "I have a headache."
        },
        {
            "role": "assistant",
            "content": "How long have you had this headache?"
        },
        {
            "role": "user",
            "content": "For about 3-5 days. When I look up my head hurts."
        }
    ],
    "summary": [
        "The patient has a headache.",
        "The patient has had the headache for 3-5 days.",
        "The patient experiences pain when looking up."
    ]
}

Note that the content above is for example to show you the structure.''')
        self.conversation_history.append({'role': 'developer', 'content': conclusion_prompt})
        
        final_response = self.client.chat.completions.create(model='gpt-4o-mini', messages=self.conversation_history)
        final_message = final_response.choices[0].message.content
        
        print(f'Assistant: {final_message}')
    
bot = SymptomAnalyzer()
bot.get_user_inputs(int(input('Enter age > ')), input('Enter sex > '), input('Enter symptoms > '))

print(bot.analyze_symptoms())