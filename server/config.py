from dbutils.secrets import serverSecret

class Config:
    MONGO_URL = "mongodb://localhost:27017/"
    SERVER_SELECT_TIMEOUT = 3
    SECRET_KEY = serverSecret
    RECLUSTER_TIMESTAMP = 0
    SONG_ID = ""
    USERNAME = "test-user"
    HEART_RATE = 0
    TIME_DISTANCE = 3600
    HR_DISTANCE = 10
    SONG_VEC_DISTANCE = 10
    RECOMMENDATION_COUNT = 5
    MIN_PTS = 5
