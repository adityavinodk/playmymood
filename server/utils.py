from flask import Flask, request, Response, session, render_template
from flask_cors import CORS
import json


def plainResponse(success, message, status):
    return Response(
        json.dumps({"message": message, "success": success}),
        status=status,
        mimetype="application/json",
    )


def responseWithData(success, message, status, data):
    return Response(
        json.dumps({"message": message, "success": success, "data": data}),
        status=status,
        mimetype="application/json",
    )
