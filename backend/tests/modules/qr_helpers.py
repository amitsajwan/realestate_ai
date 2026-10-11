"""Reading a rendered QR code back, as a phone camera would (the MahaRERA badge tests, AR-3)."""
import cv2
import numpy as np


def decode(img) -> str:
    """The text of the QR code in a PIL image, or ''. OpenCV's classic detector first, then its ArUco-based one: either may
    miss a code the other reads (a phone's scanner reads both)."""
    a = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
    for det in (cv2.QRCodeDetector(), cv2.QRCodeDetectorAruco()):
        text, _, _ = det.detectAndDecode(a)
        if text:
            return text
    return ""
