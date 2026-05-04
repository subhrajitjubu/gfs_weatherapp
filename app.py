import streamlit as st
import datetime
import matplotlib.pyplot as plt
import xarray as xr
from ncep_data_req import get_data_preprocess # Update this to your actual package/module
import io
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import (LongitudeFormatter, LatitudeFormatter,
                LatitudeLocator)
import matplotlib.ticker as mticker
import time
import metpy.calc as mpcalc

import numpy as np
import tempfile
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
from PIL import Image
import io
from folium.raster_layers import ImageOverlay
from metpy.units import units
from metpy.calc import dewpoint_from_relative_humidity
from metpy.plots import  SkewT, Hodograph
import seaborn as sns
import colormaps as cmaps

from colormaps.utils import show_cmaps_all
from colormaps.utils import show_cmaps_collection

import json







sns.set_theme( style='ticks',font_scale=1.75)
color = sns.color_palette('tab10')
# with open('DISTRICT_BOUNDARY.json', 'r') as f:
#     geojson_data = json.load(f)


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





gfs_pressure_variables = [
   # "absvprs",   # Absolute vorticity [[1]]
   # "clwmrprs",  # Cloud water mixing ratio [[1]]
    "dzdtprs",   # Vertical velocity (dz/dt) 
    #"grleprs",   # Graupel mixing ratio 
   "hgtprs",    # Geopotential height [[1]]
    #"icmrprs",   # Ice mixing ratio 
    "o3mrprs",   # Ozone mixing ratio 
    "rhprs",     # Relative humidity [[1]]
   # "rwmrprs",   # Rainwater mixing ratio 
   # "snmrprs",   # Snow mixing ratio 
    "spfhprs",   # Specific humidity [[1]]
    #"tcdcprs",   # Total cloud cover 
    "tmpprs",    # Temperature [[1]]
    "ugrdprs",   # U-component of wind (east-west) [[1]]
    "vgrdprs",   # V-component of wind (north-south) [[1]]
    "vvelprs"    # Vertical velocity (pressure vertical velocity) [[1]]
]

surface_variables = [
    'tmax2m','tmin2m','rh2m','tmp2m','spfh2m','dpt2m',
    # "no4lftxsfc",  # Surface best (4 layer) lifted index [K]
    "acpcpsfc",    # Surface convective precipitation [kg/m^2]
    # "albdosfc",    # Surface albedo [%]
    "apcpsfc",     # Surface total precipitation [kg/m^2]
    "capesfc",     # Surface convective available potential energy [J/kg]
    # "cfrzravesfc", # Surface categorical freezing rain [-]
    # "cfrzrsfc",    # Surface categorical freezing rain [-]
    # "cicepavesfc", # Surface categorical ice pellets [-]
    # "cicepsfc",    # Surface categorical ice pellets [-]
    "cinsfc",      # Surface convective inhibition [J/kg]
    # "cnwatsfc",    # Surface plant canopy surface water [kg/m^2]
    # "cpofpsfc",    # Surface percent frozen precipitation [%]
    # "cpratavesfc", # Surface convective precipitation rate [kg/m^2/s]
    # "cpratsfc",    # Surface convective precipitation rate [kg/m^2/s]
    # "crainavesfc", # Surface categorical rain [-]
    # "crainsfc",    # Surface categorical rain [-]
    # "csnowavesfc", # Surface categorical snow [-]
    # "csnowsfc",    # Surface categorical snow [-]
    # "dlwrfsfc",    # Surface downward long-wave radiation flux [W/m^2]
    "dswrfsfc",    # Surface downward short-wave radiation flux [W/m^2]
    # "fldcpsfc",    # Surface field capacity [fraction]
    # "fricvsfc",    # Surface frictional velocity [m/s]
    # "gfluxsfc",    # Surface ground heat flux [W/m^2]
    "gustsfc",     # Surface wind speed (gust) [m/s]
    "hgtsfc",      # Surface geopotential height [gpm]
    # "hindexsfc",   # Surface Haines index [numeric]
    "hpblsfc",     # Surface planetary boundary layer height [m]
    # "icecsfc",     # Surface ice cover [proportion]
    # "icetksfc",    # Surface ice thickness [m]
    # "icetmpsfc",   # Surface ice temperature [K]
    # "landsfc",     # Surface land cover (0=sea, 1=land) [proportion]
    # "lftxsfc",     # Surface surface lifted index [K]
    "lhtflsfc",    # Surface latent heat net flux [W/m^2]
    "pevprsfc",    # Surface potential evaporation rate [W/m^2]
    "prateavesfc", # Surface precipitation rate [kg/m^2/s]
    "pratesfc",    # Surface precipitation rate [kg/m^2/s]
    "pressfc",     # Surface pressure [Pa]
    "sfcrsfc",     # Surface surface roughness [m]
    "shtflsfc",    # Surface sensible heat net flux [W/m^2]
    # "snodsfc",     # Surface snow depth [m]
    # "sotypsfc",    # Surface soil type [-]
    # "sunsdsfc",    # Surface sunshine duration [s]
    "tmpsfc",      # Surface temperature [K]
    # "ugwdsfc",     # Surface zonal flux of gravity wave stress [N/m^2]
    "uflxsfc",     # Surface momentum flux, u-component [N/m^2]
    "ulwrfsfc",    # Surface upward long-wave radiation flux [W/m^2]
    "uswrfsfc",    # Surface upward short-wave radiation flux [W/m^2]
    # "vgwdsfc",     # Surface meridional flux of gravity wave stress [N/m^2]
    # "vegsfc",      # Surface vegetation [%]
    "vflxsfc",     # Surface momentum flux, v-component [N/m^2]
    "vissfc",      # Surface visibility [m]
    "watrsfc",     # Surface water runoff [kg/m^2]
    # "weasdsfc",    # Surface water equivalent of accumulated snow depth [kg/m^2]
    "wiltsfc",     # Surface wilting point [fraction]
    "prmslmsl"     # Mean seal level pressure
]


def plot_skewt(T,rh,u,v,z1,lon=60,lat=60,ax=None):

    T=T.values* units.K
    rh=rh.values
    z=z1

    T=T.to(units.degC)
    Td=dewpoint_from_relative_humidity(T, rh * units.percent)
    lev=[1000.0, 975.0, 950.0, 925.0, 900.0, 850.0, 800.0, 
        750.0, 700.0, 650.0, 600.0, 550.0, 500.0, 450.0, 400.0, 350.0, 300.0, 
        250.0, 200.0, 150.0, 100.0, 70.0, 50.0, 40.0, 30.0, 20.0]
    p=lev*units.hPa
    # start_date = datetime.datetime(yy,mm,dd, tzinfo=datetime.timezone.utc)+ timedelta(hours=ft)+timedelta(hours=utc)
    if ax is None:
      fig = plt.figure(figsize=(9,12))

    else:
        fig = ax.figure

    skew = SkewT(fig, rotation=45)


    skew.plot(p, T, 'r')
    skew.plot(p, Td, 'g')
    skew.plot_barbs(p, u, v)
    skew.ax.set_ylim(1000, 100)
    # skew.ax.set_xlim(-40, 60)

    # Set some better labels than the default
    skew.ax.set_xlabel(f'Temperature ({T.units:~P})')
    skew.ax.set_ylabel(f'Pressure ({p.units:~P})')

    timestamp = f'Atmospheric sounding  at {lon:.2f}N {lat:.2f}E  '
    plt.title(timestamp)
    # plt.figtext(0.8, 0.2, "\u00A9 Subhrajit,2025",fontsize=12,fontweight='bold',
    #              horizontalalignment="right")
    # plt.figtext(0.6, 0.2, "Data Source: NCEP_NOMADS",fontsize=12,fontweight='bold',
    #              horizontalalignment="right")

    lcl_pressure, lcl_temperature = mpcalc.lcl(p[0], T[0], Td[0])
    skew.plot(lcl_pressure, lcl_temperature, 'ko', markerfacecolor='black')

    # Calculate full parcel profile and add to plot as black line
    prof = mpcalc.parcel_profile(p, T[0], Td[0]).to('degC')
    skew.plot(p, prof, 'k', linewidth=2)

    skew.shade_cin(p, T, prof, Td)
    skew.shade_cape(p, T, prof)

    # An example of a slanted line at constant T -- in this case the 0
    # isotherm
    skew.ax.axvline(0, color='c', linestyle='--', linewidth=2)

    # Add the relevant special lines
    skew.plot_dry_adiabats()
    skew.plot_moist_adiabats()
    skew.plot_mixing_lines()
    
    plt.tight_layout()

    return fig, ax 


    # # ax = plt.axes((1.01, 0.5, 0.2, 0.2))
    # # h = Hodograph(ax, component_range=60.)
    # # h.add_grid(increment=15)
    # # h.plot(u, v)
    # # print(T)

    # plt.show()
    # plt.savefig('skewt.png', dpi=300, bbox_inches='tight')


def plot_vertical_wind_shear(ds, var_name,var_name1, extent=None, time_index=0,ax=None):

    # Set default extent if none provided
    if extent is None:
        extent = [60,100,0,40]

    # Select the time slice
    ds_time = ds
    wslice = 10 

    # Extract u and v wind components at 850 hPa and 500 hPa
    u_850 = ds_time['ugrdprs']['ugrdprs'].isel(time=time_index).sel(levels=850,method='nearest') #* units('m/s')
    v_850 = ds_time['vgrdprs']['vgrdprs'].isel(time=time_index).sel(levels=850,method='nearest')# * units('m/s')
    u_500 = ds_time['ugrdprs']['ugrdprs'].isel(time=time_index).sel(levels=200,method='nearest') #* units('m/s')
    v_500 = ds_time[f'vgrdprs']['vgrdprs'].isel(time=time_index).sel(levels=200,method='nearest')# * units('m/s')

    # Calculate wind shear components
    u_shear = (u_500 - u_850)*1
 
    
    v_shear = (v_500 - v_850)*1

    # Create meshgrid for plotting
    lon, lat = u_850['lon'], u_850['lat']
    lon_2d, lat_2d = np.meshgrid(lon, lat)
    if ax is None:
        fig = plt.figure( facecolor='white')
        # ax = plt.axes(projection=ccrs.PlateCarree())
        # ax.set_extent(extent)
        # ax.patch.set_fill(False)
        # ax.add_feature(cfeature.STATES, edgecolor='white', linewidth=2)

    # Subsample for quiver density
    wslice = slice(1, None, 7)

    # Quiver plots
    ax.quiver(lon_2d[wslice, wslice], lat_2d[wslice, wslice],
              u_850[wslice, wslice], v_850[wslice, wslice],
              headlength=4, headwidth=3, angles='xy', scale_units='xy',
              color='gold', scale=10, label='850 hPa wind')

    ax.quiver(lon_2d[wslice, wslice], lat_2d[wslice, wslice],
              u_500[wslice, wslice], v_500[wslice, wslice],
              headlength=4, headwidth=3, angles='xy', scale_units='xy',
              color='cornflowerblue', scale=8, label='200 hPa wind')

    ax.quiver(lon_2d[wslice, wslice], lat_2d[wslice, wslice],
              u_shear[wslice, wslice], v_shear[wslice, wslice],
              headlength=4, headwidth=3, angles='xy', scale_units='xy',
              scale=10, color='deeppink', label='200–850 hPa shear')

    # Add legend and title only if using standalone figure
    if ax.get_figure():
        ax.legend(loc='lower right',bbox_to_anchor=(1.3, -0.01),fontsize=8)
        # ax.set_title('850/500 hPa Wind & Vertical Shear', color='white',)

    return ax



gfs_vars=gfs_pressure_variables + surface_variables

#["tmpprs", "rhprs", 'rh2m','pratesfc',     'apcpsfc','prmslmsl',       "ugrdprs","ugrdprs", "vgrdprs",'uflxsfc']


st.set_page_config(layout="wide")
st.title(" GFS Viewer")
st.markdown("""
  <style>
    .block-container {
      padding-top: 1.9rem;
      padding-left:10px;
    }
  </style>
""", unsafe_allow_html=True)

# with st.expander("Map selection"):
#   st.markdown(" **Draw Bounding Box on Map**")

#   m = folium.Map(location=[20, 80], zoom_start=4)


#   # Add drawing control
#   draw = Draw(export=True, draw_options={
#     'polyline': False,
#     'circle': False,
#     'polygon': False,
#     'marker': True,
#     'circlemarker': False,
#     'rectangle': True,
#   })
#   draw.add_to(m)

#   output = st_folium(m, height=600, width=900, key="bbox_draw")
  
#   bbox_coords = None
#   if output and output.get("last_active_drawing") and output["last_active_drawing"]["geometry"]["type"] == "Polygon":
#     coords = output["last_active_drawing"]["geometry"]["coordinates"][0]
#     lons = [c[0] for c in coords]
#     lats = [c[1] for c in coords]
#     lon_min, lon_max = min(lons), max(lons)
#     lat_min, lat_max = min(lats), max(lats)
#     bbox_coords = (lon_min, lon_max, lat_min, lat_max)
#     st.success(f" Bounding Box Selected:\nLon: {lon_min:.2f}–{lon_max:.2f}, Lat: {lat_min:.2f}–{lat_max:.2f}")
    
#   else:
#     st.warning(" Please draw a rectangular bounding box on the map.")
    

# if "show_map" not in st.session_state:
#     st.session_state["show_map"] = True
col1, col2,col3,col4 = st.columns([20, 40,20,25])

with st.sidebar:
    st.subheader("Parameter setting")  # Optional title

    with st.expander("📅 Forecast Parameters", expanded=False):
        selected_date = st.date_input("Forecast Start Date", datetime.date.today())
        selected_utc = st.selectbox("UTC Initialization Hour", [0, 6, 12, 18])
        forecast_hour = st.slider("Forecast Length (Hours)", 1, 120, 36)

    with st.expander("🌐 Geographic Bounds", expanded=False):
        lon_min = st.number_input("Longitude Min", value=60.0)
        lon_max = st.number_input("Longitude Max", value=100.0)
        lat_min = st.number_input("Latitude Min", value=0.0)
        lat_max = st.number_input("Latitude Max", value=40.0)
        bbox_coords = (lon_min, lon_max, lat_min, lat_max)

    with st.expander(":variables Variables", expanded=True):
        variables = st.multiselect(
            "Select Variable(s)",
            gfs_vars,
            ['prmslmsl','tmpprs','rhprs','hgtprs','ugrdprs','vgrdprs']
        )
       

        pressure_level_vars = [v for v in variables if v in gfs_pressure_variables]
        surface_vars = [v for v in variables if v in surface_variables]

    st.markdown(selected_date)


    # Fetch Data Button at the bottom of sidebar
    fetch = st.button("Fetch Data")

    # Data fetching logic
    if fetch:
        st.session_state["show_map"] = False 
        with st.spinner("Fetching and processing data..."):
            ds_dict = {}
            # Fetch surface variables
            for var in surface_vars:
                ds = get_data_preprocess(
                    date=selected_date,
                    utc=selected_utc,
                    ft=forecast_hour,
                    var=var,
                    pvar="no",
                    lon_range=(bbox_coords[0], bbox_coords[1]), 
                    lat_range=(bbox_coords[2], bbox_coords[3])
                )
                ds_dict[var] = ds
            print("done surface_var")

            # Fetch pressure-level variables
            for var in pressure_level_vars:
                ds = get_data_preprocess(
                    date=selected_date,
                    utc=selected_utc,
                    ft=forecast_hour,
                    var=var,
                    pvar="yes",
                    lon_range=(bbox_coords[0], bbox_coords[1]), 
                    lat_range=(bbox_coords[2], bbox_coords[3])
                )
                ds_dict[var] = ds
                print("done pressure_var")

            # Save to session state
            st.session_state["ds_dict"] = ds_dict
            st.session_state["variables"] = variables
            st.session_state["pressure_level_vars"] = pressure_level_vars
            st.session_state["surface_vars"] = surface_vars
            st.success("All variables fetched!")

            # Download button
            if "ds_dict" in st.session_state:
                merged_ds = xr.merge([ds for ds in st.session_state["ds_dict"].values()])

                with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmpfile:
                    merged_ds.to_netcdf(tmpfile.name)
                    tmpfile.flush()
                    with open(tmpfile.name, "rb") as f:
                        st.download_button(
                            data=f,
                            label="📥 Download Data (NetCDF)",
                            file_name="gfs_data.nc",
                            mime="application/x-netcdf"
                        )
with col1:

     with st.expander("🎨 Visualization Options", expanded=True):
        colormap = st.selectbox(
            "Select Colormap",
            options=["viridis", "plasma", "inferno", "magma", "cividis", "coolwarm", "jet", "turbo"],
            index=6,
        )
        add_windshear = st.checkbox("Overlay Wind Shear", value=False)
        add_pressure_contours = st.checkbox("Overlay Surface Pressure (pressfc)", value=False)
        rob = st.checkbox("Robust set?", value=True)
        

                      


with col2:
  sns.set_theme( style='ticks',font="arial", font_scale=1.75)
  color = sns.color_palette('tab10')

 

  if "ds_dict" in st.session_state:
    ds_dict = st.session_state["ds_dict"]
    variables = st.session_state["variables"]
    
    

    viewable_vars = [v for v in variables if v != "prmslmsl"]
    selected_var = st.selectbox(" Select Variable to View", viewable_vars)

    ds = ds_dict[selected_var]

    if selected_var == pressure_level_vars:
       is_pressure_level = st.checkbox("Is this a pressure-level variable?", value=False)
    else:
       is_pressure_level = st.checkbox("Is this a pressure-level variable?", value=True)
    
    st.session_state["is_pressure_level"] = is_pressure_level

    if selected_var == pressure_level_vars:
      is_pressure_level = st.session_state["is_pressure_level"]
   
       
    

    st.markdown(f" Plot of `{selected_var}`")

    if is_pressure_level:
      time_idx = st.slider("Time Index", 1, len(ds.time) - 1, 1)
      level_idx = st.slider("Pressure Level Index", 0, len(ds.levels) - 1, 0)
      data = ds[selected_var].isel(time=time_idx, levels=level_idx)
    else:
      # time_idx = st.slider("Time Index", 0, len(ds.time) - 1, 0)
      time_idx = st.slider(" Time Index", 1, len(ds.time) - 1, key="time_slider")
      data = ds[selected_var].isel(time=time_idx)      
      
    if add_windshear:
      if "ugrdprs" not in st.session_state["ds_dict"]:
        st.warning(" 'ugrdprs' not loaded — add it to your variable list to plot contours.")
        add_pressure_contours = False # disable if not available
      else:
        uwind = st.session_state["ds_dict"]
        # vwind = st.session_state["ds_dict"]["vgrdprs"]
        wind_data = uwind#.isel(time=time_idx)

    dat1 = data.copy()
    if selected_var in ["pratesfc"]:
      dat1 = dat1 * 3600
      dat1 = dat1.where(dat1 >= 0.01)
      # dat1['pratesfc'] = xr.where(dat1['pratesfc'],dat1['pratesfc'] >= 0.1, 0) 
    elif selected_var in ["apcpsfc"]:
      dat1 = dat1.where(dat1 >= 0.01)


    else:
      dat1 = data


    st.session_state["dat1"] = dat1
    if add_pressure_contours:
      if "prmslmsl" not in st.session_state["ds_dict"]:
        st.warning(" 'prmslmsl' not loaded — add it to your variable list to plot contours.")
        add_pressure_contours = False # disable if not available
      else:
        pressfc_ds = st.session_state["ds_dict"]["prmslmsl"]
        pressure_data = pressfc_ds["prmslmsl"].isel(time=time_idx)/100

    


    fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})
    mm=dat1.plot.contourf(ax=ax, cmap=colormap, robust=rob, 
              transform=ccrs.PlateCarree(),
                  cbar_kwargs={
                      "orientation": "vertical",
                      "shrink": 0.6,
                      "aspect": 20,
                      "pad": 0.005,  "label":selected_var  })
    cbar = mm.colorbar
    cbar.ax.tick_params(labelsize=12)
    cbar.set_label(selected_var, fontsize=14, fontweight='bold',labelpad=-0.5)

    title = f"{str(dat1.time.values)[:-13]}"  # Adjust this based on your data structure
    ax.set_title(title,fontsize=12)
    levels=(bbox_coords[1]-bbox_coords[0])/2
    if add_pressure_contours:
      cs = pressure_data.plot.contour(ax=ax, colors='black', linewidths=1,
                                       levels=levels+1, transform=ccrs.PlateCarree())
      ax.clabel(cs, fontsize=8)  # Set font size to 3
      title = f"{str(dat1.time.values)[:-13]} and overlay MSLP"  # Adjust this based on your data structure
      ax.set_title(title,fontsize=12)

    if add_windshear:

      cs= plot_vertical_wind_shear(wind_data,'ugrdprs','vgrdprs',extent=bbox_coords,
                                   time_index=time_idx,ax=ax)
      title = f"{str(dat1.time.values)[:-13]} and overlay Wind shear , vector "  # Adjust this based on your data structure
      ax.set_title(title,fontsize=12)


    ax.coastlines(resolution='50m')
    gl = ax.gridlines(draw_labels=True)
    gl.top_labels = False
    gl.right_labels = False
    # gl.xlines = True
    # gl.ylines = True

    gl.ylocator = LatitudeLocator()

    gl.xformatter = LongitudeFormatter()
    gl.yformatter = LatitudeFormatter()

    # gl.xlocator = mticker.MaxNLocator(11)
    # gl.ylocator = mticker.MaxNLocator(11)

    XTEXT_SIZE = 8
    YTEXT_SIZE = 8

    gl.xlabel_style = {'size': XTEXT_SIZE, 'color': 'k', 'rotation':45, 'ha':'right'}
    gl.ylabel_style = {'size':YTEXT_SIZE, 'color': 'k', 'weight': 'normal'}
    with st.expander("🎨 Sounder ", expanded=True):
        st.pyplot(fig)







with col3:
  if "ds_dict" in st.session_state:
    # with st.expander(" Show Time Series and Data Table"):
    st.subheader(" Time Series at Location")
    lat1 = st.number_input("Latitude ", min_value=-90.0, max_value=90.0, value=20.0, step=0.1)
    lon1 = st.number_input("Longitude ", min_value=0.0, max_value=360.0, value=80.0, step=0.1)

    if selected_var == pressure_level_vars:
      is_pressure_level = st.session_state["is_pressure_level"]

    # Extract time series at nearest point
    if is_pressure_level:
        ts_data = ds[selected_var].isel(levels=level_idx).sel(lat=lat1, lon=lon1,method='nearest')[1:]
        ts_data_1= ds[selected_var].isel(time=time_idx).sel(lat=lat1, lon=lon1,method='nearest')[1:]
        
        



        # ts_data_1.plot(ax=ax3, y='levels',marker='*',color='b')
        # ax3.set_title(f"Time Series of `{selected_var}` at ({lat1:.2f}, {lon1:.2f})")
        # ax3.set_xlabel(selected_var)
        # ax3.set_ylabel("level")
        # plt.gca().invert_yaxis()
        # st.pyplot(fig3)

    else:
        ts_data = ds[selected_var].sel(lat=lat1, lon=lon1,method='nearest')[1:]

    # Scale time series if needed
    if selected_var == "pratesfc":
        ts_data = ts_data * 3600
        ts_data = ts_data.where(ts_data >= 0.1)
    elif selected_var == "apcpsfc":
        ts_data = ts_data.where(ts_data >= 0.1)
    else:
        ts_data=ts_data
    
    with st.expander("🎨 Timeseries  Options", expanded=False):
    # st.pyplot(fig2)
      fig2, ax2 = plt.subplots()
      ts_data.plot(ax=ax2, marker='o')
      ax2.set_title(f"Time Series of `{selected_var}` at ({lat1:.2f}, {lon1:.2f})")
      ax2.set_xlabel("Time")
      ax2.set_ylabel(selected_var)
      st.pyplot(fig2)
    # st.dataframe(ts_data.to_dataframe().reset_index())
with col4:
  with st.expander("🎨 Sounder ", expanded=True):

    T=ds_dict['tmpprs']['tmpprs'].isel(time=time_idx).sel(lat=lat1, lon=lon1,method='nearest')[:]
    rh=ds_dict['rhprs']['rhprs'].isel(time=time_idx).sel(lat=lat1, lon=lon1,method='nearest')[:]
    u=ds_dict['ugrdprs']['ugrdprs'].isel(time=time_idx).sel(lat=lat1, lon=lon1,method='nearest')[:]
    v=ds_dict['vgrdprs']['vgrdprs'].isel(time=time_idx).sel(lat=lat1, lon=lon1,method='nearest')[:]
    z11=ds_dict['hgtprs']['hgtprs'].isel(time=time_idx).sel(lat=lat1, lon=lon1,method='nearest')[:]
    

    fig = plt.figure(figsize=(9, 12))
    fig4, ax = plot_skewt(T, rh, u, v, z1=z11,lon=lon1, lat=lat1, ax=None)

    # st.markdown(fig4)
    st.pyplot(fig4)

    

    # st.dataframe(ts_data1.to_dataframe().reset_index())

