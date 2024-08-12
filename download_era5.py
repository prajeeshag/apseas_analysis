import cdsapi

c = cdsapi.Client()

year = 2009

c.retrieve(
    "reanalysis-era5-single-levels-monthly-means",
    {
        "format": "grib",
        "product_type": "monthly_averaged_reanalysis",
        "variable": [
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
            "2m_dewpoint_temperature",
            "2m_temperature",
            "mean_sea_level_pressure",
            "mean_total_precipitation_rate",
        ],
        "year": year,
        "month": [
            "01",
            "02",
            "03",
            "04",
            "05",
            "06",
            "07",
            "08",
            "09",
            "09",
            "10",
            "11",
            "12",
        ],
        "time": "00:00",
        "area": [
            48,
            -30,
            -7,
            85,
        ],
    },
    f"era5_surface_fields_{year}.grib",
)
