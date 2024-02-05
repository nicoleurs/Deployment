# GetAround Analysis

## Project description
GetAround is the Airbnb for cars. You can rent cars from any person for a few hours to a few days.

When using Getaround, drivers book cars for a specific time period, from an hour to a few days long. They are supposed to bring back the car on time, but it happens from time to time that drivers are late for the checkout.

Late returns at checkout can generate high friction for the next driver if the car was supposed to be rented again on the same day : Customer service often reports users unsatisfied because they had to wait for the car to come back from the previous rental or users that even had to cancel their rental because the car wasn’t returned on time.

## Project context
In order to mitigate those issues a minimum delay between two rentals coould be implemented. A car won’t be displayed in the search results if the requested checkin or checkout times are too close from an already booked rental.

It solves the late checkout issue but also potentially hurts Getaround/owners revenues: we need to find the right trade off.

The Product Manager needs to decide:

- Threshold: How long should the minimum delay be?
- Scope: Should the feature be enabled for all types of checkout : mobile, connect or paper ? (although paper is negligible)

## Objectives

Two main elements will compose this project:

(i) A dashboard allowing for comparisons bewteen different thresholds and scopes will allow the product manager to choose the best course of action.

(ii) An API with two endpoints (single and batch) allowing for the prediction of the ideal rental price per day for vehicle given its features.


## Scope
This project focuses on a getaround dataset available [here](https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/get_around_delay_analysis.xlsx) 

## Features

### Dashboard
This dashboard was made using streamlit so it can be run locally using the following command: 

```streamlit run --server.port 4000 app.py```
Given that the required packages are installed


### API_predictions
This feature is build so as to be deployed in a docker container inside a Heroku server, although it can also be run locally. 

#### Run locally
To run this locally I would still recomend building a docker container by going going into the directory and runing 

```docker build . -t <image_name>```

and then

```docker run -it -v "$(pwd):/home/app" -p 4000:4000 -e PORT=4000 <image_name>```

**Then make sure that you open your browser and type into the browser search bar ```0.0.0.0:4000/docs``` to access the endpoints and see de documentaion**

#### Run on server
This depends on the server you choose to run the app in, but for heroku:

- Place yourself in the API_predictions folder
  
- Create a new heroku applicationcurl -i -H "Content-Type: application/json" -X POST -d '{"model_key": "Citroën", "mileage": 140411, "engine_power": 100, "fuel": "diesel", "paint_color": "black", "car_type": "convertible", "private_parking_available": true, "has_gps": true, "has_air_conditioning": true, "automatic_car": true, "has_getaround_connect": true, "has_speed_regulator": true, "winter_tires": true }' 0.0.0.0:4000/predict

  
```heroku create -a <app name>```

- Push the container into the server
  
``` heroku container:push web -a <app name>```

- Release the container
  
``` heroku container:release web -a <app name>```

If the installation worked you can try out the endpoints on your browser or with curl, for example: 

```curl -i -H "Content-Type: application/json" -X POST -d '{"model_key": "Citroën", "mileage": 140411, "engine_power": 100, "fuel": "diesel", "paint_color": "black", "car_type": "convertible", "private_parking_available": true, "has_gps": true, "has_air_conditioning": true, "automatic_car": true, "has_getaround_connect": true, "has_speed_regulator": true, "winter_tires": true }' 0.0.0.0:4000/predict```

Should return a prediction ! 

*Note that the ml_model.ipynb contains all the EDA, preprocessing and training for the machine learning model used in the API. The preprocessing and the model are then saved to the model.pkl file which is then copied and used in the application*

## Contributors

This project was made by Nicolas Leurs as part of the Jedha Bootcamp Data science and engineering Fullstack course and was submitted to validate part of the French certificate "Machine Learning Engineer".

