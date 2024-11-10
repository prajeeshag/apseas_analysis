import cdsapi

c = cdsapi.Client()

year = list(map(str, list(range(2000, 2024))))
month = list(map(str, list(range(1, 13))))
c.retrieve(
    "seasonal-monthly-single-levels",
    {
        "format": "grib",
        "originating_centre": "ecmwf",
        "system": "51",
        "variable": [
            "2m_temperature",
        ],
        "product_type": ["monthly_mean"],
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
    "t2mean_seas5_monthly_2000-2023.grib",
)
