import cdsapi

c = cdsapi.Client()

year = "2009"
month = "01"
c.retrieve(
    "seasonal-monthly-single-levels",
    {
        "format": "grib",
        "originating_centre": "ecmwf",
        "system": "51",
        "variable": [
            "2m_temperature",
            "total_precipitation",
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
            "2m_dewpoint_temperature",
            "mean_sea_level_pressure",
        ],
        "product_type": "monthly_mean",
        "year": year,
        "month": month,
        "leadtime_month": [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
        ],
        "area": [
            48,
            -30,
            -7,
            85,
        ],
    },
    f"seas5_surface_monthly_{year}_{month}.grib",
)
