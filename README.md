# Medlink

##Inspiration 🧠
The concept for creating an app that enables users to list their symptoms and allows doctors to quickly book appointments was inspired by the need for more accessible and patient-focused healthcare solutions. In a time where speed and accessibility are essential, individuals often delay seeking medical attention due to the inconvenience of scheduling appointments or the inability to effectively communicate their health concerns. These delays add pressure to the healthcare system by increasing appointment backlogs, prolonging wait times, and overwhelming doctors with administrative tasks, ultimately reducing the system's efficiency and quality of care. 

##What it does ⚙️
MedLinks solves these problems by empowering patients to log their symptoms in real-time, ensuring that critical information is accurately conveyed to their doctors. For healthcare providers, it offers a streamlined platform to review patient input and prioritize care by seamlessly booking appointments. This innovative solution aims to enhance the doctor-patient relationship, reduce administrative burdens, and ensure timely interventions for improved health outcomes.

##How we built it 👷‍♀️🔧
Our web app is developed with the Flask framework for Python, HTML, Tailwind CSS, and MongoDB Atlas for the database. We used ChatGPT to summarize patient inputs.
During routing, Flask checks the permission level of the signed-in user and renders the correct version of the page. We have two access levels: patients and doctors. Neither group can access the other group’s pages.

##Challenges we ran into 💀
One of the main issues was coordinating the routing between Flask and JavaScript, which required careful handling. We also had to import and implement websockets to enable data transfer without refreshing the page, ensuring smooth user interactions. Working with the database also presented challenges, requiring optimization to meet the application's needs.

##Accomplishments that we're proud of 🎉
Patients are able to chat with the AI to get more information about the symptoms.
All data is secure and access levels work seamlessly.
Data is synchronized across all databases

##What we learned 📝 
How to make information more secure on the server. How to route and retrieve information from the backend more efficiently. Enabling session access levels

##What's next for MedLinks 🔮
Add more control over scheduling appointments for patients and adding unavailable times for doctors. Scaling.
