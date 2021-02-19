package com.example.activityplay.network;

import com.example.activityplay.model.SpotifyCurrentTrack;
import com.example.activityplay.model.SpotifyPagingObject;

import retrofit2.Call;
import retrofit2.http.GET;
import retrofit2.http.Header;
import retrofit2.http.Query;

public interface ISpotifyAPI {
    @GET("/v1/me/top/tracks")
    Call<SpotifyPagingObject> getTopTracks(@Header("Authorization") String token, @Query("limit") int limit, @Query("offset") int offset);

    @GET("/v1/me/player/currently-playing")
    Call<SpotifyCurrentTrack> getCurrentTrack(@Header("Authorization") String token);
}
