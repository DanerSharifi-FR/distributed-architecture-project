package com.archi.satellite.service

import com.archi.satellite.dto.CoordinatesDto
import com.archi.satellite.dto.TileDto
import com.archi.satellite.mapper.TileMapper
import org.springframework.stereotype.Service

@Service
class SatelliteService(
    private val fileService: FileService,
    private val owmService: OwmService,
    private val tileMapper: TileMapper,
) {
    suspend fun captureSatelliteTile(impactId: String, coordinatesDto: CoordinatesDto): TileDto {
        val layers = coordinatesDto
            .run { owmService.getTileLayersPicture(lat, lon) }
            .mapValues { (layer, picture) -> fileService.putTileLayerPicture(impactId, layer, picture)}
        return tileMapper.toTileDto(layers)
    }
}