package com.archi.satellite.mapper

import com.archi.satellite.dto.TileDto
import com.archi.satellite.model.Layers
import com.archi.satellite.model.SatelliteTile
import org.bson.types.ObjectId
import org.springframework.stereotype.Component

@Component
class TileMapper {
    fun toTileDto(tile: SatelliteTile) = TileDto(tile.layers)
    fun toTile(layers: Layers) = SatelliteTile(ObjectId(), layers)
}