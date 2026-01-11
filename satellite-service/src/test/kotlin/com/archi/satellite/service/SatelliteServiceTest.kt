package com.archi.satellite.service

import com.archi.satellite.dto.CoordinatesDto
import com.archi.satellite.dto.TileDto
import com.archi.satellite.mapper.TileMapper
import com.archi.satellite.util.ServicesCleaner
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import kotlin.test.Test

class SatelliteServiceTest: ServicesCleaner() {
    private val fileService = mockk<FileService>()

    private val owmService = mockk<OwmService>()

    private val tileMapper = TileMapper()

    private val satelliteService = SatelliteService(fileService, owmService, tileMapper)

    @Test
    fun `should capture satellite tile correctly`() = runTest {
        val impactId = "id"
        val lat = 8.0
        val lon = 9.0
        val picture = "/url/to/file"
        val layers = mapOf(
            OwmLayer.PRESSURE_NEW to byteArrayOf(),
            OwmLayer.WIND_NEW to byteArrayOf(),
        )

        coEvery { fileService.putTileLayerPicture(impactId, any(), any()) } returns picture
        coEvery { owmService.getTileLayersPicture(lat, lon) } returns layers

        val tileDto: TileDto = satelliteService.captureSatelliteTile(impactId, CoordinatesDto(lat, lon))

        assertEquals(layers.size, tileDto.layers.size)

        layers.forEach { (layer) ->
            val foundLayer = tileDto.layers[layer]
            assertNotNull(foundLayer)
            assertEquals(picture, foundLayer)
        }

        coVerify(exactly = layers.size) { fileService.putTileLayerPicture(impactId, any(), any()) }
        coVerify(exactly = 1) { owmService.getTileLayersPicture(lat, lon) }
    }
}