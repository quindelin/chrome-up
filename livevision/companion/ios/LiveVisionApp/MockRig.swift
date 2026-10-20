import Foundation
import MWDATMockDevice

/// DAT's Mock Device Kit: a simulated Ray-Ban Meta, already registered,
/// powered on and worn, whose camera plays MockGlassesFeed.mp4 (a 720x1280
/// 30 fps HEVC test pattern: the mock hands the file's samples through as-is,
/// so it must be hvc1 to match the camera config). The rest of the app cannot tell it from real
/// glasses, so the whole pipeline - session, camera, uplink, battery - runs
/// in the Simulator.
@MainActor
enum MockRig {
    private static var glasses: (any MockGlasses)?

    static func enable() throws {
        MockDeviceKit.shared.enable(config: MockDeviceKitConfig(initiallyRegistered: true, initialPermissionsGranted: true))
        guard glasses == nil else { return }
        let g = try MockDeviceKit.shared.pairGlasses(model: .rayBanMeta)
        g.powerOn()
        g.don()
        g.setBatteryLevel(73)
        g.setChargingState(.notCharging)
        glasses = g
        refeed()
    }

    /// (Re)load the test pattern into the mock camera.
    static func refeed() {
        guard let g = glasses, let feed = Bundle.main.url(forResource: "MockGlassesFeed", withExtension: "mp4") else { return }
        g.services.camera.setCameraFeed(fileURL: feed)
        log.notice("mock feed \(feed.lastPathComponent)")
    }

    static func disable() async {
        if let g = glasses { await MockDeviceKit.shared.unpairDevice(g) }
        glasses = nil
        await MockDeviceKit.shared.disable()
    }
}
