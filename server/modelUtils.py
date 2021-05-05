import pprint
import random
from collections import defaultdict

import numpy as np
import pymongo as pym
from bson import ObjectId
from scipy import spatial
from sklearn.cluster import DBSCAN


def get_clusters(data, eps):
    clustering = DBSCAN(eps=eps).fit(data)
    return clustering.labels_


def addToTimestampClusters(db, datapoint, config):
    datapoint_id = datapoint["_id"]
    str_datapoint_id = str(datapoint["_id"])
    datapoint_timestamp = datapoint["timestamp"]
    datapoint_id_dict = {"_id": datapoint_id}

    clusters = {}
    for cluster in db.clusters.find():
        clusters[str(cluster["clusterId"])] = cluster

    # find if datapoint belongs to any existing timestamp clusters
    timestamp_cluster_index = 0
    can_add_to_existing_timestamp_clusters = False
    while (
        str(timestamp_cluster_index) in clusters
        and not can_add_to_existing_timestamp_clusters
    ):
        str_timestamp_cluster_index = str(timestamp_cluster_index)
        timestamp_cluster = clusters[str_timestamp_cluster_index]["data"]
        point_count = len(timestamp_cluster["points"])
        near_count = 0
        j = 0
        while j < point_count and near_count < (config["min_pts"] - 1):
            point_timestamp = db.datapoints.find_one(
                {"_id": ObjectId(timestamp_cluster["points"][j])}
            )["timestamp"]
            if abs(point_timestamp - datapoint_timestamp) < config["time_epsilon"]:
                near_count += 1
            j += 1
        if near_count == (config["min_pts"] - 1):
            can_add_to_existing_timestamp_clusters = True
            db.datapoints.update_one(
                datapoint_id_dict,
                {"$set": {"timestamp_cluster_index": str_timestamp_cluster_index}},
            )
        timestamp_cluster_index += 1

    new_timestamp_points = []
    # do a DBSCAN on the outliers to find if there are other minCount number of outliers that can be a part of the datapoint's cluster
    outlier_timestamps = []
    for point_id in clusters["outliers"]["data"]:
        outlier_timestamps.append(
            db.datapoints.find_one({"_id": ObjectId(point_id)})["timestamp"]
        )
    all_new_timestamps = [datapoint_timestamp] + outlier_timestamps
    outlier_cluster_labels = get_clusters(
        np.array(all_new_timestamps).reshape(-1, 1).astype(np.float64),
        config["time_epsilon"],
    )
    # if new datapoint is an outlier among the outliers
    if outlier_cluster_labels[0] == -1:
        # add to the timestamp cluster
        if can_add_to_existing_timestamp_clusters:
            new_timestamp_points = [str_datapoint_id]
        # else add to outlier list
        else:
            db.datapoints.update_one(
                datapoint_id_dict, {"$set": {"timestamp_cluster_index": "outlier"}}
            )
            outliers = clusters["outliers"]["data"]
            db.clusters.update_one(
                {"clusterId": "outliers"},
                {"$set": {"data": outliers + [str_datapoint_id]}},
            )
    # if new datapoint is not an outlier among the outliers
    else:
        labels = outlier_cluster_labels[1:]
        # if there minCount outliers that are part of the same cluster as the datapoint, add all those to timestamp cluster
        indices = [i for i, x in enumerate(labels) if x == outlier_cluster_labels[0]]
        new_timestamp_points = [str_datapoint_id] + [
            clusters["outliers"]["data"][i] for i in indices
        ]

    if len(new_timestamp_points) > 0:
        # if some previous outliers become part of a cluster
        if len(new_timestamp_points) > 1:
            new_outliers = list(
                filter(
                    lambda x: x not in new_timestamp_points,
                    clusters["outliers"]["data"],
                )
            )
            db.clusters.update_one(
                {"clusterId": "outliers"}, {"$set": {"data": new_outliers}}
            )
        # if can_add to existing cluster
        if can_add_to_existing_timestamp_clusters:
            str_timestamp_cluster_index = db.datapoints.find_one(datapoint_id_dict)[
                "timestamp_cluster_index"
            ]
            cluster_centroid = clusters[str_timestamp_cluster_index]["data"]["centroid"]
            point_count = len(clusters[str_timestamp_cluster_index]["data"]["points"])
            new_centroid = (
                cluster_centroid * point_count + sum(all_new_timestamps)
            ) / (point_count + len(new_timestamp_points))
            new_timestamp_points_list = (
                clusters[str_timestamp_cluster_index]["data"]["points"]
                + new_timestamp_points
            )
            HR_clusters = clusters[str_timestamp_cluster_index]["data"]["HR"]
            addToHRClusters(db, new_timestamp_points, HR_clusters, config)
            db.clusters.update_one(
                {"clusterId": str_timestamp_cluster_index},
                {
                    "$set": {
                        "data": {
                            "centroid": new_centroid,
                            "points": new_timestamp_points_list,
                            "HR": HR_clusters,
                        }
                    }
                },
            )
        else:
            addNewTimestampCluster(db, new_timestamp_points, config)


def addToHRClusters(db, new_points, HR_clusters, config):
    new_HR_cluster_index = len(HR_clusters) - 1
    for point_id in new_points:
        datapoint_id_dict = {"_id": ObjectId(point_id)}
        datapoint_HR = db.datapoints.find_one(datapoint_id_dict)["HR"]

        # find if datapoint belongs to any existing HR clusters
        HR_cluster_index = 0
        can_add_to_existing_HR_cluster = False
        while (
            str(HR_cluster_index) in HR_clusters and not can_add_to_existing_HR_cluster
        ):
            str_HR_cluster_index = str(HR_cluster_index)
            HR_cluster = HR_clusters[str_HR_cluster_index]
            point_count = len(HR_cluster["points"])
            near_count = 0
            j = 0
            while j < point_count and near_count < (config["min_pts"] - 1):
                point_HR = db.datapoints.find_one(
                    {"_id": ObjectId(HR_cluster["points"][j])}
                )["HR"]
                if abs(point_HR - datapoint_HR) < config["HR_epsilon"]:
                    near_count += 1
                j += 1
            if near_count == (config["min_pts"] - 1):
                can_add_to_existing_HR_cluster = True
                db.datapoints.update_one(
                    datapoint_id_dict,
                    {"$set": {"HR_cluster_index": str_HR_cluster_index}},
                )
            HR_cluster_index += 1

        new_HR_points = []
        # do a dbscan on the outliers to find if there are other mincount number of outliers that can be a part of the datapoint's cluster
        outlier_HRs = []
        for outlier_point_id in HR_clusters["outliers"]:
            outlier_HRs.append(
                db.datapoints.find_one({"_id": ObjectId(outlier_point_id)})["HR"]
            )
        all_new_HRs = [datapoint_HR] + outlier_HRs
        outlier_cluster_labels = get_clusters(
            np.array(all_new_HRs).reshape(-1, 1).astype(np.float64),
            config["HR_epsilon"],
        )
        # if new datapoint is an outlier among the outliers
        if outlier_cluster_labels[0] == -1:
            # add to the HR cluster
            if can_add_to_existing_HR_cluster:
                new_HR_points = [point_id]
            # else add to outliers list
            else:
                db.datapoints.update_one(
                    datapoint_id_dict, {"$set": {"HR_cluster_index": "outlier"}}
                )
                outliers = HR_clusters["outliers"]
                HR_clusters["outliers"] = outliers + [point_id]
        # if new datapoint is not an outlier among the outliers
        else:
            labels = outlier_cluster_labels[1:]
            # if there mincount outliers that are part of the same cluster as the datapoint, add all those to HR cluster
            indices = [
                i for i, x in enumerate(labels) if x == outlier_cluster_labels[0]
            ]
            new_HR_points = [point_id] + [HR_clusters["outliers"][i] for i in indices]

        if len(new_HR_points) > 0:

            # if previous outliers now form a cluster with new points
            if len(new_HR_points) > 1:
                new_HR_outliers = list(
                    filter(lambda x: x not in new_HR_points, HR_clusters["outliers"])
                )
                HR_clusters["outliers"] = new_HR_outliers

            # if can add to existing cluster
            if can_add_to_existing_HR_cluster:
                str_HR_cluster_index = db.datapoints.find_one(datapoint_id_dict)[
                    "HR_cluster_index"
                ]
                cluster_centroid = HR_clusters[str_HR_cluster_index]["centroid"]
                point_count = len(HR_clusters[str_HR_cluster_index]["points"])
                new_centroid = (cluster_centroid * point_count + sum(all_new_HRs)) / (
                    point_count + len(new_HR_points)
                )
                new_HR_points_list = (
                    HR_clusters[str_HR_cluster_index]["points"] + new_HR_points
                )
                song_clusters = HR_clusters[str_HR_cluster_index]["songs"]
                addToSongClusters(db, new_HR_points, song_clusters, config)
                HR_clusters[str_HR_cluster_index] = {
                    "points": new_HR_points_list,
                    "centroid": new_centroid,
                    "songs": song_clusters,
                }
            # else make new HR cluster
            else:
                centroid = sum(all_new_HRs) / len(new_HR_points)
                song_clusters = makeSongClusters(db, new_HR_points, config)
                HR_clusters[str(new_HR_cluster_index)] = {
                    "points": new_HR_points,
                    "centroid": centroid,
                    "songs": song_clusters,
                }
                for point in new_HR_points:
                    db.datapoints.update_one(
                        {"_id": ObjectId(point)},
                        {"$set": {"HR_cluster_index": str(new_HR_cluster_index)}},
                    )
                new_HR_cluster_index += 1


def addToSongClusters(db, new_points, song_clusters, config):
    new_song_cluster_index = len(song_clusters) - 1
    for point_id in new_points:
        datapoint_id_dict = {"_id": ObjectId(point_id)}
        datapoint_songId = db.datapoints.find_one(datapoint_id_dict)["songId"]
        datapoint_songVec = db.songs.find_one({"songId": datapoint_songId})["metadata"]
        np_datapoint_songVec = np.array(datapoint_songVec)

        # find if datapoint belongs to any existing song clusters
        song_cluster_index = 0
        can_add_to_existing_song_cluster = False
        while (
            str(song_cluster_index) in song_clusters
            and not can_add_to_existing_song_cluster
        ):
            str_song_cluster_index = str(song_cluster_index)
            song_cluster = song_clusters[str_song_cluster_index]
            point_count = len(song_cluster["points"])
            near_count = 0
            j = 0
            while j < point_count and near_count < (config["min_pts"] - 1):
                point_song = db.datapoints.find_one(
                    {"_id": ObjectId(song_cluster["points"][j])}
                )["songId"]
                song_metadata = db.songs.find_one({"songId": point_song})["metadata"]
                distance = spatial.distance.cosine(
                    np.array(song_metadata), np_datapoint_songVec
                )
                if distance < config["song_epsilon"]:
                    near_count += 1
                j += 1
            if near_count == (config["min_pts"] - 1):
                can_add_to_existing_song_cluster = True
                db.datapoints.update_one(
                    datapoint_id_dict,
                    {"$set": {"song_cluster_index": str_song_cluster_index}},
                )
            song_cluster_index += 1

        new_song_points = []
        # do a dbscan on the outliers to find if there are other mincount number of outliers that can be a part of the datapoint's cluster
        outlier_songVecs = []
        for outlier_point_id in song_clusters["outliers"]:
            song_metadata = db.songs.find_one(
                {
                    "songId": db.datapoints.find_one(
                        {"_id": ObjectId(outlier_point_id)}
                    )["songId"]
                }
            )["metadata"]
            outlier_songVecs.append(song_metadata)
        all_new_songVecs = [datapoint_songVec] + outlier_songVecs
        outlier_cluster_labels = get_clusters(
            np.array(all_new_songVecs).astype(np.float64), config["song_epsilon"]
        )
        # if new datapoint is an outlier among the outliers
        if outlier_cluster_labels[0] == -1:
            # add to the song cluster
            if can_add_to_existing_song_cluster:
                new_song_points = [point_id]
            # else add to outliers list
            else:
                db.datapoints.update_one(
                    datapoint_id_dict, {"$set": {"song_cluster_index": "outlier"}}
                )
                outliers = song_clusters["outliers"]
                song_clusters["outliers"] = outliers + [point_id]
        # if new datapoint is not an outlier among the outliers
        else:
            labels = outlier_cluster_labels[1:]
            # if there mincount outliers that are part of the same cluster as the datapoint, add all those to song cluster
            indices = [
                i for i, x in enumerate(labels) if x == outlier_cluster_labels[0]
            ]
            new_song_points = [point_id] + [
                song_clusters["outliers"][i] for i in indices
            ]

        if len(new_song_points) > 0:

            # if previous outliers now form a cluster
            if len(new_song_points) > 1:
                new_song_outliers = list(
                    filter(
                        lambda x: x not in new_song_points, song_clusters["outliers"]
                    )
                )
                song_clusters["outliers"] = new_song_outliers

            # if can add to existing cluster
            if can_add_to_existing_song_cluster:
                str_song_cluster_index = db.datapoints.find_one(datapoint_id_dict)[
                    "song_cluster_index"
                ]
                cluster_centroid = np.array(
                    song_clusters[str_song_cluster_index]["centroid"]
                )
                point_count = len(song_clusters[str_song_cluster_index]["points"])
                new_centroid = (
                    cluster_centroid * point_count + np.sum(all_new_songVecs, axis=0)
                ) / (point_count + len(new_song_points))
                new_song_points_list = (
                    song_clusters[str_song_cluster_index]["points"] + new_song_points
                )
                song_clusters[str_song_cluster_index] = {
                    "points": new_song_points_list,
                    "centroid": new_centroid.tolist(),
                }
            # else make new song cluster
            else:
                centroid = np.sum(all_new_songVecs, axis=0) / len(new_song_points)
                song_clusters[str(new_song_cluster_index)] = {
                    "points": new_song_points,
                    "centroid": centroid.tolist(),
                }
                for point in new_song_points:
                    db.datapoints.update_one(
                        {"_id": ObjectId(point)},
                        {"$set": {"song_cluster_index": str(new_song_cluster_index)}},
                    )
                new_song_cluster_index += 1


def addNewTimestampCluster(db, new_points, config):
    data = []
    for datapoint_id in new_points:
        data.append(db.datapoints.find_one({"_id": ObjectId(datapoint_id)}))
    timestamp_cluster_index = db.clusters.find().count() - 1

    # get all timestamps
    timestamps = []
    for d in data:
        timestamps.append(d["timestamp"])
        db.datapoints.update_one(
            {"_id": ObjectId(d["_id"])},
            {"$set": {"timestamp_cluster_index": str(timestamp_cluster_index)}},
        )

    centroid = sum(timestamps) / len(new_points)
    HR_clusters = makeHRClusters(db, new_points, config)
    db.clusters.insert_one(
        {
            "clusterId": str(timestamp_cluster_index),
            "data": {"HR": HR_clusters, "centroid": centroid, "points": new_points},
        }
    )


def retrieveSimilarSongs(db, datapoint, config):
    song_data = []
    clusters = {}
    for cluster in db.clusters.find():
        clusters[str(cluster["clusterId"])] = cluster
    freq_dict = {"frequencies": []}
    timestamp_cluster_index = 0
    while str(timestamp_cluster_index) in clusters:
        freq_dict["frequencies"].append(
            len(clusters[str(timestamp_cluster_index)]["data"]["points"])
        )
        timestamp_freq_dict = {"frequencies": []}
        HR_cluster_index = 0
        HR_clusters = clusters[str(timestamp_cluster_index)]["data"]["HR"]
        while str(HR_cluster_index) in HR_clusters:
            timestamp_freq_dict["frequencies"].append(
                len(HR_clusters[str(HR_cluster_index)]["points"])
            )
            HR_freq_dict = {"frequencies": []}
            song_cluster_index = 0
            song_clusters = HR_clusters[str(HR_cluster_index)]["songs"]
            while str(song_cluster_index) in song_clusters:
                HR_freq_dict["frequencies"].append(
                    len(song_clusters[str(song_cluster_index)]["points"])
                )
                song_cluster_index += 1
            timestamp_freq_dict[str(HR_cluster_index)] = HR_freq_dict
            HR_cluster_index += 1
        freq_dict[str(timestamp_cluster_index)] = timestamp_freq_dict
        timestamp_cluster_index += 1

    points = []
    # if datapoint is not a timestamp outlier
    if datapoint["timestamp_cluster_index"] != "outlier":
        timestamp_cluster = clusters[datapoint["timestamp_cluster_index"]]["data"]
        HR_freq_dict = freq_dict[datapoint["timestamp_cluster_index"]]
        # if datapoint is not a HR outlier
        if datapoint["HR_cluster_index"] != "outlier":
            HR_cluster = timestamp_cluster["HR"][datapoint["HR_cluster_index"]]
            song_freq_dict = HR_freq_dict[datapoint["HR_cluster_index"]]
            # if datapoint is not a song outlier
            if datapoint["song_cluster_index"] != "outlier":
                # get the cluster centroid and recommend most similar songs from music library
                song_cluster = HR_cluster["songs"][datapoint["song_cluster_index"]]
                centroid_vec = np.array(song_cluster["centroid"])
                for p in db.songs.find({"username": config["username"]}):
                    if p["songId"] != datapoint["songId"]:
                        song_vec = np.array(p["metadata"])
                        distance = spatial.distance.cosine(centroid_vec, song_vec)
                        song_data.append(
                            {
                                "songId": p["songId"],
                                "genres": db.songs.find_one({"songId": p["songId"]})[
                                    "genres"
                                ],
                                "distance": distance,
                            }
                        )
                song_data = sorted(song_data, key=lambda x: x["distance"])
                count = index = 0
                rec_songs = []
                different_genre_songs = []
                datapoint_genres = db.songs.find_one(
                    {"songId": datapoint["songId"]}
                )["genres"]
                total_songs = len(song_data)
                while index < total_songs and count < config["recommendation_count"]:
                    song = song_data[index]
                    if len(
                        [genre for genre in song["genres"] if genre in datapoint_genres]
                    ):
                        rec_songs.append(song)
                        count += 1
                    else:
                        different_genre_songs.append(song)
                    index += 1
                rec_songs = rec_songs + different_genre_songs[: (5 - count)]
                points = list(map(lambda x: x["songId"], rec_songs))
            # else sample points from points under HR cluster
            else:
                if len(song_freq_dict["frequencies"]):
                    points = []
                    for i in range(config["recommendation_count"]):
                        points.append(
                            selectRandomFromSongCluster(
                                db,
                                HR_cluster["songs"],
                                song_freq_dict,
                                HR_cluster["points"],
                            )
                        )
                else:
                    datapoints = random.sample(
                        HR_cluster["points"], config["recommendation_count"]
                    )
                    points = []
                    for datapoint_id in datapoints:
                        points.append(
                            db.datapoints.find_one({"_id": ObjectId(datapoint_id)})[
                                "songId"
                            ]
                        )
        # else sample points from points under timestamp cluster
        else:
            if len(HR_freq_dict["frequencies"]):
                points = []
                for i in range(config["recommendation_count"]):
                    points.append(
                        selectRandomFromHRCluster(
                            db,
                            timestamp_cluster["HR"],
                            HR_freq_dict,
                            timestamp_cluster["points"],
                        )
                    )
            else:
                datapoints = random.sample(
                    timestamp_cluster["points"], config["recommendation_count"]
                )
                points = []
                for datapoint_id in datapoints:
                    points.append(
                        db.datapoints.find_one({"_id": ObjectId(datapoint_id)})[
                            "songId"
                        ]
                    )
    # else fetch the last 5 songs
    # TODO think of a better logic
    else:
        total_datapoints = sum(freq_dict["frequencies"])
        if len(freq_dict["frequencies"]):
            points = []
            weights = [x / total_datapoints for x in freq_dict["frequencies"]]
            for i in range(config["recommendation_count"]):
                timestamp_cluster_choice = random.choices(
                    range(len(freq_dict["frequencies"])), weights=weights, k=1
                )[0]
                points.append(
                    selectRandomFromHRCluster(
                        db,
                        clusters[str(timestamp_cluster_choice)]["data"]["HR"],
                        freq_dict[str(timestamp_cluster_choice)],
                        clusters[str(timestamp_cluster_choice)]["data"]["points"],
                    )
                )
        else:
            records = db.datapoints.find(sort=[("_id", pym.DESCENDING)]).limit(
                config["recommendation_count"]
            )
            points = [point["songId"] for point in records]

    points = [x for x in set(points) if x != datapoint["songId"]]
    return list(set(points))


def selectRandomFromHRCluster(db, HR_clusters, freq_dict, parent_points):
    total_timestamp_datapoints = sum(freq_dict["frequencies"])
    if total_timestamp_datapoints:
        weights = [x / total_timestamp_datapoints for x in freq_dict["frequencies"]]
        HR_cluster_choice = random.choices(
            range(len(freq_dict["frequencies"])), weights=weights, k=1
        )[0]
        return selectRandomFromSongCluster(
            db,
            HR_clusters[str(HR_cluster_choice)]["songs"],
            freq_dict[str(HR_cluster_choice)],
            HR_clusters[str(HR_cluster_choice)]["points"],
        )
    datapoint_id = random.sample(parent_points, 1)[0]
    return db.datapoints.find_one({"_id": ObjectId(datapoint_id)})["songId"]


def selectRandomFromSongCluster(db, song_clusters, freq_dict, parent_points):
    total_HR_datapoints = sum(freq_dict["frequencies"])
    if total_HR_datapoints:
        weights = [x / total_HR_datapoints for x in freq_dict["frequencies"]]
        song_cluster_choice = random.choices(
            range(len(freq_dict["frequencies"])), weights=weights, k=1
        )[0]
        datapoint_id = random.sample(
            song_clusters[str(song_cluster_choice)]["points"], 1
        )[0]
    else:
        datapoint_id = random.sample(parent_points, 1)[0]
    return db.datapoints.find_one({"_id": ObjectId(datapoint_id)})["songId"]


def makeTimestampClusters(db, config):
    data = []
    for record in db.datapoints.find({"username": config["username"]}):
        data.append(record)
    db.clusters.drop()
    if len(data):
        # get all timestamps
        timestamps = []
        for d in data:
            timestamps.append(d["timestamp"])
        timestamps = np.array(timestamps).reshape(-1, 1).astype(np.float64)
        timestamp_cluster_labels = get_clusters(
            np.array(timestamps), config["time_epsilon"]
        )

        # save timestamp cluster data
        clusters = defaultdict(dict)
        clusters["outliers"] = []
        for i in range(len(timestamp_cluster_labels)):
            timestamp_cluster_label = str(timestamp_cluster_labels[i])
            if timestamp_cluster_label != "-1":
                if "points" in clusters[timestamp_cluster_label].keys():
                    points_count = len(clusters[timestamp_cluster_label]["points"])
                    clusters[timestamp_cluster_label]["points"].append(
                        str(data[i]["_id"])
                    )
                    clusters[timestamp_cluster_label]["centroid"] = (
                        points_count * clusters[timestamp_cluster_label]["centroid"]
                        + data[i]["timestamp"]
                    ) / (points_count + 1)
                else:
                    clusters[timestamp_cluster_label]["points"] = [str(data[i]["_id"])]
                    clusters[timestamp_cluster_label]["centroid"] = data[i]["timestamp"]
                db.datapoints.update_one(
                    {"_id": ObjectId(data[i]["_id"])},
                    {"$set": {"timestamp_cluster_index": timestamp_cluster_label}},
                )
            else:
                clusters["outliers"].append(str(data[i]["_id"]))
                db.datapoints.update_one(
                    {"_id": ObjectId(data[i]["_id"])},
                    {"$set": {"timestamp_cluster_index": "outlier"}},
                )

        for time_cluster in clusters:
            if time_cluster != "outliers":
                HR_clusters = makeHRClusters(
                    db, clusters[time_cluster]["points"], config
                )

                clusters[time_cluster]["HR"] = dict(HR_clusters)

        # pprint.PrettyPrinter(indent=4).pprint(dict( clusters) )

        for time_cluster in clusters:
            db.clusters.insert_one(
                {"clusterId": time_cluster, "data": clusters[time_cluster]}
            )
    else:
        db.clusters.insert_one({"clusterId": "outliers", "data": []})


def makeHRClusters(db, ids, config):
    HR_points = []
    for point_id in ids:
        HR_points.append(db.datapoints.find_one({"_id": ObjectId(point_id)})["HR"])

    HR_points = np.array(HR_points).reshape(-1, 1).astype(np.float64)
    HR_cluster_labels = get_clusters(np.array(HR_points), config["HR_epsilon"])
    HR_clusters = defaultdict(dict)
    HR_clusters["outliers"] = []
    for i in range(len(HR_cluster_labels)):
        HR_cluster_label = str(HR_cluster_labels[i])
        datapoint_id = ids[i]
        heart_rate_data = db.datapoints.find_one({"_id": ObjectId(datapoint_id)})["HR"]
        if HR_cluster_label != "-1":
            if "points" in HR_clusters[HR_cluster_label]:
                point_count = len(HR_clusters[HR_cluster_label]["points"])
                HR_clusters[HR_cluster_label]["points"].append(datapoint_id)
                HR_clusters[HR_cluster_label]["centroid"] = (
                    point_count * HR_clusters[HR_cluster_label]["centroid"]
                    + heart_rate_data
                ) / (point_count + 1)
            else:
                HR_clusters[HR_cluster_label]["points"] = [datapoint_id]
                HR_clusters[HR_cluster_label]["centroid"] = heart_rate_data
            db.datapoints.update_one(
                {"_id": ObjectId(datapoint_id)},
                {"$set": {"HR_cluster_index": HR_cluster_label}},
            )
        else:
            HR_clusters["outliers"].append(datapoint_id)
            db.datapoints.update_one(
                {"_id": ObjectId(datapoint_id)},
                {"$set": {"HR_cluster_index": "outlier"}},
            )

    for HR_cluster in HR_clusters:
        if HR_cluster != "outliers":
            song_clusters = makeSongClusters(
                db, HR_clusters[HR_cluster]["points"], config
            )

            HR_clusters[HR_cluster]["songs"] = dict(song_clusters)

    return HR_clusters


def makeSongClusters(db, ids, config):
    song_points = []
    for point_id in ids:
        song_points.append(
            db.songs.find_one(
                {
                    "songId": db.datapoints.find_one({"_id": ObjectId(point_id)})[
                        "songId"
                    ]
                }
            )["metadata"]
        )
    song_points = np.array(song_points).astype(np.float64)
    song_cluster_labels = get_clusters(song_points, config["song_epsilon"])

    song_clusters = defaultdict(dict)
    song_clusters["outliers"] = []
    for i in range(len(song_cluster_labels)):
        song_cluster_label = str(song_cluster_labels[i])
        datapoint_id = ids[i]
        song_vec = np.array(
            db.songs.find_one(
                {
                    "songId": db.datapoints.find_one({"_id": ObjectId(point_id)})[
                        "songId"
                    ]
                }
            )["metadata"]
        )
        if song_cluster_label != "-1":
            if "points" in song_clusters[song_cluster_label]:
                point_count = len(song_clusters[song_cluster_label]["points"])
                song_clusters[song_cluster_label]["points"].append(datapoint_id)
                song_clusters[song_cluster_label]["centroid"] = (
                    point_count * song_clusters[song_cluster_label]["centroid"]
                    + song_vec
                ) / (point_count + 1)
            else:
                song_clusters[song_cluster_label]["points"] = [datapoint_id]
                song_clusters[song_cluster_label]["centroid"] = song_vec
            db.datapoints.update_one(
                {"_id": ObjectId(datapoint_id)},
                {"$set": {"song_cluster_index": song_cluster_label}},
            )
        else:
            song_clusters["outliers"].append(datapoint_id)
            db.datapoints.update_one(
                {"_id": ObjectId(datapoint_id)},
                {"$set": {"song_cluster_index": "outlier"}},
            )
    for song_cluster_index in song_clusters:
        if song_cluster_index != "outliers":
            song_cluster_centroid = song_clusters[song_cluster_index]["centroid"]
            song_clusters[song_cluster_index][
                "centroid"
            ] = song_cluster_centroid.tolist()

    return song_clusters
