import Photos
import UIKit
#if canImport(TikTokOpenShareSDK)
import TikTokOpenSDKCore
import TikTokOpenShareSDK
#endif

/// The device half of clip posting (docs/CLIP_POSTING.md): TikTok and X are
/// not posted by the VPS. The clip is downloaded from the outbox and handed to
/// TikTok (Share Kit, or the share sheet without a client key) or to X's
/// composer through the share sheet; you finish the post in that app.
@MainActor
enum ClipShare {
    enum Outcome {
        case shared, cancelled
        case failed(String)
        /// Handed over, but TikTok never called back (no universal link set
        /// up): you say whether it posted.
        case unconfirmed

        /// What autoclip's /clips/{id}/shared takes.
        var state: String {
            switch self {
            case .shared: "shared"
            case .cancelled: "cancelled"
            case .failed, .unconfirmed: "failed"
            }
        }
        var message: String { if case .failed(let why) = self { why } else { "" } }
    }

    enum ShareError: LocalizedError {
        case download(String), photos
        var errorDescription: String? {
            switch self {
            case .download(let why): "Couldn't download the clip: \(why)"
            case .photos: "LiveVision may not add to Photos: allow it in Settings › LiveVision › Photos."
            }
        }
    }

    /// TikTok's Share Kit takes a Photos asset, so the clip goes to Photos
    /// first. The caption is copied: TikTok doesn't take one from apps.
    static func tiktok(video: URL, caption: String) async throws -> Outcome {
        let file = try await download(video)
        UIPasteboard.general.string = caption
        #if canImport(TikTokOpenShareSDK)
        if !TikTokInfo.clientKey.isEmpty, let redirect = Settings.baseURL?.appending(path: "tiktok") {
            let id = try await saveToPhotos(file)
            let outcome: Outcome = await withCheckedContinuation { cont in
                let once = Once(cont)
                let request = TikTokShareRequest(localIdentifiers: [id], mediaType: .video,
                                                 redirectURI: redirect.absoluteString)
                pendingTikTok = request          // the SDK only calls back while it is alive
                let sent = request.send { response in
                    guard let r = response as? TikTokShareResponse else { return once.resume(.unconfirmed) }
                    switch (r.errorCode, r.shareState) {
                    case (.noError, _), (_, .success), (_, .saveAsDraft): once.resume(.shared)
                    case (.cancelled, _), (_, .cancelled): once.resume(.cancelled)
                    default: once.resume(.failed(r.errorDescription ?? "TikTok said \(r.shareState.rawValue)"))
                    }
                }
                if !sent { return once.resume(.failed("TikTok isn't installed")) }
                // without a universal link TikTok's callback goes to Safari:
                // once you're back here and it hasn't come, ask instead
                once.observer = NotificationCenter.default.addObserver(
                    forName: UIApplication.didBecomeActiveNotification, object: nil, queue: .main) { _ in
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2) { once.resume(.unconfirmed) }
                }
            }
            pendingTikTok = nil
            return outcome
        }
        #endif
        return await shareSheet([file])
    }

    /// X: its composer from the share sheet, with the video and the caption.
    static func x(video: URL, caption: String) async throws -> Outcome {
        let file = try await download(video)
        UIPasteboard.general.string = caption
        return await shareSheet([caption, file])
    }

    #if canImport(TikTokOpenShareSDK)
    private static var pendingTikTok: TikTokShareRequest?
    #endif

    /// Resumes a continuation exactly once: TikTok's callback and coming
    /// back to the app race.
    private final class Once: @unchecked Sendable {
        private var cont: CheckedContinuation<Outcome, Never>?
        var observer: NSObjectProtocol?
        init(_ cont: CheckedContinuation<Outcome, Never>) { self.cont = cont }
        func resume(_ outcome: Outcome) {
            guard let c = cont else { return }
            cont = nil
            if let observer { NotificationCenter.default.removeObserver(observer) }
            c.resume(returning: outcome)
        }
    }

    /// TikTok's callback (universal link or URL scheme). True if it was TikTok's.
    nonisolated static func handle(url: URL) -> Bool {
        #if canImport(TikTokOpenShareSDK)
        return TikTokURLHandler.handleOpenURL(url)
        #else
        return false
        #endif
    }

    // MARK: plumbing

    private static func download(_ url: URL) async throws -> URL {
        let (tmp, resp): (URL, URLResponse)
        do { (tmp, resp) = try await URLSession.shared.download(from: url) } catch {
            throw ShareError.download(error.localizedDescription)
        }
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(code) else { throw ShareError.download("HTTP \(code)") }
        // a real .mp4 name: share targets look at the extension
        let dest = FileManager.default.temporaryDirectory.appending(path: url.lastPathComponent)
        try? FileManager.default.removeItem(at: dest)
        try FileManager.default.moveItem(at: tmp, to: dest)
        return dest
    }

    private static func saveToPhotos(_ file: URL) async throws -> String {
        let status = await PHPhotoLibrary.requestAuthorization(for: .addOnly)
        guard status == .authorized || status == .limited else { throw ShareError.photos }
        final class Box: @unchecked Sendable { var id: String? }
        let box = Box()
        try await PHPhotoLibrary.shared().performChanges {
            box.id = PHAssetChangeRequest.creationRequestForAssetFromVideo(atFileURL: file)?
                .placeholderForCreatedAsset?.localIdentifier
        }
        guard let id = box.id else { throw ShareError.photos }
        return id
    }

    private static func shareSheet(_ items: [Any]) async -> Outcome {
        guard let top = topController() else { return .failed("no window to share from") }
        return await withCheckedContinuation { done in
            let sheet = UIActivityViewController(activityItems: items, applicationActivities: nil)
            sheet.completionWithItemsHandler = { _, completed, _, error in
                if let error { done.resume(returning: .failed(error.localizedDescription)) }
                else { done.resume(returning: completed ? .shared : .cancelled) }
            }
            sheet.popoverPresentationController?.sourceView = top.view
            top.present(sheet, animated: true)
        }
    }

    private static func topController() -> UIViewController? {
        let scene = UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }
            .first { $0.activationState == .foregroundActive }
        var top = scene?.keyWindow?.rootViewController
        while let next = top?.presentedViewController { top = next }
        return top
    }
}
