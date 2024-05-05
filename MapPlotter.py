import webbrowser
import plotly.express as px
import folium

class RoutePlotter:
     
    def __init__(self, data_frame):
        """
        Initializes the RoutePlotter with a DataFrame containing the route coordinates.
        Parameters:
            data_frame (pd.DataFrame): A DataFrame with columns 'latitude' and 'longitude'.
        """
        self.route_df = data_frame

    def plot_route(self):
        """
        Plots the route using Plotly based on the DataFrame provided during initialization.
        This function uses Mapbox to visualize the route. 
        """
        fig = px.line_mapbox(self.route_df, lat='latitude', lon='longitude', zoom=13)
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig.show()

class MultiRoutePlotter:

    def __init__(self, center_coords):
        self.map = folium.Map(location=center_coords, tiles="CartoDB Positron", zoom_start=13, control_scale=True)
    
    def add_route(self, coordinates, route_name, color='Red'):
        fg = folium.FeatureGroup(name=route_name, show=True).add_to(self.map)
        folium.PolyLine(coordinates, color=color, weight=2.0, opacity=1).add_to(fg)

    def show(self):
        folium.LayerControl().add_to(self.map)
        return self.map
    



