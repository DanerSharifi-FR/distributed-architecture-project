package com.archi.satellite.service

import com.archi.satellite.dto.TileDto
import com.archi.satellite.mapper.TileMapper
import com.archi.satellite.model.SatelliteTile
import com.archi.satellite.repository.ImpactRepository
import com.archi.satellite.repository.SatelliteTileRepository
import org.bson.types.ObjectId
import org.springframework.http.HttpStatus
import org.springframework.stereotype.Service
import org.springframework.web.server.ResponseStatusException

@Service
class SatelliteService(
    private val fileService: FileService,
    private val owmService: OwmService,
    private val tileMapper: TileMapper,
    private val satelliteTileRepository: SatelliteTileRepository,
    private val impactRepository: ImpactRepository,
) {
    suspend fun captureSatelliteTile(impactId: String): TileDto {
        val id = ObjectId(impactId)
        val impact = impactRepository.findById(id)
            ?: throw ResponseStatusException(HttpStatus.NOT_FOUND, "Impact with id $id not found")
        val layers = impact.position.run { owmService.getTileLayersPicture(latitude, longitude) }
            .mapValues { (layer, picture) -> fileService.putTileLayerPicture(impactId, layer, picture)}
        val tile: SatelliteTile = tileMapper.toTile(layers)
        satelliteTileRepository.save(tile)
        return tileMapper.toTileDto(tile)
    }

    suspend fun retrieveSatelliteTile(impactId: String): TileDto {
        val id = ObjectId(impactId)
        val tile = satelliteTileRepository.findById(id) ?: throw ResponseStatusException(
            HttpStatus.NOT_FOUND,
            "Satellite with id $impactId not found"
        )
        return tileMapper.toTileDto(tile)
    }
}