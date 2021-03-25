from sklearn.cluster import DBSCAN
from collections import defaultdict
import numpy as np
from scipy import spatial
import pymongo as pym
import pandas as pd
import pprint
from bson import ObjectId
from bson.binary import Binary

TIME_DISTANCE = 900
HR_DISTANCE = 2
SONG_VEC_DISTANCE = 10

def get_clusters(data, eps):
    clustering = DBSCAN(eps=eps, min_samples=0).fit(data)
    return clustering.labels_

def addToCluster(db, datapoint):
    # TODO change logic for adding new point into cluster
    makeClusters(db)

def retrieveSimilarSongs(db, datapoint):
    song_data = []
    centroid_vec = np.array( db.clusters.find_one({"clusterId": datapoint['timestamp_cluster_index']})['data']['HR'][datapoint['HR_cluster_index']]['songs'][datapoint['song_cluster_index']]['centroid'] )
    for p in db.songs.find():
        if p['songId'] != datapoint['songId']:
            song_vec = np.array(p['metadata'])
            distance = 1 - spatial.distance.cosine(centroid_vec, song_vec)
            song_data.append({"songId": p['songId'], "distance": distance})
    song_data = sorted(song_data, key = lambda x: x['distance'])
    return list(map(lambda x: x['songId'], song_data))[:5]

def makeClusters(db):
    data = []
    for record in db.datapoints.find():
        data.append(record)
    # get all timestamps
    timestamps = []
    for d in data:
        timestamps.append(d['timestamp'])
    timestamps = np.array(timestamps).reshape(-1,1).astype(np.float64)
    timestamp_cluster_labels = get_clusters(np.array(timestamps), TIME_DISTANCE)

    # save timestamp cluster data
    clusters = defaultdict(dict)
    for i in range(len(timestamp_cluster_labels)):
        timestamp_cluster_label = str(timestamp_cluster_labels[i])
        if 'points' in clusters[timestamp_cluster_label].keys():
            points_count = len( clusters[timestamp_cluster_label]['points'] )
            clusters[timestamp_cluster_label]['points'].append(str( data[i]['_id'] ))
            clusters[timestamp_cluster_label]['centroid'] = ( points_count*clusters[timestamp_cluster_label]['centroid']+data[i]['timestamp'] )/( points_count+1 )
        else:
            clusters[timestamp_cluster_label]['points'] = [str( data[i]['_id'] )]
            clusters[timestamp_cluster_label]['centroid'] = data[i]['timestamp']
        db.datapoints.update_one({"_id": ObjectId(data[i]['_id'])}, {"$set": {"timestamp_cluster_index": timestamp_cluster_label }}) 

    for time_cluster in clusters:
        HR_points = []
        for point_id in clusters[time_cluster]['points']:
            HR_points.append(db.datapoints.find_one({ '_id': ObjectId( point_id ) })['HR'])

        HR_points = np.array(HR_points).reshape(-1,1).astype(np.float64)
        HR_cluster_labels = get_clusters(np.array(HR_points), HR_DISTANCE)
        HR_clusters = defaultdict(dict)
        for i in range(len(HR_cluster_labels)):
            HR_cluster_label = str( HR_cluster_labels[i] )
            datapoint_id = clusters[time_cluster]['points'][i]
            heart_rate_data = db.datapoints.find_one({"_id":ObjectId( datapoint_id )})['HR']
            if 'points' in HR_clusters[HR_cluster_label]:
                point_count = len(HR_clusters[HR_cluster_label]['points'])
                HR_clusters[HR_cluster_label]['points'].append(datapoint_id)
                HR_clusters[HR_cluster_label]['centroid'] = (point_count*HR_clusters[HR_cluster_label]['centroid'] + heart_rate_data)/(point_count+1)
            else:
                HR_clusters[HR_cluster_label]['points'] = [datapoint_id]
                HR_clusters[HR_cluster_label]['centroid'] = heart_rate_data
            db.datapoints.update_one({"_id": ObjectId(datapoint_id)}, {"$set": {"HR_cluster_index": HR_cluster_label }}) 
        
        for HR_cluster in HR_clusters:
            song_points = []
            for point_id in HR_clusters[HR_cluster]['points']:
                song_points.append(db.songs.find_one({"songId": db.datapoints.find_one({'_id': ObjectId( point_id )})['songId'] })['metadata'])
            song_points = np.array(song_points).astype(np.float64)
            song_cluster_labels = get_clusters(song_points, SONG_VEC_DISTANCE)

            song_clusters = defaultdict(dict)
            for i in range(len(song_cluster_labels)):
                song_cluster_label = str( song_cluster_labels[i] )
                datapoint_id = HR_clusters[HR_cluster]['points'][i]
                song_vec = np.array( db.songs.find_one({"songId": db.datapoints.find_one({'_id': ObjectId( point_id )})['songId'] })['metadata'] )
                if 'points' in song_clusters[song_cluster_label]:
                    point_count = len(song_clusters[song_cluster_label]['points'])
                    song_clusters[song_cluster_label]['points'].append(datapoint_id)
                    song_clusters[song_cluster_label]['centroid'] = (point_count*song_clusters[song_cluster_label]['centroid'] + song_vec)/(point_count+1)
                else:
                    song_clusters[song_cluster_label]['points'] = [datapoint_id]
                    song_clusters[song_cluster_label]['centroid'] = song_vec
                db.datapoints.update_one({"_id": ObjectId(datapoint_id)}, {"$set": {"song_cluster_index": song_cluster_label }}) 
            for song_cluster_index in song_clusters:
                song_cluster_centroid = song_clusters[song_cluster_index]['centroid']
                song_clusters[song_cluster_index]['centroid'] = song_cluster_centroid.tolist()

            HR_clusters[HR_cluster]['songs'] = dict( song_clusters )

        clusters[time_cluster]['HR'] = dict( HR_clusters )

    # pprint.PrettyPrinter(indent=4).pprint(dict( clusters) )
    
    # Clean Cluster collection
    db.clusters.drop()

    for time_cluster in clusters:
        db.clusters.insert_one({"clusterId": time_cluster, "data": clusters[time_cluster]})
