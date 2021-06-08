package com.example.activityplay.network;

import com.example.activityplay.model.RecommendationDTO;
import com.example.activityplay.model.SpotifyCurrentTrack;
import com.example.activityplay.model.SpotifyTrack;

import java.util.List;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.POST;

public interface IBackendAPI {
    @POST("/api/songs/addMetadata")
    Call<Void> sendSongData(@Body SpotifyTrack spotifytrack);

    @POST("/api/songs/addCurrentlyPlayingTrack")
    Call<Void> addCurrentlyPlayingTrack(@Body SpotifyTrack spotifyTrack);

    @GET("api/songs/recommendations")
    Call<RecommendationDTO> getRecommendations();
}
