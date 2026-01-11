package com.archi.satellite.dto

import jakarta.validation.constraints.DecimalMax
import jakarta.validation.constraints.DecimalMin

class CoordinatesDto (
    @field:DecimalMin(value = "-90.0", message = "Latitude must be >= -90")
    @field:DecimalMax(value = "90.0", message = "Latitude must be <= 90")
    val lat: Double,

    @field:DecimalMin(value = "-180.0", message = "Longitude must be >= -180")
    @field:DecimalMax(value = "180.0", message = "Longitude must be <= 180")
    val lon: Double,
)