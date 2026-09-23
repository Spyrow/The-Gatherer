import argparse
import time
import os
import cv2
from window_capture import WindowCapture

LABELS = ["rock", "copper", "tin", "iron", "titanium", "runite", "meteorite",
          "log", "oak", "pine", "cedar", "bloodoak", "fibre"]

def main():
    parser = argparse.ArgumentParser(description="Capture Albion screenshots to build a YOLO dataset")
    parser.add_argument("--res", default="1024x720", help="Game resolution, e.g. 1280x720")
    parser.add_argument("--labels", nargs="+", default=LABELS,
                        help="Class names to cycle through (default: gathering resources)")
    parser.add_argument("--out", default="dataset", help="Output folder")
    args = parser.parse_args()

    width, height = [int(v) for v in args.res.split("x")]
    labels = args.labels
    label_index = 0
    wincap = WindowCapture(None, width=width, height=height)

    dataset_dir = args.out
    os.makedirs(dataset_dir, exist_ok=True)

    print(f"Resolution: {args.res} | Labels: {', '.join(labels)}")
    print("Keys: [s]/[space] save | [n] next class | [p] previous class | [q] quit")
    print(f"Current class: {labels[label_index]}")

    while True:
        frame = wincap.get_screenshot()

        label = labels[label_index]
        cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        cv2.imshow("Capture dataset", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break
        elif key == ord("n"):
            label_index = (label_index + 1) % len(labels)
            print(f"Current class: {labels[label_index]}")
        elif key == ord("p"):
            label_index = (label_index - 1) % len(labels)
            print(f"Current class: {labels[label_index]}")
        elif key == ord("s") or key == ord(" "):
            save_dir = os.path.join(dataset_dir, label)
            os.makedirs(save_dir, exist_ok=True)
            filename = os.path.join(save_dir, f"{label}_{int(time.time()*1000)}.png")
            cv2.imwrite(filename, frame)
            print(f"Saved: {filename}")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()