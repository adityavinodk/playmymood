import json

from flask import Response
from flask_cors import CORS


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


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ["yes", "true", "t", "y", "1"]:
        return True
    elif v.lower() in ["no", "false", "f", "n", "0"]:
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected")
