"""
            SECTION : 1 = Defining the dataset and the database
"""
import numpy as np
import pandas as pd
import json

df_cities = pd.read_csv('cities.csv')
df_daily = pd.read_csv('daily_data.csv')
df_hourly = pd.read_csv('hourly_data.csv')

#df_cities
cols_to_drop_cities = ['rank']
# df_daily
cols_to_drop_daily = [
    'temperature_2m_max', 'temperature_2m_min',
    'apparent_temperature_max', 'apparent_temperature_min', 'apparent_temperature_mean',
    'sunshine_duration', 'wind_direction_10m_dominant',
    'shortwave_radiation_sum', 'et0_fao_evapotranspiration'
]
# df_hourly
cols_to_drop_hourly = [
    'relative_humidity_2m', 'dew_point_2m', 'snow_depth',
    'pressure_msl', 'surface_pressure',
    'et0_fao_evapotranspiration', 'vapour_pressure_deficit',
    'wind_speed_100m', 'wind_direction_10m', 'wind_direction_100m',
    'soil_temperature_0_to_7cm', 'soil_temperature_7_to_28cm',
    'soil_temperature_28_to_100cm', 'soil_temperature_100_to_255cm',
    'soil_moisture_0_to_7cm', 'soil_moisture_7_to_28cm',
    'soil_moisture_28_to_100cm', 'soil_moisture_100_to_255cm',
    'shortwave_radiation', 'direct_radiation', 'diffuse_radiation',
    'direct_normal_irradiance', 'global_tilted_irradiance',
    'terrestrial_radiation', 'shortwave_radiation_instant',
    'direct_radiation_instant', 'diffuse_radiation_instant',
    'direct_normal_irradiance_instant', 'global_tilted_irradiance_instant',
    'terrestrial_radiation_instant'
]
df_cities.drop(columns=cols_to_drop_cities,inplace=True)
df_daily.drop(columns=cols_to_drop_daily,inplace=True)
df_hourly.drop(columns=cols_to_drop_hourly,inplace=True)
#print(df_cities.columns)
#print(df_daily.columns)
#print(df_hourly.columns)


target_city_names = [
    'Bangalore', 
    'Mumbai',
    'Delhi',
    'Chennai',
    'Pune',
    'Jaipur',
    'Kolkāta',   
    'Lucknow',        
    'Āgra',      
    'Vārānasi',
    'Ahmedabad',    
    'Amritsar',
    'Indore',
    'Vishākhapatnam',
    'Hyderābād'  
]


df_selected_cities = df_cities[df_cities['city_name'].isin(target_city_names)].copy()
#print(df_selected_cities)
df_daily_filtered = df_daily[df_daily['city_name'].isin(target_city_names)].copy()
# print(df_daily_filtered)
df_hourly_filtered = df_hourly[df_hourly['city_name'].isin(target_city_names)].copy()

"""
             df_daily for historical weather data
"""

df_daily_filtered['datetime'] = pd.to_datetime(df_daily_filtered['datetime'],errors='coerce')
df_daily_filtered.dropna(subset=['datetime'],inplace=True)

df_daily_filtered['month_num'] = df_daily_filtered['datetime'].dt.month
df_daily_filtered['month_name'] = df_daily_filtered['datetime'].dt.month_name() 
df_daily_filtered['is_rainy'] = (df_daily_filtered['rain_sum'].fillna(0) > 0.5).astype(int) # threshold > 0.5mm
df_daily_filtered['is_snowy'] = (df_daily_filtered['snowfall_sum'].fillna(0) > 0).astype(int)
df_daily_filtered['is_foggy'] = df_daily_filtered['weather_code'].fillna(-1).between(40, 49, inclusive='both').astype(int)

monthly_weather_stats = df_daily_filtered.groupby(['city_name', 'month_num', 'month_name']).agg(
    rain_prob=('is_rainy', 'mean'),
    snow_prob=('is_snowy', 'mean'),
    fog_prob=('is_foggy', 'mean'),
    avg_temp=('temperature_2m_mean', 'mean'), 
    avg_daylight_hours=('daylight_duration', lambda x: x.mean() / 3600), 
    avg_wind_speed=('wind_speed_10m_max', 'mean') 
).reset_index()

# print(monthly_weather_stats)

historical_weather_data = {}

month_order = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]

for city in target_city_names:
    if city in monthly_weather_stats['city_name'].unique():
        historical_weather_data[city] = {}
        city_stats = monthly_weather_stats[monthly_weather_stats['city_name']==city].set_index('month_name')
        city_stats = city_stats.reindex(month_order)

        for month in month_order:
            if month in city_stats.index and pd.notna(city_stats.loc[month, 'rain_prob']):
                row =  city_stats.loc[month]

                weather_dict = {
                    'rain_prob': round(row['rain_prob'], 3),
                    'fog_prob': round(row['fog_prob'], 3) if pd.notna(row['fog_prob']) else 0.0,
                    'avg_temp': round(row['avg_temp'], 1) if pd.notna(row['avg_temp']) else None,
                    'avg_daylight_hours': round(row['avg_daylight_hours'], 1) if pd.notna(row['avg_daylight_hours']) else None,
                    'avg_wind_speed': round(row['avg_wind_speed'], 1) if pd.notna(row['avg_wind_speed']) else None
                }

                if pd.notna(row['snow_prob']) and row['snow_prob']>0:
                    weather_dict['snow_prob'] = round(row['snow_prob'],3)
                
                historical_weather_data[city][month] = weather_dict
            else:
                print("Adding historical_weather_data[city][month] as an empty set")
                historical_weather_data[city][month] = {}


""" print("\n--- Calculated Historical Monthly Weather Averages ---")
sample_city = target_city_names[0] 
if sample_city in historical_weather_data:
     print(f"Weather Averages for {sample_city}:")
     print(json.dumps(historical_weather_data[sample_city], indent=2))
else:
     print(f"No weather data calculated for {sample_city}")

print("\nVariable 'historical_weather_data' created successfully.") """

"""
                df_hourly for historical hourly patterns

"""

try :
    df_hourly_filtered['datetime'] = pd.to_datetime(df_hourly_filtered['datetime'],errors='coerce')
    df_hourly_filtered.dropna(subset=['datetime'],inplace=True)
    df_hourly_filtered['month_name'] = df_hourly_filtered['datetime'].dt.month_name()
    df_hourly_filtered['hour'] = df_hourly_filtered['datetime'].dt.hour
except Exception as e:
    print(f"Error processing the datetime of df_hourly and the exception is {e}")

df_hourly_filtered['is_rainy_hour'] = (df_hourly_filtered['rain'].fillna(0)>0.1).astype(int)
df_hourly_filtered['is_snowy_hour'] = (df_hourly_filtered['snowfall'].fillna(0)> 0.1).astype(int)
df_hourly_filtered['is_foggy_hour'] = df_hourly_filtered['weather_code'].fillna(-1).between(40,49,inclusive='both').astype(int)

hourly_weather_stats = df_hourly_filtered.groupby(['city_name', 'month_name', 'hour']).agg(
    hourly_rain_prob=('is_rainy_hour', 'mean'),
    hourly_snow_prob=('is_snowy_hour', 'mean'),
    hourly_fog_prob=('is_foggy_hour', 'mean'),
    avg_hourly_temp=('temperature_2m', 'mean'),
    avg_hourly_wind=('wind_speed_10m', 'mean'),
    avg_cloud_cover=('cloud_cover', 'mean') # Average cloud cover %
).reset_index()

historical_hourly_weather = {}

for city in target_city_names:
    if city in hourly_weather_stats['city_name'].unique():
        historical_hourly_weather[city] = {}
        for month in month_order:
            historical_hourly_weather[city][month] = {}
            for hour in range(24):
                historical_hourly_weather[city][month][hour] = {}

for _,row in hourly_weather_stats.iterrows():
    city = row['city_name']
    month = row['month_name']
    hour = int(row['hour'])

    if city in historical_hourly_weather and month in historical_hourly_weather.get(city,{}) :
        weather_dict = {
            'rain_prob': round(row['hourly_rain_prob'], 3) if pd.notna(row['hourly_rain_prob']) else 0.0,
            'fog_prob': round(row['hourly_fog_prob'], 3) if pd.notna(row['hourly_fog_prob']) else 0.0,
            'avg_temp': round(row['avg_hourly_temp'], 1) if pd.notna(row['avg_hourly_temp']) else None,
            'avg_wind': round(row['avg_hourly_wind'], 1) if pd.notna(row['avg_hourly_wind']) else None,
            'avg_cloud_cover': round(row['avg_cloud_cover'], 1) if pd.notna(row['avg_cloud_cover']) else None
        }
        # Only add snow prob if it's non-zero
        if pd.notna(row['hourly_snow_prob']) and row['hourly_snow_prob'] > 0:
            weather_dict['snow_prob'] = round(row['hourly_snow_prob'], 3)
            
        historical_hourly_weather[city][month][hour] = weather_dict

""" print("\n--- Calculated Historical Hourly Weather Averages (Sample) ---")
sample_city = target_city_names[0] # e.g., Bangalore
sample_month = "July" # A month with likely varied weather
if sample_city in historical_hourly_weather and sample_month in historical_hourly_weather[sample_city]:
     import json
     print(f"Hourly Weather Averages for {sample_city}, {sample_month}:")
     # Print a sample (e.g., every 4 hours) to avoid flooding the console
     sampled_hours = {hour: data for hour, data in historical_hourly_weather[sample_city][sample_month].items()}
     print(json.dumps(sampled_hours, indent=2))
else:
     print(f"No hourly data calculated for {sample_city}, {sample_month}")

print("\nVariable 'historical_hourly_weather' created successfully.") """

"""
        intializing the db
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict

@dataclass
class Place:
    name: str
    category: str
    coordinates : Tuple[float, float]
    visit_duration_hours : float
    cost : int
    suitable_for: List[str] = field(default_factory=list)

    # dataclasses are by default mutable hence unhashable, set() requires the object to be hashable and hence
    def __hash__(self):
        return hash((self.name, self.coordinates))

def _initialize_poi_database(target_cities: List[str]) -> Dict[str, List[Place]]:
    print("Initializing POI database")
    all_city_pois = {}

    all_city_pois['Bangalore'] = [
        Place("Bangalore Palace", "historical", (13.0035, 77.5891), 3.0, 230,suitable_for=["sunset"]),
        Place("Church Street", "influencer", (12.9750, 77.6043), 3.0, 500, suitable_for=["nightlife"]),
        Place("Cubbon Park", "nature_scenic", (12.9779, 77.5952), 2.5, 0),
        Place("Lalbagh Garden", "nature_scenic", (12.9507, 77.5848), 2.0, 50),
        Place("Innovation Film City", "entertainment", (12.8342, 77.4987), 3.0, 600),
        Place("Wonderla Amusement Park", "entertainment", (12.8346, 77.3998), 3.0, 1100),
        Place("Museum of Art and Photography", "cultural", (12.9745, 77.5969), 2.5, 150),
        Place("Shivoham Shiva Temple","religious", (12.958,77.654), 1.5, 250, suitable_for=["sunrise"]),
        Place("Phoenix Mall of Asia", "influencer", (13.0706, 77.5914), 3.5, 1500),
        Place("Bengaluru Fort", "historical", (12.9628, 77.5759), 2.5, 15,suitable_for=["sunset"])
    ]

    all_city_pois['Mumbai'] = [
        Place("Gateway of India", "historical", (18.9220, 72.8347), 1.0, 0, suitable_for=["sunrise"]),
        Place("Elephanta Caves", "historical", (18.9633, 72.9315), 4.0, 600, suitable_for=["sunset"]), # includes ferry
        Place("Marine Drive", "nature_scenic", (18.9440, 72.8229), 1.5, 0,suitable_for=["sunset", "nightlife"]),
        Place("Siddhivinayak Temple", "religious", (19.0168, 72.8300), 1.5, 0),
        Place("CSM Vastu Sangrahalaya", "cultural", (18.9269, 72.8344), 3.0, 500),
        Place("Haji Ali Dargah", "religious", (18.9826, 72.8093), 1.0, 0),
        Place("EsselWorld", "entertainment", (19.2306, 72.8047), 6.0, 1500),
        Place("Juhu Beach", "nature_scenic", (19.1073, 72.8263), 1.5, 100,suitable_for=["sunrise","sunset"]),
        Place("Colaba Causeway", "influencer", (18.9204, 72.8300), 2.0, 200),
        Place("Phoenix Palladium", "influencer", (18.9940, 72.8244), 3.0, 750)
    ]

    all_city_pois['Delhi'] = [
        Place("Red Fort", "historical", (28.6562, 77.2410), 3.0, 500),
        Place("Qutub Minar", "historical", (28.5245, 77.1855), 2.0, 600),
        Place("Humayun's Tomb", "historical", (28.5933, 77.2507), 2.5, 550),
        Place("Lotus Temple", "religious", (28.5535, 77.2588), 1.5, 0,suitable_for=["sunset"]),
        Place("Akshardham Temple", "religious", (28.6127, 77.2773), 2.0, 0, suitable_for=["sunrise"]),
        Place("National Museum", "cultural", (28.6119, 77.2193), 3.0, 250),
        Place("National Rail Museum", "entertainment", (28.5854, 77.1800), 3.0, 100),
        Place("Garden of Five Senses", "nature_scenic", (28.5135, 77.1979), 2.0, 50),
        Place("Dilli Haat", "influencer", (28.5733, 77.2075), 2.5, 100, suitable_for=["nightlife"]),
        Place("Connaught Place", "influencer", (28.6304, 77.2177), 3.0, 300,suitable_for=["nightlife"]) 
    ]

    all_city_pois['Chennai'] = [
        Place("Fort St. George", "historical", (13.0827, 80.2870), 2.5, 50),
        Place("Government Museum", "cultural", (13.0723, 80.2606), 2.0, 100),
        Place("Kapaleeshwarar Temple", "religious", (13.0338, 80.2699), 1.5, 0, suitable_for=["sunrise"]),
        Place("VGP Universal Kingdom", "entertainment", (12.9175, 80.2470), 4.0, 650),
        Place("Marina Beach", "nature_scenic", (13.0500, 80.2824), 2.0, 0, suitable_for=["sunset","nightlife"]),
        Place("Phoenix MarketCity", "influencer", (12.9921, 80.2167), 3.0, 1000, suitable_for=["nightlife"]),
        Place("Santhome Cathedral Basilica", "religious", (13.0335, 80.2792), 1.0, 0),
        Place("Birla Planetarium", "entertainment", (13.0103, 80.2321), 1.5, 150),
        Place("Elliot’s Beach", "nature_scenic", (13.0008, 80.2664), 2.0, 0, suitable_for=["sunset","sunrise"]),
        Place("Express Avenue Mall", "influencer", (13.0601, 80.2652), 2.5, 800, suitable_for=["nightlife"])
    ]

    all_city_pois['Pune'] = [
        Place("Shaniwar Wada", "historical", (18.5195, 73.8553), 2.0, 50),
        Place("Raja Dinkar Kelkar Museum", "cultural", (18.5099, 73.8567), 2.0, 100),
        Place("Dagadusheth Halwai Ganapati Temple", "religious", (18.5189, 73.8554), 1.0, 0, suitable_for=["sunrise"]),
        Place("Aga Khan Palace", "historical", (18.5523, 73.9034), 2.0, 100, suitable_for=["sunset"]),
        Place("Phoenix Marketcity Pune", "influencer", (18.5626, 73.9191), 3.0, 900, suitable_for=["nightlife"]),
        Place("Pataleshwar Cave Temple", "religious", (18.5309, 73.8474), 1.0, 0),
        Place("Osho Garden", "nature_scenic", (18.5360, 73.8937), 1.5, 0, suitable_for=["sunset"]),
        Place("Appu Ghar", "entertainment", (18.6496, 73.7783), 3.5, 500),
        Place("Khadakwasla Dam", "nature_scenic", (18.4456, 73.7630), 2.0, 0),
        Place("FC Road", "influencer", (18.5204, 73.8521), 2.5, 200, suitable_for=["nightlife"])
    ]

    all_city_pois['Jaipur'] = [
        Place("Amber Fort", "historical", (26.9855, 75.8513), 3.0, 200),
        Place("City Palace", "cultural", (26.9258, 75.8237), 2.5, 150),
        Place("Hawa Mahal", "historical", (26.9239, 75.8267), 1.5, 100),
        Place("Birla Mandir", "religious", (26.8943, 75.8135), 1.0, 0),
        Place("Jantar Mantar", "cultural", (26.9258, 75.8246), 1.5, 100),
        Place("Nahargarh Fort", "historical", (26.9375, 75.8124), 2.0, 100),
        Place("Chokhi Dhani", "entertainment", (26.7717, 75.8189), 3.0, 800),
        Place("Jal Mahal", "nature_scenic", (26.9533, 75.8460), 1.5, 0, suitable_for=["sunset"]),
        Place("Albert Hall Museum", "cultural", (26.9118, 75.8196), 2.0, 150),
        Place("Bapu Bazaar", "influencer", (26.9176, 75.8265), 2.5, 300, suitable_for=["nightlife"])
    ]

    all_city_pois['Kolkāta'] = [
        Place("Victoria Memorial", "historical", (22.5448, 88.3426), 2.5, 30),
        Place("Indian Museum", "cultural", (22.5570, 88.3508), 2.0, 50),
        Place("Dakshineswar Kali Temple", "religious", (22.6548, 88.3570), 1.5, 0),
        Place("Nicco Park", "entertainment", (22.5737, 88.4310), 3.5, 700),
        Place("Eco Park", "nature_scenic", (22.6198, 88.4496), 3.0, 200),
        Place("Park Street", "influencer", (22.5535, 88.3501), 2.5, 500, suitable_for=["nightlife"]),
        Place("Howrah Bridge", "historical", (22.5850, 88.3468), 1.0, 0, suitable_for=["sunset"]),
        Place("Birla Planetarium", "cultural", (22.5455, 88.3476), 1.5, 100),
        Place("Science City", "entertainment", (22.5390, 88.4033), 3.0, 200),
        Place("Botanical Garden", "nature_scenic", (22.5392, 88.3090), 2.0, 100)
    ]

    all_city_pois['Lucknow'] = [
        Place("Bara Imambara", "historical", (26.8703, 80.9126), 2.5, 50),
        Place("State Museum Lucknow", "cultural", (26.8500, 80.9466), 2.0, 50),
        Place("Chota Imambara", "religious", (26.8712, 80.9107), 1.5, 30),
        Place("Ambedkar Memorial Park", "nature_scenic", (26.8468, 80.9783), 2.0, 50),
        Place("Janeshwar Mishra Park", "nature_scenic", (26.8453, 80.9872), 2.0, 0),
        Place("Wave Mall", "influencer", (26.8643, 80.9962), 2.5, 800, suitable_for=["nightlife"]),
        Place("Hazratganj Market", "influencer", (26.8527, 80.9463), 2.0, 300, suitable_for=["nightlife"]),
        Place("Anandi Water Park", "entertainment", (26.9583, 81.0370), 3.5, 650),
        Place("British Residency", "historical", (26.8590, 80.9407), 2.0, 30),
        Place("La Martiniere College", "cultural", (26.8368, 80.9469), 1.5, 0)
    ]

    all_city_pois['Āgra'] = [
        Place("Taj Mahal", "historical", (27.1751, 78.0421), 3.0, 250, suitable_for=["sunrise","sunset"]),
        Place("Agra Fort", "historical", (27.1795, 78.0211), 2.5, 50),
        Place("Itmad-ud-Daulah's Tomb", "cultural", (27.1950, 78.0380), 1.5, 30),
        Place("Mehtab Bagh", "nature_scenic", (27.1829, 78.0419), 2.0, 30, suitable_for=["sunset"]),
        Place("Sikandra Fort", "historical", (27.2277, 77.9614), 2.0, 20),
        Place("Guru ka Tal", "religious", (27.2166, 77.9681), 1.5, 0),
        Place("Mankameshwar Temple", "religious", (27.1822, 78.0149), 1.0, 0),
        Place("Agra Planetarium", "entertainment", (27.1711, 78.0419), 2.0, 150),
        Place("TDI Mall", "influencer", (27.1574, 77.9941), 2.0, 600, suitable_for=["nightlife"]),
        Place("Taj Nature Walk", "nature_scenic", (27.1667, 78.0516), 1.5, 50)
    ]

    all_city_pois['Vārānasi'] = [
        Place("Kashi Vishwanath Temple", "religious", (25.3109, 83.0104), 1.5, 0, suitable_for=["sunrise"]),
        Place("Dashashwamedh Ghat", "cultural", (25.3069, 83.0105), 2.0, 0, suitable_for=["sunset"]),
        Place("Assi Ghat", "nature_scenic", (25.2843, 83.0063), 1.5, 0, suitable_for=["sunset"]),
        Place("Ramnagar Fort", "historical", (25.2828, 83.0317), 2.0, 30),
        Place("Sarnath Archaeological Site", "historical", (25.3769, 83.0220), 2.5, 50),
        Place("Bharat Kala Bhavan Museum", "cultural", (25.2685, 82.9864), 2.0, 50),
        Place("Banaras Hindu University", "influencer", (25.2677, 82.9913), 2.0, 0),
        Place("IP Sigra Mall", "influencer", (25.3092, 82.9978), 2.5, 500, suitable_for=["nightlife"]),
        Place("Aarohi Water Park", "entertainment", (25.4215, 82.9990), 3.0, 700),
        Place("Rajdari and Devdari Waterfalls", "nature_scenic", (25.0839, 83.0697), 4.0, 0)
    ]

    all_city_pois['Ahmedabad'] = [
        Place("Sabarmati Ashram", "historical", (23.0600, 72.5800), 2.0, 0),
        Place("Adalaj Stepwell", "historical", (23.1704, 72.5802), 1.5, 25),
        Place("Kankaria Lake", "nature_scenic", (22.9928, 72.6036), 2.5, 50),
        Place("Jama Masjid", "religious", (23.0225, 72.5891), 1.0, 0),
        Place("ISKCON Temple Ahmedabad", "religious", (23.0346, 72.5155), 1.0, 0, suitable_for=["sunrise"]),
        Place("Law Garden Night Market", "influencer", (23.0205, 72.5571), 2.0, 300, suitable_for=["nightlife"]),
        Place("Alpha One Mall", "influencer", (23.0419, 72.5308), 2.5, 800, suitable_for=["nightlife"]),
        Place("Calico Museum of Textiles", "cultural", (23.0465, 72.5803), 2.0, 100),
        Place("Science City Ahmedabad", "entertainment", (23.0908, 72.5075), 3.5, 400),
        Place("Manek Chowk", "cultural", (23.0224, 72.5871), 2.0, 200, suitable_for=["nightlife"])
    ]

    all_city_pois['Amritsar'] = [
        Place("Golden Temple", "religious", (31.6200, 74.8765), 2.0, 0, suitable_for=["sunrise"]),
        Place("Jallianwala Bagh", "historical", (31.6205, 74.8800), 1.5, 0),
        Place("Partition Museum", "cultural", (31.6235, 74.8768), 2.0, 50),
        Place("Wagah Border", "influencer", (31.6040, 74.5730), 3.0, 0, suitable_for=["sunset"]),
        Place("Gobindgarh Fort", "historical", (31.6312, 74.8647), 2.5, 100),
        Place("Maharaja Ranjit Singh Museum", "cultural", (31.6398, 74.8722), 1.5, 50),
        Place("Durgiana Temple", "religious", (31.6300, 74.8727), 1.0, 0),
        Place("Sun City Water Park", "entertainment", (31.6856, 74.8377), 3.0, 650),
        Place("Company Bagh", "nature_scenic", (31.6411, 74.8719), 2.0, 0, suitable_for=["sunset"]),
        Place("Trilium Mall", "influencer", (31.6637, 74.8945), 2.5, 800, suitable_for=["nightlife"])
    ]

    all_city_pois['Indore'] = [
        Place("Rajwada Palace", "historical", (22.7170, 75.8555), 2.0, 30),
        Place("Lal Bagh Palace", "historical", (22.6958, 75.8573), 2.0, 50),
        Place("Central Museum Indore", "cultural", (22.7148, 75.8688), 1.5, 20),
        Place("Bada Ganpati Temple", "religious", (22.7228, 75.8556), 1.0, 0, suitable_for=["sunrise"]),
        Place("Khajrana Ganesh Temple", "religious", (22.7179, 75.8838), 1.0, 0),
        Place("Chappan Dukan", "influencer", (22.7285, 75.8850), 2.0, 300, suitable_for=["nightlife"]),
        Place("Treasure Island Mall", "influencer", (22.7190, 75.8790), 2.5, 800, suitable_for=["nightlife"]),
        Place("Ralamandal Wildlife Sanctuary", "nature_scenic", (22.6435, 75.9133), 3.0, 50, suitable_for=["sunset"]),
        Place("Crescent Water Park", "entertainment", (22.7692, 75.9906), 3.5, 700),
        Place("Patalpani Waterfall", "nature_scenic", (22.5537, 75.7674), 3.0, 0, suitable_for=["sunset"])
    ]

    all_city_pois['Vishākhapatnam'] = [
        Place("Kailasagiri Hill Park", "nature_scenic", (17.7496, 83.3420), 2.5, 50, suitable_for=["sunset"]),
        Place("Ramakrishna Beach", "nature_scenic", (17.7190, 83.3160), 2.0, 0, suitable_for=["sunrise","sunset"]),
        Place("INS Kurusura Submarine Museum", "historical", (17.7194, 83.3420), 2.0, 50),
        Place("Borra Caves", "historical", (18.2831, 83.0398), 3.5, 100),
        Place("Simhachalam Temple", "religious", (17.7635, 83.2671), 1.5, 0, suitable_for=["sunrise"]),
        Place("VUDA Park", "entertainment", (17.7199, 83.3313), 2.0, 50),
        Place("Indira Gandhi Zoological Park", "entertainment", (17.7712, 83.3436), 3.0, 100),
        Place("Teneti Park", "nature_scenic", (17.7499, 83.3450), 1.5, 0, suitable_for=["sunset"]),
        Place("CMR Central Mall", "influencer", (17.7260, 83.3045), 2.5, 700, suitable_for=["nightlife"]),
        Place("RK Beach Road", "influencer", (17.7175, 83.3337), 2.0, 0, suitable_for=["sunset","nightlife"])
    ]

    all_city_pois['Hyderābād'] = [
        Place("Charminar", "historical", (17.3616, 78.4747), 1.5, 50),
        Place("Golconda Fort", "historical", (17.3833, 78.4011), 2.5, 100),
        Place("Salar Jung Museum", "cultural", (17.3713, 78.4804), 2.5, 50),
        Place("Birla Mandir", "religious", (17.4062, 78.4691), 1.5, 0, suitable_for=["sunrise"]),
        Place("Chilkur Balaji Temple", "religious", (17.3304, 78.3150), 1.5, 0),
        Place("Hussain Sagar Lake", "nature_scenic", (17.4239, 78.4738), 2.0, 0, suitable_for=["sunset"]),
        Place("Nehru Zoological Park", "entertainment", (17.3520, 78.4497), 3.0, 80),
        Place("Ramoji Film City", "entertainment", (17.2558, 78.6808), 5.0, 1250),
        Place("Shilparamam", "cultural", (17.4505, 78.3882), 2.0, 60),
        Place("Inorbit Mall", "influencer", (17.4366, 78.3827), 2.5, 900, suitable_for=["nightlife"]),
        Place("Necklace Road", "influencer", (17.4251, 78.4721), 2.0, 200, suitable_for=["sunset","nightlife"])
    ]


    for city in target_cities:
        if city not in all_city_pois:
            print(f"adding empty poi list for {city}. Need to add real data!")
            all_city_pois[city] = []

    return all_city_pois

all_city_pois = _initialize_poi_database(target_city_names)
""" print(f"Loaded POI data for {len(all_city_pois)} cities.")
sample_city = "Delhi"
if sample_city in all_city_pois and all_city_pois[sample_city]:
    print(f"Sample POI for {sample_city}: {all_city_pois[sample_city][0]}")
    print(f"Total POIs for {sample_city}: {len(all_city_pois[sample_city])}")  """


CITY_AVG_SPEEDS_KMH = {
    'Bangalore': 20,  
    'Mumbai': 22,    
    'Delhi': 28,     
    'Chennai': 25,
    'Pune': 24,
    'Jaipur': 30,     
    'Kolkāta': 23,
    'Lucknow': 28,
    'Āgra': 27,
    'Vārānasi': 25,   
    'Ahmedabad': 29,
    'Amritsar': 28,
    'Indore': 30,
    'Vishākhapatnam': 27,
    'Hyderābād': 26
}

CITY_CONGESTION_FACTORS = {
    'Bangalore': 1.9,
    'Mumbai': 1.7,
    'Delhi': 1.6,
    'Chennai': 1.8,
    'Pune': 1.5,
    'Jaipur': 1.2,
    'Kolkāta': 1.5,
    'Lucknow': 1.4,
    'Āgra': 1.3,
    'Vārānasi': 1.4,   
    'Ahmedabad': 1.5,
    'Amritsar': 1.2,
    'Indore': 1.2,
    'Vishākhapatnam': 1.4,
    'Hyderābād': 1.5
}

# heuristic: 1.0 = normal, >1.0 = busy, <1.0 = offseason
SEASONAL_TOURISM_FACTORS = {
    "Bangalore": {
        "January": 1.1, "February": 1.1, "March": 1.0, 
        "April": 1.2, "May": 1.2, "June": 1.0,
        "July": 1.0, "August": 1.0, "September": 1.2,
        "October": 1.3, "November": 1.2, "December": 1.3
    },
    "Mumbai": {
        "January": 1.3, "February": 1.2, "March": 1.1,
        "April": 1.1, "May": 1.4, "June": 0.8, 
        "July": 0.8, "August": 0.9, "September": 1.1,
        "October": 1.3, "November": 1.4, "December": 1.5
    },
    "Delhi": {
        "January": 1.4, "February": 1.3, "March": 1.2,
        "April": 1.0, "May": 0.8, "June": 0.7, 
        "July": 0.9, "August": 0.9, "September": 1.0,
        "October": 1.4, "November": 1.5, "December": 1.6
    },
    "Chennai": {
        "January": 1.2, "February": 1.1, "March": 1.0,
        "April": 0.9, "May": 0.8, "June": 0.9, 
        "July": 1.0, "August": 1.1, "September": 1.2,
        "October": 1.3, "November": 1.4, "December": 1.4
    },
    "Pune": {
        "January": 1.3, "February": 1.2, "March": 1.1,
        "April": 1.0, "May": 0.9, "June": 1.0, 
        "July": 1.1, "August": 1.1, "September": 1.2,
        "October": 1.3, "November": 1.4, "December": 1.5
    },
    "Jaipur": {
        "January": 1.5, "February": 1.4, "March": 1.2,
        "April": 0.9, "May": 0.7, "June": 0.7, 
        "July": 0.8, "August": 0.9, "September": 1.1,
        "October": 1.4, "November": 1.5, "December": 1.6
    },
    "Kolkāta": {
        "January": 1.3, "February": 1.2, "March": 1.1,
        "April": 1.0, "May": 0.9, "June": 0.8, 
        "July": 0.9, "August": 1.0, "September": 1.1,
        "October": 1.5, "November": 1.4, "December": 1.3
    },
    "Lucknow": {
        "January": 1.4, "February": 1.3, "March": 1.1,
        "April": 1.0, "May": 0.8, "June": 0.7, 
        "July": 0.9, "August": 1.0, "September": 1.1,
        "October": 1.3, "November": 1.4, "December": 1.5
    },
    "Āgra": {
        "January": 1.5, "February": 1.4, "March": 1.3,
        "April": 1.0, "May": 0.8, "June": 0.7, 
        "July": 0.9, "August": 1.0, "September": 1.1,
        "October": 1.4, "November": 1.5, "December": 1.6
    },
    "Vārānasi": {
        "January": 1.5, "February": 1.4, "March": 1.2,
        "April": 1.0, "May": 0.8, "June": 0.7, 
        "July": 0.8, "August": 0.9, "September": 1.1,
        "October": 1.3, "November": 1.5, "December": 1.5
    },
    "Ahmedabad": {
        "January": 1.4, "February": 1.3, "March": 1.1,
        "April": 0.9, "May": 0.8, "June": 0.8, 
        "July": 0.9, "August": 1.0, "September": 1.1,
        "October": 1.3, "November": 1.4, "December": 1.5
    },
    "Amritsar": {
        "January": 1.5, "February": 1.4, "March": 1.2,
        "April": 1.0, "May": 0.8, "June": 0.7, 
        "July": 0.9, "August": 0.9, "September": 1.1,
        "October": 1.4, "November": 1.5, "December": 1.6
    },
    "Indore": {
        "January": 1.3, "February": 1.2, "March": 1.1,
        "April": 1.0, "May": 0.9, "June": 0.8, 
        "July": 1.0, "August": 1.1, "September": 1.2,
        "October": 1.3, "November": 1.4, "December": 1.5
    },
    "Vishākhapatnam": {
        "January": 1.3, "February": 1.2, "March": 1.1,
        "April": 1.0, "May": 0.9, "June": 0.9, 
        "July": 1.0, "August": 1.1, "September": 1.2,
        "October": 1.3, "November": 1.4, "December": 1.5
    },
    "Hyderābād": {
        "January": 1.3, "February": 1.2, "March": 1.1,
        "April": 1.0, "May": 0.9, "June": 0.9, 
        "July": 1.0, "August": 1.1, "September": 1.2,
        "October": 1.3, "November": 1.4, "December": 1.5
    },
    "default": {
        "January": 1.2, "February": 1.1, "March": 1.0, "April": 1.3,
        "May": 1.4, "June": 1.1, "July": 1.0, "August": 1.0,
        "September": 1.1, "October": 1.3, "November": 1.3, "December": 1.5
    }
}

"""
            SECTION 2 = defining the traveler profile for personalization
"""


@dataclass
class TravelerProfile:
    pace : str = "relaxed"
    timing : str = "normal"
    wants_nightlife : bool = False
    wants_sunrise : bool = False
    wants_sunset : bool = False

    max_places_per_day : int = 3
    day_start_hour : int = 10
    day_end_hour : int = 20

    def calculate_rules(self):
        if self.pace == 'relaxed':
            self.max_places_per_day = 3
        else: 
            self.max_places_per_day = 4
        
        if self.timing == 'early_bird':
            self.day_start_hour = 8
            self.day_end_hour = 20  
        elif self.timing == 'night_owl':
            self.day_start_hour = 12 
            self.day_end_hour = 23  
        
        if self.wants_nightlife:
            # Extend the day if nightlife is requested
            self.day_end_hour = max(self.day_end_hour, 23)

def _get_validated_input(prompt: str, valid_options : List[str]) -> str:
    while True:
        print(prompt)
        for i, option in enumerate(valid_options, start=1):
            print(f"{i}) {option}")
        choice = input("Your choice: ").strip().lower()

        if choice in [opt.lower() for opt in valid_options]:
            return choice

        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(valid_options):
                return valid_options[idx - 1]
        print("Invalid choice. Please try again.")

def _get_multi_select_input(prompt: str,max_valid_number:int) -> List[int]:
    while True:
        choice = input(f"{prompt} ").strip()

        if not choice:
            return [] 

        try:
            selected_indices = []
            valid_selections = True
            parts = [idx.strip() for idx in choice.split(',')]

            for part in parts:
                if not part.isdigit():
                    raise ValueError(f"'{part}' is not a number")
                idx = int(part)-1

                if 0<=idx<max_valid_number:
                    if idx not in selected_indices:
                        selected_indices.append(idx)
                else:
                    print(f"Invalid number: {part}. Please enter numbers between 1 and {max_valid_number}.")
                    valid_selections = False

            if valid_selections:
                return selected_indices
        except ValueError as e:
            print(f"Invalid input. {e}. Please enter numbers separated by commas (e.g., '1, 3').")


def get_city_selection(city_names: List[str]) -> str:
    print("\n============================================================")
    print("🏖️  Welcome to the Personalized Vacation Trip Planner")
    print("============================================================")
    print("Please select your city destination:")
    
    for i, city in enumerate(city_names, start=1):
        print(f"  ({i}) {city}")

    while True:
        choice = input(f"Your choice (enter a number 1-{len(city_names)}): ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(city_names):
                selected_city = city_names[idx - 1]
                print(f"You have selected : {selected_city}\n")
                return selected_city
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(city_names)}.")
        except ValueError:
            print("Invalid input. Please enter a number only.")

def get_poi_selection(city_name : str) -> List[Place]:
    print("\n" + "="*60)
    print(f"📍 Select Places to Visit in {city_name}")
    print("="*60)

    city_poi_list = all_city_pois.get(city_name, [])
    if not city_poi_list:
        print(f"Sorry, no POI data found for {city_name}.")
        return []

    # group pois by category
    pois_by_category = {
        "historical": [p for p in city_poi_list if p.category == 'historical'],
        "religious": [p for p in city_poi_list if p.category == 'religious'],
        "cultural": [p for p in city_poi_list if p.category == 'cultural'],
        "entertainment": [p for p in city_poi_list if p.category == 'entertainment'],
        "nature_scenic": [p for p in city_poi_list if p.category == 'nature_scenic'],
        "influencer": [p for p in city_poi_list if p.category == 'influencer'],
    }

    selected_places = []

    for category, places in pois_by_category.items():
        if not places:
            continue

        print(f"\n--- Category: {category.title()} ---")
        place_names_with_numbers = [f"({i+1}) {p.name} (Est. {p.visit_duration_hours} hrs, ₹{p.cost})" for i, p in enumerate(places)]
        # place_names_only = [p.name.lower() for p in places]
        
        print(f"Available {category} places:")
        for item in place_names_with_numbers:
            print(item)

        selected_indices = _get_multi_select_input("Enter numbers (e.g., '1, 3') or press Enter to skip:", len(places))

        temp_selection_list = []
        if selected_indices:
            for idx in selected_indices:
                selected_place = places[idx]
                if selected_place not in selected_places:
                    temp_selection_list.append(selected_place)
                else:
                    print(f"You've already selected {selected_place.name}.")
        
        if temp_selection_list:
            selected_places.extend(temp_selection_list)
            print(f"Added: {[p.name for p in temp_selection_list]}")

    print("\n--- Your Final Selected Places ---")
    if not selected_places:
        print("No places selected.")
    else:
        for p in selected_places:
            print(f"- {p.name}")
    return selected_places

def get_traveler_profile() -> TravelerProfile:
    print("\n" + "="*60)
    print("👤 Tell Us About Your Travel Style")
    print("="*60)
    profile = TravelerProfile()

    pace_choice = _get_validated_input(
        "What's your preferred travel pace?",
        ["relaxed", "fast-paced"]
    )
    profile.pace = "fast" if "fast" in pace_choice else "relaxed"

    timing_choice = _get_validated_input(
        "\nWhat kind of a person are you ?",
        ["Early Bird", "Night Owl", "Normal (10AM-10PM)"]
    )
    if "early" in timing_choice.lower():
        profile.timing = "early_bird"
    elif "night" in timing_choice.lower():
        profile.timing = "night_owl"
    else:
        profile.timing = "normal"

    nightlife_choice = _get_validated_input(
        "\nDo you want to include nightlife activities?",
        ["yes", "no"]
    )
    profile.wants_nightlife = True if "yes" in nightlife_choice else False

    sun_choice = _get_validated_input(
        "\nAre you interested in planning for sunrise or sunset views?",
        ["sunrise", "sunset", "both", "none"]
    )
    if "sunrise" in sun_choice: profile.wants_sunrise = True
    if "sunset" in sun_choice: profile.wants_sunset = True
    if "both" in sun_choice:
        profile.wants_sunrise = True
        profile.wants_sunset = True
    
    profile.calculate_rules()

    print(f"\nProfile set! (Pace: {profile.pace}, Timing: {profile.timing}, Max Places/Day: {profile.max_places_per_day})")
    return profile


def get_trip_constraints() -> Tuple[int,int,str]:
    print("\n" + "="*60)
    print("📅 Enter Your Trip Constraints")
    print("="*60)

    budget = 0
    while budget<= 0:
        try:
            budget = int(input("Enter your budget : "))
            if budget <= 0:
                print("Budget must be positive")
        except ValueError:
            print("Please enter a valid number")

    days = 0
    while days<=0:
        try:
            days = int(input("Enter yours days of stay : "))
            if days<=0:
                print("days must be positive")
        except ValueError:
            print("Please enter a valid number")

    month = _get_validated_input(
        "\nWhat month are you travelling ?",
        month_order
    )

    print(f"\nConstraints set: ₹{budget}, {days} days in {month}")
    return budget, days, month

from math import radians, sin, cos, sqrt, atan2

def calculate_haversine_distance(coord1: tuple, coord2: tuple) -> float:
    r = 6371.0  
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = r * c
    return distance

def calculate_travel_time(place_from: Place, place_to: Place, city_name:str, city_data:pd.Series, month_weather:dict, hourly_weather_db:dict, month_name:str,hour_of_the_day:int) -> float:
    # month_weather is historical_weather_data[city][month] 
    # hourly_weater_db is historical_hourly_month[city][month]
    base_distance_kms = calculate_haversine_distance(place_from.coordinates, place_to.coordinates)
    avg_base_speed = CITY_AVG_SPEEDS_KMH.get(city_name,25)
    if avg_base_speed == 0:
        return float('inf')
    
    base_time_hours = base_distance_kms / avg_base_speed

    congestion_factor = CITY_CONGESTION_FACTORS.get(city_name, 1.2)

    seasonal_weather_factor = 1.0
    if month_weather.get('rain_prob', 0) > 0.4:
        seasonal_weather_factor += 0.5 
    if month_weather.get('fog_prob', 0) > 0.3:
        seasonal_weather_factor += 0.3
    if month_weather.get('avg_wind_speed', 0) > 15:
        seasonal_weather_factor += 0.05
    if month_weather.get('snow_prob', 0) > 0:
        seasonal_weather_factor += 0.2

    city_tourism_factors = SEASONAL_TOURISM_FACTORS.get(city_name, SEASONAL_TOURISM_FACTORS["default"])
    seasonal_tourism_factor = city_tourism_factors.get(month_name, 1.0) 

    daily_weather_factor = 1.0
    hour_data = hourly_weather_db.get(hour_of_the_day,{})

    if hour_data.get('rain_prob',0)>0.2:
        daily_weather_factor += 0.4
    if hour_data.get('fog_prob',0)> 0.15:
        daily_weather_factor += 0.2
    if hour_data.get('avg_wind',0) > 15:
        daily_weather_factor+=0.1
    if hour_data.get('snow_prob', 0) > 0:
        daily_weather_factor+=0.2

    final_travel_time = (
        base_time_hours * congestion_factor * seasonal_weather_factor * seasonal_tourism_factor * daily_weather_factor
    )

    return final_travel_time


"""
            SECTION 3 = optimization engine 
"""

def find_cluster_center(cluster: List[Place]) -> Tuple[float, float]:
    if not cluster:
        return (0.0, 0.0) 
        
    avg_lat = sum(p.coordinates[0] for p in cluster) / len(cluster)
    avg_lon = sum(p.coordinates[1] for p in cluster) / len(cluster)
    
    return (avg_lat, avg_lon)

def custome_greedy_clustering_heuristic(selected_places : List[Place], num_days: int) -> List[List[Place]]:
    print(f"Running CGCH for {len(selected_places)} places into {num_days} days")

    if len(selected_places) < num_days:
        print("Fewer places than available days, assigning each place to one day")
        return [[place] for place in selected_places]
    
    unassigned_places = list(selected_places)
    clusters = [[] for _ in range(num_days)]

    first_place = unassigned_places.pop(0)
    clusters[0].append(first_place)

    last_chosen_place = first_place

    for i in range(1,num_days):
        farthest_place = None
        max_distance = -1

        for place in unassigned_places:
            distance = calculate_haversine_distance(place.coordinates, last_chosen_place.coordinates)

            if distance > max_distance:
                max_distance = distance
                farthest_place = place
        
        clusters[i].append(farthest_place)
        unassigned_places.remove(farthest_place)

        last_chosen_place = farthest_place
    
    print("Seeds chosen for each day:")
    for i, cluster in enumerate(clusters):
        print(f"  Day {i+1}: {cluster[0].name}")
    
    for place in unassigned_places:
        cluster_centers = [find_cluster_center(c) for c in clusters]
        distances = []

        for center in cluster_centers:
            distance = calculate_haversine_distance(place.coordinates, center)
            distances.append(distance)

        # find which cluster (day) is closest to this place
        nearest_cluster_index = distances.index(min(distances))

        clusters[nearest_cluster_index].append(place)

    print("Clustering complete. Day group sizes:")
    for i, cluster in enumerate(clusters):
        print(f"  Day {i+1}: {len(cluster)} places")

    return clusters


def find_worst_place(cluster: List[Place]) -> Place:
    center = find_cluster_center(cluster)

    farthest_place = None
    max_dist = -1

    for place in cluster:
        dist = calculate_haversine_distance(place.coordinates, center)

        if dist> max_dist:
            max_dist = dist
            farthest_place = place

    
    return farthest_place

def calculate_cluster_distance(clusterA : List[Place], clusterB:List[Place]) -> float:
    return calculate_haversine_distance(find_cluster_center(clusterA), find_cluster_center(clusterB))

def heuristic_cascade_balance_clusters(clusters: List[List[Place]], profile: TravelerProfile) -> List[List[Place]]:
    print("running constraint programming algorithm for balancing as well as overflow handling")
    max_per_day = profile.max_places_per_day

    overflow_indices = [i for i,c in enumerate(clusters) if len(c)>max_per_day]
    processed_count = 0
    max_processing_attempts = len(clusters)*5 # limit to prevent infinite loops

    while overflow_indices and processed_count< max_processing_attempts:
        # first overflowing cluster
        original_cluster_index = overflow_indices.pop(0)
        original_cluster = clusters[original_cluster_index]
        processed_count += 1

        if len(original_cluster) <= max_per_day:
            continue

        print(f"Balancing day {original_cluster_index+1} (size {len(original_cluster)})")

        place_to_move = find_worst_place(original_cluster)
        original_cluster.remove(place_to_move)

        # list of all other clusters and how far they are from original cluster
        other_clusters_sorted = []
        for i,cluster in enumerate(clusters):
            if i != original_cluster_index:
                distance = calculate_cluster_distance(original_cluster, cluster)
                other_clusters_sorted.append((distance, i , cluster))

        for j in range(len(other_clusters_sorted) - 1):
            for k in range(j+1, len(other_clusters_sorted)):
                if other_clusters_sorted[j][0] > other_clusters_sorted[k][0]:
                    other_clusters_sorted[j], other_clusters_sorted[k] = other_clusters_sorted[k], other_clusters_sorted[j]

        current_place_to_add = place_to_move

        for (dist, nearest_index, nearest_cluster) in other_clusters_sorted:
            nearest_cluster.append(current_place_to_add)

            if len(nearest_cluster) <= max_per_day:
                print(f"Moved {current_place_to_add.name} to day {nearest_index+1}. cascade stops")
                current_place_to_add = None
                break
            else:
                print(f"moved {current_place_to_add.name} to day {nearest_index+1}. cascade continues")
                place_to_cascade = find_worst_place(nearest_cluster)
                nearest_cluster.remove(place_to_cascade)
                current_place_to_add = place_to_cascade
                if nearest_index not in overflow_indices:
                    overflow_indices.append(nearest_index)
                
        
        if current_place_to_add:
            print(f"!! could not find a suitable day for {current_place_to_add.name}. adding it back")
            original_cluster.append(current_place_to_add)
        
        if len(original_cluster) > max_per_day:
            if original_cluster_index not in overflow_indices:
                overflow_indices.append(original_cluster_index)



    final_overflow = [i+1 for i,c in enumerate(clusters) if len(c)> max_per_day]

    if final_overflow:
        print(f"Balancing failed.Impossible itinerary to adjust while having user satisfied. overflowing days :{final_overflow}")
        return None
        
    print("balacing complete, final group sizes")
    for i, c in enumerate(clusters):
        print(f" Day {i+1} : {len(c)} places")

    return clusters

@dataclass
class OptimizedDay:
    day_number : int
    route : List[Place]
    total_day_time_hours : float
    total_day_cost : int

def nearest_neighbor_optimized_day_route(day_cluster: List[Place], day_num:int,profile:TravelerProfile,city_name:str,city_data:pd.Series,month_weather:dict, hourly_weather_db:dict, month_name:str) -> OptimizedDay:
    print(f"Optimizing route for {day_num} using NN")
    current_time_hours = float(profile.day_start_hour)
    total_day_time_spent = 0.0
    total_day_cost = 0
    ordered_route=[]

    if not day_cluster:
        return OptimizedDay(day_num,[],0,0)
    
    unvisited = list(day_cluster)
    general_places = []
    sunrise_candidates = []
    sunset_candidates = []
    nightlife_candidates = []

    for place in unvisited:
        if profile.wants_nightlife and "nightlife" in place.suitable_for:
            nightlife_candidates.append(place)
        elif profile.wants_sunset and "sunset" in place.suitable_for:
            sunset_candidates.append(place)
        elif profile.wants_sunrise and "sunrise" in place.suitable_for:
            sunrise_candidates.append(place)
        else:
            general_places.append(place)

    start_place = None
    if profile.wants_sunrise and profile.timing == "early_bird" and sunrise_candidates:
        start_place = sunrise_candidates.pop(0) # prioritize sunrise
        print(f"  - Prioritizing start: {start_place.name} (Sunrise spot)")

    
    if not start_place:
        if general_places:
            start_place = general_places.pop(0)
        elif sunset_candidates:
            start_place = sunset_candidates.pop(0) 
        elif sunrise_candidates:
            start_place = sunrise_candidates.pop(0) 
        elif nightlife_candidates:
            start_place = nightlife_candidates.pop(0) 
    
    ordered_route.append(start_place)
    total_day_time_spent += start_place.visit_duration_hours
    total_day_cost += start_place.cost
    current_time_hours += start_place.visit_duration_hours
    print(f"Start at : {start_place.name}")

    places_to_route_nn = general_places + sunrise_candidates + sunset_candidates
    nightlife_places_nn = nightlife_candidates

    while places_to_route_nn:
        current_place = ordered_route[-1]
        best_next_place = None
        shortest_travel_time = float('inf')

        for next_place in places_to_route_nn:
            hour_of_day = int(current_time_hours) % 24
            travel_time = calculate_travel_time(current_place, next_place,city_name, city_data, month_weather, hourly_weather_db, month_name, hour_of_day )

            if travel_time < shortest_travel_time:
                shortest_travel_time = travel_time
                best_next_place = next_place

        
        if best_next_place:
            total_day_time_spent += shortest_travel_time
            current_time_hours += shortest_travel_time
            total_day_time_spent += best_next_place.visit_duration_hours
            current_time_hours += best_next_place.visit_duration_hours
            total_day_cost += best_next_place.cost
            ordered_route.append(best_next_place)
            places_to_route_nn.remove(best_next_place)
            print(f"{shortest_travel_time:.2f} hrs travel -> {best_next_place.name}")
        else:
            break

    if nightlife_places_nn:
        print("  - Routing nightlife activities at the end of the day...")

    while nightlife_places_nn:
        current_place = ordered_route[-1]
        best_next_place = None
        shortest_travel_time = float('inf')

        for next_place in nightlife_places_nn:
            hour_of_day = int(current_time_hours) % 24
            travel_time = calculate_travel_time(current_place, next_place, city_name, city_data, month_weather, hourly_weather_db, month_name, hour_of_day)
            
            if travel_time < shortest_travel_time:
                shortest_travel_time = travel_time
                best_next_place = next_place

        if best_next_place:
            total_day_time_spent += shortest_travel_time
            current_time_hours += shortest_travel_time
            total_day_time_spent += best_next_place.visit_duration_hours
            current_time_hours += best_next_place.visit_duration_hours
            total_day_cost += best_next_place.cost
            ordered_route.append(best_next_place)
            nightlife_places_nn.remove(best_next_place)
            print(f"{shortest_travel_time:.2f} hrs travel -> {best_next_place.name} (nightlife)")
        else:
            break

    print(f"  Day {day_num} optimized. total time: {total_day_time_spent:.2f} hrs. total cost: {total_day_cost}")

    return OptimizedDay(day_num,ordered_route,total_day_time_spent,total_day_cost)
    
import random
class ACO_Solver:

    def __init__(self, distance_matrix, ant_count, iterations, alpha=1.0,beta=3.0,evaporation_rate=0.4):
        self.num_nodes = len(distance_matrix)
        self.distance_matrix = distance_matrix
        self.ant_count = ant_count
        self.iterations = iterations
        self.alpha = alpha                # pheromone importance
        self.beta = beta                  # heuristic (distance) importance
        self.evaporation_rate = evaporation_rate

        self.pheromone_matrix = np.ones((self.num_nodes, self.num_nodes))
        self.heuristic_matrix = np.zeros((self.num_nodes, self.num_nodes))

        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                if i!=j:
                    dist = self.distance_matrix[i][j]
                    self.heuristic_matrix[i][j] = 1.0 / dist if dist > 0 else 1e6


    def _choose_next_node(self, current_node, unvisited):
        probabilites = []
        total_prob = 0.0

        for node in unvisited:
            tau = self.pheromone_matrix[current_node][node]**self.alpha
            eta = self.heuristic_matrix[current_node][node]**self.beta
            prob = tau*eta
            probabilites.append((node, prob))
            total_prob+= prob

        if total_prob == 0:
            return random.choice(unvisited)
        rand = random.uniform(0.0,total_prob)
        cumulative_prob =  0.0

        for node, prob in probabilites:
            cumulative_prob += prob
            if cumulative_prob>= rand:
                return node
            
        return probabilites[-1][0]
    
    def _build_ant_tour(self):
        tour = []
        unvisited = list(range(self.num_nodes))
        start_node = random.choice(unvisited)
        tour.append(start_node)
        unvisited.remove(start_node)
        current_node = start_node

        while unvisited:
            next_node = self._choose_next_node(current_node, unvisited)
            tour.append(next_node)
            unvisited.remove(next_node)
            current_node = next_node

        tour.append(tour[0])
        return tour
    
    def _calculate_tour_cost(self, tour):
        cost = 0.0
        for i in range(len(tour) -1):
            node_a = tour[i]
            node_b = tour[i+1]
            cost+= self.distance_matrix[node_a][node_b]
        return cost
    
    def _update_pheromones(self, ant_tours):
        self.pheromone_matrix *= (1.0-self.evaporation_rate)

        for tour, cost in ant_tours:
            pheromone_deposit = 1.0/cost

            for i in range(len(tour) -1):
                node_a = tour[i]
                node_b = tour[i+1]
                self.pheromone_matrix[node_a][node_b] += pheromone_deposit
                self.pheromone_matrix[node_b][node_a] += pheromone_deposit # symmetric

    def solve(self):
        best_tour = None
        best_cost = float('inf')

        for i in range(self.iterations):
            ant_tours = []

            for _ in range(self.ant_count):
                tour = self._build_ant_tour()
                cost = self._calculate_tour_cost(tour)
                ant_tours.append((tour,cost))

                if cost < best_cost:
                    best_cost = cost
                    best_tour = tour

            self._update_pheromones(ant_tours)

            if (i+1) %10 == 0:
                print(f"ACO iteration {i+1}/{self.iterations}, best cost : {best_cost:.2f}")

        return best_tour[:-1], best_cost
    

def optimize_trip_sequence(optimized_days: List[OptimizedDay], profile: TravelerProfile, city_name:str,city_data:pd.Series, month_weather:dict, hourly_weather_db:dict, month_name:str) -> List[OptimizedDay]:
    print(f"running ACO for {len(optimized_days)} days")
    num_days = len(optimized_days)
    if num_days < 2:
        return optimized_days
    
    distance_matrix = np.zeros((num_days,num_days))

    for i in range(num_days):
        for j in range(num_days):
            if i == j:
                distance_matrix[i][j] = float('inf')
                continue

            place_from = optimized_days[i].route[-1]
            place_to = optimized_days[j].route[0]
            hour_of_day = int(profile.day_start_hour)

            cost = calculate_travel_time(place_from, place_to, city_name, city_data, month_weather, hourly_weather_db, month_name, hour_of_day)
            distance_matrix[i][j] = cost if cost> 0 else 1e-6


    aco = ACO_Solver(distance_matrix,10,100,1.0,3.0,0.4)

    optimal_path, best_cost = aco.solve()
    print(f"ACO solver found optimal path : {optimal_path} at {best_cost:.2f} cost")

    day_map = {i:day for i,day in enumerate(optimized_days)}
    final_sequenced_itinerary = []
    for index in optimal_path:
        final_sequenced_itinerary.append(day_map[index])

    return final_sequenced_itinerary


"""
            SECTION 4 = final validation and remodification
"""

def validate_and_display_itinerary(final_itinerary:List[OptimizedDay], profile: TravelerProfile, budget:int, city_name:str, city_data:pd.Series, month_weather:dict,hourly_weather_db:dict,month_name:str):


    total_cost = 0
    is_over_time = False

    for day in final_itinerary:
        total_cost += day.total_day_cost
        available_hours = profile.day_end_hour - profile.day_start_hour

        if day.total_day_time_hours > available_hours:
            is_over_time = True
            print(f"⚠️  WARNING: Day {day.day_number} is too long!")
            print(f"    - Required time: {day.total_day_time_hours:.2f} hours")
            print(f"    - Your limit: {available_hours} hours")

    is_over_budget= total_cost>budget
    coverage = 0

    if is_over_budget:
        coverage = total_cost-budget
        print(f"⚠️  WARNING (Budget): You are ₹{coverage} over your ₹{budget} budget.")
        print(f"    - Estimated Cost: ₹{total_cost}")
    
    if is_over_time:
        print("\nNote: one or more days are packed")

    if is_over_time or is_over_budget:
        print("\n" + "!"*40)
        print("Fixes Required: Your itinerary has issues.")
        print("!"*40)
        
        all_places = []
        for day in final_itinerary:
            for place in day.route:
                all_places.append(place)

        all_places_without_duplicates = list(set(all_places)) #using set method for dataclass
        def get_place_cost(place):
            return place.cost

        all_places_in_itinerary = sorted(all_places_without_duplicates,key = get_place_cost,reverse=True)

        most_expensive = None
        if is_over_budget and all_places_in_itinerary:
            most_expensive = all_places_in_itinerary[0]
        
        OPT_ACCEPT = "I'll accept all issues (show plan as-is)."
        OPT_ADD_BUDGET = f"Add the extra amount (₹{coverage}) and finalize."
        OPT_REMODIFY = "Try re-balancing with a 'faster' pace (fixes time)."
        OPT_MANUAL_DROP = "Let me manually choose place(s) to drop (fixes time/budget)."
        OPT_AUTO_DROP_1 = f"Auto-drop most expensive: {most_expensive.name} (saves ₹{most_expensive.cost})" if most_expensive else ""
        OPT_AUTO_DROP_2 = "Auto-drop the 2 most expensive places."
        OPT_EXIT = "Exit planner. Too many issues."

        options = []
        options.append(OPT_ACCEPT)

        if is_over_budget and coverage > 0 and coverage <= 200:
            options.append(OPT_ADD_BUDGET)
        
        if is_over_time and profile.pace != "fast":
            options.append(OPT_REMODIFY)
        
        options.append(OPT_MANUAL_DROP)    

        if is_over_budget and most_expensive:
            options.append(OPT_AUTO_DROP_1)
            if coverage>budget*0.2 and len(all_places_in_itinerary)>1:
                options.append(OPT_AUTO_DROP_2)

        options.append(OPT_EXIT)

        choice = _get_validated_input("What would you like to do?", options)    

        if choice == OPT_ACCEPT:
            print("Acepting issues and showing plan")
            pass
        elif choice == OPT_ADD_BUDGET:
            print(f"Great! Accepting the new total cost of ₹{total_cost}.")
            pass
        elif choice == OPT_REMODIFY:
            return "REMODIFY", None
        elif choice == OPT_MANUAL_DROP:
            print("\nWhich place would you like to drop?")
            place_options = [f"({i+1}) {p.name} for {p.cost} " for i,p in enumerate(all_places_in_itinerary)]
            for opt in place_options:
                print(f"   {opt}")
            
            indices = _get_multi_select_input("Enter numbers to drop (e.g., '1, 3') or press Enter to cancel:",len(all_places_in_itinerary))

            if not indices:
                print("No places dropped. Accepting plan as-is.")
                return "ACCEPT", None
            places_to_drop = [all_places_in_itinerary[i] for i in indices]
            return "DROP", places_to_drop
        elif choice == OPT_AUTO_DROP_1:
            place_to_drop = all_places_in_itinerary[0]
            return "DROP", [place_to_drop] 
        elif choice == OPT_AUTO_DROP_2:
            places_to_drop = all_places_in_itinerary[:2]
            return "DROP", places_to_drop
        elif choice == OPT_EXIT:
            return "EXIT", None
        

        print("Showing the packed plan as-is...")


    print("\n" + "="*60)
    print("🌟 Your Final Optimized Itinerary 🌟")
    print("="*60)    
    
    for i,day in enumerate(final_itinerary):
        print("\n" + "-"*40)
        print(f"📅 DAY {i + 1} (Original Day {day.day_number})")
        print(f"  Cost: ₹{day.total_day_cost} | Est. Time: {day.total_day_time_hours:.2f} hrs")
        print("-" * 40)

        current_time = float(profile.day_start_hour)

        for j, place in enumerate(day.route):
            visit_time = place.visit_duration_hours
            start_hour_str = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
            end_hour_str = f"{int(current_time + visit_time):02d}:{int(((current_time + visit_time) % 1) * 60):02d}"
            print(f"  [{start_hour_str} - {end_hour_str}] Visit: {place.name}")
            current_time += visit_time
            if j < len(day.route) - 1: # If not the last place
                next_place = day.route[j+1]
                hour_of_day = int(current_time)%24
                travel_time = calculate_travel_time(place,next_place, city_name,city_data,month_weather,hourly_weather_db,month_name,hour_of_day)
                print(f"     ( ~{travel_time*60:.0f} min travel )")
                current_time += travel_time
        
    print("\n" + "="*60)
    print(f"🎉 TOTAL ESTIMATED COST: ₹{total_cost}")
    print("="*60)

    return "ACCEPT", None

def main():
    selected_city = get_city_selection(target_city_names)
    master_selected_places = get_poi_selection(selected_city)
    if not master_selected_places:
        print("No places selected. Exiting.")
        return
    
    profile = get_traveler_profile()
    budget, num_days, month_name = get_trip_constraints()
    original_profile_pace = profile.pace

    try:
        df_selected_cities.set_index('city_name', inplace=True, drop=False)
        city_data = df_selected_cities.loc[selected_city]
        month_weather = historical_weather_data[selected_city][month_name]
        hourly_weather_db = historical_hourly_weather[selected_city][month_name]
    except KeyError:
        print(f"Error: Missing data for {selected_city} or {month_name}. Exiting.")
        return
    except Exception as e:
        print(f"An unexpected data error occurred: {e}")
        return

    while True:
        if not master_selected_places:
            print("You have removed all places from your trip. Exiting.")
            break
    
        unbalanced_clusters = custome_greedy_clustering_heuristic(master_selected_places,num_days)
        clusters_copy = [list(c) for c in unbalanced_clusters]
        balanced_clusters = heuristic_cascade_balance_clusters(clusters_copy,profile)

        if balanced_clusters is None:
            print("\n" + "!"*60)
            print("Initial balancing failed. Your constraints are too tight.")
            print("!"*60)

            options = []

            OPT_FAST_PACE = "Try to see all places (fast-paced, 4 places/day)"
            OPT_RECALC = "Let me drop a place and recalculate"
            OPT_EXIT_FEWER = "Exit and select fewer places"
            
            
            if profile.pace != "fast":
                options.append(OPT_FAST_PACE)
            options.append(OPT_RECALC)
            options.append(OPT_EXIT_FEWER)
            choice = _get_validated_input("What would you like to do?",options)
            if OPT_FAST_PACE in choice:
                print("Re-configuring for 'fast-paced' and trying again...")
                profile.pace = "fast"
                profile.calculate_rules() 
                continue
            elif OPT_RECALC in choice:
                    print("\nWhich place would you like to drop?")
                    place_options = [f"({i+1}) {p.name}" for i, p in enumerate(master_selected_places)]
                    for opt in place_options:
                        print(f"  {opt}")
                    
                    indices = _get_multi_select_input("Enter numbers to drop (e.g., '1, 3'):", len(master_selected_places))
                
                    if not indices:
                        print("No places dropped. Exiting.")
                        return
                    places_to_drop = [master_selected_places[i] for i in indices]
                    if not isinstance(places_to_drop, list):
                        places_to_drop = [places_to_drop]
                    print(f"Removing {len(places_to_drop)} place(s) from your list and re-calculating...")
                    for p_to_drop in places_to_drop: 
                        if p_to_drop in master_selected_places:
                            print(f" - Removing {p_to_drop.name}")
                            master_selected_places.remove(p_to_drop)
                        else:
                            print(f" - Warning: {p_to_drop.name} was already removed or not found.")
                
                    profile.pace = original_profile_pace
                    profile.calculate_rules()
                    continue
            else:
                print("Exiting. Please re-run and select fewer places.")
                return
    
        optimized_days = []
        for i, cluster in enumerate(balanced_clusters):
            if not cluster:
                continue

            day_plan = nearest_neighbor_optimized_day_route(cluster,i+1,profile,selected_city,city_data,month_weather,hourly_weather_db,month_name)
            optimized_days.append(day_plan)

        final_sequenced_itinerary = optimize_trip_sequence(optimized_days,profile,selected_city,city_data,month_weather,hourly_weather_db,month_name)
        action, data = validate_and_display_itinerary(final_sequenced_itinerary, profile, budget, selected_city,city_data, month_weather, hourly_weather_db, month_name)
        if action == "ACCEPT":
            print("\nEnjoy your trip!")
            break 
        elif action == "REMODIFY":
            if profile.pace == "fast":
                print("Already at fastest pace. Cannot re-modify further.")
                print("Please try dropping a place instead.")
                continue 
            print("Attempting to re-balance with 'fast-paced'...")
            profile.pace = "fast"
            profile.calculate_rules()
            continue
        elif action == "DROP":
            places_to_drop = data
            if not isinstance(places_to_drop, list):
                places_to_drop = [places_to_drop]
            print(f"Removing {len(places_to_drop)} place(s) from your list and re-calculating...")
            for place_to_drop in places_to_drop:
                if place_to_drop in master_selected_places:
                    print(f" - Removing {place_to_drop.name}")
                    master_selected_places.remove(place_to_drop)
                else:
                    print(f" - Warning: {place_to_drop.name} was already removed or not found.")
            profile.pace = original_profile_pace
            profile.calculate_rules()
            continue 
        elif action == "EXIT":
            print("Exiting planner. Goodbye!")
            break


if __name__ == "__main__":
    main()