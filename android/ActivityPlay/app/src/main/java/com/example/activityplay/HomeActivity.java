package com.example.activityplay;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.widget.Button;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.example.activityplay.model.RecommendationDTO;
import com.example.activityplay.model.SpotifyCurrentTrack;
import com.example.activityplay.model.SpotifyTrack;
import com.example.activityplay.network.IBackendAPI;
import com.example.activityplay.network.ISpotifyAPI;
import com.example.activityplay.networkmanager.BackendRetrofitBuilder;
import com.example.activityplay.networkmanager.SpotifyRetrofitBuilder;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import retrofit2.Retrofit;

public class HomeActivity extends AppCompatActivity {
    static SharedPreferences sharedPreferences;

    static SpotifyCurrentTrack currentTrack = new SpotifyCurrentTrack();
    static RecommendationDTO recommendationDTO = new RecommendationDTO();

    static Handler handler;

    static boolean stopDataCollection = false;
    // handler.removeMessages(0);

    @Override
    public void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_home);

        sharedPreferences = getSharedPreferences("com.example.activityplay", Context.MODE_PRIVATE);

        Log.d("CURRENT_TRACK", "onCreate: Starting handler...");
        SpotifyTrack dummySpotifyTrack = new SpotifyTrack();
        dummySpotifyTrack.setId("");
        currentTrack.setItem(dummySpotifyTrack);

        handler = new Handler();

        Button playBtn = findViewById(R.id.bt_play);

        playBtn.setOnClickListener(view -> {
            stopDataCollection = !stopDataCollection;
            if(stopDataCollection == true) {
                playBtn.setText("STOP");
                handler.post(recommendationsRunnable);
            }
            else {
                playBtn.setText("PLAY");
                handler.post(dataCollectorRunnable);
            }

        });

        handler.post(dataCollectorRunnable);

    }

    private final Runnable dataCollectorRunnable = new Runnable() {
        @Override
        public void run() {

            sharedPreferences = getSharedPreferences("com.example.activityplay", Context.MODE_PRIVATE);

            Retrofit spotifyRetrofit = SpotifyRetrofitBuilder.getInstance();
            ISpotifyAPI iSpotifyAPI = spotifyRetrofit.create(ISpotifyAPI.class);

            Log.d("CURRENT_TRACK", "Token: " +sharedPreferences.getString("isLoggedIn", ""));

            Call<SpotifyCurrentTrack> spotifyCurrentTrackCall = iSpotifyAPI.getCurrentTrack("Bearer " +sharedPreferences.getString("isLoggedIn", ""), "from_token");

            spotifyCurrentTrackCall.enqueue(new Callback<SpotifyCurrentTrack>() {
                @Override
                public void onResponse(Call<SpotifyCurrentTrack> call, Response<SpotifyCurrentTrack> response) {

                    Log.d("CURRENT_TRACK", "onResponse: Call made to Spotify with response " +response.code() +" " +response.message());

                    if(response.body() != null && response.code()==200){

                        if (!currentTrack.getItem().getId().equals(response.body().getItem().getId())) {

                            currentTrack.setItem(response.body().getItem());

                            Retrofit backendRetrofit = BackendRetrofitBuilder.getInstance();
                            IBackendAPI iBackendAPI = backendRetrofit.create(IBackendAPI.class);

                            Call<Void> backendSendCurrentTrackCall = iBackendAPI.addCurrentlyPlayingTrack(response.body().getItem());
                            backendSendCurrentTrackCall.enqueue(new Callback<Void>() {
                                @Override
                                public void onResponse(Call<Void> call, Response<Void> response) {
                                    Log.d("CURRENT_TRACK", "onResponse: Sent to server with response " +response.code());
                                }

                                @Override
                                public void onFailure(Call<Void> call, Throwable t) {
                                    Log.d("CURRENT_TRACK", "onFailure: Send to backend server failed");
                                }
                            });
                        }
                    }

                    else{
                        Log.d("CURRENT_TRACK", "onResponse: Call made to Spotify with response " +response.code() +". Nothing playing (if 200) else error.");
                    }
                }

                @Override
                public void onFailure(Call<SpotifyCurrentTrack> call, Throwable t) {
                    Log.d("CURRENT_TRACK", "onFailure: Call to Spotify failed");
                }
            });

            if(!stopDataCollection)
                handler.postDelayed(dataCollectorRunnable, 5000);

        }
    };



    private final Runnable recommendationsRunnable = new Runnable() {
        @Override
        public void run() {

            sharedPreferences = getSharedPreferences("com.example.activityplay", Context.MODE_PRIVATE);

            Retrofit spotifyRetrofit = SpotifyRetrofitBuilder.getInstance();
            ISpotifyAPI iSpotifyAPI = spotifyRetrofit.create(ISpotifyAPI.class);

            Log.d("CURRENT_TRACK_R", "Token: " +sharedPreferences.getString("isLoggedIn", ""));

            Call<SpotifyCurrentTrack> spotifyCurrentTrackCall = iSpotifyAPI.getCurrentTrack("Bearer " +sharedPreferences.getString("isLoggedIn", ""), "from_token");

            spotifyCurrentTrackCall.enqueue(new Callback<SpotifyCurrentTrack>() {
                @Override
                public void onResponse(Call<SpotifyCurrentTrack> call, Response<SpotifyCurrentTrack> response) {

                    SpotifyCurrentTrack spotifyCurrentTrack = response.body();

                    Log.d("CURRENT_TRACK_R", "onResponse: Call made to Spotify with response " +response.code());
                    Log.d("CURRENT_TRACK_R", "onResponse: Call made to Spotify with body " +spotifyCurrentTrack.getItem().getId());
                    Log.d("CURRENT_TRACK_R", "onResponse: Current track on phone " +currentTrack.getItem().getId());

                    Log.d("CURRENT_TRACK_R", "onResponse: Equality = " +spotifyCurrentTrack.getItem().getId().equals(currentTrack.getItem().getId()));

                    boolean a = spotifyCurrentTrack.getItem().getId().equals(currentTrack.getItem().getId());

                    if(!a){
                        Log.d("CHECK", "onResponse: A = TRUE " +a);
                    }

                    if (!a) {

                        Log.d("RECOMMENDATIONS", "onResponse: TRACK CHANGED, FETCHING RECOMMENDATIONS");
                        currentTrack.setItem(response.body().getItem());

                        Retrofit backendRetrofit = BackendRetrofitBuilder.getInstance();
                        IBackendAPI iBackendAPI = backendRetrofit.create(IBackendAPI.class);

                        Call<RecommendationDTO> backendGetRecommendations = iBackendAPI.getRecommendations();
                        Log.d("RECOMMENDATIONS", "run: Fetching recommendations");
                        backendGetRecommendations.enqueue(new Callback<RecommendationDTO>() {
                            @Override
                            public void onResponse(Call<RecommendationDTO> call, Response<RecommendationDTO> response) {
                                if (response.code() == 200) {
                                    Log.d("RECOMMENDATIONS", "onResponseBackend: Succesfully received recommendations from backend");

                                    Call<Void> spotifyQueue = iSpotifyAPI.addToQueue(
                                            "Bearer " + sharedPreferences.getString("isLoggedIn", ""),
                                            "spotify:track:" + response.body().getData().get(0)
                                    );
                                    spotifyQueue.enqueue(new Callback<Void>() {
                                        @Override
                                        public void onResponse(Call<Void> call, Response<Void> response2) {
                                            if (response2.code() == 204) {
                                                Log.d("RECOMMENDATIONS", "onResponseSpotify: Added " + response.body().getData().get(0) + " to queue");
                                            } else if (response2.code() == 404) {
                                                Log.d("RECOMMENDATIONS", "onResponseSpotify: Device or Track not found");
                                            } else if (response2.code() == 403) {
                                                Log.d("RECOMMENDATIONS", "onResponseSpotify: User not Premium");
                                            }
                                        }

                                        @Override
                                        public void onFailure(Call<Void> call, Throwable t) {
                                            Log.d("RECOMMENDATIONS", "onFailureSpotify: Failed to enqueue Spotify call");
                                        }
                                    });

                                }
                                else{
                                    Log.d("RECOMMENDATIONS", "onResponse: Response = " +response.code());
                                }
                            }

                            @Override
                            public void onFailure(Call<RecommendationDTO> call, Throwable t) {
                                Log.d("RECOMMENDATIONS", "onFailureBackend: Failed to enqueue backend call");
                            }
                        });
                    }
                    else{
                        Log.d("RECOMMENDATIONS", "currentTrack: " +currentTrack.getItem().getId());
                        Log.d("RECOMMENDATIONS", "spotifyTrack: " +spotifyCurrentTrack.getItem().getId());
                    }
                }

                @Override
                public void onFailure(Call<SpotifyCurrentTrack> call, Throwable t) {
                    Log.d("CURRENT_TRACK_R", "onFailure: Call to Spotify failed");
                }
            });

            sharedPreferences = getSharedPreferences("com.example.activityplay", Context.MODE_PRIVATE);


            if(stopDataCollection)
                handler.postDelayed(recommendationsRunnable, 5000);

        }
    };

}
