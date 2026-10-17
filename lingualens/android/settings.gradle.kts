pluginManagement {
    repositories {
        google { content { includeGroupByRegex("com\\.android.*"); includeGroupByRegex("com\\.google.*"); includeGroupByRegex("androidx.*") } }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        // Meta Wearables Device Access Toolkit (DAT) is on Maven Central:
        // com.meta.wearable:mwdat-core / -display / -mockdevice / ...
    }
}

rootProject.name = "LinguaLens"
include(":app")
