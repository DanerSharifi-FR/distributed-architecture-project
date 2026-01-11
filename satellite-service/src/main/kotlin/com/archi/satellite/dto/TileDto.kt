package com.archi.satellite.dto

import com.archi.satellite.service.OwmLayer

typealias LayersDto = Map<OwmLayer, String>

class TileDto(
    val layers: LayersDto
)