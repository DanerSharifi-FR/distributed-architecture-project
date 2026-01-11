package com.archi.satellite.service

import com.archi.satellite.config.SatelliteProperties
import com.archi.satellite.util.ServicesCleaner
import io.mockk.InternalPlatformDsl.toArray
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.web.reactive.function.client.WebClient
import org.springframework.web.reactive.function.client.awaitBody
import java.net.URL
import javax.imageio.ImageIO
import kotlin.test.assertEquals

class FileServiceTest @Autowired constructor(
    private val fileService: FileService,
    private val properties: SatelliteProperties,
    private val webClient: WebClient,
): ServicesCleaner() {
    @Test
    fun `should store a tile layer correctly`() = runTest {
        val picture = byteArrayOf(8)

        val key = fileService.putTileLayerPicture("id", OwmLayer.WIND_NEW, picture)

        val foundPicture = webClient
            .get()
            .uri("${properties.minio.endpoint}/$key")
            .retrieve()
            .awaitBody<ByteArray>()

        assertEquals(picture.size, foundPicture.size)
        picture.forEachIndexed { index, expectedByte -> assertEquals(expectedByte, foundPicture[index]) }
    }
}