package com.example.activityplay.network;

import com.example.activityplay.model.SpotifyTrack;

import java.util.List;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.POST;

public interface IBackendAPI {
    @POST("/api/songs/addMetadata")
    Call<Void> sendTopTracks(@Body SpotifyTrack spotifytrack);
}
