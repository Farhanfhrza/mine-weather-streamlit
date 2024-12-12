
import pandas as pd
import requests
import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
from matplotlib import font_manager

# Menambahkan font custom
font_path = '/mnt/data/file-ngwyeoEN29l1M3O1QpdxCwkj'
font_prop = font_manager.FontProperties(fname=font_path)

class WeatherConditionMapper:
    def __init__(self):
        self.weather_conditions = {
            1000: {'description': 'Sunny', 'risk_level': 1, 'mining_impact': 'Optimal Conditions'},
            1003: {'description': 'Partly Cloudy', 'risk_level': 1, 'mining_impact': 'Good Conditions'},
            1006: {'description': 'Cloudy', 'risk_level': 2, 'mining_impact': 'Slightly Impacted'},
            1009: {'description': 'Overcast', 'risk_level': 3, 'mining_impact': 'Potential Disruption'},
            1030: {'description': 'Mist', 'risk_level': 4, 'mining_impact': 'High Risk'},
            1063: {'description': 'Patchy Rain Possible', 'risk_level': 3, 'mining_impact': 'Preparation Required'},
            1066: {'description': 'Patchy Snow Possible', 'risk_level': 4, 'mining_impact': 'Limited Operations'},
            1087: {'description': 'Thundery Outbreaks Possible', 'risk_level': 5, 'mining_impact': 'Cease Operations'},
            1114: {'description': 'Blowing Snow', 'risk_level': 5, 'mining_impact': 'Cease Operations'},
            1117: {'description': 'Blizzard', 'risk_level': 5, 'mining_impact': 'Cease Operations'},
            1135: {'description': 'Fog', 'risk_level': 4, 'mining_impact': 'High Risk'},
            1192: {'description': 'Heavy Rain at Times', 'risk_level': 4, 'mining_impact': 'Limited Operations'},
            1276: {'description': 'Moderate or Heavy Rain with Thunder', 'risk_level': 5, 'mining_impact': 'Cease Operations'}
        }

    def get_condition_details(self, code):
        return self.weather_conditions.get(code, {'description': 'Unknown Condition', 'risk_level': 3, 'mining_impact': 'Requires Evaluation'})

    def assess_mining_risk(self, weather_code):
        condition = self.get_condition_details(weather_code)
        recommendations = {
            1: "✅ Normal Operations",
            2: "⚠️ Proceed with Caution",
            3: "🟠 Consider Partial Suspension",
            4: "🔴 Consider Halting Operations",
            5: "🛑 Cease All Operations"
        }
        return {
            'risk_level': condition['risk_level'],
            'description': condition['description'],
            'mining_impact': condition['mining_impact'],
            'recommendation': recommendations.get(condition['risk_level'], "Further Evaluation Needed")
        }

class MiningWeatherAnalyzer:
    def __init__(self):
        self.condition_mapper = WeatherConditionMapper()
        self.weather_limits = {
            'temperature': {'min': 0, 'max': 40},
            'humidity': {'min': 30, 'max': 80},
            'wind_speed': {'max': 30}
        }

    def generate_hourly_weather_data(self, location="jakarta", days=1):
        try:
            api_key = 'dfc14da3dd7a4209bd4145623240912'
            url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days={days}"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                all_hourly_data = []

                for forecast_day in data['forecast']['forecastday']:
                    hourly_data = forecast_day['hour']
                    for hour in hourly_data:
                        all_hourly_data.append({
                            'timestamp': hour['time'],
                            'temperature': hour['temp_c'],
                            'humidity': hour['humidity'],
                            'wind_speed': hour['wind_kph'],
                            'weather_code': hour['condition']['code'],
                            'weather_description': hour['condition']['text']
                        })

                return pd.DataFrame(all_hourly_data)
            else:
                st.error(f"API Error: {response.status_code}")
        except requests.RequestException as e:
            st.error(f"Request Exception: {e}")
        except Exception as e:
            st.error(f"Unexpected Error: {e}")

    def analyze_mining_conditions(self, hourly_data):
        analysis_results = []
        for _, row in hourly_data.iterrows():
            weather_risk = self.condition_mapper.assess_mining_risk(row['weather_code'])
            additional_risks = []

            if (row['temperature'] < self.weather_limits['temperature']['min'] or 
                row['temperature'] > self.weather_limits['temperature']['max']):
                additional_risks.append(f"Extreme Temperature: {row['temperature']}°C")

            if (row['humidity'] < self.weather_limits['humidity']['min'] or 
                row['humidity'] > self.weather_limits['humidity']['max']):
                additional_risks.append(f"Abnormal Humidity: {row['humidity']}%")

            if row['wind_speed'] > self.weather_limits['wind_speed']['max']:
                additional_risks.append(f"High Wind Speed: {row['wind_speed']} km/h")

            analysis_results.append({
                'timestamp': row['timestamp'],
                'weather_description': row['weather_description'],
                'temperature': row['temperature'],
                'humidity': row['humidity'],
                'wind_speed': row['wind_speed'],
                'risk_level': weather_risk['risk_level'],
                'mining_impact': weather_risk['mining_impact'],
                'recommendation': weather_risk['recommendation'],
                'additional_risks': ', '.join(additional_risks) if additional_risks else 'No Additional Risks'
            })

        return pd.DataFrame(analysis_results)

# Fungsi untuk menampilkan grafik
def plot_analysis(weather_analysis):
    plt.figure(figsize=(10, 5))
    weather_analysis['risk_level'].value_counts().sort_index().plot(kind='bar', fontproperties=font_prop)
    plt.title('Distribusi Level Risiko', fontproperties=font_prop)
    plt.xlabel('Level Risiko', fontproperties=font_prop)
    plt.ylabel('Jumlah Jam', fontproperties=font_prop)
    plt.xticks(rotation=0, fontproperties=font_prop)
    plt.tight_layout()
    return plt

# Fungsi utama Streamlit
def main():
    st.title("Analisis Cuaca untuk Operasi Pertambangan")
    
    location = st.text_input("Masukkan lokasi (default: Jakarta)", "Jakarta")
    days = st.number_input("Masukkan jumlah hari untuk menganalisis (default: 1)", min_value=1, value=1)
    
    analyzer = MiningWeatherAnalyzer()
    hourly_weather = analyzer.generate_hourly_weather_data(location, days)
    
    if hourly_weather is not None:
        weather_analysis = analyzer.analyze_mining_conditions(hourly_weather)
        
        st.write("--- Rangkuman Analisis Cuaca ---")
        st.write(f"Lokasi: {location}")
        st.write(f"Hari yang dianalisis: {days}")
        st.write(f"Total Jam yang dianalisis: {len(weather_analysis)}")
        
        # Menampilkan rekomendasi
        recommendation_counts = weather_analysis['recommendation'].value_counts()
        st.write("--- Distribusi Rekomendasi ---")
        for rec, count in recommendation_counts.items():
            st.write(f"{rec}: {count} jam")
        
        # Analisis level risiko
        max_risk_level = weather_analysis['risk_level'].max()
        st.write(f"--- Level Risiko Maksimum: {max_risk_level} ---")
        
        # Menampilkan grafik
        # plt = plot_analysis(weather_analysis)
        # st.pyplot(plt)
        
        # Opsi untuk tampilan analisis rinci
        if st.button("Lihat analisis rinci per jam"):
            for _, row in weather_analysis.iterrows():
                st.write(f"🕒 Timestamp: {row['timestamp']}")
                st.write(f"☁️ Cuaca: {row['weather_description']}")
                st.write(f"🌡️ Suhu: {row['temperature']}°C")
                st.write(f"💧 Kelembapan: {row['humidity']}%")
                st.write(f"💨 Kecepatan Angin: {row['wind_speed']} km/h")
                st.write(f"⚠️ Level Risiko: {row['risk_level']}")
                st.write(f"⛏️ Dampak Pertambangan: {row['mining_impact']}")
                st.write(f"📋 Rekomendasi: {row['recommendation']}")
                st.write(f"🚨 Risiko Tambahan: {row['additional_risks']}")
                st.write("---")
    
if __name__ == '__main__':
    main()
