package com.archi.satellite.model

import com.archi.satellite.model.Impact.Companion.DOCUMENT_NAME
import org.bson.types.ObjectId
import org.springframework.data.annotation.Id
import org.springframework.data.mongodb.core.mapping.Document

@Document(collection = DOCUMENT_NAME)
class Impact(
    @Id
    val id: ObjectId,
    val position: FlightPosition,
) {
    companion object {
        const val DOCUMENT_NAME = "impact"
    }

    class FlightPosition(
        val latitude: Double,
        val longitude: Double,
    )
}