package com.archi.satellite.controller

import com.archi.satellite.dto.TileDto
import com.archi.satellite.model.Impact
import com.archi.satellite.model.SatelliteTile
import com.archi.satellite.repository.ImpactRepository
import com.archi.satellite.repository.SatelliteTileRepository
import com.archi.satellite.service.OwmLayer
import com.archi.satellite.util.ServicesCleaner
import kotlinx.coroutines.test.runTest
import org.bson.types.ObjectId
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient
import org.springframework.test.web.reactive.server.WebTestClient
import org.springframework.test.web.reactive.server.expectBody
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull

@AutoConfigureWebTestClient
class SatelliteControllerTest @Autowired constructor(
    private val webTestClient: WebTestClient,
    @Autowired private val impactRepository: ImpactRepository,
    @Autowired private val satelliteTileRepository: SatelliteTileRepository,
): ServicesCleaner() {
    suspend fun createImpact(
        id: ObjectId = ObjectId(),
        lat: Double = 90.0,
        lon: Double = -180.0
    ): Impact = Impact(
        id,
        Impact.FlightPosition(lat, lon)
    ).also { impactRepository.save(it) }

    fun webTestClientCreateSatellite(
        impactId: String,
    ): WebTestClient.ResponseSpec = webTestClient
        .put()
        .uri("/satellites/tiles/impacts/$impactId")
        .exchange()

    fun webTestClientRetrieveSatellite(
        impactId: String,
    ): WebTestClient.ResponseSpec = webTestClient
        .get()
        .uri("/satellites/tiles/impacts/$impactId")
        .exchange()

    @Test
    fun `should not create satellite tile if id is incorrect`() = runTest {
        createImpact()
        webTestClientCreateSatellite("id")
            .expectStatus().isBadRequest
    }

    @Test
    fun `should not create satellite tile and return 404 if an impact does not exist`() = runTest {
        webTestClientCreateSatellite(ObjectId().toString())
            .expectStatus().isNotFound
    }

    @Test
    fun `should create satellite tile of an impact correctly`() = runTest {
        val impact = createImpact()
        val tileDto = webTestClientCreateSatellite(impact.id.toString())
            .expectStatus().isOk
            .expectBody<TileDto>()
            .returnResult().responseBody

        assertNotNull(tileDto)
        assertEquals(tileDto.layers.size, OwmLayer.entries.size)
        OwmLayer.entries.forEach { layer ->
            assertNotNull(tileDto.layers[layer])
        }
    }

    @Test
    fun `should not retrieve satellite tile if id is incorrect`() = runTest {
        createImpact()
        webTestClientRetrieveSatellite("id")
            .expectStatus().isBadRequest
    }

    @Test
    fun `should not retrieve satellite tile and return 404 if it does not exist`() = runTest {
        webTestClientRetrieveSatellite(ObjectId().toString())
            .expectStatus().isNotFound
    }

    @Test
    fun `should retrieve a satellite tile of an impact correctly`() = runTest {
        val impact = createImpact()
        val tile = SatelliteTile(impact.id, mapOf(OwmLayer.WIND_NEW to "/path/to/file"))
        satelliteTileRepository.save(tile)
        val tileDto = webTestClientRetrieveSatellite(impact.id.toString())
            .expectStatus().isOk
            .expectBody<TileDto>()
            .returnResult().responseBody

        assertNotNull(tileDto)
        assertEquals(tile.layers.size, tileDto.layers.size)
        tile.layers.entries.forEach { (layer, file) ->
            assertEquals(file, tileDto.layers[layer])
        }
    }
}