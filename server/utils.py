from flask import Flask, request, Response, session, render_template
from flask_cors import CORS
import json

def response(success, message, status):
    return Response(json.dumps({'message':message, 'success':success}), status=status, mimetype='application/json')
