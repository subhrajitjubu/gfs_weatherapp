Hugging Face's logo
Hugging Face
Models
Datasets
Spaces
Buckets
new
Docs
Enterprise
Pricing


Spaces:
odisha
/
wms-gfs


like
0

Logs
App
Files
Settings
wms-gfs
/
app.py

ayeshh
Merge branch 'main' of https://huggingface.co/spaces/odisha/wms-gfs
2f0685d
11 months ago
raw

Copy download link
history
blame
edit
delete
10.7 kB
import streamlit as st
import datetime
import matplotlib.pyplot as plt
import xarray as xr
from ncep_data_req import get_data_preprocess # Update this to your actual package/module
import io
# import cartopy.crs as ccrs
# import cartopy.feature as cfeature
# from cartopy.mpl.ticker import (LongitudeFormatter, LatitudeFormatter,
                # LatitudeLocator)
import matplotlib.ticker as mticker
import time
import numpy as np
import tempfile
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
from PIL import Image
import io
from folium.raster_layers import ImageOverlay


import json
with open('DISTRICT_BOUNDARY.json', 'r') as f:
    geojson_data = json.load(f)


def plot_to_numpy_array(data, colormap="viridis", robust=False):
  fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
  data.plot.contourf(ax=ax, cmap=colormap, robust=robust,
                     add_colorbar=False)
  
  ax.set_axis_off()

  buf = io.BytesIO()
  plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0, transparent=True)
  buf.seek(0)
  plt.close(fig)

  img = Image.open(buf).convert("RGBA")
  return np.array(img) # Return as NumPy array

def plotc_to_numpy_array(data, linewidth=5,color='k'):
  fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
  CS=data.plot.contour(ax=ax,levels=11,linewidths=linewidth,color='black',kwargs=dict(inline=True))
  ax.clabel(CS)

  ax.set_axis_off()

  buf = io.BytesIO()
  plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0, transparent=True)
  buf.seek(0)
  plt.close(fig)

  img = Image.open(buf).convert("RGBA")
  return np.array(img) # Return as NumPy array



gfs_vars=["tmpprs", "rhprs", 'rh2m','pratesfc',
     'apcpsfc','prmslmsl',
      "ugrdprs","ugrdprs", "vgrdprs",'uflxsfc']


st.set_page_config(layout="wide")
st.title(" GFS Viewer")
st.markdown("""
  <style>
    .block-container {
      padding-top: 1.9rem;
    }
  </style>
""", unsafe_allow_html=True)
with st.expander("Map selection"):
  st.markdown(" **Draw Bounding Box on Map**")

  m = folium.Map(location=[20, 80], zoom_start=4)


  # Add drawing control
  draw = Draw(export=True, draw_options={
    'polyline': False,
    'circle': False,
    'polygon': False,
    'marker': True,
    'circlemarker': False,
    'rectangle': True,
  })
  draw.add_to(m)

  output = st_folium(m, height=600, width=900, key="bbox_draw")
  
  bbox_coords = None
  if output and output.get("last_active_drawing") and output["last_active_drawing"]["geometry"]["type"] == "Polygon":
    coords = output["last_active_drawing"]["geometry"]["coordinates"][0]
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)
    bbox_coords = (lon_min, lon_max, lat_min, lat_max)
    st.success(f" Bounding Box Selected:\nLon: {lon_min:.2f}–{lon_max:.2f}, Lat: {lat_min:.2f}–{lat_max:.2f}")
    
  else:
    st.warning(" Please draw a rectangular bounding box on the map.")
    

if "show_map" not in st.session_state:
    st.session_state["show_map"] = True
col1, col2,col3 = st.columns([20, 70,20])

with col1:
#   with st.expander("Forecast Parameters"):

  # st.subheader("Forecast Parameters")
    selected_date = st.date_input(" Forecast Start Date", datetime.date.today())
    selected_utc = st.selectbox(" UTC Initialization Hour", [0, 6, 12, 18])
    forecast_hour = st.slider(" Forecast Length (Hours)", 1, 120, 6)
    variables = st.multiselect(" Variable", gfs_vars,['prmslmsl'])
    is_pressure_level = st.checkbox("Is this a pressure-level variable?", value=False)
    # st.markdown(" **Select Geographic Bounds**")
    # lon_min = st.number_input("Longitude Min", value=60.0)
    # lon_max = st.number_input("Longitude Max", value=100.0)
    # lat_min = st.number_input("Latitude Min", value=0.0)
    # lat_max = st.number_input("Latitude Max", value=40.0)



    add_pressure_contours = st.checkbox(" Overlay Surface Pressure (pressfc)", value=False)
    rob=st.checkbox("Robust set?", value=False)

    colormap = st.selectbox(
    " Select Colormap",
    options=["viridis", "plasma", "inferno", "magma", "cividis", "coolwarm", "jet", "turbo"],
    index=0, )
    fetch = st.button(" Fetch Data")
    if fetch:
        st.session_state["show_map"] = False 
        with st.spinner("Fetching and processing data..."):
            ds_dict = {}

            for var in variables:
                ds = get_data_preprocess(
                    date=selected_date,
                    utc=selected_utc,
                    ft=forecast_hour,
                    var=var,
                    pvar="yes" if is_pressure_level else "no",
                    lon_range=(bbox_coords[0], bbox_coords[1]), lat_range=(bbox_coords[2], bbox_coords[3])

                )
                ds_dict[var] = ds

            # Save to session state
            st.session_state["ds_dict"] = ds_dict
            st.session_state["variables"] = variables
            st.session_state["is_pressure_level"] = is_pressure_level
            st.success(" All variables fetched!")
            if "ds_dict" in st.session_state:
                merged_ds = xr.merge([ds for ds in st.session_state["ds_dict"].values()])

                with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmpfile:
                    merged_ds.to_netcdf(tmpfile.name)
                    tmpfile.flush()
                    with open(tmpfile.name, "rb") as f:
                        st.download_button(
                        data=f,label="Download Data in Netcdf format",
                        file_name="gfs_data.nc",
                        mime="application/x-netcdf"
                        )

  

with col2:
  # Save fetched data in session state
  


  # Now allow plot to update even if only sliders change
  if "ds_dict" in st.session_state:
    ds_dict = st.session_state["ds_dict"]
    variables = st.session_state["variables"]
    is_pressure_level = st.session_state["is_pressure_level"]

    viewable_vars = [v for v in variables if v != "prmslmsl"]
    selected_var = st.selectbox(" Select Variable to View", viewable_vars)

    ds = ds_dict[selected_var]

    st.markdown(f" Plot of `{selected_var}`")

    if is_pressure_level:
      time_idx = st.slider("Time Index", 1, len(ds.time) - 1, 1)
      level_idx = st.slider("Pressure Level Index", 0, len(ds.levels) - 1, 0)
      data = ds[selected_var].isel(time=time_idx, levels=level_idx)
    else:
      # time_idx = st.slider("Time Index", 0, len(ds.time) - 1, 0)
      time_idx = st.slider(" Time Index", 1, len(ds.time) - 1, key="time_slider")
      data = ds[selected_var].isel(time=time_idx)      

    dat1 = data.copy()
    if selected_var in ["pratesfc"]:
      dat1 = data * 3600
      dat1 = dat1.where(dat1 >= 0.01)
      # dat1['pratesfc'] = xr.where(dat1['pratesfc'],dat1['pratesfc'] >= 0.1, 0) 
    elif selected_var in ["apcpsfc"]:
      dat1 = dat1.where(dat1 >= 0.01)


    else:
      dat1 = data


    st.session_state["dat"] = dat1
    img = plot_to_numpy_array(dat1, colormap=colormap, robust=rob,)
    
  # Get spatial bounds of the image
    lat_bounds = [float(dat1.lat.min()), float(dat1.lat.max())]
    lon_bounds = [float(dat1.lon.min()), float(dat1.lon.max())]
    bounds = [[lat_bounds[0], lon_bounds[0]], [lat_bounds[1], lon_bounds[1]]]

    # Create the map
    m = folium.Map(location=[np.mean(lat_bounds), np.mean(lon_bounds)], zoom_start=4,)
   # folium.GeoJson(        geojson_data,        style_function=lambda feature: {            'fillColor': None,
   #         'color': 'black',
    #        'weight': 1,
    # #       
      #  },
     #   tooltip=folium.GeoJsonTooltip(fields=['District'])
    #).add_to(m)
    if add_pressure_contours:
      if "prmslmsl" not in st.session_state["ds_dict"]:
        st.warning(" 'prmslmsl' not loaded — add it to your variable list to plot contours.")
        add_pressure_contours = False # disable if not available
      else:
        pressfc_ds = st.session_state["ds_dict"]["prmslmsl"]
        pressure_data = pressfc_ds["prmslmsl"].isel(time=time_idx)
        img1 = plotc_to_numpy_array(pressure_data,linewidth=2,)
        ImageOverlay(
        image=img1,
        bounds=bounds,
        opacity=1,
        interactive=False,
        cross_origin=False,
        ).add_to(m)



    
 

    # Add the overlay
    ImageOverlay(
      image=img,
      bounds=bounds,
      opacity=0.6,
      interactive=True,
      cross_origin=False,
    ).add_to(m)

    
    # Optional marker to allow click
    m.add_child(folium.LatLngPopup())

    # Show the map in Streamlit
    click_data = st_folium(m, width=1200, height=600)
    st.session_state["click_data"] = click_data

with col3:
  if "ds_dict" in st.session_state:
    if "click_data" in st.session_state:
        click_info = st.session_state["click_data"]

        selected_point = None
        if click_info and click_info.get("last_clicked"):
            selected_point = click_info["last_clicked"]
            lon_click = selected_point["lng"]
            lat_click = selected_point["lat"]
            st.success(f" Selected Point: Lon = {lon_click:.2f}, Lat = {lat_click:.2f}")
            
            with st.expander(" Show Time Series and Data Table"):
                st.subheader(" Time Series at Location")
                # lat1 = st.number_input("Latitude (0 to 40)", min_value=0.0, max_value=40.0, value=20.0, step=0.1)
                # lon1 = st.number_input("Longitude (60 to 100)", min_value=60.0, max_value=100.0, value=80.0, step=0.1)
                # Extract time series at nearest point
                if is_pressure_level:
                    ts_data = ds[selected_var].isel(levels=level_idx, lat=lat1, lon=lon1,method='nearest')[1:]
                else:
                    ts_data = ds[selected_var].sel(lat=lat_click, lon=lon_click,method='nearest')[1:]

                # Scale time series if needed
                if selected_var == "pratesfc":
                    ts_data = ts_data * 3600
                    ts_data = ts_data.where(ts_data >= 0.1)
                elif selected_var == "apcpsfc":
                    ts_data = ts_data.where(ts_data >= 0.1)
                else:
                    ts_data=ts_data
                
                # st.pyplot(fig2)
                fig2, ax2 = plt.subplots()
                ts_data.plot(ax=ax2, marker='o')
                ax2.set_title(f"Time Series of `{selected_var}` at ({lat_click:.2f}, {lon_click:.2f})")
                ax2.set_xlabel("Time")
                ax2.set_ylabel(selected_var)
                st.pyplot(fig2)
                st.dataframe(ts_data.to_dataframe().reset_index())



