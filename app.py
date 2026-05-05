import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import urllib.request
import os
from pathlib import Path
import requests

st.set_page_config(page_title="CHIRPS Rainfall Viewer", layout="wide")

st.title("🌧️ CHIRPS Global Monthly Rainfall Viewer")
st.markdown("Data from [CHIRPS-2.0 Global Monthly](https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/netcdf/byYear/)")

@st.cache_data
def download_data(url):
    """Download NetCDF file from CHIRPS."""
    with st.spinner("Downloading CHIRPS rainfall data..."):
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp_path = tmp.name
        return tmp_path

@st.cache_data
def load_data(file_path):
    """Load NetCDF file using xarray."""
    with xr.open_dataset(file_path) as ds:
        data = ds.load()
    return data

DATA_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/netcdf/byYear/chirps-v2.0.1981.monthly.nc"

try:
    #nc_file = download_data(DATA_URL)
    ds = load_data(DATA_URL)['precip']
    
    st.sidebar.header("Settings")
    
    # Get available variables and dimensions
    precip_var = None
    for var_name in ds.data_vars:
        if "precip" in var_name.lower() or "rain" in var_name.lower() or "chirps" in var_name.lower():
            precip_var = var_name
            break
    if precip_var is None:
        precip_var = list(ds.data_vars)[0]
    
    # Available years/months from time dimension
    if "time" in ds.dims:
        times = ds["time"].values
        time_options = [str(t)[:10] for t in times]
        selected_time_idx = st.sidebar.selectbox("Select Time", range(len(time_options)), format_func=lambda i: time_options[i])
    elif "year" in ds.dims or "month" in ds.dims:
        years = ds["year"].values if "year" in ds.dims else [1]
        months = ds["month"].values if "month" in ds.dims else [1]
        selected_year = st.sidebar.selectbox("Select Year", years)
        selected_month = st.sidebar.selectbox("Select Month", months)
        selected_time_idx = None
    else:
        selected_time_idx = 0
        times = None
    
    # Region selection
    region = st.sidebar.radio("Region", ["Global", "Custom Region"])
    lat_range = (-60.0, 60.0)
    lon_range = (-180.0, 180.0)
    
    if region == "Custom Region":
        col1, col2 = st.sidebar.columns(2)
        lat_min = col1.number_input("Lat Min", value=-60.0, max_value=60.0)
        lat_max = col2.number_input("Lat Max", value=60.0, max_value=90.0)
        col3, col4 = st.sidebar.columns(2)
        lon_min = col3.number_input("Lon Min", value=-180.0)
        lon_max = col4.number_input("Lon Max", value=180.0)
        lat_range = (lat_min, lat_max)
        lon_range = (lon_min, lon_max)
    
    # Color map selection
    cmap = st.sidebar.selectbox("Colormap", ["viridis", "plasma", "inferno", "YlGnBu", "Blues", "RdYlBu_r"])
    
    # Get precipitation data
    precip_data = ds[precip_var]
    
    # Subset by time
    if selected_time_idx is not None and times is not None:
        precip_slice = precip_data.isel(time=selected_time_idx)
        time_label = time_options[selected_time_idx]
    elif selected_time_idx is None:
        precip_slice = precip_data.sel(year=selected_year, month=selected_month)
        time_label = f"{selected_year}-{selected_month:02d}"
    else:
        precip_slice = precip_data
        time_label = "All Time"
    
    # Subset by region
    precip_slice = precip_slice.sel(lat=slice(lat_range[0], lat_range[1]), 
                                     lon=slice(lon_range[0], lon_range[1]))
    
    # Plot
    st.subheader(f"Rainfall for {time_label}")
    
    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    
    # Handle missing values
    precip_plot = precip_slice.where(precip_slice > 0)
    
    # Create plot
    img = ax.imshow(precip_plot.values, 
                    cmap=cmap,
                    aspect="auto",
                    interpolation="nearest",
                    vmin=0)
    
    # Add colorbar
    cbar = plt.colorbar(img, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Rainfall (mm)", fontsize=10)
    
    # Add title and labels
    ax.set_title(f"CHIRPS Monthly Rainfall - {time_label}", fontsize=14, fontweight="bold")
    
    # Add coordinate labels
    lats = precip_slice.lat.values
    lons = precip_slice.lon.values
    
    if len(lats) > 5:
        lat_ticks = np.linspace(0, len(lats)-1, 6, dtype=int)
        ax.set_yticks(lat_ticks)
        ax.set_yticklabels([f"{lats[t]:.1f}°" for t in lat_ticks])
    else:
        ax.set_yticklabels([])
        
    if len(lons) > 5:
        lon_ticks = np.linspace(0, len(lons)-1, 7, dtype=int)
        ax.set_xticks(lon_ticks)
        ax.set_xticklabels([f"{lons[t]:.1f}°" for t in lon_ticks])
    else:
        ax.set_xticklabels([])
    
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Show data info
    st.sidebar.divider()
    st.sidebar.subheader("Data Information")
    st.sidebar.write(f"**Variable:** {precip_var}")
    st.sidebar.write(f"**Shape:** {precip_slice.shape}")
    st.sidebar.write(f"**Lat Range:** {lat_range[0]} to {lat_range[1]}")
    st.sidebar.write(f"**Lon Range:** {lon_range[0]} to {lon_range[1]}")
    st.sidebar.write(f"**Max Rainfall:** {float(precip_slice.max()):.2f} mm")
    st.sidebar.write(f"**Min Rainfall:** {float(precip_slice.min()):.2f} mm")
    st.sidebar.write(f"**Mean Rainfall:** {float(precip_slice.mean()):.2f} mm")
    
    # Show statistics table
    st.subheader("Statistical Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mean Rainfall", f"{float(precip_slice.mean()):.2f} mm")
    col2.metric("Max Rainfall", f"{float(precip_slice.max()):.2f} mm")
    col3.metric("Min Rainfall", f"{float(precip_slice.min()):.2f} mm")
    col4.metric("Std Dev", f"{float(precip_slice.std()):.2f} mm")
    
    # Cleanup
    os.unlink(nc_file)
    
except Exception as e:
    st.error(f"Error: {str(e)}")
    st.info("Make sure the CHIRPS NetCDF file is accessible and has valid precipitation data.")
