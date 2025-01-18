from pymongo import MongoClient
import certifi

client = MongoClient(
    "mongodb+srv://alexeyddudarev:iHltPOFFuZ5oB91k@medlinks.sqkll.mongodb.net/?retryWrites=true&w=majority&appName=medlinks",
    tls=True,
    tlsCAFile=certifi.where()
)