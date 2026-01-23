package com.archi.satellite.mapper

import com.archi.satellite.config.SatelliteProperties
import com.archi.satellite.dto.TileDto
import com.archi.satellite.model.Layers
import com.archi.satellite.model.SatelliteTile
import com.archi.satellite.service.FileService
import org.bson.types.ObjectId
import org.springframework.stereotype.Component

@Component
class TileMapper(
    properties: SatelliteProperties,
) {
    val apiUrl = properties.minio.publicEndpoint
    fun toTileDto(tile: SatelliteTile) = TileDto(tile.layers.mapValues { (_, file) ->
        "$apiUrl/$file"
    })
    fun toTile(impactId: ObjectId, layers: Layers) = SatelliteTile(impactId, layers)
}