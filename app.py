import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import os
import requests
import tempfile

st.set_page_config(page_title="CHIRPS Rainfall Viewer", layout="wide")
st.title("🌧️ CHIRPS Global Monthly Rainfall Viewer")

@st.cache_data(ttl=86400)
def fetch_nc_file(year_int):
    """Download and cache the NetCDF file for the specified year."""
    url = f"https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/netcdf/byYear/chirps-v2.0.{year_int}.monthly.nc"
    cache_dir = os.path.join(tempfile.gettempdir(), "chirps_cache")
    os.makedirs(cache_dir, exist_ok=True)
    file_path = os.path.join(cache_dir, f"chirps_v2.0_{year_int}.nc")
    
    if not os.path.exists(file_path):
        with st.spinner(f"Downloading {year_int} data..."):
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
    return url

with st.sidebar:
    st.header("Configuration")
    selected_year = st.selectbox("Select Year", list(range(1981, 2024)))
    
    months_map = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 
                  7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
    selected_month = st.selectbox("Select Month", list(range(1, 13)), format_func=lambda m: months_map[m])
    
    region = st.radio("Region", ["Global", "Custom"])
    lat_bounds = (-60.0, 60.0)
    lon_bounds = (-180.0, 180.0)
    
    if region == "Custom":
        c1, c2 = st.columns(2)
        lat_bounds = (c1.number_input("Lat Min", value=-60.0), c2.number_input("Lat Max", value=60.0))
        c3, c4 = st.columns(2)
        lon_bounds = (c3.number_input("Lon Min", value=-180.0), c4.number_input("Lon Max", value=180.0))
        
    selected_cmap = st.selectbox("Colormap", ["viridis", "plasma", "YlGnBu", "Blues", "RdYlBu_r"])

file_path = fetch_nc_file(selected_year)
ds = xr.open_dataset(file_path,engine="netcdf4")

# Identify precipitation variable
var_candidates = [v for v in ds.data_vars if "precip" in v.lower()]
data_var = var_candidates[0] if var_candidates else list(ds.data_vars)[0]

# Slice data
if "time" in ds.dims:
    precip_data = ds[data_var].isel(time=selected_month - 1)
else:
    precip_data = ds[data_var]

precip_data = precip_data.sel(latitude=slice(*lat_bounds), longitude=slice(*lon_bounds))
precip_plot = precip_data.where(precip_data > 0)

fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
img = ax.imshow(precip_plot.values, cmap=selected_cmap, aspect="auto", interpolation="nearest")
plt.colorbar(img, ax=ax, fraction=0.046, pad=0.04, label="Rainfall (mm)")
ax.set_title(f"CHIRPS Rainfall - {months_map[selected_month]} {selected_year}", fontweight="bold")

lat_vals = precip_plot.latitude.values
lon_vals = precip_plot.longitude.values
if len(lat_vals) > 5:
    lat_ticks = np.linspace(0, len(lat_vals)-1, 6, dtype=int)
    ax.set_yticks(lat_ticks)
    ax.set_yticklabels([f"{lat_vals[t]:.1f}°" for t in lat_ticks])
if len(lon_vals) > 5:
    lon_ticks = np.linspace(0, len(lon_vals)-1, 7, dtype=int)
    ax.set_xticks(lon_ticks)
    ax.set_xticklabels([f"{lon_vals[t]:.1f}°" for t in lon_ticks])

ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
plt.tight_layout()

st.pyplot(fig)

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Mean", f"{float(precip_data.mean()):.2f} mm")
with col2: st.metric("Max", f"{float(precip_data.max()):.2f} mm")
with col3: st.metric("Min", f"{float(precip_data.min()):.2f} mm")
with col4: st.metric("Std", f"{float(precip_data.std()):.2f} mm")

ds.close()
