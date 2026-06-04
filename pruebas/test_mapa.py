import folium

m = folium.Map(
    location=[40.4, -3.7], zoom_start=6
)
m.save("test.html")
