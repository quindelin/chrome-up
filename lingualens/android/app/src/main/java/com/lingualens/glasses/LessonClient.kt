package com.lingualens.glasses

import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

/**
 * Talks to the LinguaLens server. Every call maps 1:1 to a route in
 * server/main.py, so the wrapper is a thin client - the curriculum and the
 * gate live server-side.
 */
class LessonClient(
    private val baseUrl: String,
    private val clientId: String
) {
    private val http = OkHttpClient.Builder()
        .callTimeout(60, TimeUnit.SECONDS)
        .build()

    fun state(): JSONObject = get("/api/state")

    fun course(): JSONObject = get("/api/course")

    fun next(): JSONObject = form("/api/next")

    fun startLesson(lessonId: Int): JSONObject =
        form("/api/lesson/start", "lesson_id" to lessonId.toString())

    fun review(): JSONObject = form("/api/review/start", "limit" to "20")

    fun think(text: String): JSONObject = form("/api/think", "text" to text)

    fun simulate(quality: String): JSONObject = form("/api/attempt/sim", "quality" to quality)

    /** Uploads one WAV attempt and returns the grade. */
    fun submit(wav: ByteArray): JSONObject {
        val body = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("client_id", clientId)
            .addFormDataPart("encoding", "wav")
            .addFormDataPart(
                "file", "attempt.wav",
                wav.toRequestBody("audio/wav".toMediaType())
            )
            .build()
        val request = Request.Builder().url("$baseUrl/api/attempt").post(body).build()
        http.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IOException("attempt failed: ${response.code}")
            return JSONObject(response.body!!.string())
        }
    }

    private fun get(path: String): JSONObject {
        val request = Request.Builder().url("$baseUrl$path?client_id=$clientId").get().build()
        http.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IOException("$path failed: ${response.code}")
            return JSONObject(response.body!!.string())
        }
    }

    private fun form(path: String, vararg fields: Pair<String, String>): JSONObject {
        val body = FormBody.Builder().add("client_id", clientId)
        fields.forEach { (k, v) -> body.add(k, v) }
        val request = Request.Builder().url("$baseUrl$path").post(body.build()).build()
        http.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IOException("$path failed: ${response.code}")
            return JSONObject(response.body!!.string())
        }
    }
}
