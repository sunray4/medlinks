from openai import OpenAI
import config
import json
import os

class SymptomAnalyzer:
    def __init__(self):
        self.age = None
        self.sex = None
        self.symptoms = None
        
        self.client = OpenAI(api_key=config.OPENAI_KEY)
        self.model = 'gpt-4o-mini'
        self.conversation_history = [
            {'role': 'developer', 'content': 'You are a doctor intern. The patient (the user) will provide you with some symptoms that they are facing, and you will ask follow-up questions that will help the real doctor diagnose the patient. Your follow-up questions should provide a comprehensive understanding of the patient\'s symptoms. Ask one question at a time, without any formatting (i.e. no bullet points, no numbering), just the question in pure String. Conclude the conversation after approximately 5 to 6 questions. IMPORTANT: You will not ask the user to consult external evaluation. Your purpose is not to diagnose the patient, but to ask relative follow-up questions that can provide external doctors a better understanding of the situation. The user is the patient, and your questions will be first person. You are to ask the questions directly about the patient (user), not their child or relatives.'},
        ]
        
        self.questions_counter = 0
        self.max_questions = 6
        
        self.data = None
        self.can_ask = False
        
    def get_user_inputs(self, age, sex):
        self.can_ask = True
        self.age = age
        self.sex = sex
        
        prompt = (
            f'Patient details:\n'
            f'Age: {self.age}\n'
            f'Sex: {self.sex}\n'
        )
        
        self.conversation_history.append({'role': 'user', 'content': prompt})
        
    def generate_conclusion(self):
        if not self.conversation_history == []:
            self.can_ask = False
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
    "possible_next_steps": [
        "Monitor the headache and any additional symptoms.",
        "Encourage hydration and regular meals.",
        "Consider evaluating sleep hygiene and stress management.",
        "If the headache persists or worsens, consult a healthcare professional."
    ],
    "summary": [
        "The patient has a sharp, constant headache.",
        "The headache started suddenly after waking up.",
        "There are no accompanying symptoms such as nausea or changes in vision.",
        "The patient has experienced shorter sleep recently.",
        "The patient has not been drinking enough fluids or eating regularly."
    ]
}

Note that the content above is for example to show you the structure.''')
            self.conversation_history.append({'role': 'developer', 'content': conclusion_prompt})
            
            final_response = self.client.chat.completions.create(model=self.model, messages=self.conversation_history)
            final_message = final_response.choices[0].message.content
            
            try:
                self.data = json.loads(final_message)
                
                with open('temp/patient.json', 'w') as file:
                    file.write(json.dumps(self.data, indent=4))
                    
                return self.data
            except:
                return final_message
        
    def add_user_response(self, content):
        if self.can_ask:
            self.conversation_history.append({'role': 'user', 'content': content})
            self.questions_counter += 1
            
            if self.questions_counter >= self.max_questions:
                return self.generate_conclusion()
            else:
                response = self.client.chat.completions.create(model=self.model, messages=self.conversation_history)
                assistant_message = response.choices[0].message.content
                
                self.conversation_history.append({'role': 'assistant', 'content': assistant_message})
                
                return assistant_message
        else:
            # return ValueError('Chat session has ended or is not live. Please call the get_user_inputs() method first.')
            return 'MedGPT is processing your symptoms...'
            
        
    def analyze_symptoms(self):
        while self.questions_counter < self.max_questions:
            response = self.client.chat.completions.create(model=self.model, messages=self.conversation_history)
            
            assistant_message = response.choices[0].message.content
            print(f'Assistant: {assistant_message}')
            
            user_input = input('You: ')
            self.conversation_history.append({'role': 'assistant', 'content': assistant_message})
            self.conversation_history.append({'role': 'user', 'content': user_input})
            
            self.questions_counter += 1