package com.archi.satellite.mapper

import com.archi.satellite.dto.LayersDto
import com.archi.satellite.dto.TileDto
import org.springframework.stereotype.Component

@Component
class TileMapper {
    fun toTileDto(layersDto: LayersDto) = TileDto(layersDto)
}