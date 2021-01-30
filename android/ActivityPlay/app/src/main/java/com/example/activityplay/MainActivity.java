package com.example.activityplay;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;

import com.example.activityplay.model.SpotifyPagingObject;
import com.example.activityplay.model.SpotifyTrack;
import com.example.activityplay.model.CurrentlyPlayingTrack;
import com.example.activityplay.network.IBackendAPI;
import com.example.activityplay.network.ISpotifyAPI;
import com.example.activityplay.networkmanager.BackendRetrofitBuilder;
import com.example.activityplay.networkmanager.SpotifyRetrofitBuilder;
import com.spotify.sdk.android.authentication.AuthenticationClient;
import com.spotify.sdk.android.authentication.AuthenticationRequest;
import com.spotify.sdk.android.authentication.AuthenticationResponse;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import retrofit2.Retrofit;

public class MainActivity extends AppCompatActivity {

    private static final String CLIENT_ID = "7755c51dfb7d46c8abafd1b0ebe7df97";
    private static final String REDIRECT_URI = "com-example-activityplay://callback";
    private static final int RC_SPOTIFY = 1337;

    SharedPreferences sharedPreferences;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        SharedPreferences sharedPreferences = getSharedPreferences("com.example.activityplay", Context.MODE_PRIVATE);

        Button btSignIn = findViewById(R.id.bt_signin);

        if(sharedPreferences.contains("isLoggedIn")){
            btSignIn.setText("Enter");
            btSignIn.setOnClickListener(view -> {
                startActivity(new Intent(this, HomeActivity.class));
            });
        }
        else{
            AuthenticationRequest.Builder builder = new AuthenticationRequest.Builder(CLIENT_ID, AuthenticationResponse.Type.TOKEN, REDIRECT_URI);
            builder.setScopes(new String[]{"user-top-read"});
            AuthenticationRequest request = builder.build();
            findViewById(R.id.bt_signin).setOnClickListener(view -> {
                AuthenticationClient.openLoginActivity(this, RC_SPOTIFY, request);
            });
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        AuthenticationResponse authorizationResponse = AuthenticationClient.getResponse(resultCode, data);

        if (authorizationResponse.getType() == AuthenticationResponse.Type.TOKEN) {

            Log.d("SPOTIFYLOGIN", "onActivityResult: Logged in successfully");

            sharedPreferences = getSharedPreferences("com.example.activityplay", Context.MODE_PRIVATE);
            SharedPreferences.Editor editor = sharedPreferences.edit();
            editor.putString("isLoggedIn", authorizationResponse.getAccessToken());
            startActivity(new Intent(MainActivity.this, HomeActivity.class));

            Retrofit spotifyRetrofit = SpotifyRetrofitBuilder.getInstance();
            ISpotifyAPI iSpotifyAPI = spotifyRetrofit.create(ISpotifyAPI.class);

            Call<SpotifyPagingObject> spotifyPagingObjectCall = iSpotifyAPI.getTopTracks("Bearer " +authorizationResponse.getAccessToken(), 50, 0);

            spotifyPagingObjectCall.enqueue(new Callback<SpotifyPagingObject>() {
                @Override
                public void onResponse(Call<SpotifyPagingObject> call, Response<SpotifyPagingObject> response) {

                    if(response.isSuccessful() && response.code()==200){
                        Log.d("SPOTIFYGETTOPTRACKS", "onResponse: " +response.body().getItems().toString());

                        Retrofit backendRetrofit = BackendRetrofitBuilder.getInstance();
                        IBackendAPI iBackendAPI = backendRetrofit.create(IBackendAPI.class);
                        List<SpotifyTrack> spotifyTracks = response.body().getItems();
                        for(SpotifyTrack track : spotifyTracks){
                            Call<Void> backendTopTracksCall = iBackendAPI.sendSongData(track);
                            backendTopTracksCall.enqueue(new Callback<Void>() {
                                @Override
                                public void onResponse(Call<Void> call, Response<Void> response) {
                                    Log.d("BACKENDSENDTOPTRACKS", "onResponse: STATUS = " +response.code());
                                }

                                @Override
                                public void onFailure(Call<Void> call, Throwable t) {
                                    Log.d("BACKENDSENDTOPTRACKS", "onFailure: Backend call failed");
                                }
                            });
                        }
                    }

                    else {
                        Log.d("SPOTIFYGETTOPTRACKS", "onResponse: Encountered error " +response.code() );
                    }

                }

                @Override
                public void onFailure(Call<SpotifyPagingObject> call, Throwable t) {
                    Log.d("SPOTIFYGETTOPTRACKS", "onFailure: Couldn't connect to Spotify Web API");
                }
            });

            // Call<CurrentlyPlayingTrack> spotifyCurrentlyPlayingTrackCall = iSpotifyAPI.getCurrentlyPlayingTrack("Bearer " +authorizationResponse.getAccessToken());
            // SpotifyCurrentlyPlayingTrack.enqueue(new Callback<CurrentlyPlayingTrack>(){
            //     @Override
            //     public void onResponse(Call<CurrentlyPlayingTrack> call, Response<CurrentlyPlayingTrack> response){
            //         if(response.isSuccessful() && response.code()==200){
            //             Log.d("SPOTIFYGETCURRENTLYPLAYINGTRACK", "onResponse: "+response.body().getItem().toString());

            //             SpotifyTrack spotifyTrack = response.body().getItem();
            //             Call<Void> sendCurrentSongDataCall = iBackendAPI.sendCurrentlyPlayingTrack(spotifyTrack);
            //             sendCurrentSongDataCall.enqueue(new Callback<Void>(){
            //                 @Override
            //                 public void onResponse(Call<Void> call, Response<Void> response){
            //                     Log.d("BACKENDSENDCURRENTSONGDATA", "onResponse: STATUS = "+response.code());
            //                 }
            //                 public void onFailure(Call<Void> call, Throwable t){
            //                     Log.d("BACKENDSENDCURRENTSONGDATA", "onFailure: Backend call failed");
            //                 }
            //             })

            //         }
            //     }

            //     @Override
            //     public void onFailure(Call<CurrentlyPlayingTrack> call, Throwable t){
            //         Log.d("SPOTIFYGETCURRENTLYPLAYINGTRACK", "onFailure: Couldn't connect to Spotify Web API");
            //     }
            // })

        }

    }
}