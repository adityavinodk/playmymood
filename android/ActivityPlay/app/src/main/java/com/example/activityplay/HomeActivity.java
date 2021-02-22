package com.example.activityplay;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.PersistableBundle;
import android.util.Log;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.example.activityplay.model.SpotifyCurrentTrack;
import com.example.activityplay.model.SpotifyPagingObject;
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
    SpotifyCurrentTrack currentTrack = new SpotifyCurrentTrack();

    static Handler handler;

    @Override
    public void onCreate(@Nullable Bundle savedInstanceState, @Nullable PersistableBundle persistentState) {
        super.onCreate(savedInstanceState, persistentState);

        sharedPreferences = getSharedPreferences("com.example.activityplay", Context.MODE_PRIVATE);

        Log.d("CURRENT_TRACK", "onCreate: Starting handler...");

        handler = new Handler();
        handler.post(runnable);

    }

    private final Runnable runnable = new Runnable() {
        @Override
        public void run() {

            Log.d("CURRENT_TRACK", "run: Initiating current playing track handler");

            sharedPreferences = getSharedPreferences("com.example.activityplay", Context.MODE_PRIVATE);

            Retrofit spotifyRetrofit = SpotifyRetrofitBuilder.getInstance();
            ISpotifyAPI iSpotifyAPI = spotifyRetrofit.create(ISpotifyAPI.class);

            Call<SpotifyCurrentTrack> spotifyCurrentTrackCall = iSpotifyAPI.getCurrentTrack("Bearer " +sharedPreferences.getString("isLoggedIn", ""));

            spotifyCurrentTrackCall.enqueue(new Callback<SpotifyCurrentTrack>() {
                @Override
                public void onResponse(Call<SpotifyCurrentTrack> call, Response<SpotifyCurrentTrack> response) {

                    Log.d("CURRENT_TRACK", "onResponse: Call made to Spotify with response " +response.code());

                    if(response.body() != null && response.code()==200){

                        if (!currentTrack.equals(response.body())) {

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

            handler.postDelayed(runnable, 5000);

        }
    };

}
