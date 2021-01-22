package com.example.activityplay.model;

import java.util.List;

public class SpotifyPagingObject {
    String href;
    List<SpotifyTrack> items;

    public String getHref() {
        return href;
    }

    public void setHref(String href) {
        this.href = href;
    }

    public List<SpotifyTrack> getItems() {
        return items;
    }

    public void setItems(List<SpotifyTrack> items) {
        this.items = items;
    }
}
