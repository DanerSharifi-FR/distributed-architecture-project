package com.archi.satellite.controller

import com.archi.satellite.dto.CoordinatesDto
import com.archi.satellite.dto.TileDto
import com.archi.satellite.service.OwmLayer
import com.archi.satellite.util.ServicesCleaner
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
): ServicesCleaner() {
    fun webTestClientCreateSatellite(
        impactId: String = ObjectId().toString(),
        lat: Double = 90.0,
        lon: Double = -180.0
    ): WebTestClient.ResponseSpec = webTestClient
        .put()
        .uri("/satellites/tiles/impacts/${impactId}")
        .bodyValue(CoordinatesDto(lat, lon))
        .exchange()

    @Test
    fun `should not create satellite tile if id is incorrect`() {
        webTestClientCreateSatellite(impactId = "id")
            .expectStatus().isBadRequest
    }

    @Test
    fun `should not create satellite tile if longitude is greater than 180`() {
        webTestClientCreateSatellite(lon = 181.0)
            .expectStatus().isBadRequest
    }

    @Test
    fun `should not create satellite tile if latitude is greater than 90`() {
        webTestClientCreateSatellite(lat = 91.0)
            .expectStatus().isBadRequest
    }

    @Test
    fun `should not create satellite tile if longitude is less than -180`() {
        webTestClientCreateSatellite(lon = -181.0)
            .expectStatus().isBadRequest
    }

    @Test
    fun `should not create satellite tile if latitude is less than -90`() {
        webTestClientCreateSatellite(lat = -91.0)
            .expectStatus().isBadRequest
    }

    @Test
    fun `should create satellite tile of an impact correctly`() {
        val tileDto = webTestClientCreateSatellite()
            .expectStatus().isOk
            .expectBody<TileDto>()
            .returnResult().responseBody

        assertNotNull(tileDto)
        assertEquals(tileDto.layers.size, OwmLayer.entries.size)
        OwmLayer.entries.forEach { layer ->
            assertNotNull(tileDto.layers[layer])
        }
    }
}