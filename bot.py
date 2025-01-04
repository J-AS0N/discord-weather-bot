import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
import json

# Load environment variable from .env file
load_dotenv()

# Access the environment variables
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# defines the prefix for the bot's command
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    # Allows the bot to greet in the discord channel
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    await channel.send("Hi, Weather bot is ready!")

    #while True:
        #response = input("Hi, want to know the weather? (Y/N): ")
        #if response == 'y' or response == 'Y':
            #print("Great!")
            #break
        #elif response == 'n' or response == 'N':
            #print(".")
            #break
        #else:
            #print('Invalid input. Please try again.')


# !hello command
@bot.command()
async def hello(ctx):
    await ctx.send("Hello, I'm the weather bot")

'''
- If the user has a set location (e.g., London):
    When they type !weather, the bot should automatically fetch and display the weather for London (their saved city).
- If the user doesn't have a set location:
    When they type !weather without specifying a city, the bot should send an alert asking them to set their location first (using !setlocation <city>).
- If the user provides a city directly (e.g., !weather Paris):
    Regardless of whether they have a saved location or not, the bot should fetch and display the weather for the city they typed in (Paris, in this case).
'''
# !weather <city> command - !weather if you have a set location     !weather <city> if you want to check city that's not set 
@bot.command()
async def weather(ctx, *, city: str): # takes in a argument 'city' && ( * ) allows it to take the whole input (including spaces)
    user_preference = load_preference()
    if ctx.author.id in user_preference:
        city = user_preference[ctx.author.id]   # set the city to 

    else:
        await ctx.send("You can set your city with !setlocation <city>")


    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"

    # make request to the OpenWeatherMap API
    try:
        response = requests.get(url)

        if response.status_code == 200:     # if successful
            data = response.json()
            
            # retrieve data from API
            city_name = data["name"]
            weather = data["weather"][0]["main"]
            temperature = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]

            # Weather summary sent by the weather bot
            await ctx.send(f"The weather in {city_name} is {weather} with a temperature of {temperature}°C. \n Humidity: {humidity} \n Wind Speed: {wind} m/s")

        else:
            await ctx.send(f"Error:  ***{city}*** not found. Please try again.")
            print("Error:", response.status_code, "City not found. Please check the city name")
            return None
        
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

    # Weather summary sent by the weather bot
    #await ctx.send(f"The weather in {city_name} is {weather} with a temperature of {temperature}°C. \n Humidity: {humidity} \n Wind Speed: {wind} m/s")

    
#forecast command (16-day forecast) - Needed to upgrade plan :(
@bot.command()
async def forecast(ctx, *, city: str):
    geoLocation = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}"
    print(f"fetching geoLocation for {city}")

    try:
        location_response = requests.get(geoLocation)
        print(f"Location Response Code: {location_response.status_code}")

        if location_response.status_code == 200:
            data = location_response.json()

            #retrieve longitude / latitude
            lon = data["coord"]["lon"]
            lat = data["coord"]["lat"]
            
        else:
            await ctx.send("Error: Could not find Longitude and Latitude.")
    except requests.exceptions.RequestException as e:
        print("Error: ", e)
        return None

    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast/daily?lat={lat}&lon={lon}&cnt={16}&appid={WEATHER_API_KEY}"

    try:
        forecast_response = requests.get(forecast_url)

        if forecast_response.status_code == 200:
            forecast_data = forecast_response.json()
            forecast_list = forecast_data['list']   # list of data for the 16 day weather forecast

            # Information for each 
            for day in forecast_list:
                timestamp = day["dt"]
                min_temp = day["temp"]["min"]
                max_temp = day["temp"]["max"]
                weather_description = day["weather"][0]["description"]

                # Convert "dt" to a readable date
                date = datetime.datetime.utcfromtimestamp(timestamp)
                formatted_date = date.strftime('%B %-d, %Y')
                #formatted_date = formatted_date.replace(' 0', ' ')  # replaces ' 0' with ' ' (removes the 0)

                # Convert Kelvin to Celsius
                min_temp_cel = min_temp - 273.15
                max_temp_cel = max_temp - 273.15

                forecast_message = f"{formatted_date}: {weather_description} \n Min Temperature: {min_temp_cel} \n Max Temperature: {max_temp_cel}"
            
            await ctx.send(forecast_message)

    except requests.exceptions.RequestException as e:
        print("Error: ", e)
        return None


def load_preference():
    try:
        with open("user_preference.json", "r") as f:    # open and read the file
            return json.load(f)
    except FileNotFoundError:
        return {}


# modifies/updates and saves the JSON file
def save_preference(preferences):
    with open("user_preference.json", "w") as f:
        json.dump(preferences, f, indent=4)     # converts Python dictionary into JSON format



# !setlocation <city>   -   allows users to set a default city / location
@bot.command()
async def setlocation(ctx, *, city: str):
    user_id = str(ctx.author.id)    # grabs the User ID
    preferences = load_preference()
    preferences[user_id] = city     # set the user_id to their city in the dictionary
    save_preference(preferences)

    await ctx.send(f"You've successfully set your default city to {city}")








# Run the bot
bot.run(DISCORD_BOT_TOKEN)