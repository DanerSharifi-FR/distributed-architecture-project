package com.archi.satellite.repository

import com.archi.satellite.model.SatelliteTile
import org.bson.types.ObjectId
import org.springframework.data.repository.kotlin.CoroutineCrudRepository
import org.springframework.stereotype.Repository

@Repository
interface SatelliteTileRepository: CoroutineCrudRepository<SatelliteTile, ObjectId>