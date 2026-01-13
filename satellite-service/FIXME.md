# Hey Thomas 👋

J'ai essaye de build ton service et ca compile pas. Voici les trucs a fix enfin selon chatgpt vu que je comprend rien à tout code (t nul bouuuuuuuu) :

## 1. Erreur de compilation dans OwmService.kt

**Fichier :** `src/main/kotlin/com/archi/satellite/service/OwmService.kt`

**Ligne 16 :** `java.lang.Math.powExact` n'existe pas en Java

**Fix :** Supprimer cette ligne (elle est pas utilisee) :
```kotlin
// Supprimer ca :
import java.lang.Math.powExact
```

**Autres imports inutilises a supprimer (ligne 4, 15) :**
```kotlin
import io.netty.handler.codec.bytes.ByteArrayEncoder  // pas utilise
import java.lang.Math.pow  // doublon avec kotlin.math.pow
```

**Import duplique (ligne 9 et 13) :**
- `bodyToMono` est importe 2 fois

## 2. Ajouter un Dockerfile

Ton service a pas de Dockerfile. En voici un qui marche :

```dockerfile
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app
COPY . .
RUN chmod +x mvnw && ./mvnw package -DskipTests

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

## 3. Endpoint a finir

Dans `SatelliteController.kt` tu as un `TODO()` :
```kotlin
@GetMapping("/tiles/impacts/{impactId}")
suspend fun getSatelliteTile(...) = TODO()
```

Faut l'implementer pour que l'impact-service puisse recuperer les tuiles.

---

Une fois que c'est fait, dis-moi et j'integre ton service dans le docker-compose global !

- Clovis
