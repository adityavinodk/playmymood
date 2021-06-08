import random

import numpy as np
import pymongo as pym
import requests as req


def addUser(db, username, genre_count):
    count_existing_users = db.clusters.count_documents({"username": username})
    if count_existing_users > 0:
        db.users.insert_one(
            {
                "username": username,
                "genreVector": np.zeros(genre_count).tolist(),
                "musicLibrary": [],
            }
        )


def addSongToUserMusicLibrary(db, username, song_id):
    music_library = set(db.users.find_one({"username": username})["musicLibrary"])
    music_library.add(song_id)
    db.users.update_one(
        {"username": username}, {"$set": {"musicLibrary": list(music_library)}}
    )


def addSongToSimilarUsers(db, username, song_id, genres, probability):
    user_data = db.users.find_one({"username": username})
    song_data = db.songs.find_one({"songId": song_id})
    user_genre_vector = user_data["genreVector"]
    song_genre_list = song_data["genres"]
    for genre in song_genre_list:
        if genre in genres:
            genre_index = genres.index(genre)
            user_genre_vector[genre_index] += 1
    user_genre_vector = np.array(user_genre_vector)
    norm = np.linalg.norm(user_genre_vector)
    user_genre_vector = user_genre_vector / norm

    users_list = []
    for user in db.users.find():
        if user["username"] != username:
            users_list.append(
                {"username": username, "genreVector": user["genreVector"]}
            )

    if len(users_list) > 0:
        other_genre_vectors = np.array(users_list[0]["metadata"])[np.newaxis].T
        for i in range(1, len(users_list)):
            user_metadata_vector = np.array(users_list[i]["metadata"])[np.newaxis].T
            other_genre_vectors = np.concatenate(
                (other_genre_vectors, user_metadata_vector), axis=1
            )

    cosine_mul_values = np.matmul(user_genre_vector[np.newaxis], other_genre_vectors)
    most_similar_users = cosine_mul_values.argsort()[0].tolist()[-2:]

    for user_index in most_similar_users:
        if random.random() <= probability:
            addSongToUserMusicLibrary(db, users_list[user_index]["username"], song_id)

    db.users.update_one(
        {"username": username}, {"$set": {"genreVector": user_genre_vector.tolist()}}
    )
