package com.archi.satellite.service

import com.archi.satellite.dto.TileDto
import com.archi.satellite.mapper.TileMapper
import com.archi.satellite.model.Impact
import com.archi.satellite.model.SatelliteTile
import com.archi.satellite.repository.ImpactRepository
import com.archi.satellite.repository.SatelliteTileRepository
import com.archi.satellite.util.ServicesCleaner
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.bson.types.ObjectId
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import kotlin.test.Test

class SatelliteServiceTest: ServicesCleaner() {
    private val fileService = mockk<FileService>()

    private val owmService = mockk<OwmService>()

    private val satelliteTileRepository = mockk<SatelliteTileRepository>()

    private val impactRepository = mockk<ImpactRepository>()

    private val tileMapper = TileMapper()

    private val satelliteService = SatelliteService(
        fileService,
        owmService,
        tileMapper,
        satelliteTileRepository,
        impactRepository,
    )

    @Test
    fun `should capture satellite tile correctly`() = runTest {
        val impact = Impact(
            ObjectId(),
            Impact.FlightPosition(8.0, 9.0)
        )
        val impactId = impact.id.toString()
        val (lat, lon) = impact.position.run { Pair(latitude, longitude) }
        val picture = "/url/to/file"
        val layers = mapOf(
            OwmLayer.PRESSURE_NEW to byteArrayOf(),
            OwmLayer.WIND_NEW to byteArrayOf(),
        )

        coEvery { fileService.putTileLayerPicture(impactId, any(), any()) } returns picture
        coEvery { owmService.getTileLayersPicture(lat, lon) } returns layers
        coEvery { impactRepository.findById(impact.id) } returns impact
        coEvery { satelliteTileRepository.save(any()) } answers {firstArg()}

        val tileDto: TileDto = satelliteService.captureSatelliteTile(impactId)

        assertEquals(layers.size, tileDto.layers.size)

        layers.forEach { (layer) ->
            val foundLayer = tileDto.layers[layer]
            assertNotNull(foundLayer)
            assertEquals(picture, foundLayer)
        }

        coVerify(exactly = layers.size) { fileService.putTileLayerPicture(impactId, any(), any()) }
        coVerify(exactly = 1) { owmService.getTileLayersPicture(lat, lon) }
        coVerify(exactly = 1) { impactRepository.findById(impact.id) }
        coVerify(exactly = 1) { satelliteTileRepository.save(any()) }
    }

    @Test
    fun `should retrieve a satellite tile correctly`() = runTest {
        val tile = SatelliteTile(ObjectId(), mapOf(OwmLayer.WIND_NEW to "/path/to/file"))

        coEvery { satelliteTileRepository.findById(tile.impactId) } returns tile
        val tileDto = satelliteService.retrieveSatelliteTile(tile.impactId.toString())

        assertEquals(tileDto.layers.size, tile.layers.size)
        tile.layers.forEach { (layer, file) ->
            kotlin.test.assertEquals(file, tileDto.layers[layer])
        }

        coVerify(exactly = 1) { satelliteTileRepository.findById(tile.impactId) }
    }
}