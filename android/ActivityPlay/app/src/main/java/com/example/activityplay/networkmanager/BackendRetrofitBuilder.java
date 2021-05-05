package com.example.activityplay.networkmanager;

import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public class BackendRetrofitBuilder {
    private static Retrofit instance;

    private BackendRetrofitBuilder() {
        // private constructor
    }

    public static Retrofit getInstance() {
        if (instance == null) {
            synchronized (com.example.activityplay.networkmanager.SpotifyRetrofitBuilder.class) {
                if (instance == null) {
                    instance = new Retrofit.Builder().baseUrl("https://playmymood.ml/")
                            .addConverterFactory(GsonConverterFactory.create()).client(new OkHttpClient()).build();
                }
            }
        }
        return instance;
    }
}
