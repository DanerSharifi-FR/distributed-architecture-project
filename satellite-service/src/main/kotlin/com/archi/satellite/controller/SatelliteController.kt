
package com.archi.satellite.controller

import com.archi.satellite.dto.TileDto
import com.archi.satellite.service.SatelliteService
import com.archi.satellite.validator.ValidId
import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.responses.ApiResponse
import io.swagger.v3.oas.annotations.responses.ApiResponses
import jakarta.validation.Valid
import org.bson.types.ObjectId
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PutMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

// TODO add authentication

@RestController
@RequestMapping("/satellites")
class SatelliteController(private val satelliteService: SatelliteService) {
    @GetMapping("/tiles/impacts/{impactId}")
    @Operation(summary = "Retrieve satellite tile of an impact")
    @ApiResponses(
        ApiResponse(responseCode = "200"),
        ApiResponse(responseCode = "404", description = "The satellite tile with this impactId does not exist")
    )
    suspend fun getSatelliteTile(
        @PathVariable @ValidId impactId: String
    ): TileDto = satelliteService.retrieveSatelliteTile(impactId)

    @PutMapping("/tiles/impacts/{impactId}")
    @Operation(summary = "Create satellite tile of an impact")
    @ApiResponses(
        ApiResponse(responseCode = "200"),
        ApiResponse(responseCode = "404", description = "The impact with this id does not exist")
    )
    suspend fun putSatelliteTile(
        @PathVariable @ValidId impactId: String,
    ): TileDto = satelliteService.captureSatelliteTile(impactId)
}