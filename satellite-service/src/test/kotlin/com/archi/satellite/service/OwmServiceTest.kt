package com.archi.satellite.service

import com.archi.satellite.util.ServicesCleaner
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import io.mockk.spyk
import io.mockk.verify
import kotlinx.coroutines.test.runTest
import org.bouncycastle.util.test.SimpleTest.runTest
import org.springframework.beans.factory.annotation.Autowired
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull

class OwmServiceTest @Autowired constructor(
    owmService: OwmService
): ServicesCleaner() {
    private val owmService = spyk<OwmService>(owmService)

    @Test
    fun `should compute tiles coordinates correctly`() {
        // Neutral
        assertEquals(2 to 2, owmService.getTilesCoordinates(0.0, 0.0))

        // Max range
        assertEquals(3 to 0, owmService.getTilesCoordinates(90.0, 180.0))
        assertEquals(0 to 0, owmService.getTilesCoordinates(90.0, -180.0))
        assertEquals(3 to 3, owmService.getTilesCoordinates(-90.0, 180.0))
        assertEquals(0 to 3, owmService.getTilesCoordinates(-90.0, -180.0))

        // Semi range
        assertEquals(3 to 1, owmService.getTilesCoordinates(45.0, 90.0))
        assertEquals(1 to 1, owmService.getTilesCoordinates(45.0, -90.0))
        assertEquals(3 to 2, owmService.getTilesCoordinates(-45.0, 90.0))
        assertEquals(1 to 2, owmService.getTilesCoordinates(-45.0, -90.0))
    }

    @Test
    fun `should retrieve tile layer successfully`() = runTest {
        val lat = 8.0
        val lon = 9.0

        every { owmService.getTilesCoordinates(lat, lon) } returns (2 to 3)

        owmService.getTileLayerPicture(OwmLayer.WIND_NEW, lat, lon)

        verify(exactly = 1) { owmService.getTilesCoordinates(lat, lon) }
    }

    @Test
    fun `should retrieve tile layers correctly`() = runTest {
        val layersCount = OwmLayer.entries.size
        val lat = 8.0
        val lon = 9.0

        val pictures = mutableListOf<ByteArray>()

        coEvery { owmService.getTileLayerPicture(any(), lat, lon) } answers {
            byteArrayOf().also {
                pictures.add(it)
            }
        }

        val layers = owmService.getTileLayersPicture(lat, lon)

        assertEquals(layersCount, layers.size)

        OwmLayer.entries.forEach { layer ->
            val picture = layers[layer]
            assertNotNull(picture)
            assertNotNull(pictures.find({ it === picture }))

            coVerify(exactly = 1) { owmService.getTileLayerPicture(layer, lat, lon) }
        }
    }
}