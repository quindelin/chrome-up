import java.util.Properties
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// DAT attestation credentials live in local.properties (never committed):
//   mwdat_application_id=...
//   mwdat_client_token=...
// Leave them out while the Meta AI app is in Developer Mode - attestation is
// skipped there and "0" is accepted.
val localProperties = Properties().apply {
    val file = rootDir.resolve("local.properties")
    if (file.exists()) file.inputStream().use { load(it) }
}

android {
    namespace = "com.lingualens.glasses"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.lingualens.glasses"
        minSdk = 31           // DAT requires Android 12+ (BLUETOOTH_CONNECT, setCommunicationDevice)
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"

        manifestPlaceholders["mwdat_application_id"] =
            localProperties.getProperty("mwdat_application_id", "0")
        manifestPlaceholders["mwdat_client_token"] =
            localProperties.getProperty("mwdat_client_token", "0")
    }

    buildFeatures { viewBinding = true }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    packaging { resources { excludes += "/META-INF/{AL2.0,LGPL2.1}" } }
}

kotlin { compilerOptions { jvmTarget = JvmTarget.JVM_17 } }

dependencies {
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-ktx:1.9.2")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.6")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.constraintlayout:constraintlayout:2.2.0")

    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")

    testImplementation("junit:junit:4.13.2")

    // ---- Meta Wearables Device Access Toolkit (DAT) ----
    // Every artifact must share one version. 1.0.1 matches Meta's
    // DisplayAccess sample (samples/DisplayAccess/gradle/libs.versions.toml).
    val mwdat = "1.0.1"
    implementation("com.meta.wearable:mwdat-core:$mwdat")
    implementation("com.meta.wearable:mwdat-display:$mwdat")
    // MockDeviceKit: a simulated Ray-Ban Display for testing with no hardware
    implementation("com.meta.wearable:mwdat-mockdevice:$mwdat")
    // RF scope heading from the glasses IMU (rf/MotionSource.kt), when wired:
    // implementation("com.meta.wearable:mwdat-motion:$mwdat")
}
