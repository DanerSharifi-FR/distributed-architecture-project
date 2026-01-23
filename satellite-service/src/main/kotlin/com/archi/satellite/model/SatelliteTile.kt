package com.archi.satellite.model

import com.archi.satellite.model.SatelliteTile.Companion.DOCUMENT_NAME
import com.archi.satellite.service.OwmLayer
import org.bson.types.ObjectId
import org.springframework.data.annotation.Id
import org.springframework.data.mongodb.core.mapping.Document

typealias Layers = Map<OwmLayer, String>

@Document(collection = DOCUMENT_NAME)
class SatelliteTile(
    @Id
    val impactId: ObjectId,
    val layers: Layers,
) {
    companion object {
        const val DOCUMENT_NAME = "satellite-tile"
    }
}