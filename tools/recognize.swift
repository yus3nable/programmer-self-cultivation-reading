import Foundation
import Vision
import ImageIO

// Local, resumable OCR. Coordinates use the original image's top-left origin.
let args = CommandLine.arguments
guard args.count == 5 else {
    fatalError("usage: recognize <images-dir> <output-dir> <first-page> <last-page>")
}
let images = URL(fileURLWithPath: args[1])
let output = URL(fileURLWithPath: args[2])
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
for number in Int(args[3])!...Int(args[4])! {
    let name = String(format: "p%04d", number)
    let destination = output.appendingPathComponent(name + ".json")
    if FileManager.default.fileExists(atPath: destination.path) { continue }
    try autoreleasepool {
        let input = images.appendingPathComponent(name + ".png")
        guard let source = CGImageSourceCreateWithURL(input as CFURL, nil),
              let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
            throw NSError(domain: "OCR", code: number, userInfo: [NSLocalizedDescriptionKey: "Cannot load image"])
        }
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = ["zh-Hans", "en-US"]
        request.usesLanguageCorrection = false
        request.minimumTextHeight = 0.003
        try VNImageRequestHandler(cgImage: image).perform([request])
        let lines: [[String: Any]] = (request.results ?? []).compactMap { observation in
            guard let text = observation.topCandidates(1).first else { return nil }
            let box = observation.boundingBox
            return ["text": text.string, "confidence": text.confidence,
                    "bbox": [box.minX * Double(image.width), (1 - box.maxY) * Double(image.height),
                             box.maxX * Double(image.width), (1 - box.minY) * Double(image.height)]]
        }
        let data = try JSONSerialization.data(withJSONObject: ["page": number, "width": image.width,
                        "height": image.height, "engine": "Apple Vision accurate zh-Hans en-US", "lines": lines], options: [.sortedKeys])
        try data.write(to: destination, options: .atomic)
        print("OCR \(number): \(lines.count) lines")
        fflush(stdout)
    }
}
