import requests
import uuid

'''
Known problems:
1. the question is not actually skipped when user selects '0'
    a) the same question is asked again the next iteration
2. could dynamically adjust max # questions, instead of setting to fixed 8
'''

class Infermedica:
    def __init__(self):
        self.app_id = '54d345b3'
        self.app_key = '1bf5ea2c6acf5d85c98193fb1114467b'
        
        self.max_questions = 8
        self.questions_counter = 0
        
    def api_request(self, endpoint, method='GET', data=None):
        url = f'https://api.us.infermedica.com/v3/{endpoint}'
        headers = {
            'App-Id': self.app_id,
            'App-Key': self.app_key,
            'Content-Type': 'application/json',
            'Interview-Id': str(uuid.uuid4())
        }
        
        if method == 'GET':
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, headers=headers, json=data)
        
        return response.json()
    
    def get_symptoms(self):
        self.age = int(input('Enter your age > '))
        self.sex = input('Enter your sex (male/female) > ').lower()
        
        self.symptoms = input('Describe your symptoms > ')
        
        parse_data = {
            'text': self.symptoms,
            'age': {'value': self.age},
            'sex': self.sex
        }
        
        parsed_response = self.api_request('parse', method='POST', data=parse_data)
        print(parsed_response)
        initial_evidence = [{'id': item['id'], 'choice_id': 'present'} for item in parsed_response['mentions']]
        
        diagnosis_data = {
            'sex': self.sex,
            'age': {'value': self.age},
            'evidence': initial_evidence
        }
        
        while self.questions_counter < self.max_questions:
            diagnosis = self.api_request('diagnosis', method='POST', data=diagnosis_data)
            question = diagnosis.get('question')
            
            if not question:
                break
            
            print('\n' + question['text'])
            for i, item in enumerate(question['items']):
                print(f'{i+1}. {item["name"]}')
            print('0. Skip this question')
                
            answer = input('\nSelect the number corresponding to your answer (\'0\' to skip) > ')
            if answer == '0':
                choice_id = 'unknown'
            else:
                choice_id = question['items'][int(answer)-1]['id']
            
            diagnosis_data['evidence'].append({'id': choice_id, 'choice_id': 'present'})
            self.questions_counter += 1
            
            if diagnosis.get('should_stop'):
                break
            
        conditions = diagnosis.get('conditions', [])
        if conditions:
            print('\nBased on your symptoms, here are the possible conditions:')
            for condition in conditions:
                print(f'{condition["name"]} ({condition["probability"]:.2f})')
            print()
        else:
            print('No conditions found.')
                
# test
infermedica = Infermedica()
infermedica.get_symptoms()