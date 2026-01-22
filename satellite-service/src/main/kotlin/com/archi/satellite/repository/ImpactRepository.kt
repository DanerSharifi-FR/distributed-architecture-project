package com.archi.satellite.repository

import com.archi.satellite.model.Impact
import org.bson.types.ObjectId
import org.springframework.data.repository.kotlin.CoroutineCrudRepository
import org.springframework.stereotype.Repository

@Repository
interface ImpactRepository: CoroutineCrudRepository<Impact, ObjectId>