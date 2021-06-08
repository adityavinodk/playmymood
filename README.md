# Personalized Hybrid Music Recommendation Engine based on Body Monitoring Parameters

## About this Project

We have built a personalized hybrid music recommendation engine that recommends songs not just based on the listening history of the user but also the current body monitoring parameters of the user such as the heart rate. We believe that the user's activity should be modelled while catering to the recommendations and we are using the heart rate as a indication of the intensity of the current activity of the user.

We build a heirarchical nested clustering model per user where each datapoint is based on three parameters - (timestamp, heart rate, song metadata vector). We strongly believe that modelling these 3 characteristics can help identify patterns in the daily music listening patterns of the users.

## Project Setup

The project requires a working Android device, Spotify Premium Account and a Fitbit Versa smartwatch.

1. Build the android app present in the `android/` folder and install it onto your android device
2. Build the fitbit app and download it onto your android phone through the companion app
3. Switch to our app's clockface on the Fitbit app. Start playing the Spotify songs on the background
4. Download the server files locally and start mongoDB. Setup developer access in Spotify and download the developer credentials into `dbutils/secrets.py`. A template for the same is given under `dbutils/sample_secrets.py`
5. Run `python app.py` once mongoDB starts and the secrets file has been added.
6. Start our Android app and press play to start recieving recommendations. Enjoy!
