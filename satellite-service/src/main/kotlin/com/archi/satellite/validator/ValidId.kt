package com.archi.satellite.validator

import jakarta.validation.Constraint
import jakarta.validation.ConstraintValidator
import jakarta.validation.ConstraintValidatorContext
import jakarta.validation.Payload
import org.bson.types.ObjectId
import kotlin.reflect.KClass


class IdValidator : ConstraintValidator<ValidId, String> {
    override fun isValid(value: String?, context: ConstraintValidatorContext?): Boolean {
        if (value.isNullOrBlank()) return false
        return ObjectId.isValid(value)
    }
}

@Target(AnnotationTarget.FIELD, AnnotationTarget.VALUE_PARAMETER)
@Retention(AnnotationRetention.RUNTIME)
@Constraint(validatedBy = [IdValidator::class])
annotation class ValidId(
    val message: String = "Invalid ObjectId",
    val groups: Array<KClass<*>> = [],
    val payload: Array<KClass<out Payload>> = []
)
