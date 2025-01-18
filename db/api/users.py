from flask import Blueprint, request, jsonify
from db import get_movie, get_movies, get_movies_by_country, \
    get_movies_faceted, add_comment, update_comment, delete_comment

from flask_cors import CORS
from utils import expect
from datetime import datetime
