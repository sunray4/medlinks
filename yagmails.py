import yagmail

yag = yagmail.SMTP('from', 'app specific password')

contents = [
    'email body',
    'another text'
]

yag.send('to', 'subject test', contents)